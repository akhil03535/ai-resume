import enum
import uuid

from sqlalchemy import JSON, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.common.models import UUIDPKMixin, TimestampMixin


class MatchStatus(str, enum.Enum):
    MATCHED = "MATCHED"
    PARTIAL = "PARTIAL"
    MISSING = "MISSING"


class RecommendationSeverity(str, enum.Enum):
    STRENGTH = "STRENGTH"
    ISSUE = "ISSUE"
    SUGGESTION = "SUGGESTION"


class ResumeAnalysis(Base, UUIDPKMixin, TimestampMixin):
    """One analysis run: a resume (source OR generated) scored against a JD."""
    __tablename__ = "resume_analyses"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    resume_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("resumes.id", ondelete="CASCADE"), nullable=True)
    generated_resume_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("generated_resumes.id", ondelete="CASCADE"), nullable=True
    )
    job_description_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("job_descriptions.id", ondelete="CASCADE"))

    ats_score: Mapped[int] = mapped_column(Integer)
    job_match_score: Mapped[int] = mapped_column(Integer)
    completeness_score: Mapped[int] = mapped_column(Integer)

    # component breakdown, keyed by name -> 0-100, so the UI can explain the score (spec #13)
    ats_components: Mapped[dict] = mapped_column(JSON)
    category_scores: Mapped[dict] = mapped_column(JSON)   # radar chart: skills/keywords/experience/projects/education/formatting
    section_scores: Mapped[dict] = mapped_column(JSON)    # summary/skills/experience/projects/education/achievements

    resume = relationship("Resume", back_populates="analyses")
    job_description = relationship("JobDescription")
    skill_matches = relationship("SkillMatch", back_populates="analysis", cascade="all, delete-orphan")
    keyword_matches = relationship("KeywordMatch", back_populates="analysis", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="analysis", cascade="all, delete-orphan")


class SkillMatch(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "skill_matches"

    analysis_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("resume_analyses.id", ondelete="CASCADE"))
    requirement_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("job_requirements.id", ondelete="CASCADE"))
    skill_label: Mapped[str] = mapped_column(String(150))
    status: Mapped[MatchStatus] = mapped_column(Enum(MatchStatus))
    similarity_score: Mapped[float] = mapped_column(Float)  # 0..1, semantic similarity where used
    is_verified: Mapped[bool] = mapped_column(default=False)

    analysis = relationship("ResumeAnalysis", back_populates="skill_matches")


class KeywordMatch(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "keyword_matches"

    analysis_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("resume_analyses.id", ondelete="CASCADE"))
    keyword: Mapped[str] = mapped_column(String(150))
    status: Mapped[MatchStatus] = mapped_column(Enum(MatchStatus))
    occurrences: Mapped[int] = mapped_column(Integer, default=0)

    analysis = relationship("ResumeAnalysis", back_populates="keyword_matches")


class Recommendation(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "recommendations"

    analysis_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("resume_analyses.id", ondelete="CASCADE"))
    severity: Mapped[RecommendationSeverity] = mapped_column(Enum(RecommendationSeverity))
    text: Mapped[str] = mapped_column(Text)

    analysis = relationship("ResumeAnalysis", back_populates="recommendations")
