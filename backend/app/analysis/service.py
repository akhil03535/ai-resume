import re

from sqlalchemy.orm import Session

from app.common.exceptions import AppError, NotFoundError
from app.jobs.models import JobDescription, JobRequirement, RequirementImportance, RequirementType
from app.profiles.models import SkillVerificationStatus
from app.profiles.service import get_profile_or_404, profile_to_dict
from app.resumes.models import GeneratedResume
from app.analysis.models import (
    KeywordMatch,
    MatchStatus,
    Recommendation,
    RecommendationSeverity,
    ResumeAnalysis,
    SkillMatch,
)
from app.analysis import scoring


def _resume_body_text(profile_dict: dict, skill_labels: list[str]) -> str:
    """Flattened text used for token-overlap/semantic matching against JD
    requirements. Takes the caller's already-REJECTED-filtered skill_labels
    rather than profile_dict['skills'] directly - profile_dict includes every
    candidate_skill regardless of verification status, and including a
    rejected skill's name in this text would let it re-enter matching via
    the token-overlap/semantic fallback paths even though it's explicitly
    excluded from the exact-match candidate_skill_labels check elsewhere.
    A rejected skill must never count as matched, in the dashboard or
    anywhere else (see spec: 'a rejected skill must never leak')."""
    parts = [profile_dict.get("summary") or ""]
    for exp in profile_dict["experience"]:
        parts.append(exp["title"])
        parts.append(exp["company"])
        parts.extend(exp["bullets"])
        parts.extend(exp["technologies"])
    for proj in profile_dict["projects"]:
        parts.append(proj["name"])
        parts.append(proj["description"] or "")
        parts.extend(proj["bullets"])
        parts.extend(proj["technologies"])
    parts.extend(skill_labels)
    return "\n".join(p for p in parts if p)


def run_analysis(db: Session, user_id, jd_id, resume_id=None, generated_resume_id=None) -> ResumeAnalysis:
    jd = db.get(JobDescription, jd_id)
    if not jd or jd.user_id != user_id:
        raise NotFoundError("Job description not found.")
    if not jd.is_analyzed:
        raise AppError("Analyze the job description before running a match.", code="jd_not_analyzed")

    profile = get_profile_or_404(db, user_id)

    # The document actually being scored. For a generated/edited resume this
    # MUST be its own current `content` - not a fresh re-derivation from the
    # candidate profile - otherwise editing bullets, removing a skill, or any
    # other in-editor change would have zero effect on Re-analyze, silently
    # scoring stale profile data instead of what the user is looking at.
    if generated_resume_id is not None:
        generated_resume = db.get(GeneratedResume, generated_resume_id)
        if not generated_resume or generated_resume.user_id != user_id:
            raise NotFoundError("Generated resume not found.")
        resume_dict = generated_resume.content
        # The generator already filters to eligible (non-rejected) skills,
        # and edits in the editor mutate this list directly - so this is
        # exactly "what's actually on the document right now".
        skill_labels = list(resume_dict.get("skills", []))
        source_label = "this resume"
    else:
        resume_dict = profile_to_dict(profile)
        skill_labels = [
            cs.skill.name for cs in profile.candidate_skills
            if cs.verification_status != SkillVerificationStatus.REJECTED
        ]
        source_label = "your profile"

    # "is_verified" stays informational and always reflects the candidate's
    # actual verification records, regardless of which document is being
    # scored - it answers "does evidence exist for this skill", not "is it
    # currently included in this particular document".
    verified_labels = {
        cs.skill.normalized_name for cs in profile.candidate_skills
        if cs.verification_status in (SkillVerificationStatus.VERIFIED, SkillVerificationStatus.EXTRACTED)
    }
    resume_body = _resume_body_text(resume_dict, skill_labels)

    skill_reqs = [r for r in jd.requirements if r.requirement_type in (RequirementType.SKILL, RequirementType.TECHNOLOGY)]
    keyword_reqs = [r for r in jd.requirements if r.requirement_type == RequirementType.KEYWORD]

    skill_match_rows = []
    matched_required = partial_required = total_required = 0
    matched_preferred = partial_preferred = total_preferred = 0

    for req in skill_reqs:
        status, score = scoring.classify_requirement_match(req.label, skill_labels, resume_body)
        skill_match_rows.append({
            "requirement_id": req.id,
            "skill_label": req.label,
            "status": status,
            "similarity_score": round(score, 3),
            "is_verified": scoring.normalize(req.label) in verified_labels,
        })
        is_required = req.importance == RequirementImportance.REQUIRED
        if is_required:
            total_required += 1
            matched_required += 1 if status == "MATCHED" else 0
            partial_required += 1 if status == "PARTIAL" else 0
        else:
            total_preferred += 1
            matched_preferred += 1 if status == "MATCHED" else 0
            partial_preferred += 1 if status == "PARTIAL" else 0

    required_ratio = (matched_required + 0.5 * partial_required) / total_required if total_required else 1.0
    preferred_ratio = (matched_preferred + 0.5 * partial_preferred) / total_preferred if total_preferred else 1.0

    keyword_match_rows = []
    matched_kw = 0
    for req in keyword_reqs:
        occurrences = len(re.findall(re.escape(scoring.normalize(req.label)), scoring.normalize(resume_body)))
        status = "MATCHED" if occurrences > 0 else ("PARTIAL" if scoring.token_overlap_score(req.label, resume_body) >= 0.5 else "MISSING")
        if status == "MATCHED":
            matched_kw += 1
        keyword_match_rows.append({"keyword": req.label, "status": status, "occurrences": occurrences})
    keyword_ratio = matched_kw / len(keyword_reqs) if keyword_reqs else 1.0

    experience_ratio = min(1.0, scoring.token_overlap_score(jd.raw_text[:3000], resume_body) + 0.15)
    project_ratio = min(1.0, len(resume_dict["projects"]) / 3) if resume_dict["projects"] else 0.0
    education_ratio = 1.0 if resume_dict["education"] else 0.3
    formatting_ratio = scoring.compute_formatting_score(resume_body)

    section_scores = scoring.compute_section_completeness(resume_dict)
    section_completeness_ratio = sum(section_scores.values()) / (100 * len(section_scores))

    ats_components = scoring.compute_ats_components(
        required_match_ratio=required_ratio,
        preferred_match_ratio=preferred_ratio,
        keyword_coverage_ratio=keyword_ratio,
        experience_relevance_ratio=experience_ratio,
        project_relevance_ratio=project_ratio,
        section_completeness_ratio=section_completeness_ratio,
        formatting_ratio=formatting_ratio,
        education_alignment_ratio=education_ratio,
    )
    job_match_score = scoring.compute_job_match_score(required_ratio, preferred_ratio, experience_ratio)
    completeness_score = round(section_completeness_ratio * 100)

    category_scores = {
        "skills": round((required_ratio * 0.7 + preferred_ratio * 0.3) * 100),
        "keywords": round(keyword_ratio * 100),
        "experience": round(experience_ratio * 100),
        "projects": round(project_ratio * 100),
        "education": round(education_ratio * 100),
        "formatting": round(formatting_ratio * 100),
    }

    analysis = ResumeAnalysis(
        user_id=user_id,
        resume_id=resume_id,
        generated_resume_id=generated_resume_id,
        job_description_id=jd_id,
        ats_score=ats_components["final_score"],
        job_match_score=job_match_score,
        completeness_score=completeness_score,
        ats_components=ats_components,
        category_scores=category_scores,
        section_scores=section_scores,
    )
    db.add(analysis)
    db.flush()

    for row in skill_match_rows:
        db.add(SkillMatch(analysis_id=analysis.id, status=MatchStatus(row["status"]), **{
            k: v for k, v in row.items() if k != "status"
        }))
    for row in keyword_match_rows:
        db.add(KeywordMatch(analysis_id=analysis.id, status=MatchStatus(row["status"]), **{
            k: v for k, v in row.items() if k != "status"
        }))

    for rec in _build_recommendations(skill_match_rows, keyword_match_rows, section_scores, ats_components, source_label):
        db.add(Recommendation(analysis_id=analysis.id, severity=rec[0], text=rec[1]))

    db.flush()
    return analysis


