from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class RunAnalysisRequest(BaseModel):
    job_description_id: UUID
    resume_id: UUID | None = None
    generated_resume_id: UUID | None = None


class SkillMatchOut(BaseModel):
    skill_label: str
    status: str
    similarity_score: float
    is_verified: bool

    model_config = {"from_attributes": True}


class KeywordMatchOut(BaseModel):
    keyword: str
    status: str
    occurrences: int

    model_config = {"from_attributes": True}


class RecommendationOut(BaseModel):
    severity: str
    text: str

    model_config = {"from_attributes": True}


class ResumeAnalysisResponse(BaseModel):
    id: UUID
    job_description_id: UUID
    ats_score: int
    job_match_score: int
    completeness_score: int
    ats_components: dict
    category_scores: dict
    section_scores: dict
    skill_matches: list[SkillMatchOut]
    keyword_matches: list[KeywordMatchOut]
    recommendations: list[RecommendationOut]
    created_at: datetime

    model_config = {"from_attributes": True}
