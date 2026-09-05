import redis

from app.core import redis as redis_module


class _AlwaysFailingRedisClient:
    """Simulates a Redis instance that is completely unreachable."""
    def get(self, key):
        raise redis.ConnectionError("Connection refused")

    def set(self, key, value, ex=None):
        raise redis.ConnectionError("Connection refused")


def test_cache_get_degrades_to_miss_when_redis_unavailable(monkeypatch):
    monkeypatch.setattr(redis_module, "get_redis", lambda: _AlwaysFailingRedisClient())
    # Must NOT raise - a Redis outage should look exactly like a cache miss
    # to every caller (resume parsing, JD analysis), not crash the request.
    result = redis_module.cache_get("some:key")
    assert result is None


def test_cache_set_degrades_silently_when_redis_unavailable(monkeypatch):
    monkeypatch.setattr(redis_module, "get_redis", lambda: _AlwaysFailingRedisClient())
    # Must NOT raise - failing to cache a result is not a request failure.
    redis_module.cache_set("some:key", {"data": "value"})


def test_corrupted_cache_entry_is_ignored_not_crashed(monkeypatch):
    class _CorruptedClient:
        def get(self, key):
            return "{not valid json"

    monkeypatch.setattr(redis_module, "get_redis", lambda: _CorruptedClient())
    result = redis_module.cache_get("some:key")
    assert result is None


def test_resume_parse_ai_call_still_succeeds_when_redis_is_down(db_session, monkeypatch):
    """End-to-end proof: a Redis outage during resume parsing must not
    prevent the AI provider from being called and must not surface as
    'AI service unavailable' - the actual AI call should still succeed."""
    import uuid
    from unittest.mock import MagicMock
    from app.users.models import User
    from app.resumes.models import Resume, ResumeStatus
    from app.resumes import service as resumes_service
    from app.ai.schemas import ParsedResume, ParsedPersonalInfo

    user = User(id=uuid.uuid4(), email="redistest@example.com", hashed_password="x", full_name="Redis Test")
    db_session.add(user)
    db_session.flush()
    resume = Resume(
        id=uuid.uuid4(), user_id=user.id, original_filename="r.pdf",
        file_path="/tmp/r.pdf", file_type="pdf", status=ResumeStatus.UPLOADED,
        extracted_text="Jane Doe, Python Developer",
    )
    db_session.add(resume)
    db_session.flush()

    fake_parsed = ParsedResume(personal_information=ParsedPersonalInfo(full_name="Jane Doe"), skills=["Python"])
    fake_provider = MagicMock()
    fake_provider.parse_resume.return_value = fake_parsed
    monkeypatch.setattr(resumes_service, "get_ai_provider", lambda: fake_provider)

    # Simulate total Redis unavailability for both cache read and write.
    monkeypatch.setattr(resumes_service, "cache_get", lambda key: None)
    monkeypatch.setattr(resumes_service, "cache_set", lambda *a, **k: None)

    updated_resume, updated = resumes_service.parse_resume(db_session, user.id, resume.id)

    assert updated is True
    assert updated_resume.status == ResumeStatus.PARSED
    fake_provider.parse_resume.assert_called_once()
