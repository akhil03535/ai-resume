import hashlib

from sqlalchemy.orm import Session

from app.common.exceptions import NotFoundError
from app.core.redis import cache_get, cache_set
from app.ai.factory import get_ai_provider
from app.analysis.scoring import normalize
from app.jobs.models import JobDescription, JobRequirement, RequirementImportance, RequirementType
from app.jobs.schemas import JobDescriptionCreateRequest


def create_job_description(db: Session, user_id, data: JobDescriptionCreateRequest) -> JobDescription:
    jd = JobDescription(
        user_id=user_id, title=data.title, company_name=data.company_name, raw_text=data.raw_text
    )
    db.add(jd)
    db.flush()
    return jd


def get_jd_or_404(db: Session, user_id, jd_id) -> JobDescription:
    jd = db.get(JobDescription, jd_id)
    if not jd or jd.user_id != user_id:
        raise NotFoundError("Job description not found.")
    return jd


def analyze_job_description(db: Session, user_id, jd_id) -> JobDescription:
    jd = get_jd_or_404(db, user_id, jd_id)

    cache_key = f"jd_analysis:{hashlib.sha256(jd.raw_text.encode()).hexdigest()}"
    cached = cache_get(cache_key)

    if cached:
        from app.ai.schemas import AnalyzedJobDescription
        analyzed = AnalyzedJobDescription.model_validate(cached)
    else:
        provider = get_ai_provider()
        analyzed = provider.analyze_job_description(jd.raw_text)
        cache_set(cache_key, analyzed.model_dump(mode="json"), ttl_seconds=60 * 60 * 24)

    jd.role_title = analyzed.role_title
    jd.domain = analyzed.domain
    jd.experience_requirement = analyzed.experience_requirement
    jd.education_requirement = analyzed.education_requirement
    jd.responsibilities = analyzed.responsibilities
    jd.is_analyzed = True

    jd.requirements.clear()
    db.flush()

    for req in analyzed.requirements:
        req_type = req.type.upper() if req.type.upper() in RequirementType.__members__ else "KEYWORD"
        importance = req.importance.upper() if req.importance.upper() in RequirementImportance.__members__ else "PREFERRED"
        db.add(JobRequirement(
            job_description_id=jd.id,
            label=req.label,
            normalized_label=normalize(req.label),
            requirement_type=RequirementType(req_type),
            importance=RequirementImportance(importance),
        ))

    db.flush()
    return jd


def list_job_descriptions(db: Session, user_id) -> list[JobDescription]:
    return list(
        db.query(JobDescription).filter(JobDescription.user_id == user_id).order_by(JobDescription.created_at.desc()).all()
    )
