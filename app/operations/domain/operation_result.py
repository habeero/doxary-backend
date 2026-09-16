from dataclasses import dataclass
from datetime import datetime

from app.analysis.contracts import AnalysisResult


@dataclass(frozen=True)
class OperationResult:
    """Temporary delivery envelope; never a server Document or durable Flutter state."""

    operation_result_id: str
    operation_id: str
    schema_version: str
    result: AnalysisResult
    created_at: datetime
    expires_at: datetime
    deleted_at: datetime | None = None

    def is_expired(self, at: datetime) -> bool:
        return at >= self.expires_at or self.deleted_at is not None
