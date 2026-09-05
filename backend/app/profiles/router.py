from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.common.deps import get_current_user
from app.users.models import User
from app.profiles.models import CandidateProfile
from app.profiles.schemas import CandidateProfileResponse, CandidateProfileUpdateRequest
from app.profiles import service

router = APIRouter(prefix="/api/profile", tags=["profile"])


def _serialize(profile: CandidateProfile) -> dict:
    data = CandidateProfileResponse.model_validate(profile, from_attributes=True).model_dump()
    data["candidate_skills"] = [
        {
            "id": cs.id,
            "skill_name": cs.skill.name,
            "proficiency": cs.proficiency,
            "source": cs.source.value,
            "verification_status": cs.verification_status.value,
        }
        for cs in profile.candidate_skills
    ]
    return data


@router.get("", response_model=CandidateProfileResponse)
def get_my_profile(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = service.get_or_create_profile(db, current_user.id)
    return _serialize(profile)


@router.put("", response_model=CandidateProfileResponse)
def update_my_profile(
    data: CandidateProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = service.get_or_create_profile(db, current_user.id)
    profile = service.replace_profile_children(db, profile, data)
    return _serialize(profile)
