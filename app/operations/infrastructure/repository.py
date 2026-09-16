from sqlalchemy.orm import Session

from app.core.time import as_utc
from app.operations.domain.operation import Operation, OperationStatus, OperationType
from app.operations.infrastructure.operation_record import OperationRecord


class SqlAlchemyOperationRepository:
    """Stages operation changes; the caller owns commit/rollback."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, operation: Operation) -> None:
        self._session.add(
            OperationRecord(
                operation_id=operation.operation_id,
                request_id=operation.request_id,
                client_document_id=operation.client_document_id,
                operation_type=operation.operation_type.value,
                status=operation.status.value,
                created_at=operation.created_at,
                started_at=operation.started_at,
                completed_at=operation.completed_at,
                failure_code=operation.failure_code,
            )
        )

    def get(self, operation_id: str) -> Operation | None:
        record = self._session.get(OperationRecord, operation_id)
        if record is None:
            return None
        return Operation(
            operation_id=record.operation_id,
            request_id=record.request_id,
            client_document_id=record.client_document_id,
            operation_type=OperationType(record.operation_type),
            status=OperationStatus(record.status),
            created_at=as_utc(record.created_at),
            started_at=as_utc(record.started_at),
            completed_at=as_utc(record.completed_at),
            failure_code=record.failure_code,
        )
