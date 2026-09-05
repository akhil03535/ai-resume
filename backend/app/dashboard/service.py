from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.analysis.models import ResumeAnalysis, Recommendation, RecommendationSeverity
from app.resumes.models import Resume, GeneratedResume
from app.profiles.service import get_or_create_profile, profile_to_dict
from app.analysis.scoring import compute_section_completeness


class DashboardResponse(BaseModel):
    latest_ats_score: int | None
    latest_job_match_score: int | None
    resume_completeness: int
    resume_count: int
    generated_resume_count: int
    recent_analyses: list[dict]
    recent_generated_resumes: list[dict]
    top_recommendations: list[dict]


def get_dashboard(db: Session, user_id) -> DashboardResponse:
    profile = get_or_create_profile(db, user_id)
    section_scores = compute_section_completeness(profile_to_dict(profile))
    completeness = round(sum(section_scores.values()) / len(section_scores))

    latest_analysis = (
        db.query(ResumeAnalysis)
        .filter(ResumeAnalysis.user_id == user_id)
        .order_by(ResumeAnalysis.created_at.desc())
        .first()
    )

    recent_analyses = (
        db.query(ResumeAnalysis)
        .filter(ResumeAnalysis.user_id == user_id)
        .order_by(ResumeAnalysis.created_at.desc())
        .limit(5)
        .all()
    )

    recent_generated = (
        db.query(GeneratedResume)
        .filter(GeneratedResume.user_id == user_id)
        .order_by(GeneratedResume.created_at.desc())
        .limit(5)
        .all()
    )

    top_recs = []
    if latest_analysis:
        top_recs = [
            {"severity": r.severity.value, "text": r.text}
            for r in latest_analysis.recommendations
            if r.severity in (RecommendationSeverity.ISSUE, RecommendationSeverity.SUGGESTION)
        ][:5]

    return DashboardResponse(
        latest_ats_score=latest_analysis.ats_score if latest_analysis else None,
        latest_job_match_score=latest_analysis.job_match_score if latest_analysis else None,
        resume_completeness=completeness,
        resume_count=db.query(Resume).filter(Resume.user_id == user_id).count(),
        generated_resume_count=db.query(GeneratedResume).filter(GeneratedResume.user_id == user_id).count(),
        recent_analyses=[
            {"id": str(a.id), "ats_score": a.ats_score, "job_match_score": a.job_match_score, "created_at": a.created_at.isoformat()}
            for a in recent_analyses
        ],
        recent_generated_resumes=[
            {"id": str(g.id), "version_name": g.version_name, "ats_score": g.ats_score, "created_at": g.created_at.isoformat()}
            for g in recent_generated
        ],
        top_recommendations=top_recs,
    )
