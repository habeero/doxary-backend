from typing import Protocol

from app.operations.domain.operation_result import OperationResult


class OperationResultRepository(Protocol):
    def add(self, result: OperationResult) -> None: ...

    def get(self, operation_id: str) -> OperationResult | None: ...
