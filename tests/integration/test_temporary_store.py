from datetime import UTC, datetime, timedelta

from app.intake.domain.input import DocumentInput, InputFile, InputKind
from app.intake.infrastructure.local_store import LocalTemporaryDocumentStore


def _input(filename: str = "../../escape.pdf") -> DocumentInput:
    return DocumentInput(
        kind=InputKind.PDF,
        client_document_id="client-doc",
        output_language="ar",
        output_style="standard",
        files=(InputFile(b"%PDF-1.7", "application/pdf", filename, None, "digest"),),
    )


def test_store_uses_generated_isolated_paths_and_preserves_metadata(tmp_path):
    store = LocalTemporaryDocumentStore(tmp_path)
    reference = store.store("operation-1", _input(), datetime.now(UTC) + timedelta(hours=1))

    assert reference.storage_reference == "operation-1"
    assert (tmp_path / "operation-1" / "file-0000.bin").exists()
    assert not (tmp_path / "escape.pdf").exists()
    assert (
        store.retrieve_metadata(reference.storage_reference).file_metadata[0]["original_filename"]
        == "../../escape.pdf"
    )


def test_delete_and_expiry_cleanup_are_deterministic(tmp_path):
    store = LocalTemporaryDocumentStore(tmp_path)
    expired = store.store(
        "expired", _input("expired.pdf"), datetime.now(UTC) - timedelta(seconds=1)
    )
    active = store.store("active", _input("active.pdf"), datetime.now(UTC) + timedelta(hours=1))

    assert store.delete_expired(datetime.now(UTC)) == 1
    assert not (tmp_path / expired.storage_reference).exists()
    store.delete(active.storage_reference)
    assert not (tmp_path / active.storage_reference).exists()
