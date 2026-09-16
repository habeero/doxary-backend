import pytest
from app.core.config.settings import Settings
from pydantic import ValidationError


def test_ai_defaults_disabled_without_secret(monkeypatch):
    monkeypatch.delenv("DOXARY_AI_ENABLED", raising=False)
    monkeypatch.delenv("DOXARY_OPENAI_API_KEY", raising=False)
    settings = Settings.load({"app_env": "test", "ai_enabled": False, "openai_api_key": None})
    assert settings.ai_enabled is False


def test_enabled_ai_requires_key():
    with pytest.raises(ValidationError, match="DOXARY_OPENAI_API_KEY"):
        Settings.load({"app_env": "test", "ai_enabled": True, "openai_api_key": None})


def test_explicit_overrides_are_applied():
    settings = Settings.load(
        {
            "app_env": "test",
            "ai_enabled": True,
            "openai_api_key": "runtime-only",
            "ai_model": "custom-model",
            "ai_reasoning_effort": "high",
            "ai_timeout_seconds": 12,
        }
    )
    assert settings.ai_model == "custom-model"
    assert settings.ai_reasoning_effort == "high"
    assert settings.ai_timeout_seconds == 12


def test_timeout_must_be_positive():
    with pytest.raises(ValidationError, match="must be positive"):
        Settings.load({"app_env": "test", "ai_timeout_seconds": 0})
