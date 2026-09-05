import pytest

from app.common.exceptions import AIProviderError
from app.ai.groq_provider import GroqProvider


def test_parses_clean_json():
    result = GroqProvider._parse_json_defensively('{"skills": ["Java", "Python"]}')
    assert result == {"skills": ["Java", "Python"]}


def test_strips_markdown_json_fence():
    raw = '```json\n{"role_title": "Backend Engineer"}\n```'
    result = GroqProvider._parse_json_defensively(raw)
    assert result == {"role_title": "Backend Engineer"}


def test_strips_plain_markdown_fence():
    raw = '```\n{"summary": "test"}\n```'
    result = GroqProvider._parse_json_defensively(raw)
    assert result == {"summary": "test"}


def test_extracts_json_from_surrounding_prose():
    raw = 'Here is the extracted data:\n{"skills": ["AWS"]}\nLet me know if you need anything else!'
    result = GroqProvider._parse_json_defensively(raw)
    assert result == {"skills": ["AWS"]}


def test_empty_response_raises_clean_error():
    with pytest.raises(AIProviderError):
        GroqProvider._parse_json_defensively("")

    with pytest.raises(AIProviderError):
        GroqProvider._parse_json_defensively(None)

    with pytest.raises(AIProviderError):
        GroqProvider._parse_json_defensively("   ")


def test_completely_malformed_output_raises_clean_error_not_crash():
    with pytest.raises(AIProviderError):
        GroqProvider._parse_json_defensively("I cannot process this request.")


def test_error_message_never_leaks_raw_ai_output():
    """The exception message shown to the client must stay generic - raw AI
    output only goes to server logs, never into the user-facing message."""
    try:
        GroqProvider._parse_json_defensively("some totally broken $$$ output")
        assert False, "should have raised"
    except AIProviderError as e:
        assert "$$$" not in e.message
        assert "broken" not in e.message
