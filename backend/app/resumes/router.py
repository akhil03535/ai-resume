from uuid import UUID

from fastapi import APIRouter, Depends, UploadFile
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.common.deps import get_current_user
from app.users.models import User
from app.resumes.schemas import ResumeParseResponse, ResumeResponse
from app.resumes import service
from app.common.rate_limit import rate_limit

router = APIRouter(prefix="/api/resumes", tags=["resumes"])


@router.post("/upload", response_model=ResumeResponse, status_code=201)
def upload(
    file: UploadFile,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    resume = service.upload_resume(db, current_user.id, file)
    return resume


@router.get("", response_model=list[ResumeResponse])
def list_my_resumes(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return service.list_resumes(db, current_user.id)


@router.get("/{resume_id}", response_model=ResumeResponse)
def get_resume(resume_id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return service.get_resume_or_404(db, current_user.id, resume_id)


@router.post("/{resume_id}/parse", response_model=ResumeParseResponse, dependencies=[Depends(rate_limit("ai_parse", max_requests=20, window_seconds=60))])
def parse(resume_id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    resume, updated = service.parse_resume(db, current_user.id, resume_id)
    return ResumeParseResponse(resume=resume, profile_updated=updated)
