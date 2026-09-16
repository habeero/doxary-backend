import hashlib
import json
from datetime import UTC, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.core.errors import ApplicationError, ErrorCode
from app.core.identifiers import new_opaque_id
from app.core.time import utc_now
from app.idempotency.record import IdempotencyRecord
from app.intake.application.temporary_store import TemporaryDocumentStore
from app.intake.domain.input import DocumentInput
from app.intake.infrastructure.temporary_input_record import TemporaryInputRecord
from app.operations.domain.operation import Operation, OperationStatus, OperationType
from app.operations.infrastructure.operation_record import OperationRecord


class SubmissionService:
    """Creates accepted operations and temporary input with compensating cleanup."""

    def __init__(
        self,
        session_factory: sessionmaker[Session],
        store: TemporaryDocumentStore,
        retention_hours: int,
    ) -> None:
        self._session_factory = session_factory
        self._store = store
        self._retention = timedelta(hours=retention_hours)

    def submit(
        self, document_input: DocumentInput, idempotency_key: str, request_id: str
    ) -> Operation:
        now = utc_now()
        key_hash = _sha256(idempotency_key)
        fingerprint = _fingerprint(document_input)
        with self._session_factory() as session:
            existing = session.scalar(
                select(IdempotencyRecord).where(
                    IdempotencyRecord.scope == "anonymous",
                    IdempotencyRecord.key_hash == key_hash,
                )
            )
            if existing is not None:
                if existing.request_fingerprint != fingerprint:
                    raise ApplicationError(
                        ErrorCode.IDEMPOTENCY_CONFLICT,
                        "The idempotency key was already used for different input.",
                        409,
                    )
                if existing.operation_id is None:
                    raise ApplicationError(
                        ErrorCode.INTERNAL_ERROR, "The submission is unavailable.", 500
                    )
                operation = session.get(OperationRecord, existing.operation_id)
                if operation is None:
                    raise ApplicationError(
                        ErrorCode.INTERNAL_ERROR, "The submission is unavailable.", 500
                    )
                return _operation_from_record(operation)

            operation_id = new_opaque_id()
            expires_at = now + self._retention
            stored = None
            try:
                stored = self._store.store(operation_id, document_input, expires_at)
                operation = Operation(
                    operation_id=operation_id,
                    request_id=request_id,
                    client_document_id=document_input.client_document_id,
                    operation_type=OperationType.DOCUMENT_ANALYSIS,
                    status=OperationStatus.ACCEPTED,
                    created_at=now,
                )
                session.add(
                    OperationRecord(
                        operation_id=operation.operation_id,
                        request_id=operation.request_id,
                        client_document_id=operation.client_document_id,
                        operation_type=operation.operation_type.value,
                        status=operation.status.value,
                        created_at=operation.created_at,
                    )
                )
                # Ensure the FK target exists before SQLAlchemy flushes the idempotency row.
                session.flush()
                session.add(
                    IdempotencyRecord(
                        idempotency_record_id=new_opaque_id(),
                        scope="anonymous",
                        key_hash=key_hash,
                        request_fingerprint=fingerprint,
                        request_id=request_id,
                        operation_id=operation_id,
                        state="accepted",
                        created_at=now,
                        expires_at=expires_at,
                    )
                )
                session.add(
                    TemporaryInputRecord(
                        operation_id=operation_id,
                        input_kind=document_input.kind.value,
                        client_document_id=document_input.client_document_id,
                        output_language=document_input.output_language,
                        output_style=document_input.output_style,
                        storage_reference=stored.storage_reference,
                        file_metadata=list(stored.file_metadata),
                        created_at=stored.created_at,
                        expires_at=stored.expires_at,
                    )
                )
                session.commit()
                return operation
            except ApplicationError:
                if stored is not None:
                    self._store.delete(stored.storage_reference)
                raise
            except Exception as error:
                session.rollback()
                if stored is not None:
                    self._store.delete(stored.storage_reference)
                raise ApplicationError(
                    ErrorCode.STORAGE_FAILURE, "Temporary input could not be accepted.", 503, True
                ) from error


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _fingerprint(document_input: DocumentInput) -> str:
    payload: dict[str, Any] = {
        "client_document_id": document_input.client_document_id,
        "kind": document_input.kind.value,
        "output_language": document_input.output_language,
        "output_style": document_input.output_style,
        "files": [
            {"sha256": file.sha256, "media_type": file.media_type, "page_index": file.page_index}
            for file in document_input.files
        ],
    }
    return _sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")))


def _operation_from_record(record: OperationRecord) -> Operation:
    return Operation(
        operation_id=record.operation_id,
        request_id=record.request_id,
        client_document_id=record.client_document_id,
        operation_type=OperationType(record.operation_type),
        status=OperationStatus(record.status),
        created_at=record.created_at.replace(tzinfo=UTC)
        if record.created_at.tzinfo is None
        else record.created_at,
        started_at=record.started_at,
        completed_at=record.completed_at,
        failure_code=record.failure_code,
    )
