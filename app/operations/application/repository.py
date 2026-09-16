from typing import Protocol

from app.operations.domain.operation import Operation


class OperationRepository(Protocol):
    def add(self, operation: Operation) -> None: ...

    def get(self, operation_id: str) -> Operation | None: ...
