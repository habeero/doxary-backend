from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum


class OperationType(StrEnum):
    DOCUMENT_ANALYSIS = "document_analysis"
    DOCUMENT_QUESTION = "document_question"
    REPLY_DRAFT = "reply_draft"
    REANALYSIS = "reanalysis"


class OperationStatus(StrEnum):
    ACCEPTED = "accepted"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    PARTIAL = "partial"
    FAILED = "failed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


_ALLOWED_TRANSITIONS = {
    OperationStatus.ACCEPTED: {
        OperationStatus.PROCESSING,
        OperationStatus.CANCELLED,
        OperationStatus.EXPIRED,
    },
    OperationStatus.PROCESSING: {
        OperationStatus.SUCCEEDED,
        OperationStatus.PARTIAL,
        OperationStatus.FAILED,
        OperationStatus.CANCELLED,
        OperationStatus.EXPIRED,
    },
}


@dataclass(frozen=True)
class Operation:
    operation_id: str
    request_id: str
    operation_type: OperationType
    status: OperationStatus
    created_at: datetime
    client_document_id: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    failure_code: str | None = None

    def transition_to(self, target: OperationStatus, occurred_at: datetime) -> "Operation":
        if target not in _ALLOWED_TRANSITIONS.get(self.status, set()):
            raise ValueError(f"Cannot transition operation from {self.status} to {target}")
        if target is OperationStatus.PROCESSING:
            return replace(self, status=target, started_at=occurred_at)
        return replace(self, status=target, completed_at=occurred_at)
