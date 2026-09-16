from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.analysis.contracts import AnalysisResult
from app.operations.domain.operation_result import OperationResult
from app.operations.infrastructure.operation_result_record import OperationResultRecord


class PersistedResultInvalidError(ValueError):
    """Raised when stored data cannot be revalidated as the Doxary contract."""


class SqlAlchemyOperationResultRepository:
    """Stores validated contract data and stages changes; callers own transactions."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, result: OperationResult) -> None:
        if result.schema_version != result.result.schema_version:
            raise ValueError("operation result and analysis schema versions must match")
        payload = result.result.model_dump(mode="json")
        self._session.add(
            OperationResultRecord(
                operation_result_id=result.operation_result_id,
                operation_id=result.operation_id,
                schema_version=result.schema_version,
                result_payload=payload,
                created_at=result.created_at,
                expires_at=result.expires_at,
                deleted_at=result.deleted_at,
            )
        )

    def get(self, operation_id: str) -> OperationResult | None:
        record = (
            self._session.query(OperationResultRecord)
            .filter_by(operation_id=operation_id)
            .one_or_none()
        )
        if record is None or record.deleted_at is not None or _is_expired(record.expires_at):
            return None
        try:
            result = AnalysisResult.model_validate(record.result_payload)
        except Exception as error:
            raise PersistedResultInvalidError(
                "persisted operation result failed contract validation"
            ) from error
        if record.schema_version != result.schema_version:
            raise PersistedResultInvalidError(
                "persisted schema version does not match result payload"
            )
        return OperationResult(
            operation_result_id=record.operation_result_id,
            operation_id=record.operation_id,
            schema_version=record.schema_version,
            result=result,
            created_at=_aware_utc(record.created_at),
            expires_at=_aware_utc(record.expires_at),
            deleted_at=record.deleted_at,
        )


def _is_expired(value: datetime) -> bool:
    return _aware_utc(value) <= datetime.now(UTC)


def _aware_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)
