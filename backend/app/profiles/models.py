import enum
import uuid

from sqlalchemy import JSON, Boolean, Date, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.common.models import UUIDPKMixin, TimestampMixin


class SkillSource(str, enum.Enum):
    EXTRACTED = "EXTRACTED"      # came from parsing an uploaded resume
    MANUAL = "MANUAL"            # user typed it in directly
    VERIFICATION = "VERIFICATION"  # added via the missing-skill verification flow


class SkillVerificationStatus(str, enum.Enum):
    EXTRACTED = "EXTRACTED"   # AI found it in the resume text, not yet reviewed
    VERIFIED = "VERIFIED"     # user confirmed real project/work experience with evidence
    BASIC = "BASIC"           # user has basic/theoretical knowledge only
    REJECTED = "REJECTED"     # user said no - must never be used by the generator


class CandidateProfile(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "candidate_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)

    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    headline: Mapped[str | None] = mapped_column(String(255), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    links: Mapped[list[dict]] = mapped_column(JSON, default=list)  # [{"label": "GitHub", "url": "..."}]

    user = relationship("User", back_populates="profile")
    educations = relationship("Education", back_populates="profile", cascade="all, delete-orphan", order_by="desc(Education.end_date)")
    experiences = relationship("Experience", back_populates="profile", cascade="all, delete-orphan", order_by="desc(Experience.start_date)")
    projects = relationship("Project", back_populates="profile", cascade="all, delete-orphan")
    certifications = relationship("Certification", back_populates="profile", cascade="all, delete-orphan")
    achievements = relationship("Achievement", back_populates="profile", cascade="all, delete-orphan")
    candidate_skills = relationship("CandidateSkill", back_populates="profile", cascade="all, delete-orphan")


class Education(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "educations"

    profile_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("candidate_profiles.id", ondelete="CASCADE"))
    institution: Mapped[str] = mapped_column(String(255))
    degree: Mapped[str | None] = mapped_column(String(255), nullable=True)
    field_of_study: Mapped[str | None] = mapped_column(String(255), nullable=True)
    start_date: Mapped[Date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[Date | None] = mapped_column(Date, nullable=True)
    gpa: Mapped[str | None] = mapped_column(String(20), nullable=True)

    profile = relationship("CandidateProfile", back_populates="educations")


class Experience(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "experiences"

    profile_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("candidate_profiles.id", ondelete="CASCADE"))
    company: Mapped[str] = mapped_column(String(255))
    title: Mapped[str] = mapped_column(String(255))
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    start_date: Mapped[Date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[Date | None] = mapped_column(Date, nullable=True)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False)
    bullets: Mapped[list[str]] = mapped_column(JSON, default=list)
    technologies: Mapped[list[str]] = mapped_column(JSON, default=list)

    profile = relationship("CandidateProfile", back_populates="experiences")


class Project(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "projects"

    profile_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("candidate_profiles.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    bullets: Mapped[list[str]] = mapped_column(JSON, default=list)
    technologies: Mapped[list[str]] = mapped_column(JSON, default=list)
    url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    start_date: Mapped[Date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[Date | None] = mapped_column(Date, nullable=True)

    profile = relationship("CandidateProfile", back_populates="projects")


class Certification(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "certifications"

    profile_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("candidate_profiles.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(255))
    issuer: Mapped[str | None] = mapped_column(String(255), nullable=True)
    issue_date: Mapped[Date | None] = mapped_column(Date, nullable=True)
    credential_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    profile = relationship("CandidateProfile", back_populates="certifications")


class Achievement(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "achievements"

    profile_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("candidate_profiles.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    date: Mapped[Date | None] = mapped_column(Date, nullable=True)

    profile = relationship("CandidateProfile", back_populates="achievements")


class Skill(Base, UUIDPKMixin, TimestampMixin):
    """Global, de-duplicated skill dictionary (e.g. 'Kafka', 'Docker').
    Shared across all candidates and job descriptions so matching is consistent."""
    __tablename__ = "skills"

    name: Mapped[str] = mapped_column(String(150), unique=True, index=True)
    normalized_name: Mapped[str] = mapped_column(String(150), index=True)  # lowercase, no punctuation
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)  # e.g. "language", "cloud", "database"

    candidate_links = relationship("CandidateSkill", back_populates="skill")


class CandidateSkill(Base, UUIDPKMixin, TimestampMixin):
    """A skill as it relates to one candidate: proficiency, verification status,
    and evidence. This - not the global Skill row - is what the generator reads."""
    __tablename__ = "candidate_skills"

    profile_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("candidate_profiles.id", ondelete="CASCADE"))
    skill_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("skills.id", ondelete="CASCADE"))

    proficiency: Mapped[str | None] = mapped_column(String(50), nullable=True)  # beginner/intermediate/advanced/expert
    source: Mapped[SkillSource] = mapped_column(Enum(SkillSource), default=SkillSource.EXTRACTED)
    verification_status: Mapped[SkillVerificationStatus] = mapped_column(
        Enum(SkillVerificationStatus), default=SkillVerificationStatus.EXTRACTED
    )

    profile = relationship("CandidateProfile", back_populates="candidate_skills")
    skill = relationship("Skill", back_populates="candidate_links")
    verification = relationship("SkillVerification", back_populates="candidate_skill", uselist=False, cascade="all, delete-orphan")

    @property
    def skill_name(self) -> str:
        """Lets Pydantic's from_attributes mode read this directly (schemas
        expect `skill_name`, but the FK-normalized model only stores the
        related Skill row) without every caller having to hand-build dicts."""
        return self.skill.name if self.skill else ""
