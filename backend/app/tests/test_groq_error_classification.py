import groq
import httpx
import pytest

from app.ai.groq_provider import _classify_groq_error
from app.core.config import settings


def _fake_response(status_code: int) -> httpx.Response:
    request = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")
    return httpx.Response(status_code=status_code, request=request)


@pytest.mark.parametrize(
    "exc_factory,expected_code,expected_log_tag",
    [
        (lambda: groq.AuthenticationError("invalid api key", response=_fake_response(401), body=None), "ai_invalid_api_key", "B - INVALID API KEY"),
        (lambda: groq.PermissionDeniedError("forbidden", response=_fake_response(403), body=None), "ai_forbidden", "C - FORBIDDEN"),
        (lambda: groq.RateLimitError("rate limited", response=_fake_response(429), body=None), "ai_rate_limited", "D - RATE LIMIT"),
        (lambda: groq.NotFoundError("model not found", response=_fake_response(404), body=None), "ai_invalid_model", "G - INVALID MODEL"),
        (lambda: groq.BadRequestError("bad request", response=_fake_response(400), body=None), "ai_bad_request", "J - BAD REQUEST"),
        (lambda: groq.InternalServerError("groq down", response=_fake_response(500), body=None), "ai_provider_error", "J - GROQ INTERNAL ERROR"),
        (lambda: groq.APITimeoutError(request=httpx.Request("POST", "https://api.groq.com/x")), "ai_timeout", "F - TIMEOUT"),
        (lambda: groq.APIConnectionError(message="connection refused", request=httpx.Request("POST", "https://api.groq.com/x")), "ai_network_error", "E - NETWORK FAILURE"),
        (lambda: RuntimeError("something totally unexpected"), "ai_unknown_error", "J - UNKNOWN PROVIDER ERROR"),
    ],
)
def test_each_error_category_maps_to_a_distinct_code_and_log_tag(exc_factory, expected_code, expected_log_tag, monkeypatch):
    monkeypatch.setattr(settings, "GROQ_API_KEY", "gsk_fake_key_for_test_purposes_only")
    code, log_line, user_message = _classify_groq_error(exc_factory(), model="llama-3.3-70b-versatile")

    assert code == expected_code
    assert expected_log_tag in log_line
    assert user_message  # always a non-empty, safe message


def test_missing_api_key_gets_its_own_distinct_code_and_message(monkeypatch):
    monkeypatch.setattr(settings, "GROQ_API_KEY", "")
    code, log_line, user_message = _classify_groq_error(
        groq.AuthenticationError("invalid api key", response=_fake_response(401), body=None),
        model="llama-3.3-70b-versatile",
    )
    assert code == "ai_missing_api_key"
    assert "A - MISSING API KEY" in log_line
    assert "GROQ_API_KEY" in user_message


def test_api_key_never_appears_in_log_or_user_message(monkeypatch):
    secret_key = "gsk_super_secret_value_that_must_never_be_logged"
    monkeypatch.setattr(settings, "GROQ_API_KEY", secret_key)
    code, log_line, user_message = _classify_groq_error(
        groq.AuthenticationError("invalid api key", response=_fake_response(401), body=None),
        model="llama-3.3-70b-versatile",
    )
    assert secret_key not in log_line
    assert secret_key not in user_message


def test_all_codes_are_distinct_across_categories(monkeypatch):
    """Every category the product spec asks to distinguish must actually
    map to a different `code` value - this is the whole point of item #4:
    the frontend/API contract should be able to tell these apart, not just
    server logs."""
    monkeypatch.setattr(settings, "GROQ_API_KEY", "gsk_fake")
    cases = [
        groq.AuthenticationError("x", response=_fake_response(401), body=None),
        groq.PermissionDeniedError("x", response=_fake_response(403), body=None),
        groq.RateLimitError("x", response=_fake_response(429), body=None),
        groq.NotFoundError("x", response=_fake_response(404), body=None),
        groq.BadRequestError("x", response=_fake_response(400), body=None),
        groq.APITimeoutError(request=httpx.Request("POST", "https://api.groq.com/x")),
        groq.APIConnectionError(message="x", request=httpx.Request("POST", "https://api.groq.com/x")),
        RuntimeError("x"),
    ]
    codes = [_classify_groq_error(exc, model="m")[0] for exc in cases]
    assert len(codes) == len(set(codes)), f"expected all-distinct codes, got: {codes}"
