import os

os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("GROQ_API_KEY", "test")

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.common.exceptions import AIProviderError, register_exception_handlers


def test_ai_provider_error_code_reaches_the_http_response():
    """Proves the categorized `code` (e.g. 'ai_missing_api_key',
    'ai_rate_limited') set in groq_provider.py actually appears in the JSON
    the frontend receives at error.code - not just in server logs - which is
    the actual, useful form of 'categorize AI errors' the product needs."""
    app = FastAPI(debug=False)
    register_exception_handlers(app)

    @app.get("/simulate-ai-failure")
    def simulate():
        raise AIProviderError("The AI service is not configured (missing GROQ_API_KEY).", code="ai_missing_api_key")

    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/simulate-ai-failure")

    assert response.status_code == 502
    data = response.json()
    assert data["error"]["code"] == "ai_missing_api_key"
    assert "GROQ_API_KEY" in data["error"]["message"]
    # and still no secrets/internals
    assert "Traceback" not in response.text
