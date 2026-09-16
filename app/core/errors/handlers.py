import logging

from flask import Flask, jsonify

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
