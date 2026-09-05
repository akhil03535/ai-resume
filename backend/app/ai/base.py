"""
AIProvider is the single seam between this application and any LLM vendor.

Nothing outside app/ai/* should import Groq (or any other vendor SDK)
directly - route everything through this interface so the provider can be
swapped later (spec #5, #34) without touching resume/job/generator logic.
"""
from abc import ABC, abstractmethod

from app.ai.schemas import AnalyzedJobDescription, BulletImprovement, ParsedResume


class AIProvider(ABC):
    @abstractmethod
    def parse_resume(self, raw_text: str) -> ParsedResume:
        """Turn raw extracted resume text into structured, validated data.
        Must not invent any experience, skill, or credential not present in raw_text."""

    @abstractmethod
    def analyze_job_description(self, raw_text: str) -> AnalyzedJobDescription:
        """Extract role, requirements (required vs preferred), and keywords from a JD."""

    @abstractmethod
    def improve_bullet(self, bullet_text: str, mode: str, context: str | None = None) -> BulletImprovement:
        """Rewrite a single resume bullet. `mode` in {improve, concise, ats_friendly,
        technical, impact}. Must preserve factual meaning and never add unverified metrics."""

    @abstractmethod
    def generate_summary(self, profile_facts: dict, jd_context: dict) -> str:
        """Write a professional summary using only the supplied verified facts,
        prioritized toward the given job description context."""
