from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.common.deps import get_current_user
from app.users.models import User
from app.analysis.schemas import ResumeAnalysisResponse, RunAnalysisRequest
from app.analysis import service

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


@router.post("/run", response_model=ResumeAnalysisResponse, status_code=201)
def run(data: RunAnalysisRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return service.run_analysis(
        db, current_user.id, data.job_description_id, data.resume_id, data.generated_resume_id
    )


@router.get("/{analysis_id}", response_model=ResumeAnalysisResponse)
def get_one(analysis_id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return service.get_analysis_or_404(db, current_user.id, analysis_id)


@router.get("/by-job/{jd_id}", response_model=list[ResumeAnalysisResponse])
def list_for_job(jd_id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return service.list_analyses_for_jd(db, current_user.id, jd_id)
