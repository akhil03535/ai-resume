from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.common.deps import get_current_user
from app.users.models import User
from app.jobs.schemas import JobDescriptionCreateRequest, JobDescriptionResponse
from app.jobs import service
from app.common.rate_limit import rate_limit

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.post("", response_model=JobDescriptionResponse, status_code=201)
def create(data: JobDescriptionCreateRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return service.create_job_description(db, current_user.id, data)


@router.get("", response_model=list[JobDescriptionResponse])
def list_mine(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return service.list_job_descriptions(db, current_user.id)


@router.get("/{jd_id}", response_model=JobDescriptionResponse)
def get_one(jd_id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return service.get_jd_or_404(db, current_user.id, jd_id)


@router.post("/{jd_id}/analyze", response_model=JobDescriptionResponse, dependencies=[Depends(rate_limit("ai_analyze", max_requests=20, window_seconds=60))])
def analyze(jd_id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return service.analyze_job_description(db, current_user.id, jd_id)
