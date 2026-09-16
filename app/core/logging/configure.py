import json
import logging
from datetime import UTC, datetime

from flask import Flask

from app.core.config.settings import Settings


class JsonFormatter(logging.Formatter):
    """Emit only an approved, content-free set of operational fields."""

    allowed_fields = (
        "request_id",
        "operation_id",
        "endpoint",
        "method",
        "status",
        "duration_ms",
        "error_category",
    )

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "event": record.getMessage(),
        }
        for field in self.allowed_fields:
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = str(value)
        return json.dumps(payload, separators=(",", ":"), sort_keys=True)


def configure_logging(app: Flask, settings: Settings) -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    app.logger.handlers.clear()
    app.logger.addHandler(handler)
    app.logger.setLevel(settings.log_level.upper())
    app.logger.propagate = False
