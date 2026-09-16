from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from app.analysis.contracts import (
    AnalysisResult,
    AnalysisStatus,
    Explanation,
    ExplanationStyle,
)
from app.core.database import Base
from app.core.identifiers import new_opaque_id
from app.operations.domain import Operation, OperationStatus, OperationType
from app.operations.domain.operation_result import OperationResult
from app.operations.infrastructure.operation_result_record import OperationResultRecord
from app.operations.infrastructure.operation_result_repository import (
    PersistedResultInvalidError,
    SqlAlchemyOperationResultRepository,
)
from app.operations.infrastructure.repository import SqlAlchemyOperationRepository
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session


@pytest.fixture
def session():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as database_session:
        yield database_session


def make_operation() -> Operation:
    return Operation(
        operation_id=new_opaque_id(),
        request_id=new_opaque_id(),
        operation_type=OperationType.DOCUMENT_ANALYSIS,
        status=OperationStatus.ACCEPTED,
        created_at=datetime.now(UTC),
    )


def make_result(operation_id: str, expires_at: datetime | None = None) -> OperationResult:
    analysis = AnalysisResult(
        analysis_status=AnalysisStatus.COMPLETE,
        client_document_id="client-doc",
        explanation=Explanation(
            language="ar", style=ExplanationStyle.STANDARD, summary="ملخص", body="شرح"
        ),
        extracted_facts={
            "amounts": [{"value": Decimal("1.25"), "currency": "EUR", "purpose": "Gebühr"}]
        },
    )
    return OperationResult(
        operation_result_id=new_opaque_id(),
        operation_id=operation_id,
        schema_version=analysis.schema_version,
        result=analysis,
        created_at=datetime.now(UTC),
        expires_at=expires_at or datetime.now(UTC) + timedelta(hours=1),
    )


def test_validated_result_round_trips_and_repository_does_not_commit(session):
    operation = make_operation()
    SqlAlchemyOperationRepository(session).add(operation)
    result = make_result(operation.operation_id)
    repository = SqlAlchemyOperationResultRepository(session)

    repository.add(result)
    assert session.new
    session.commit()
    loaded = repository.get(operation.operation_id)

    assert loaded is not None
    assert loaded.result.schema_version == "analysis_result.v1"
    assert loaded.result.extracted_facts.amounts[0].value == Decimal("1.25")


def test_one_result_per_operation_and_expired_results_are_unavailable(session):
    operation = make_operation()
    SqlAlchemyOperationRepository(session).add(operation)
    repository = SqlAlchemyOperationResultRepository(session)
    repository.add(make_result(operation.operation_id, datetime.now(UTC) - timedelta(seconds=1)))
    session.commit()

    assert repository.get(operation.operation_id) is None

    second_operation = make_operation()
    SqlAlchemyOperationRepository(session).add(second_operation)
    repository.add(make_result(second_operation.operation_id))
    repository.add(make_result(second_operation.operation_id))
    with pytest.raises(IntegrityError):
        session.commit()


def test_corrupt_persisted_payload_fails_closed(session):
    operation = make_operation()
    SqlAlchemyOperationRepository(session).add(operation)
    session.add(
        OperationResultRecord(
            operation_result_id=new_opaque_id(),
            operation_id=operation.operation_id,
            schema_version="analysis_result.v1",
            result_payload={"analysis_status": "complete", "client_document_id": "doc"},
            created_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(hours=1),
        )
    )
    session.commit()

    with pytest.raises(PersistedResultInvalidError):
        SqlAlchemyOperationResultRepository(session).get(operation.operation_id)
