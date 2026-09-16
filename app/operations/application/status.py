from datetime import UTC, datetime
from enum import StrEnum

from sqlalchemy.orm import Session, sessionmaker

from app.analysis.contracts import AnalysisResult
from app.core.errors import ApplicationError, ErrorCode
from app.operations.domain.operation import OperationStatus
from app.operations.infrastructure.operation_record import OperationRecord
from app.operations.infrastructure.operation_result_record import OperationResultRecord


class PublicOperationStatus(StrEnum):
    ACCEPTED = "accepted"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class OperationStatusView:
    def __init__(
        self,
        operation_id: str,
        status: PublicOperationStatus,
        result: AnalysisResult | None = None,
        failure_code: str | None = None,
    ):
        self.operation_id = operation_id
        self.status = status
        self.result = result
        self.failure_code = failure_code


class OperationStatusQuery:
    """Read-only application boundary for the public operation status resource."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def get(self, operation_id: str) -> OperationStatusView:
        with self._session_factory() as session:
            operation = session.get(OperationRecord, operation_id)
            if operation is None:
                raise ApplicationError(
                    ErrorCode.OPERATION_NOT_FOUND, "Operation was not found.", 404
                )

            status = _public_status(operation.status)
            if status in {PublicOperationStatus.ACCEPTED, PublicOperationStatus.PROCESSING}:
                return OperationStatusView(operation_id, status)
            if status is PublicOperationStatus.FAILED:
                return OperationStatusView(
                    operation_id, status, failure_code=_public_failure(operation.failure_code)
                )

            result_record = (
                session.query(OperationResultRecord)
                .filter_by(operation_id=operation_id)
                .one_or_none()
            )
            if result_record is None:
                raise ApplicationError(
                    ErrorCode.INTERNAL_ERROR, "Operation result is unavailable.", 500
                )
            if result_record.deleted_at is not None or _utc(
                result_record.expires_at
            ) <= datetime.now(UTC):
                raise ApplicationError(
                    ErrorCode.OPERATION_EXPIRED, "Operation result has expired.", 410
                )
            try:
                result = AnalysisResult.model_validate(result_record.result_payload)
                if result_record.schema_version != result.schema_version:
                    raise ValueError("schema version mismatch")
            except Exception as error:
                raise ApplicationError(
                    ErrorCode.INTERNAL_ERROR, "Operation result is unavailable.", 500
                ) from error
            return OperationStatusView(operation_id, PublicOperationStatus.SUCCEEDED, result=result)


def _public_status(status: str) -> PublicOperationStatus:
    if status == OperationStatus.ACCEPTED.value:
        return PublicOperationStatus.ACCEPTED
    if status == OperationStatus.PROCESSING.value:
        return PublicOperationStatus.PROCESSING
    if status in {OperationStatus.SUCCEEDED.value, OperationStatus.PARTIAL.value}:
        return PublicOperationStatus.SUCCEEDED
    return PublicOperationStatus.FAILED


def _public_failure(code: str | None) -> str:
    if code == "missing_temporary_input":
        return "input_unavailable"
    if code in {
        "capability_unavailable",
        "provider_timeout",
        "provider_unavailable",
        "provider_failure",
        "structured_output_invalid",
    }:
        return "analysis_unavailable"
    return "processing_failed"


def _utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)
