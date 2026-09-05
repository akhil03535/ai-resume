import io
import re
import uuid
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.common.exceptions import FileProcessingError, NotFoundError
from app.core import storage
from app.core.config import settings
from app.resumes import service as resumes_service
from app.resumes.models import Resume


PDF_BYTES = b"%PDF-test"


class _FakeBucket:
    def __init__(self, downloaded=None, upload_error=None):
        self.downloaded = downloaded
        self.upload_error = upload_error
        self.uploaded = []
        self.removed = []

    def upload(self, path, content, file_options=None):
        if self.upload_error:
            raise self.upload_error
        self.uploaded.append((path, content, file_options))

    def download(self, path):
        return self.downloaded

    def remove(self, paths):
        self.removed.append(paths)


class _FakeClient:
    def __init__(self, bucket):
        self.bucket = bucket
        self.storage = self

    def from_(self, bucket_name):
        assert bucket_name == "resumes"
        return self.bucket


def _upload_file(filename="resume.pdf", content=PDF_BYTES):
    return SimpleNamespace(filename=filename, file=io.BytesIO(content))


def test_local_filesystem_storage_still_works(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "ENV", "development")
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))

    path = storage.store_resume(uuid.uuid4(), ".pdf", PDF_BYTES)

    assert path.startswith(str(tmp_path))
    assert path.endswith(".pdf")
    assert open(path, "rb").read() == PDF_BYTES


def test_production_upload_uses_expected_private_object_key(monkeypatch):
    monkeypatch.setattr(settings, "ENV", "production")
    monkeypatch.setattr(settings, "SUPABASE_URL", "https://storage.example")
    bucket = _FakeBucket()
    monkeypatch.setattr(storage, "_get_supabase_client", lambda: _FakeClient(bucket))
    user_id = uuid.uuid4()

    path = storage.store_resume(user_id, ".pdf", PDF_BYTES)

    assert re.fullmatch(rf"resumes/{user_id}/[0-9a-f-]+\.pdf", path)
    assert bucket.uploaded[0][0] == path
    assert bucket.uploaded[0][1] == PDF_BYTES


def test_production_resume_record_stores_object_key(monkeypatch):
    monkeypatch.setattr(settings, "ENV", "production")
    user_id = uuid.uuid4()
    object_key = f"resumes/{user_id}/{uuid.uuid4()}.pdf"
    db = MagicMock()
    monkeypatch.setattr(resumes_service, "storage", MagicMock(
        store_resume=lambda *_: object_key,
        read_resume=lambda *_: PDF_BYTES,
        delete_resume=MagicMock(),
    ))
    monkeypatch.setattr(resumes_service, "extract_text_from_bytes", lambda *_: "resume text")

    resume = resumes_service.upload_resume(db, user_id, _upload_file())

    assert resume.file_path == object_key
    assert not resume.file_path.startswith("/app/uploads/")


def test_storage_upload_failure_creates_no_database_record(monkeypatch):
    db = MagicMock()
    monkeypatch.setattr(
        resumes_service,
        "validate_upload",
        lambda *_: (".pdf", "pdf"),
    )
    monkeypatch.setattr(
        resumes_service.storage,
        "store_resume",
        MagicMock(side_effect=FileProcessingError("The resume could not be saved.")),
    )

    with pytest.raises(FileProcessingError):
        resumes_service.upload_resume(db, uuid.uuid4(), _upload_file())

    db.add.assert_not_called()


def test_database_failure_after_upload_attempts_object_cleanup(monkeypatch):
    db = MagicMock()
    db.flush.side_effect = RuntimeError("database unavailable")
    object_key = "resumes/user/resume.pdf"
    delete = MagicMock()
    monkeypatch.setattr(resumes_service, "validate_upload", lambda *_: (".pdf", "pdf"))
    monkeypatch.setattr(resumes_service.storage, "store_resume", lambda *_: object_key)
    monkeypatch.setattr(resumes_service.storage, "delete_resume", delete)

    with pytest.raises(RuntimeError):
        resumes_service.upload_resume(db, uuid.uuid4(), _upload_file())

    delete.assert_called_once_with(object_key)


def test_production_object_retrieval_returns_bytes_without_exposing_credentials(monkeypatch):
    monkeypatch.setattr(settings, "ENV", "production")
    bucket = _FakeBucket(downloaded=PDF_BYTES)
    monkeypatch.setattr(storage, "_get_supabase_client", lambda: _FakeClient(bucket))

    result = storage.read_resume("resumes/user/resume.pdf")

    assert result == PDF_BYTES
    assert "SUPABASE_SECRET_KEY" not in repr(result)


def test_existing_resume_ownership_check_remains_intact():
    owner_id = uuid.uuid4()
    other_user_id = uuid.uuid4()
    resume = SimpleNamespace(user_id=owner_id)
    db = MagicMock()
    db.get.return_value = resume

    with pytest.raises(NotFoundError):
        resumes_service.get_resume_or_404(db, other_user_id, uuid.uuid4())