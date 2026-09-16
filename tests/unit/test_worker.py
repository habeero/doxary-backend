from datetime import UTC, datetime, timedelta

from app.core.database.metadata import Base
from app.intake.infrastructure.temporary_input_record import TemporaryInputRecord
from app.operations.infrastructure.attempt_record import OperationAttemptRecord
from app.operations.infrastructure.operation_record import OperationRecord
from app.worker.runtime import AnalysisWorker, ExecutionOutcome
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


class Store:
    def load(self, reference):
        return object()


class Executor:
    def __init__(self, outcome):
        self.outcome = outcome

    def execute(self, document):
        return self.outcome


def worker_fixture():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    now = datetime.now(UTC)
    with factory.begin() as session:
        session.add(
            OperationRecord(
                operation_id="op-1",
                request_id="r-1",
                operation_type="document_analysis",
                status="accepted",
                created_at=now,
            )
        )
        session.add(
            TemporaryInputRecord(
                operation_id="op-1",
                input_kind="pdf",
                storage_reference="op-1",
                file_metadata=[],
                created_at=now,
                expires_at=now + timedelta(hours=1),
            )
        )
    return factory


def test_claim_and_successful_execution():
    factory = worker_fixture()
    worker = AnalysisWorker(factory, Store(), Executor(ExecutionOutcome("success")), worker_id="w1")
    assert worker.run_once() is True
    with factory() as session:
        assert session.get(OperationRecord, "op-1").status == "succeeded"
        assert session.query(OperationAttemptRecord).count() == 1


def test_retryable_failure_is_bounded():
    factory = worker_fixture()
    worker = AnalysisWorker(
        factory,
        Store(),
        Executor(ExecutionOutcome("failure", "provider_timeout", True)),
        worker_id="w1",
        retry_delay_seconds=0,
        max_attempts=1,
    )
    assert worker.run_once() is True
    with factory() as session:
        record = session.get(OperationRecord, "op-1")
        assert record.status == "failed"
        assert record.failure_code == "provider_timeout"
