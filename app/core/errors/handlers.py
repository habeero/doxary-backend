import logging

from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException

from app.core.errors.application_error import ApplicationError, ErrorCode
from app.core.request_context.correlation import current_request_id

logger = logging.getLogger(__name__)


def _error_response(error: ApplicationError):
    return (
        jsonify(
            {
                "error": {
                    "code": error.code.value,
                    "message": error.message,
                    "retryable": error.retryable,
                    "details": error.details,
                },
                "request_id": current_request_id(),
            }
        ),
        error.status_code,
    )


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(ApplicationError)
    def handle_application_error(error: ApplicationError):
        return _error_response(error)

    @app.errorhandler(HTTPException)
    def handle_http_exception(error: HTTPException):
        code = (
            "not_found"
            if error.code == 404
            else "method_not_allowed"
            if error.code == 405
            else "http_error"
        )
        return jsonify(
            {
                "error": {
                    "code": code,
                    "message": error.description,
                    "retryable": False,
                    "details": {},
                },
                "request_id": current_request_id(),
            }
        ), error.code

    @app.errorhandler(Exception)
    def handle_unexpected_error(error: Exception):
        logger.error(
            "unexpected_request_error",
            extra={"request_id": current_request_id(), "error_category": ErrorCode.INTERNAL_ERROR},
        )
        safe_error = ApplicationError(
            code=ErrorCode.INTERNAL_ERROR,
            message="An unexpected error occurred.",
            status_code=500,
        )
        return _error_response(safe_error)
