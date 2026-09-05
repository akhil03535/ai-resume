from uuid import UUID

from pydantic import BaseModel, Field


class EvidenceInput(BaseModel):
    source_type: str  # PROJECT | INTERNSHIP | WORK | COURSE | OTHER
    description: str = Field(min_length=5, max_length=1000)


class SkillVerifyRequest(BaseModel):
    skill_name: str
    answer: str  # "yes" | "basic" | "no"
    evidence: list[EvidenceInput] = Field(default_factory=list)


class CandidateSkillOut(BaseModel):
    id: UUID
    skill_name: str
    verification_status: str
    source: str

    model_config = {"from_attributes": True}


class MissingSkillPrompt(BaseModel):
    """One 'Do you know X?' card for the frontend verification UI (spec #3)."""
    skill_name: str
    requirement_importance: str  # REQUIRED | PREFERRED
    job_requirement_id: UUID
