import json
import shutil
from datetime import UTC, datetime
from pathlib import Path

from app.intake.application.temporary_store import StoredInput
from app.intake.domain.input import DocumentInput, InputFile, InputKind


class LocalTemporaryDocumentStore:
    """Stores each submission below a server-owned operation directory."""

    def __init__(self, root: Path) -> None:
        self._root = root.resolve()

    def store(
        self, operation_id: str, document_input: DocumentInput, expires_at: datetime
    ) -> StoredInput:
        directory = (self._root / operation_id).resolve()
        if directory.parent != self._root:
            raise ValueError("invalid operation storage identity")
        metadata: list[dict[str, object]] = []
        try:
            directory.mkdir(parents=True, exist_ok=False)
            for index, file in enumerate(document_input.files):
                target = directory / f"file-{index:04d}.bin"
                target.write_bytes(file.content)
                metadata.append(
                    {
                        "media_type": file.media_type,
                        "original_filename": file.original_filename,
                        "page_index": file.page_index,
                        "size_bytes": len(file.content),
                        "sha256": file.sha256,
                    }
                )
            created_at = datetime.now(UTC)
            payload = {
                "storage_reference": operation_id,
                "created_at": created_at.isoformat(),
                "expires_at": expires_at.isoformat(),
                "input_kind": document_input.kind.value,
                "files": metadata,
            }
            (directory / "manifest.json").write_text(
                json.dumps(payload, separators=(",", ":")), encoding="utf-8"
            )
            return StoredInput(operation_id, created_at, expires_at, tuple(metadata))
        except Exception:
            shutil.rmtree(directory, ignore_errors=True)
            raise

    def delete(self, storage_reference: str) -> None:
        directory = self._directory(storage_reference)
        if directory.exists():
            shutil.rmtree(directory)

    def retrieve_metadata(self, storage_reference: str) -> StoredInput:
        payload = json.loads(
            (self._directory(storage_reference) / "manifest.json").read_text(encoding="utf-8")
        )
        return StoredInput(
            storage_reference=payload["storage_reference"],
            created_at=datetime.fromisoformat(payload["created_at"]),
            expires_at=datetime.fromisoformat(payload["expires_at"]),
            file_metadata=tuple(payload["files"]),
        )

    def load(self, storage_reference: str) -> DocumentInput:
        stored = self.retrieve_metadata(storage_reference)
        files = []
        for index, metadata in enumerate(stored.file_metadata):
            content = (self._directory(storage_reference) / f"file-{index:04d}.bin").read_bytes()
            files.append(
                InputFile(
                    content=content,
                    media_type=str(metadata["media_type"]),
                    original_filename=str(metadata["original_filename"]),
                    page_index=metadata.get("page_index"),
                    sha256=str(metadata["sha256"]),
                )
            )
        manifest = json.loads(
            (self._directory(storage_reference) / "manifest.json").read_text(encoding="utf-8")
        )
        return DocumentInput(kind=InputKind(str(manifest["input_kind"])), files=tuple(files))

    def delete_expired(self, at: datetime) -> int:
        if not self._root.exists():
            return 0
        deleted = 0
        for directory in self._root.iterdir():
            if not directory.is_dir():
                continue
            try:
                expires_at = datetime.fromisoformat(
                    json.loads((directory / "manifest.json").read_text(encoding="utf-8"))[
                        "expires_at"
                    ]
                )
            except (OSError, ValueError, KeyError, json.JSONDecodeError):
                continue
            if expires_at <= at:
                shutil.rmtree(directory)
                deleted += 1
        return deleted

    def _directory(self, storage_reference: str) -> Path:
        if len(Path(storage_reference).parts) != 1:
            raise ValueError("invalid storage reference")
        directory = (self._root / storage_reference).resolve()
        if directory.parent != self._root:
            raise ValueError("invalid storage reference")
        return directory