def _build_recommendations(skill_rows, keyword_rows, section_scores, ats_components, source_label: str = "your profile") -> list[tuple]:
    """Rule-based (not LLM-generated) so recommendations are always grounded
    in the actual computed matches - see spec #17: 'not generic motivational text'."""
    recs = []

    strong_skills = [r["skill_label"] for r in skill_rows if r["status"] == "MATCHED"]
    if strong_skills:
        preview = ", ".join(strong_skills[:3])
        recs.append((RecommendationSeverity.STRENGTH, f"Strong alignment on {preview}."))

    missing_required = [r["skill_label"] for r in skill_rows if r["status"] == "MISSING"]
    for skill in missing_required[:5]:
        recs.append((RecommendationSeverity.ISSUE, f"{skill} was not found in {source_label}. Consider whether you have relevant experience to verify."))

    unverified = [r["skill_label"] for r in skill_rows if r["status"] == "MATCHED" and not r["is_verified"]]
    for skill in unverified[:3]:
        recs.append((RecommendationSeverity.ISSUE, f"{skill} appears in your resume but hasn't been explicitly verified."))

    missing_keywords = [r["keyword"] for r in keyword_rows if r["status"] == "MISSING"]
    if missing_keywords:
        preview = ", ".join(missing_keywords[:5])
        recs.append((RecommendationSeverity.SUGGESTION, f"Improve keyword coverage for: {preview}."))

    weak_sections = [name for name, score in section_scores.items() if score < 50]
    for section in weak_sections:
        recs.append((RecommendationSeverity.SUGGESTION, f"Your {section} section is underdeveloped - add more detail."))

    if ats_components["formatting"] < 70:
        recs.append((RecommendationSeverity.SUGGESTION, "Simplify formatting to improve ATS parsing reliability."))

    return recs


def list_analyses_for_jd(db: Session, user_id, jd_id) -> list[ResumeAnalysis]:
    return list(
        db.query(ResumeAnalysis)
        .filter(ResumeAnalysis.user_id == user_id, ResumeAnalysis.job_description_id == jd_id)
        .order_by(ResumeAnalysis.created_at.desc())
        .all()
    )


def get_analysis_or_404(db: Session, user_id, analysis_id) -> ResumeAnalysis:
    analysis = db.get(ResumeAnalysis, analysis_id)
    if not analysis or analysis.user_id != user_id:
        raise NotFoundError("Analysis not found.")
    return analysis
