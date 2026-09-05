from datetime import date as date_type
from uuid import UUID

from pydantic import BaseModel, Field


class EducationSchema(BaseModel):
    id: UUID | None = None
    institution: str
    degree: str | None = None
    field_of_study: str | None = None
    start_date: date_type | None = None
    end_date: date_type | None = None
    gpa: str | None = None

    model_config = {"from_attributes": True}


class ExperienceSchema(BaseModel):
    id: UUID | None = None
    company: str
    title: str
    location: str | None = None
    start_date: date_type | None = None
    end_date: date_type | None = None
    is_current: bool = False
    bullets: list[str] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class ProjectSchema(BaseModel):
    id: UUID | None = None
    name: str
    description: str | None = None
    bullets: list[str] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)
    url: str | None = None
    start_date: date_type | None = None
    end_date: date_type | None = None

    model_config = {"from_attributes": True}


class CertificationSchema(BaseModel):
    id: UUID | None = None
    name: str
    issuer: str | None = None
    issue_date: date_type | None = None
    credential_url: str | None = None

    model_config = {"from_attributes": True}


class AchievementSchema(BaseModel):
    id: UUID | None = None
    title: str
    description: str | None = None
    date: date_type | None = None

    model_config = {"from_attributes": True}


class CandidateSkillSchema(BaseModel):
    id: UUID
    skill_name: str
    proficiency: str | None = None
    source: str
    verification_status: str

    model_config = {"from_attributes": True}


class CandidateProfileResponse(BaseModel):
    id: UUID
    full_name: str | None = None
    headline: str | None = None
    summary: str | None = None
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    links: list[dict] = Field(default_factory=list)
    educations: list[EducationSchema] = Field(default_factory=list)
    experiences: list[ExperienceSchema] = Field(default_factory=list)
    projects: list[ProjectSchema] = Field(default_factory=list)
    certifications: list[CertificationSchema] = Field(default_factory=list)
    achievements: list[AchievementSchema] = Field(default_factory=list)
    candidate_skills: list[CandidateSkillSchema] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class CandidateProfileUpdateRequest(BaseModel):
    """Full replace-style update used by the profile review/correction screen
    (spec #9: 'allow user correction'). Frontend sends the corrected full set."""
    full_name: str | None = None
    headline: str | None = None
    summary: str | None = None
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    links: list[dict] | None = None
    educations: list[EducationSchema] | None = None
    experiences: list[ExperienceSchema] | None = None
    projects: list[ProjectSchema] | None = None
    certifications: list[CertificationSchema] | None = None
    achievements: list[AchievementSchema] | None = None
    skill_names: list[str] | None = None  # manually added/edited skill list
