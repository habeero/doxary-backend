from collections.abc import Mapping
from typing import Any

from flask import Flask

from app.api.v1.blueprint import api_v1
from app.bootstrap.container import build_container
from app.core.config.settings import Settings
from app.core.errors.handlers import register_error_handlers
from app.core.logging.configure import configure_logging
from app.core.request_context.correlation import register_request_correlation


def create_app(config_overrides: Mapping[str, Any] | None = None) -> Flask:
    """Create an isolated Flask application without import-time resource creation."""
    settings = Settings.load(config_overrides)
    app = Flask(__name__)
    app.config.from_mapping(settings.as_flask_config())
    app.config["PROPAGATE_EXCEPTIONS"] = False

    configure_logging(app, settings)
    app.extensions["doxary_container"] = build_container(settings)
    register_request_correlation(app)
    register_error_handlers(app)
    app.register_blueprint(api_v1, url_prefix="/api/v1")
    return app
