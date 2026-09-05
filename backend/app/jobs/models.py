import enum
import uuid

from sqlalchemy import JSON, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.common.models import UUIDPKMixin, TimestampMixin


class RequirementImportance(str, enum.Enum):
    REQUIRED = "REQUIRED"
    PREFERRED = "PREFERRED"


class RequirementType(str, enum.Enum):
    SKILL = "SKILL"
    TECHNOLOGY = "TECHNOLOGY"
    KEYWORD = "KEYWORD"


class JobDescription(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "job_descriptions"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(255))
    company_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    raw_text: Mapped[str] = mapped_column(Text)

    role_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    domain: Mapped[str | None] = mapped_column(String(255), nullable=True)
    experience_requirement: Mapped[str | None] = mapped_column(String(255), nullable=True)
    education_requirement: Mapped[str | None] = mapped_column(String(255), nullable=True)
    responsibilities: Mapped[list[str]] = mapped_column(JSON, default=list)
    is_analyzed: Mapped[bool] = mapped_column(default=False)

    user = relationship("User", back_populates="job_descriptions")
    requirements = relationship("JobRequirement", back_populates="job_description", cascade="all, delete-orphan")


class JobRequirement(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "job_requirements"

    job_description_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("job_descriptions.id", ondelete="CASCADE"))
    label: Mapped[str] = mapped_column(String(150))               # e.g. "Kafka"
    normalized_label: Mapped[str] = mapped_column(String(150))    # e.g. "kafka"
    requirement_type: Mapped[RequirementType] = mapped_column(Enum(RequirementType))
    importance: Mapped[RequirementImportance] = mapped_column(Enum(RequirementImportance))

    job_description = relationship("JobDescription", back_populates="requirements")
