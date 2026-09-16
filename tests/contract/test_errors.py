from app.core.errors import ApplicationError, ErrorCode
from flask import Blueprint


def test_typed_error_uses_documented_envelope(app, client):
    routes = Blueprint("error_contract", __name__)

    @routes.get("/typed-error")
    def typed_error():
        raise ApplicationError(
            code=ErrorCode.VALIDATION_ERROR,
            message="Input is invalid.",
            status_code=400,
            details={"field": "example"},
        )

    app.register_blueprint(routes)
    response = client.get("/typed-error")

    assert response.status_code == 400
    assert response.json["error"] == {
        "code": "validation_error",
        "message": "Input is invalid.",
        "retryable": False,
        "details": {"field": "example"},
    }
    assert response.json["request_id"] == response.headers["X-Request-ID"]


def test_unexpected_error_is_sanitized(app, client):
    routes = Blueprint("unexpected_error_contract", __name__)

    @routes.get("/unexpected-error")
    def unexpected_error():
        raise RuntimeError("sensitive document text must not be returned")

    app.register_blueprint(routes)
    response = client.get("/unexpected-error")

    assert response.status_code == 500
    assert response.json["error"]["code"] == "internal_error"
    assert "sensitive document text" not in response.get_data(as_text=True)
