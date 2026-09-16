from datetime import UTC, datetime

import pytest
from app.operations.domain import Operation, OperationStatus, OperationType


def test_operation_has_only_documented_lifecycle_transitions():
    accepted = Operation(
        operation_id="operation",
        request_id="request",
        operation_type=OperationType.DOCUMENT_ANALYSIS,
        status=OperationStatus.ACCEPTED,
        created_at=datetime.now(UTC),
    )

    processing = accepted.transition_to(OperationStatus.PROCESSING, datetime.now(UTC))
    complete = processing.transition_to(OperationStatus.SUCCEEDED, datetime.now(UTC))

    assert processing.started_at is not None
    assert complete.completed_at is not None
    with pytest.raises(ValueError):
        complete.transition_to(OperationStatus.PROCESSING, datetime.now(UTC))
