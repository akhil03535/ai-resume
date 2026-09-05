from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class GenerateResumeRequest(BaseModel):
    job_description_id: UUID
    template_slug: str = "ats_classic"
    version_name: str = Field(min_length=1, max_length=255)
    target_role: str | None = None
    target_company: str | None = None
    sections: list[str] = Field(
        default_factory=lambda: ["summary", "skills", "experience", "projects", "education", "certifications", "achievements"]
    )


class GeneratedResumeResponse(BaseModel):
    id: UUID
    version_name: str
    template_slug: str
    target_role: str | None
    target_company: str | None
    content: dict
    ats_score: int | None
    job_match_score: int | None
    source_ats_score: int | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ImproveBulletRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2000)
    mode: str = "improve"  # improve | concise | ats_friendly | technical | impact
    context: str | None = None


class ImproveBulletResponse(BaseModel):
    improved_text: str
    notes: str | None = None


class UpdateGeneratedResumeRequest(BaseModel):
    content: dict
    version_name: str | None = None
