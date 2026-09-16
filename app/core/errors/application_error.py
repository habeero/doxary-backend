from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class ErrorCode(StrEnum):
    VALIDATION_ERROR = "validation_error"
    UNSUPPORTED_MEDIA = "unsupported_media"
    MALFORMED_FILE = "malformed_file"
    CORRUPT_FILE = "corrupt_file"
    DOCUMENT_QUALITY_INSUFFICIENT = "document_quality_insufficient"
    CAPABILITY_UNAVAILABLE = "capability_unavailable"
    QUOTA_EXCEEDED = "quota_exceeded"
    RATE_LIMITED = "rate_limited"
    PROVIDER_TIMEOUT = "provider_timeout"
    PROVIDER_UNAVAILABLE = "provider_unavailable"
    PROVIDER_FAILURE = "provider_failure"
    STRUCTURED_OUTPUT_INVALID = "structured_output_invalid"
    OPERATION_NOT_FOUND = "operation_not_found"
    OPERATION_EXPIRED = "operation_expired"
    CONTEXT_NOT_FOUND = "context_not_found"
    CONTEXT_EXPIRED = "context_expired"
    INTERNAL_ERROR = "internal_error"
    INVALID_MULTIPART = "invalid_multipart"
    UNSUPPORTED_INPUT_KIND = "unsupported_input_kind"
    FILE_TOO_LARGE = "file_too_large"
    TOO_MANY_PAGES = "too_many_pages"
    EMPTY_FILE = "empty_file"
    CONFLICTING_PAGE_ORDER = "conflicting_page_order"
    IDEMPOTENCY_CONFLICT = "idempotency_conflict"
    STORAGE_FAILURE = "storage_failure"


@dataclass(frozen=True)
class ApplicationError(Exception):
    code: ErrorCode
    message: str
    status_code: int
    retryable: bool = False
    details: dict[str, Any] = field(default_factory=dict)
