from uuid import UUID, uuid4

from flask import Flask, Response, g, request

REQUEST_ID_KEY = "doxary_request_id"


def _valid_request_id(value: str | None) -> bool:
    if not value:
        return False
    try:
        UUID(value)
    except (ValueError, TypeError, AttributeError):
        return False
    return True


def current_request_id() -> str:
    return getattr(g, REQUEST_ID_KEY, "unknown")


def register_request_correlation(app: Flask) -> None:
    @app.before_request
    def assign_request_id() -> None:
        candidate = request.headers.get(app.config["REQUEST_ID_HEADER"])
        setattr(g, REQUEST_ID_KEY, candidate if _valid_request_id(candidate) else str(uuid4()))

    @app.after_request
    def return_request_id(response: Response) -> Response:
        response.headers[app.config["REQUEST_ID_HEADER"]] = current_request_id()
        return response
