from datetime import UTC, datetime, timedelta

from app.core.database.metadata import Base
from app.intake.infrastructure.temporary_input_record import TemporaryInputRecord
from app.operations.infrastructure.attempt_record import OperationAttemptRecord
from app.operations.infrastructure.operation_record import OperationRecord
from app.worker.runtime import AnalysisWorker, ExecutionOutcome
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


class Store:
    def __init__(self, missing=False):
        self.missing = missing

    def load(self, reference):
        if self.missing:
            raise FileNotFoundError(reference)
        return object()


class Executor:
    def __init__(self, outcome=None, error=None):
        self.outcome, self.error = outcome, error

    def execute(self, document):
        if self.error:
            raise self.error
        return self.outcome


def fixture(status="accepted", lease=None, expires=None, deleted=None):
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    now = datetime.now(UTC)
    with factory.begin() as s:
        s.add(
            OperationRecord(
                operation_id="op-1",
                request_id="r-1",
                operation_type="document_analysis",
                status=status,
                created_at=now,
                worker_id="old" if lease else None,
                lease_expires_at=lease,
            )
        )
        s.add(
            TemporaryInputRecord(
                operation_id="op-1",
                input_kind="pdf",
                storage_reference="op-1",
                file_metadata=[],
                created_at=now,
                expires_at=expires or now + timedelta(hours=1),
                deleted_at=deleted,
            )
        )
    return factory


def state(factory):
    with factory() as s:
        return s.get(OperationRecord, "op-1"), s.query(OperationAttemptRecord).all()


def test_no_work_available():
    assert AnalysisWorker(fixture(status="succeeded"), Store()).run_once() is False


def test_claim_success_and_attempt_history():
    f = fixture()
    w = AnalysisWorker(f, Store(), Executor(ExecutionOutcome("success")), worker_id="w1")
    assert w.run_once() is True
    r, a = state(f)
    assert r.status == "succeeded" and a[0].attempt_number == 1 and a[0].outcome == "succeeded"


def test_active_lease_not_reclaimed_but_stale_lease_is():
    assert (
        AnalysisWorker(
            fixture(status="processing", lease=datetime.now(UTC) + timedelta(minutes=5)), Store()
        ).claim_one()
        is None
    )
    f = fixture(status="processing", lease=datetime.now(UTC) - timedelta(seconds=1))
    assert AnalysisWorker(f, Store(), worker_id="new").claim_one() == "op-1"


def test_retryable_failure_is_bounded_by_attempt_history():
    f = fixture()
    w = AnalysisWorker(
        f,
        Store(),
        Executor(ExecutionOutcome("failure", "provider_timeout", True)),
        retry_delay_seconds=0,
        max_attempts=2,
    )
    w.run_once()
    assert state(f)[0].status == "accepted"
    w.run_once()
    assert state(f)[0].status == "failed" and len(state(f)[1]) == 2


def test_nonretryable_unavailable_missing_expired_deleted_fail():
    cases = [
        (Executor(ExecutionOutcome("failure", "invalid_input", False)), Store(), {}),
        (None, Store(), {}),
        (None, Store(missing=True), {}),
        (None, Store(), {"expires": datetime.now(UTC) - timedelta(seconds=1)}),
        (None, Store(), {"deleted": datetime.now(UTC)}),
    ]
    for executor, store, kwargs in cases:
        f = fixture(**kwargs)
        AnalysisWorker(f, store, executor, max_attempts=1).run_once()
        assert state(f)[0].status == "failed"


def test_executor_exception_isolated_and_run_once_bounded():
    f = fixture()
    w = AnalysisWorker(f, Store(), Executor(error=RuntimeError("boom")), max_attempts=1)
    assert w.run_once() is True and state(f)[0].failure_code == "internal_error"
    assert w.run_once() is False
