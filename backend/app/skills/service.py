from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.exceptions import AppError, NotFoundError
from app.jobs.models import JobRequirement, RequirementImportance
from app.analysis.models import MatchStatus, SkillMatch, ResumeAnalysis
from app.profiles.models import CandidateSkill, SkillSource, SkillVerificationStatus
from app.profiles.service import get_profile_or_404, add_candidate_skill
from app.skills.models import EvidenceSourceType, SkillVerification, VerificationEvidence
from app.skills.schemas import SkillVerifyRequest


ANSWER_TO_STATUS = {
    "yes": SkillVerificationStatus.VERIFIED,
    "basic": SkillVerificationStatus.BASIC,
    "no": SkillVerificationStatus.REJECTED,
}


def get_missing_important_skills_for_analysis(db: Session, user_id, analysis_id) -> list[dict]:
    """Important (REQUIRED) skills the latest analysis flagged as MISSING,
    that the candidate hasn't already answered a verification question for
    (spec #3). Drives the interactive 'Do you know Kafka?' prompts."""
    analysis = db.get(ResumeAnalysis, analysis_id)
    if not analysis or analysis.user_id != user_id:
        raise NotFoundError("Analysis not found.")

    profile = get_profile_or_404(db, user_id)
    already_answered = {
        cs.skill.normalized_name for cs in profile.candidate_skills
        if cs.verification is not None
    }

    prompts = []
    for match in analysis.skill_matches:
        if match.status != MatchStatus.MISSING:
            continue
        requirement = db.get(JobRequirement, match.requirement_id)
        if not requirement or requirement.importance != RequirementImportance.REQUIRED:
            continue
        if requirement.normalized_label in already_answered:
            continue
        prompts.append({
            "skill_name": requirement.label,
            "requirement_importance": requirement.importance.value,
            "job_requirement_id": requirement.id,
        })
    return prompts


def submit_skill_verification(db: Session, user_id, data: SkillVerifyRequest) -> CandidateSkill:
    if data.answer not in ANSWER_TO_STATUS:
        raise AppError("answer must be one of: yes, basic, no", code="invalid_answer")

    profile = get_profile_or_404(db, user_id)
    status = ANSWER_TO_STATUS[data.answer]

    candidate_skill = add_candidate_skill(
        db, profile, data.skill_name, source=SkillSource.VERIFICATION, verification_status=status
    )
    # in case the skill already existed (e.g. EXTRACTED but user is now
    # explicitly confirming/rejecting it), always apply the latest answer
    candidate_skill.verification_status = status
    db.flush()

    # replace any prior verification record for this skill
    existing = db.scalar(
        select(SkillVerification).where(SkillVerification.candidate_skill_id == candidate_skill.id)
    )
    if existing:
        db.delete(existing)
        db.flush()

    verification = SkillVerification(candidate_skill_id=candidate_skill.id, answer=data.answer)
    db.add(verification)
    db.flush()

    if data.answer == "yes":
        if not data.evidence:
            raise AppError(
                "Please describe where and how you used this skill before it can be verified.",
                code="evidence_required",
            )
        for item in data.evidence:
            source_type = item.source_type.upper()
            if source_type not in EvidenceSourceType.__members__:
                source_type = "OTHER"
            db.add(VerificationEvidence(
                verification_id=verification.id,
                source_type=EvidenceSourceType(source_type),
                description=item.description,
            ))
        db.flush()

    return candidate_skill


def eligible_skills_for_generation(profile) -> list[dict]:
    """Skills the generator is allowed to surface as real experience, plus
    ones only eligible for a 'technical exposure' listing (spec #3/#18)."""
    verified, basic = [], []
    for cs in profile.candidate_skills:
        if cs.verification_status == SkillVerificationStatus.VERIFIED:
            evidence_text = None
            if cs.verification and cs.verification.evidence:
                evidence_text = " ".join(e.description for e in cs.verification.evidence)
            verified.append({"name": cs.skill.name, "evidence": evidence_text})
        elif cs.verification_status == SkillVerificationStatus.BASIC:
            basic.append({"name": cs.skill.name})
        elif cs.verification_status == SkillVerificationStatus.EXTRACTED:
            # extracted-but-unreviewed skills are treated as candidate-asserted
            # (they came from the candidate's own uploaded resume text) and are
            # eligible, but never override an explicit REJECTED answer.
            verified.append({"name": cs.skill.name, "evidence": None})
    return {"verified": verified, "basic": basic}
