"""
Every AI call in this system returns one of these strictly-validated shapes.
The LLM is never trusted to freeform its way into the database - if its
output doesn't fit these models, we retry once and then surface a clean
error (spec #10, #34).
"""
from pydantic import BaseModel, Field


class ParsedLink(BaseModel):
    label: str
    url: str


class ParsedEducation(BaseModel):
    institution: str
    degree: str | None = None
    field_of_study: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    gpa: str | None = None


class ParsedExperience(BaseModel):
    company: str
    title: str
    location: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    is_current: bool = False
    bullets: list[str] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)


class ParsedProject(BaseModel):
    name: str
    description: str | None = None
    bullets: list[str] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)
    url: str | None = None


class ParsedCertification(BaseModel):
    name: str
    issuer: str | None = None
    issue_date: str | None = None


class ParsedAchievement(BaseModel):
    title: str
    description: str | None = None


class ParsedPersonalInfo(BaseModel):
    full_name: str | None = None
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    headline: str | None = None
    summary: str | None = None


class ParsedResume(BaseModel):
    """Output of AIProvider.parse_resume. Mirrors spec #10's JSON shape."""
    personal_information: ParsedPersonalInfo = Field(default_factory=ParsedPersonalInfo)
    education: list[ParsedEducation] = Field(default_factory=list)
    experience: list[ParsedExperience] = Field(default_factory=list)
    projects: list[ParsedProject] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    certifications: list[ParsedCertification] = Field(default_factory=list)
    achievements: list[ParsedAchievement] = Field(default_factory=list)
    links: list[ParsedLink] = Field(default_factory=list)


class ExtractedRequirement(BaseModel):
    label: str
    type: str  # "skill" | "technology" | "keyword"
    importance: str  # "required" | "preferred"


class AnalyzedJobDescription(BaseModel):
    """Output of AIProvider.analyze_job_description."""
    role_title: str | None = None
    domain: str | None = None
    experience_requirement: str | None = None
    education_requirement: str | None = None
    responsibilities: list[str] = Field(default_factory=list)
    requirements: list[ExtractedRequirement] = Field(default_factory=list)


class BulletImprovement(BaseModel):
    """Output of AIProvider.improve_bullet. The model is instructed never to
    invent metrics that were not present in the original bullet (spec #21)."""
    improved_text: str
    notes: str | None = None
