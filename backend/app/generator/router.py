from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.common.deps import get_current_user
from app.users.models import User
from app.templates.registry import list_templates
from app.documents.pdf_export import render_resume_pdf
from app.documents.docx_export import render_resume_docx
from app.generator.schemas import (
    GenerateResumeRequest,
    GeneratedResumeResponse,
    ImproveBulletRequest,
    ImproveBulletResponse,
    UpdateGeneratedResumeRequest,
)
from app.generator import service
from app.common.rate_limit import rate_limit

router = APIRouter(prefix="/api/generator", tags=["generator"])


@router.get("/templates")
def templates():
    return list_templates()


@router.post("/generate", response_model=GeneratedResumeResponse, status_code=201, dependencies=[Depends(rate_limit("ai_generate", max_requests=20, window_seconds=60))])
def generate(data: GenerateResumeRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return service.generate_resume(db, current_user.id, data)


@router.get("/resumes", response_model=list[GeneratedResumeResponse])
def list_mine(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return service.list_generated_resumes(db, current_user.id)


@router.get("/resumes/{resume_id}", response_model=GeneratedResumeResponse)
def get_one(resume_id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return service.get_generated_resume_or_404(db, current_user.id, resume_id)


@router.put("/resumes/{resume_id}", response_model=GeneratedResumeResponse)
def update(resume_id: UUID, data: UpdateGeneratedResumeRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return service.update_generated_resume(db, current_user.id, resume_id, data.content, data.version_name)


@router.post("/resumes/{resume_id}/reanalyze", response_model=GeneratedResumeResponse)
def reanalyze(resume_id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return service.reanalyze_generated_resume(db, current_user.id, resume_id)


@router.post("/resumes/{resume_id}/duplicate", response_model=GeneratedResumeResponse, status_code=201)
def duplicate(resume_id: UUID, new_name: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return service.duplicate_generated_resume(db, current_user.id, resume_id, new_name)


@router.put("/resumes/{resume_id}/rename", response_model=GeneratedResumeResponse)
def rename(resume_id: UUID, new_name: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return service.rename_generated_resume(db, current_user.id, resume_id, new_name)


@router.delete("/resumes/{resume_id}", status_code=204)
def delete(resume_id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    service.delete_generated_resume(db, current_user.id, resume_id)


@router.post("/improve-bullet", response_model=ImproveBulletResponse, dependencies=[Depends(rate_limit("ai_improve", max_requests=30, window_seconds=60))])
def improve_bullet(data: ImproveBulletRequest, current_user: User = Depends(get_current_user)):
    return service.improve_bullet(data.text, data.mode, data.context)


@router.get("/resumes/{resume_id}/export/pdf")
def export_pdf(resume_id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    resume = service.get_generated_resume_or_404(db, current_user.id, resume_id)
    pdf_bytes = render_resume_pdf(resume.content, resume.template_slug)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{resume.version_name}.pdf"'},
    )


@router.get("/resumes/{resume_id}/export/docx")
def export_docx(resume_id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    resume = service.get_generated_resume_or_404(db, current_user.id, resume_id)
    docx_bytes = render_resume_docx(resume.content)
    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{resume.version_name}.docx"'},
    )
