from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from app.core.database import Base
from app.core.identifiers import new_opaque_id
from app.idempotency.record import IdempotencyRecord
from app.operations.domain import Operation, OperationStatus, OperationType
from app.operations.infrastructure.attempt_record import OperationAttemptRecord
from app.operations.infrastructure.repository import SqlAlchemyOperationRepository
from app.usage.infrastructure.ledger import SqlAlchemyUsageLedger
from app.usage.infrastructure.usage_event_record import UsageEventRecord
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session


@pytest.fixture
def session():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as database_session:
        yield database_session


def _operation() -> Operation:
    return Operation(
        operation_id=new_opaque_id(),
        request_id=new_opaque_id(),
        client_document_id="client-side-correlation-only",
        operation_type=OperationType.DOCUMENT_ANALYSIS,
        status=OperationStatus.ACCEPTED,
        created_at=datetime.now(UTC),
    )


def test_operation_repository_stages_without_committing_and_round_trips(session):
    operation = _operation()
    repository = SqlAlchemyOperationRepository(session)

    repository.add(operation)
    assert session.new
    assert (
        repository.get(operation.operation_id).client_document_id == "client-side-correlation-only"
    )
    session.commit()

    assert repository.get(operation.operation_id) == operation


def test_attempt_number_is_unique_per_operation(session):
    operation = _operation()
    SqlAlchemyOperationRepository(session).add(operation)
    session.add_all(
        [
            OperationAttemptRecord(
                attempt_id=new_opaque_id(), operation_id=operation.operation_id, attempt_number=1
            ),
            OperationAttemptRecord(
                attempt_id=new_opaque_id(), operation_id=operation.operation_id, attempt_number=1
            ),
        ]
    )

    with pytest.raises(IntegrityError):
        session.commit()


def test_usage_ledger_uses_decimal_and_immutable_pricing_snapshot(session):
    operation = _operation()
    SqlAlchemyOperationRepository(session).add(operation)
    event = UsageEventRecord(
        usage_event_id=new_opaque_id(),
        operation_id=operation.operation_id,
        operation_type=operation.operation_type.value,
        cost_amount=Decimal("0.01234567"),
        currency="EUR",
        pricing_snapshot_json='{"input_unit_price":"0.00123456","currency":"EUR"}',
        created_at=datetime.now(UTC),
    )

    SqlAlchemyUsageLedger(session).append(event)
    session.commit()
    persisted = session.get(UsageEventRecord, event.usage_event_id)

    assert persisted.cost_amount == Decimal("0.01234567")
    assert persisted.pricing_snapshot_json == event.pricing_snapshot_json


def test_idempotency_scope_and_expiry_are_persisted(session):
    operation = _operation()
    SqlAlchemyOperationRepository(session).add(operation)
    session.add(
        IdempotencyRecord(
            idempotency_record_id=new_opaque_id(),
            scope="anonymous-device-hash",
            key_hash="a" * 64,
            request_fingerprint="b" * 64,
            request_id=operation.request_id,
            operation_id=operation.operation_id,
            state="accepted",
            created_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(hours=24),
        )
    )
    session.commit()

    assert session.query(IdempotencyRecord).one().operation_id == operation.operation_id
