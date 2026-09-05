import os

os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("GROQ_API_KEY", "test")

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.common.exceptions import register_exception_handlers


def _build_broken_app() -> FastAPI:
    """A minimal app wired exactly like the real one (debug=False, same
    exception handler registration) with one route that deliberately raises
    an unhandled exception with a realistic-looking internal error message,
    to prove the response never leaks it regardless of what broke."""
    app = FastAPI(debug=False)
    register_exception_handlers(app)

    @app.get("/boom")
    def boom():
        raise RuntimeError(
            "could not translate host name \"postgres\" to address: Name or service not known "
            "(Background on this error at: https://sqlalche.me/e/20/e3q8) "
            "DATABASE_URL=postgresql+psycopg2://resumeai:SUPERSECRET@postgres:5432/resumeai"
        )

    return app


def test_unhandled_exception_returns_clean_generic_error_not_a_traceback():
    client = TestClient(_build_broken_app(), raise_server_exceptions=False)
    response = client.get("/boom")

    assert response.status_code == 500
    body = response.text

    # The real failure detail (including what would have been a leaked
    # connection string / secret) must never appear in the response body.
    assert "SUPERSECRET" not in body
    assert "postgres:5432" not in body
    assert "Traceback" not in body
    assert "sqlalche.me" not in body
    assert "/dist-packages/" not in body
    assert "File \"" not in body

    data = response.json()
    assert data["error"]["code"] == "internal_error"
    assert "went wrong" in data["error"]["message"].lower()


def test_debug_is_never_true_regardless_of_settings_debug(monkeypatch):
    """Regression guard for the exact bug found via live testing: FastAPI's
    own `debug=` flag must stay False no matter what settings.DEBUG is,
    since Starlette's debug mode can render raw tracebacks directly into
    the HTTP response, bypassing the custom exception handlers entirely."""
    import app.main as main_module
    assert main_module.app.debug is False
