import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_production_rejects_insecure_jwt_default():
    with pytest.raises(ValidationError, match="JWT_SECRET must be explicitly configured"):
        Settings(_env_file=None, ENV="production", JWT_SECRET="change-me-in-production")


def test_production_accepts_explicit_jwt_secret_without_exposing_it():
    secret = "test-production-secret"
    settings = Settings(_env_file=None, ENV="production", DEBUG=False, JWT_SECRET=secret)

    assert settings.ENV == "production"
    assert settings.DEBUG is False
    assert settings.JWT_SECRET == secret


def test_development_defaults_remain_unchanged():
    settings = Settings(_env_file=None)

    assert settings.ENV == "development"
    assert settings.DEBUG is True