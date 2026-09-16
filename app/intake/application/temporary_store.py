from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from app.intake.domain.input import DocumentInput


@dataclass(frozen=True)
class StoredInput:
    storage_reference: str
    created_at: datetime
    expires_at: datetime
    file_metadata: tuple[dict[str, object], ...]


class TemporaryDocumentStore(Protocol):
    def store(
        self, operation_id: str, document_input: DocumentInput, expires_at: datetime
    ) -> StoredInput: ...

    def delete(self, storage_reference: str) -> None: ...

    def retrieve_metadata(self, storage_reference: str) -> StoredInput: ...

    def delete_expired(self, at: datetime) -> int: ...
