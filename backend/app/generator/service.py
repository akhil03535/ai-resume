from sqlalchemy.orm import Session

from app.common.exceptions import AppError, NotFoundError
from app.ai.factory import get_ai_provider
from app.jobs.models import JobDescription
from app.profiles.service import get_profile_or_404, profile_to_dict
from app.resumes.models import GeneratedResume
from app.skills.service import eligible_skills_for_generation
from app.generator.schemas import GenerateResumeRequest
from app.analysis.service import run_analysis


def _prioritize(items: list[dict], jd_text: str, text_key: str) -> list[dict]:
    """Cheap relevance sort - items whose text overlaps more with the JD move
    first, without ever adding or removing facts (spec #18: 'prioritize
    information relevant to the JD')."""
    from app.analysis.scoring import token_overlap_score

    def score(item):
        return token_overlap_score(jd_text[:2000], item.get(text_key, "") or "")

    return sorted(items, key=score, reverse=True)


def generate_resume(db: Session, user_id, data: GenerateResumeRequest) -> GeneratedResume:
    jd = db.get(JobDescription, data.job_description_id)
    if not jd or jd.user_id != user_id:
        raise NotFoundError("Job description not found.")

    profile = get_profile_or_404(db, user_id)
    profile_dict = profile_to_dict(profile)
    eligible = eligible_skills_for_generation(profile)

    allowed_skill_names = {s["name"] for s in eligible["verified"]}
    # BASIC-only skills are excluded from the main skills list per spec #3 -
    # they may only appear in a separate "technical exposure" bucket, which
    # the frontend can render from `content.technical_exposure`.
    content = {
        "personal_information": profile_dict["personal_information"],
        "skills": [s for s in profile_dict["skills"] if s in allowed_skill_names] if "skills" in data.sections else [],
        "technical_exposure": [s["name"] for s in eligible["basic"]],
        "experience": _prioritize(profile_dict["experience"], jd.raw_text, "title") if "experience" in data.sections else [],
        "projects": _prioritize(profile_dict["projects"], jd.raw_text, "description") if "projects" in data.sections else [],
        "education": profile_dict["education"] if "education" in data.sections else [],
        "certifications": profile_dict["certifications"] if "certifications" in data.sections else [],
        "achievements": profile_dict["achievements"] if "achievements" in data.sections else [],
        "links": profile_dict["links"],
    }

    if "summary" in data.sections:
        provider = get_ai_provider()
        try:
            content["summary"] = provider.generate_summary(
                profile_facts={
                    "headline": profile_dict["personal_information"]["headline"],
                    "skills": content["skills"],
                    "top_experience": content["experience"][:2],
                    "top_projects": content["projects"][:2],
                },
                jd_context={"role_title": jd.role_title, "domain": jd.domain},
            )
        except Exception:
            content["summary"] = profile_dict.get("summary") or ""
    else:
        content["summary"] = ""

    generated = GeneratedResume(
        user_id=user_id,
        job_description_id=jd.id,
        template_slug=data.template_slug,
        version_name=data.version_name,
        target_role=data.target_role,
        target_company=data.target_company,
        content=content,
    )
    db.add(generated)
    db.flush()

    # Score the freshly generated resume against the same JD immediately so
    # the editor can show a live ATS/job-match score (spec #20, #22).
    generated_analysis = run_analysis(db, user_id, jd.id, generated_resume_id=generated.id)
    generated.ats_score = generated_analysis.ats_score
    generated.job_match_score = generated_analysis.job_match_score
    db.flush()
    return generated


def get_generated_resume_or_404(db: Session, user_id, resume_id) -> GeneratedResume:
    resume = db.get(GeneratedResume, resume_id)
    if not resume or resume.user_id != user_id:
        raise NotFoundError("Generated resume not found.")
    return resume


def update_generated_resume(db: Session, user_id, resume_id, content: dict, version_name: str | None) -> GeneratedResume:
    resume = get_generated_resume_or_404(db, user_id, resume_id)
    resume.content = content
    if version_name:
        resume.version_name = version_name
    db.flush()
    return resume


def reanalyze_generated_resume(db: Session, user_id, resume_id) -> GeneratedResume:
    resume = get_generated_resume_or_404(db, user_id, resume_id)
    if resume.ats_score is not None and resume.source_ats_score is None:
        resume.source_ats_score = resume.ats_score
    analysis = run_analysis(db, user_id, resume.job_description_id, generated_resume_id=resume.id)
    resume.ats_score = analysis.ats_score
    resume.job_match_score = analysis.job_match_score
    db.flush()
    return resume


def duplicate_generated_resume(db: Session, user_id, resume_id, new_name: str) -> GeneratedResume:
    original = get_generated_resume_or_404(db, user_id, resume_id)
    copy = GeneratedResume(
        user_id=user_id,
        job_description_id=original.job_description_id,
        template_slug=original.template_slug,
        version_name=new_name,
        target_role=original.target_role,
        target_company=original.target_company,
        content=original.content,
        ats_score=original.ats_score,
        job_match_score=original.job_match_score,
    )
    db.add(copy)
    db.flush()
    return copy


def rename_generated_resume(db: Session, user_id, resume_id, new_name: str) -> GeneratedResume:
    resume = get_generated_resume_or_404(db, user_id, resume_id)
    resume.version_name = new_name
    db.flush()
    return resume


def delete_generated_resume(db: Session, user_id, resume_id) -> None:
    resume = get_generated_resume_or_404(db, user_id, resume_id)
    db.delete(resume)
    db.flush()


def list_generated_resumes(db: Session, user_id) -> list[GeneratedResume]:
    return list(
        db.query(GeneratedResume).filter(GeneratedResume.user_id == user_id).order_by(GeneratedResume.created_at.desc()).all()
    )


def improve_bullet(text: str, mode: str, context: str | None):
    provider = get_ai_provider()
    return provider.improve_bullet(text, mode, context)
