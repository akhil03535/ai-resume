from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.exceptions import NotFoundError
from app.ai.schemas import ParsedResume
from app.profiles.models import (
    Achievement,
    CandidateProfile,
    CandidateSkill,
    Certification,
    Education,
    Experience,
    Project,
    Skill,
    SkillSource,
    SkillVerificationStatus,
)
from app.analysis.scoring import normalize


def get_or_create_profile(db: Session, user_id) -> CandidateProfile:
    profile = db.scalar(select(CandidateProfile).where(CandidateProfile.user_id == user_id))
    if not profile:
        profile = CandidateProfile(user_id=user_id)
        db.add(profile)
        db.flush()
    return profile


def get_profile_or_404(db: Session, user_id) -> CandidateProfile:
    profile = db.scalar(select(CandidateProfile).where(CandidateProfile.user_id == user_id))
    if not profile:
        raise NotFoundError("Candidate profile not found.")
    return profile


def upsert_skill(db: Session, name: str) -> Skill:
    norm = normalize(name)
    skill = db.scalar(select(Skill).where(Skill.normalized_name == norm))
    if not skill:
        skill = Skill(name=name.strip(), normalized_name=norm)
        db.add(skill)
        db.flush()
    return skill


def add_candidate_skill(
    db: Session,
    profile: CandidateProfile,
    skill_name: str,
    source: SkillSource,
    verification_status: SkillVerificationStatus = SkillVerificationStatus.EXTRACTED,
) -> CandidateSkill:
    skill = upsert_skill(db, skill_name)
    existing = db.scalar(
        select(CandidateSkill).where(
            CandidateSkill.profile_id == profile.id, CandidateSkill.skill_id == skill.id
        )
    )
    if existing:
        return existing

    candidate_skill = CandidateSkill(
        skill_id=skill.id, source=source, verification_status=verification_status
    )
    profile.candidate_skills.append(candidate_skill)
    db.flush()
    return candidate_skill


def apply_parsed_resume(db: Session, profile: CandidateProfile, parsed: ParsedResume) -> CandidateProfile:
    """Populate the candidate profile from AI-parsed resume data. Everything
    lands with source=EXTRACTED / verification_status=EXTRACTED - nothing is
    auto-verified (spec #8: 'Do not treat an AI-extracted skill as automatically verified')."""
    info = parsed.personal_information
    profile.full_name = info.full_name or profile.full_name
    profile.headline = info.headline or profile.headline
    profile.summary = info.summary or profile.summary
    profile.email = info.email or profile.email
    profile.phone = info.phone or profile.phone
    profile.location = info.location or profile.location
    profile.links = [link.model_dump() for link in parsed.links] or profile.links

    for edu in parsed.education:
        profile.educations.append(Education(
            institution=edu.institution, degree=edu.degree,
            field_of_study=edu.field_of_study, gpa=edu.gpa,
        ))

    for exp in parsed.experience:
        profile.experiences.append(Experience(
            company=exp.company, title=exp.title, location=exp.location,
            is_current=exp.is_current, bullets=exp.bullets, technologies=exp.technologies,
        ))

    for proj in parsed.projects:
        profile.projects.append(Project(
            name=proj.name, description=proj.description,
            bullets=proj.bullets, technologies=proj.technologies, url=proj.url,
        ))

    for cert in parsed.certifications:
        profile.certifications.append(Certification(name=cert.name, issuer=cert.issuer))

    for ach in parsed.achievements:
        profile.achievements.append(Achievement(title=ach.title, description=ach.description))

    db.flush()

    for skill_name in parsed.skills:
        add_candidate_skill(db, profile, skill_name, source=SkillSource.EXTRACTED)

    # also pull in technologies mentioned inside experience/project bullets
    for exp in parsed.experience:
        for tech in exp.technologies:
            add_candidate_skill(db, profile, tech, source=SkillSource.EXTRACTED)
    for proj in parsed.projects:
        for tech in proj.technologies:
            add_candidate_skill(db, profile, tech, source=SkillSource.EXTRACTED)

    db.flush()
    return profile


def replace_profile_children(db: Session, profile: CandidateProfile, data) -> CandidateProfile:
    """Full-replace update used by the review/correction screen."""
    for field in ["full_name", "headline", "summary", "email", "phone", "location", "links"]:
        value = getattr(data, field)
        if value is not None:
            setattr(profile, field, value)

    if data.educations is not None:
        profile.educations.clear()
        db.flush()
        for e in data.educations:
            profile.educations.append(Education(profile_id=profile.id, **e.model_dump(exclude={"id"})))

    if data.experiences is not None:
        profile.experiences.clear()
        db.flush()
        for e in data.experiences:
            profile.experiences.append(Experience(profile_id=profile.id, **e.model_dump(exclude={"id"})))

    if data.projects is not None:
        profile.projects.clear()
        db.flush()
        for p in data.projects:
            profile.projects.append(Project(profile_id=profile.id, **p.model_dump(exclude={"id"})))

    if data.certifications is not None:
        profile.certifications.clear()
        db.flush()
        for c in data.certifications:
            profile.certifications.append(Certification(profile_id=profile.id, **c.model_dump(exclude={"id"})))

    if data.achievements is not None:
        profile.achievements.clear()
        db.flush()
        for a in data.achievements:
            profile.achievements.append(Achievement(profile_id=profile.id, **a.model_dump(exclude={"id"})))

    if data.skill_names is not None:
        existing_names = {cs.skill.normalized_name for cs in profile.candidate_skills}
        for name in data.skill_names:
            if normalize(name) not in existing_names:
                add_candidate_skill(db, profile, name, source=SkillSource.MANUAL, verification_status=SkillVerificationStatus.VERIFIED)

    db.flush()
    return profile


def profile_to_dict(profile: CandidateProfile) -> dict:
    """Shape used as input to the scoring engine / generator - only includes
    VERIFIED and BASIC skills' evidence where relevant; callers decide which
    skills are eligible per context (see skills/service.py, generator/service.py)."""
    return {
        "personal_information": {
            "full_name": profile.full_name,
            "email": profile.email,
            "phone": profile.phone,
            "location": profile.location,
            "headline": profile.headline,
            "summary": profile.summary,
        },
        "summary": profile.summary,
        "skills": [cs.skill.name for cs in profile.candidate_skills],
        "education": [
            {"institution": e.institution, "degree": e.degree, "field_of_study": e.field_of_study,
             "start_date": str(e.start_date) if e.start_date else None,
             "end_date": str(e.end_date) if e.end_date else None, "gpa": e.gpa}
            for e in profile.educations
        ],
        "experience": [
            {"company": e.company, "title": e.title, "location": e.location,
             "start_date": str(e.start_date) if e.start_date else None,
             "end_date": str(e.end_date) if e.end_date else None,
             "is_current": e.is_current, "bullets": e.bullets, "technologies": e.technologies}
            for e in profile.experiences
        ],
        "projects": [
            {"name": p.name, "description": p.description, "bullets": p.bullets,
             "technologies": p.technologies, "url": p.url}
            for p in profile.projects
        ],
        "certifications": [{"name": c.name, "issuer": c.issuer} for c in profile.certifications],
        "achievements": [{"title": a.title, "description": a.description} for a in profile.achievements],
        "links": profile.links or [],
    }
