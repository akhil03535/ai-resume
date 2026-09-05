"""
Centralized application configuration.

All environment-driven settings live here. Nothing else in the codebase
should call os.environ directly - import `settings` instead.
"""
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- App ---
    APP_NAME: str = "AI Resume Analyzer"
    ENV: str = "development"
    DEBUG: bool = True
    API_PREFIX: str = "/api"

    # --- Database ---
    DATABASE_URL: str = "postgresql+psycopg2://resumeai:resumeai@postgres:5432/resumeai"

    # --- Redis ---
    REDIS_URL: str = "redis://redis:6379/0"

    # --- Auth ---
    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24h
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 14  # 14d

    # --- CORS ---
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    # --- Uploads ---
    MAX_UPLOAD_SIZE_MB: int = 8
    ALLOWED_UPLOAD_EXTENSIONS: List[str] = [".pdf", ".docx"]
    UPLOAD_DIR: str = "/app/uploads"

    # --- AI provider ---
    AI_PROVIDER: str = "groq"
    GROQ_API_KEY: str = ""
    AI_MODEL: str = "llama-3.3-70b-versatile"
    AI_TEMPERATURE: float = 0.2
    AI_MAX_RETRIES: int = 2  # passed directly to tenacity's stop_after_attempt() -
    # this is TOTAL attempts (including the first), not retries-after-failure

    # --- Scoring weights (centralized, see analysis/scoring.py) ---
    ATS_WEIGHT_REQUIRED_SKILLS: float = 0.30
    ATS_WEIGHT_PREFERRED_SKILLS: float = 0.10
    ATS_WEIGHT_KEYWORDS: float = 0.15
    ATS_WEIGHT_EXPERIENCE: float = 0.15
    ATS_WEIGHT_PROJECTS: float = 0.10
    ATS_WEIGHT_SECTION_COMPLETENESS: float = 0.10
    ATS_WEIGHT_FORMATTING: float = 0.05
    ATS_WEIGHT_EDUCATION: float = 0.05

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
