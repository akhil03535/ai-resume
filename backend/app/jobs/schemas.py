from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class JobDescriptionCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    company_name: str | None = None
    raw_text: str = Field(min_length=20)


class JobRequirementResponse(BaseModel):
    id: UUID
    label: str
    requirement_type: str
    importance: str

    model_config = {"from_attributes": True}


class JobDescriptionResponse(BaseModel):
    id: UUID
    title: str
    company_name: str | None
    raw_text: str
    role_title: str | None
    domain: str | None
    experience_requirement: str | None
    education_requirement: str | None
    responsibilities: list[str]
    is_analyzed: bool
    requirements: list[JobRequirementResponse] = []
    created_at: datetime

    model_config = {"from_attributes": True}
