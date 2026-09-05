import uuid
from pathlib import Path

from app.common.exceptions import FileProcessingError
from app.core.config import settings


def uses_supabase() -> bool:
    return settings.ENV.lower() == "production"


def _get_supabase_client():
    if not settings.SUPABASE_URL or not settings.SUPABASE_SECRET_KEY:
        raise FileProcessingError("Persistent resume storage is not configured.")

    from supabase import create_client

    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SECRET_KEY)


def _object_key(user_id, extension: str) -> str:
    return f"resumes/{user_id}/{uuid.uuid4()}{extension}"


def store_resume(user_id, extension: str, raw_bytes: bytes) -> str:
    if not uses_supabase():
        upload_dir = Path(settings.UPLOAD_DIR)
        upload_dir.mkdir(parents=True, exist_ok=True)
        local_path = upload_dir / f"{uuid.uuid4()}{extension}"
        local_path.write_bytes(raw_bytes)
        return str(local_path)

    object_key = _object_key(user_id, extension)
    try:
        client = _get_supabase_client()
        client.storage.from_(settings.SUPABASE_STORAGE_BUCKET).upload(
            object_key,
            raw_bytes,
            file_options={
                "content-type": "application/pdf"
                if extension == ".pdf"
                else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            },
        )
    except Exception as exc:
        raise FileProcessingError("The resume could not be saved.") from exc
    return object_key


def read_resume(file_path: str) -> bytes:
    if not uses_supabase():
        try:
            return Path(file_path).read_bytes()
        except OSError as exc:
            raise FileProcessingError("The uploaded resume could not be read.") from exc

    try:
        client = _get_supabase_client()
        return client.storage.from_(settings.SUPABASE_STORAGE_BUCKET).download(file_path)
    except Exception as exc:
        raise FileProcessingError("The uploaded resume could not be read.") from exc


def delete_resume(file_path: str) -> None:
    if not uses_supabase():
        return

    try:
        client = _get_supabase_client()
        client.storage.from_(settings.SUPABASE_STORAGE_BUCKET).remove([file_path])
    except Exception:
        return