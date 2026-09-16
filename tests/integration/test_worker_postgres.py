"""Opt-in live PostgreSQL claim/lease verification.

Run with DOXARY_DATABASE_URL set and ``pytest -m postgres``. These tests do
not run as part of the portable SQLite suite.
"""

import os
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from app.intake.infrastructure.temporary_input_record import TemporaryInputRecord
from app.operations.infrastructure.attempt_record import OperationAttemptRecord
from app.operations.infrastructure.operation_record import OperationRecord
from app.worker.runtime import AnalysisWorker
from sqlalchemy import create_engine, delete
from sqlalchemy.orm import sessionmaker

pytestmark = [
    pytest.mark.postgres,
    pytest.mark.skipif(
        not os.getenv("DOXARY_DATABASE_URL"),
        reason="set DOXARY_DATABASE_URL for live PostgreSQL tests",
    ),
]


class Store:
    def load(self, reference):
        return object()


def setup_db():
    engine = create_engine(os.environ["DOXARY_DATABASE_URL"], pool_pre_ping=True)
    return engine, sessionmaker(bind=engine, expire_on_commit=False)


def add_operation(factory, *, status="accepted", lease=None):
    operation_id = str(uuid4())
    now = datetime.now(UTC)
    with factory.begin() as session:
        session.add(
            OperationRecord(
                operation_id=operation_id,
                request_id=str(uuid4()),
                operation_type="document_analysis",
                status=status,
                created_at=now,
                worker_id="active" if lease else None,
                lease_expires_at=lease,
            )
        )
        session.flush()
        session.add(
            TemporaryInputRecord(
                operation_id=operation_id,
                input_kind="pdf",
                storage_reference=operation_id,
                file_metadata=[],
                created_at=now,
                expires_at=now + timedelta(hours=1),
            )
        )
    return operation_id


def cleanup(engine, ids):
    with engine.begin() as connection:
        connection.execute(
            delete(OperationAttemptRecord).where(OperationAttemptRecord.operation_id.in_(ids))
        )
        connection.execute(
            delete(TemporaryInputRecord).where(TemporaryInputRecord.operation_id.in_(ids))
        )
        connection.execute(delete(OperationRecord).where(OperationRecord.operation_id.in_(ids)))


def test_live_claim_and_skip_locked_selects_distinct_operations():
    engine, factory = setup_db()
    ids = [add_operation(factory), add_operation(factory)]
    try:
        workers = [AnalysisWorker(factory, Store(), worker_id=f"pg-{i}") for i in range(2)]
        with ThreadPoolExecutor(max_workers=2) as pool:
            claimed = list(pool.map(lambda worker: worker.claim_one(), workers))
        assert set(claimed) == set(ids)
    finally:
        cleanup(engine, ids)
        engine.dispose()


def test_live_same_operation_can_only_be_claimed_once():
    engine, factory = setup_db()
    operation_id = add_operation(factory)
    try:
        workers = [AnalysisWorker(factory, Store(), worker_id=f"pg-{i}") for i in range(2)]
        with ThreadPoolExecutor(max_workers=2) as pool:
            claimed = list(pool.map(lambda worker: worker.claim_one(), workers))
        assert claimed.count(operation_id) == 1 and claimed.count(None) == 1
    finally:
        cleanup(engine, [operation_id])
        engine.dispose()


def test_live_active_and_stale_leases():
    engine, factory = setup_db()
    active = add_operation(
        factory, status="processing", lease=datetime.now(UTC) + timedelta(minutes=5)
    )
    stale = add_operation(
        factory, status="processing", lease=datetime.now(UTC) - timedelta(seconds=1)
    )
    try:
        worker = AnalysisWorker(factory, Store(), worker_id="pg-reclaimer")
        assert worker.claim_one() == stale
        assert worker.claim_one() is None
    finally:
        cleanup(engine, [active, stale])
        engine.dispose()


def test_live_claim_commits_before_later_work_can_update_row():
    engine, factory = setup_db()
    operation_id = add_operation(factory)
    try:
        worker = AnalysisWorker(factory, Store(), worker_id="pg-transaction")
        assert worker.claim_one() == operation_id
        with factory.begin() as session:
            record = session.get(OperationRecord, operation_id)
            record.failure_code = "lock_released"
        with factory() as session:
            assert session.get(OperationRecord, operation_id).failure_code == "lock_released"
    finally:
        cleanup(engine, [operation_id])
        engine.dispose()
