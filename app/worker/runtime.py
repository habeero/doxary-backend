import logging
import socket
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Protocol

from sqlalchemy import or_, select

from app.core.time import utc_now
from app.intake.application.temporary_store import TemporaryDocumentStore
from app.intake.domain.input import DocumentInput
from app.intake.infrastructure.temporary_input_record import TemporaryInputRecord
from app.operations.infrastructure.attempt_record import OperationAttemptRecord
from app.operations.infrastructure.operation_record import OperationRecord

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class ExecutionOutcome:
    kind: str
    failure_code: str | None = None
    retryable: bool = False


class DocumentAnalysisExecutor(Protocol):
    def execute(self, document: DocumentInput) -> ExecutionOutcome: ...


class UnavailableAnalysisExecutor:
    def execute(self, document: DocumentInput) -> ExecutionOutcome:
        return ExecutionOutcome("failure", "capability_unavailable", True)


class AnalysisWorker:
    def __init__(
        self,
        session_factory,
        document_store: TemporaryDocumentStore,
        executor: DocumentAnalysisExecutor | None = None,
        *,
        worker_id: str | None = None,
        lease_seconds: int = 300,
        poll_interval_seconds: float = 2.0,
        max_attempts: int = 3,
        retry_delay_seconds: int = 5,
    ):
        self.session_factory = session_factory
        self.store = document_store
        self.executor = executor or UnavailableAnalysisExecutor()
        self.worker_id = worker_id or f"{socket.gethostname()}-{uuid.uuid4().hex[:12]}"
        self.lease_seconds = lease_seconds
        self.poll_interval_seconds = poll_interval_seconds
        self.max_attempts = max_attempts
        self.retry_delay_seconds = retry_delay_seconds

    def claim_one(self, now: datetime | None = None) -> str | None:
        now = now or utc_now()
        with self.session_factory() as session, session.begin():
            stmt = (
                select(OperationRecord)
                .where(
                    OperationRecord.operation_type == "document_analysis",
                    or_(
                        OperationRecord.status == "accepted", OperationRecord.status == "processing"
                    ),
                    or_(
                        OperationRecord.next_attempt_at.is_(None),
                        OperationRecord.next_attempt_at <= now,
                    ),
                    or_(
                        OperationRecord.status == "accepted",
                        OperationRecord.lease_expires_at <= now,
                    ),
                    select(TemporaryInputRecord.operation_id)
                    .where(TemporaryInputRecord.operation_id == OperationRecord.operation_id)
                    .exists(),
                )
                .order_by(OperationRecord.created_at)
                .with_for_update(skip_locked=True)
                .limit(1)
            )
            record = session.execute(stmt).scalar_one_or_none()
            if record is None:
                return None
            record.status = "processing"
            record.started_at = record.started_at or now
            record.worker_id = self.worker_id
            record.claimed_at = now
            record.lease_expires_at = now + timedelta(seconds=self.lease_seconds)
            record.next_attempt_at = None
            attempt_number = (
                session.query(OperationAttemptRecord)
                .filter_by(operation_id=record.operation_id)
                .count()
                + 1
            )
            session.add(
                OperationAttemptRecord(
                    attempt_id=str(uuid.uuid4()),
                    operation_id=record.operation_id,
                    attempt_number=attempt_number,
                    started_at=now,
                    outcome="processing",
                )
            )
            return record.operation_id

    def process_one(self) -> bool:
        operation_id = self.claim_one()
        if not operation_id:
            return False
        now = utc_now()
        try:
            with self.session_factory() as session:
                input_record = session.get(TemporaryInputRecord, operation_id)
            document = self.store.load(input_record.storage_reference) if input_record else None
            if document is None:
                raise RuntimeError("missing_temporary_input")
            outcome = self.executor.execute(document)
            self._finish(operation_id, outcome, now)
        except Exception as exc:
            code = (
                "missing_temporary_input"
                if str(exc) == "missing_temporary_input"
                else "internal_error"
            )
            self._finish(
                operation_id, ExecutionOutcome("failure", code, code == "internal_error"), now
            )
            log.exception(
                "worker operation failed",
                extra={"operation_id": operation_id, "worker_id": self.worker_id},
            )
        return True

    def _finish(self, operation_id: str, outcome: ExecutionOutcome, now: datetime) -> None:
        with self.session_factory() as session, session.begin():
            record = session.get(OperationRecord, operation_id)
            attempt = session.execute(
                select(OperationAttemptRecord)
                .where(
                    OperationAttemptRecord.operation_id == operation_id,
                    OperationAttemptRecord.outcome == "processing",
                )
                .order_by(OperationAttemptRecord.attempt_number.desc())
            ).scalar_one()
            attempt.completed_at = now
            attempt.outcome = "succeeded" if outcome.kind == "success" else "failed"
            attempt.failure_code = outcome.failure_code
            record.worker_id = record.claimed_at = record.lease_expires_at = None
            if outcome.kind == "success":
                record.status = "succeeded"
                record.completed_at = now
            elif outcome.retryable and attempt.attempt_number < self.max_attempts:
                record.status = "accepted"
                record.failure_code = outcome.failure_code
                record.next_attempt_at = now + timedelta(seconds=self.retry_delay_seconds)
            else:
                record.status = "failed"
                record.failure_code = outcome.failure_code
                record.completed_at = now

    def run_once(self) -> bool:
        return self.process_one()

    def run(self, stop_event) -> None:
        while not stop_event.is_set():
            if not self.process_one():
                stop_event.wait(self.poll_interval_seconds)
