from collections.abc import Mapping
from pathlib import Path
from typing import Any, Literal

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized runtime configuration loaded once at application composition."""

    model_config = SettingsConfigDict(
        env_prefix="DOXARY_", env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    app_env: Literal["development", "test", "production"] = "development"
    database_url: str | None = None
    debug: bool = False
    testing: bool = False
    log_level: str = "INFO"
    request_id_header: str = "X-Request-ID"
    temporary_input_root: Path = Path(".doxary-tmp")
    max_file_bytes: int = 10 * 1024 * 1024
    max_submission_bytes: int = 25 * 1024 * 1024
    max_image_pages: int = 20
    temporary_input_retention_hours: int = 24
    worker_poll_interval_seconds: float = 2.0
    worker_lease_seconds: int = 300
    worker_max_attempts: int = 3
    worker_retry_delay_seconds: int = 5
    ai_enabled: bool = False
    openai_api_key: str | None = None
    ai_model: str = "gpt-4o-mini"
    ai_reasoning_effort: Literal["low", "medium", "high"] | None = None
    ai_timeout_seconds: float = 60.0

    @field_validator("ai_model", mode="before")
    @classmethod
    def default_empty_model(cls, value: object) -> object:
        return "gpt-4o-mini" if value is None or str(value).strip() == "" else value

    @model_validator(mode="after")
    def require_database_for_production(self) -> "Settings":
        if self.app_env == "production" and not self.database_url:
            raise ValueError("DOXARY_DATABASE_URL is required when DOXARY_APP_ENV=production")
        if self.app_env == "production":
            self.debug = False
        if self.ai_enabled and not self.openai_api_key:
            raise ValueError("DOXARY_OPENAI_API_KEY is required when DOXARY_AI_ENABLED=true")
        if self.ai_timeout_seconds <= 0:
            raise ValueError("DOXARY_AI_TIMEOUT_SECONDS must be positive")
        return self

    @classmethod
    def load(cls, overrides: Mapping[str, Any] | None = None) -> "Settings":
        normalized = {key.lower(): value for key, value in (overrides or {}).items()}
        return cls(**normalized)

    def as_flask_config(self) -> dict[str, Any]:
        return {
            "DEBUG": self.debug,
            "TESTING": self.testing,
            "REQUEST_ID_HEADER": self.request_id_header,
            "MAX_CONTENT_LENGTH": self.max_submission_bytes,
        }

    @property
    def resolved_database_url(self) -> str:
        return self.database_url or "sqlite+pysqlite:///:memory:"
