from functools import lru_cache

from app.core.config import settings
from app.ai.base import AIProvider


@lru_cache
def get_ai_provider() -> AIProvider:
    """Swap providers here based on settings.AI_PROVIDER. Every other module
    depends only on the AIProvider interface, never on a concrete vendor."""
    if settings.AI_PROVIDER == "groq":
        from app.ai.groq_provider import GroqProvider
        return GroqProvider()

    raise ValueError(f"Unknown AI_PROVIDER: {settings.AI_PROVIDER}")
