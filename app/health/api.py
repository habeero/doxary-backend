from flask import Blueprint, jsonify

from app.core.request_context.correlation import current_request_id

health_blueprint = Blueprint("health", __name__)


@health_blueprint.get("/health")
def health():
    """Process liveness only; it deliberately does not claim database readiness."""
    return jsonify({"status": "ok", "request_id": current_request_id()})
