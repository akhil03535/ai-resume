import enum
import uuid

from sqlalchemy import JSON, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.common.models import UUIDPKMixin, TimestampMixin


class ResumeStatus(str, enum.Enum):
    UPLOADED = "UPLOADED"
    PARSING = "PARSING"
    PARSED = "PARSED"
    FAILED = "FAILED"


class Resume(Base, UUIDPKMixin, TimestampMixin):
    """An uploaded source resume file (spec #9)."""
    __tablename__ = "resumes"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    original_filename: Mapped[str] = mapped_column(String(500))
    file_path: Mapped[str] = mapped_column(String(1000))
    file_type: Mapped[str] = mapped_column(String(10))  # "pdf" | "docx"
    status: Mapped[ResumeStatus] = mapped_column(Enum(ResumeStatus), default=ResumeStatus.UPLOADED)
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    parse_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    user = relationship("User", back_populates="resumes")
    analyses = relationship("ResumeAnalysis", back_populates="resume", cascade="all, delete-orphan")


class ResumeTemplate(Base, UUIDPKMixin, TimestampMixin):
    """Data-driven template metadata (spec #19). Rendering rules live in
    app/templates/*.py, keyed by `slug`."""
    __tablename__ = "resume_templates"

    slug: Mapped[str] = mapped_column(String(100), unique=True)
    name: Mapped[str] = mapped_column(String(150))
    description: Mapped[str] = mapped_column(Text)
    is_ats_safe: Mapped[bool] = mapped_column(default=True)


class GeneratedResume(Base, UUIDPKMixin, TimestampMixin):
    """One tailored, generated resume (spec #22 versioning)."""
    __tablename__ = "generated_resumes"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    job_description_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("job_descriptions.id", ondelete="SET NULL"), nullable=True
    )
    template_slug: Mapped[str] = mapped_column(String(100), default="ats_classic")

    version_name: Mapped[str] = mapped_column(String(255))
    target_role: Mapped[str | None] = mapped_column(String(255), nullable=True)
    target_company: Mapped[str | None] = mapped_column(String(255), nullable=True)

    content: Mapped[dict] = mapped_column(JSON)  # full structured resume JSON (see documents/parser.py schema)

    ats_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    job_match_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_ats_score: Mapped[int | None] = mapped_column(Integer, nullable=True)  # before/after comparison

    user = relationship("User")
    job_description = relationship("JobDescription")
