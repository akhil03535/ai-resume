from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.common.deps import get_current_user
from app.users.models import User
from app.skills.schemas import CandidateSkillOut, MissingSkillPrompt, SkillVerifyRequest
from app.skills import service

router = APIRouter(prefix="/api/skills", tags=["skills"])


@router.get("/analyses/{analysis_id}/missing", response_model=list[MissingSkillPrompt])
def missing_skills(analysis_id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return service.get_missing_important_skills_for_analysis(db, current_user.id, analysis_id)


@router.post("/verify", response_model=CandidateSkillOut)
def verify(data: SkillVerifyRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    candidate_skill = service.submit_skill_verification(db, current_user.id, data)
    return CandidateSkillOut(
        id=candidate_skill.id,
        skill_name=candidate_skill.skill.name,
        verification_status=candidate_skill.verification_status.value,
        source=candidate_skill.source.value,
    )
