from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ResumeResponse(BaseModel):
    id: UUID
    original_filename: str
    file_type: str
    status: str
    parse_error: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ResumeParseResponse(BaseModel):
    resume: ResumeResponse
    profile_updated: bool
