import hashlib

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.common.exceptions import FileProcessingError, NotFoundError
from app.core.redis import cache_get, cache_set
from app.core import storage
from app.documents.parser import extract_text_from_bytes, validate_upload
from app.resumes.models import Resume, ResumeStatus
from app.ai.factory import get_ai_provider
from app.profiles import service as profile_service


def upload_resume(db: Session, user_id, file: UploadFile) -> Resume:
    raw_bytes = file.file.read()
    if not raw_bytes:
        raise FileProcessingError("The uploaded file is empty.")

    extension, file_type = validate_upload(file, raw_bytes)
    file_path = storage.store_resume(user_id, extension, raw_bytes)

    resume = Resume(
        user_id=user_id,
        original_filename=file.filename,
        file_path=file_path,
        file_type=file_type,
        status=ResumeStatus.UPLOADED,
    )
    try:
        db.add(resume)
        db.flush()
    except Exception:
        storage.delete_resume(file_path)
        raise

    try:
        text = extract_text_from_bytes(storage.read_resume(file_path), file_type)
        resume.extracted_text = text
    except FileProcessingError as exc:
        resume.status = ResumeStatus.FAILED
        resume.parse_error = exc.message
        db.commit()  # persist the failure state before the error propagates and
        # get_db's dependency rolls back the rest of the (now-errored) transaction
        raise

    db.flush()
    return resume


def get_resume_or_404(db: Session, user_id, resume_id) -> Resume:
    resume = db.get(Resume, resume_id)
    if not resume or resume.user_id != user_id:
        raise NotFoundError("Resume not found.")
    return resume


def parse_resume(db: Session, user_id, resume_id) -> tuple[Resume, bool]:
    """Runs the AI parser over the extracted text and merges results into the
    candidate profile. Cached by a hash of the resume text to avoid re-billing
    the AI provider if parse is retried on identical content (spec #35)."""
    resume = get_resume_or_404(db, user_id, resume_id)
    if not resume.extracted_text:
        raise FileProcessingError("This resume has no extracted text to parse.")

    resume.status = ResumeStatus.PARSING
    db.flush()

    cache_key = f"resume_parse:{hashlib.sha256(resume.extracted_text.encode()).hexdigest()}"
    cached = cache_get(cache_key)

    try:
        if cached:
            from app.ai.schemas import ParsedResume
            parsed = ParsedResume.model_validate(cached)
        else:
            provider = get_ai_provider()
            parsed = provider.parse_resume(resume.extracted_text)
            cache_set(cache_key, parsed.model_dump(mode="json"), ttl_seconds=60 * 60 * 24)
    except Exception as exc:
        resume.status = ResumeStatus.FAILED
        resume.parse_error = str(getattr(exc, "message", exc))
        db.commit()  # persist the failure state before re-raising (see note above)
        raise

    profile = profile_service.get_or_create_profile(db, user_id)
    profile_service.apply_parsed_resume(db, profile, parsed)

    resume.status = ResumeStatus.PARSED
    db.flush()
    return resume, True


def list_resumes(db: Session, user_id) -> list[Resume]:
    return list(
        db.query(Resume).filter(Resume.user_id == user_id).order_by(Resume.created_at.desc()).all()
    )
