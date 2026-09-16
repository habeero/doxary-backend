from collections.abc import Mapping
from typing import Any, Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized runtime configuration loaded once at application composition."""

    model_config = SettingsConfigDict(env_prefix="DOXARY_", extra="ignore")

    app_env: Literal["development", "test", "production"] = "development"
    database_url: str | None = None
    debug: bool = False
    testing: bool = False
    log_level: str = "INFO"
    request_id_header: str = "X-Request-ID"

    @model_validator(mode="after")
    def require_database_for_production(self) -> "Settings":
        if self.app_env == "production" and not self.database_url:
            raise ValueError("DOXARY_DATABASE_URL is required when DOXARY_APP_ENV=production")
        if self.app_env == "production":
            self.debug = False
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
        }

    @property
    def resolved_database_url(self) -> str:
        return self.database_url or "sqlite+pysqlite:///:memory:"
