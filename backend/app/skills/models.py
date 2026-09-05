import enum
import uuid

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.common.models import UUIDPKMixin, TimestampMixin


class EvidenceSourceType(str, enum.Enum):
    PROJECT = "PROJECT"
    INTERNSHIP = "INTERNSHIP"
    WORK = "WORK"
    COURSE = "COURSE"
    OTHER = "OTHER"


class SkillVerification(Base, UUIDPKMixin, TimestampMixin):
    """One row per (candidate_skill) verification interview - i.e. the
    'Do you know Kafka?' interaction and its outcome (spec #3)."""
    __tablename__ = "skill_verifications"

    candidate_skill_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("candidate_skills.id", ondelete="CASCADE"), unique=True
    )
    answer: Mapped[str] = mapped_column(String(30))  # "yes" | "basic" | "no"

    candidate_skill = relationship("CandidateSkill", back_populates="verification")
    evidence = relationship("VerificationEvidence", back_populates="verification", cascade="all, delete-orphan")


class VerificationEvidence(Base, UUIDPKMixin, TimestampMixin):
    """The 'where' and 'how' the user described using a verified skill."""
    __tablename__ = "verification_evidence"

    verification_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("skill_verifications.id", ondelete="CASCADE")
    )
    source_type: Mapped[EvidenceSourceType] = mapped_column(Enum(EvidenceSourceType))
    description: Mapped[str] = mapped_column(Text)

    verification = relationship("SkillVerification", back_populates="evidence")
