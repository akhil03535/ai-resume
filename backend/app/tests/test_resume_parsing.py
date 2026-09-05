import uuid
from unittest.mock import MagicMock

import pytest

from app.users.models import User
from app.resumes.models import Resume, ResumeStatus
from app.resumes import service as resumes_service
from app.ai.schemas import ParsedResume, ParsedPersonalInfo
from app.common.exceptions import AIProviderError


def _make_user(db_session):
    user = User(id=uuid.uuid4(), email="parser@example.com", hashed_password="x", full_name="Parser Test")
    db_session.add(user)
    db_session.flush()
    return user


def _make_resume(db_session, user, text="John Doe\nSoftware Engineer\nSkills: Python, Docker"):
    resume = Resume(
        id=uuid.uuid4(), user_id=user.id, original_filename="r.pdf",
        file_path="/tmp/r.pdf", file_type="pdf", status=ResumeStatus.UPLOADED,
        extracted_text=text,
    )
    db_session.add(resume)
    db_session.flush()
    return resume


def test_successful_parse_populates_profile(db_session, monkeypatch):
    user = _make_user(db_session)
    resume = _make_resume(db_session, user)

    fake_parsed = ParsedResume(
        personal_information=ParsedPersonalInfo(full_name="John Doe", headline="Software Engineer"),
        skills=["Python", "Docker"],
    )
    fake_provider = MagicMock()
    fake_provider.parse_resume.return_value = fake_parsed
    monkeypatch.setattr(resumes_service, "get_ai_provider", lambda: fake_provider)
    monkeypatch.setattr(resumes_service, "cache_get", lambda key: None)
    monkeypatch.setattr(resumes_service, "cache_set", lambda *a, **k: None)

    updated_resume, updated = resumes_service.parse_resume(db_session, user.id, resume.id)

    assert updated is True
    assert updated_resume.status == ResumeStatus.PARSED
    fake_provider.parse_resume.assert_called_once()


def test_malformed_ai_output_marks_resume_failed_and_persists(db_session, monkeypatch):
    """Reproduces the exact bug found via live testing: get_db() rolls back
    the whole transaction on any exception, which was silently wiping out
    the FAILED status + parse_error we deliberately set before re-raising.
    This test simulates that exact get_db lifecycle (commit-on-success,
    rollback-on-exception) to make sure the fix actually holds."""
    user = _make_user(db_session)
    resume = _make_resume(db_session, user)
    db_session.commit()  # simulate the successful upload request completing

    fake_provider = MagicMock()
    fake_provider.parse_resume.side_effect = AIProviderError("The AI service returned an unexpected response. Please try again.")
    monkeypatch.setattr(resumes_service, "get_ai_provider", lambda: fake_provider)
    monkeypatch.setattr(resumes_service, "cache_get", lambda key: None)

    # Simulate get_db's dependency behavior for the /parse request: the
    # service should commit its own failure-state write internally, and
    # this outer rollback (mimicking get_db's `except: db.rollback()`)
    # must NOT be able to undo it.
    try:
        resumes_service.parse_resume(db_session, user.id, resume.id)
        assert False, "expected AIProviderError"
    except AIProviderError:
        db_session.rollback()

    db_session.expire_all()  # force a real re-read, don't trust in-memory state
    persisted = db_session.get(Resume, resume.id)
    assert persisted.status == ResumeStatus.FAILED
    assert persisted.parse_error is not None
    assert "unexpected response" in persisted.parse_error
