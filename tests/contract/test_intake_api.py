import io
from uuid import uuid4

from werkzeug.datastructures import FileStorage, MultiDict


def _file(name: str, content: bytes, media_type: str) -> tuple[str, FileStorage]:
    return (
        "files",
        FileStorage(stream=io.BytesIO(content), filename=name, content_type=media_type),
    )


def _fields(kind: str = "pdf", style: str = "standard") -> dict[str, str]:
    return {
        "client_document_id": "client-doc-1",
        "output_language": "ar",
        "output_style": style,
        "input_kind": kind,
    }


def test_single_pdf_returns_202_without_analysis_result(client, app):
    response = client.post(
        "/api/v1/document-analyses",
        data={**_fields(), "files": (io.BytesIO(b"%PDF-1.7\nnot analyzed"), "letter.pdf")},
        headers={"Idempotency-Key": str(uuid4())},
        content_type="multipart/form-data",
    )

    assert response.status_code == 202
    assert set(response.json) == {"operation_id", "status", "request_id"}
    assert response.json["status"] == "accepted"
    assert "analysis" not in response.json
    store = app.extensions["doxary_document_store"]
    assert (
        store.retrieve_metadata(response.json["operation_id"]).file_metadata[0]["media_type"]
        == "application/pdf"
    )


def test_ordered_multi_image_submission_is_accepted(client):
    data = MultiDict(
        [
            ("client_document_id", "client-doc-2"),
            ("output_language", "de"),
            ("output_style", "simple"),
            ("input_kind", "images"),
            ("page_indexes", "0"),
            ("page_indexes", "1"),
            _file("second.png", b"\x89PNG\r\n\x1a\npage-two", "image/png"),
            _file("first.jpg", b"\xff\xd8\xffpage-one", "image/jpeg"),
        ]
    )

    response = client.post(
        "/api/v1/document-analyses",
        data=data,
        headers={"Idempotency-Key": str(uuid4())},
        content_type="multipart/form-data",
    )

    assert response.status_code == 202


def test_invalid_combinations_and_files_are_rejected(client):
    response = client.post(
        "/api/v1/document-analyses",
        data={
            **_fields("images"),
            "page_indexes": ["0"],
            "files": (io.BytesIO(b"%PDF-1.7"), "wrong.pdf"),
        },
        headers={"Idempotency-Key": str(uuid4())},
        content_type="multipart/form-data",
    )

    assert response.status_code == 415
    assert response.json["error"]["code"] == "unsupported_media"


def test_same_idempotency_key_reuses_operation_without_duplicate_input(client):
    key = str(uuid4())
    first = client.post(
        "/api/v1/document-analyses",
        data={**_fields(), "files": (io.BytesIO(b"%PDF-1.7\ninput"), "first.pdf")},
        headers={"Idempotency-Key": key},
        content_type="multipart/form-data",
    )
    second = client.post(
        "/api/v1/document-analyses",
        data={**_fields(), "files": (io.BytesIO(b"%PDF-1.7\ninput"), "renamed.pdf")},
        headers={"Idempotency-Key": key},
        content_type="multipart/form-data",
    )

    assert first.status_code == second.status_code == 202
    assert first.json["operation_id"] == second.json["operation_id"]


def test_same_idempotency_key_with_different_content_conflicts(client):
    key = str(uuid4())
    client.post(
        "/api/v1/document-analyses",
        data={**_fields(), "files": (io.BytesIO(b"%PDF-1.7\nfirst"), "first.pdf")},
        headers={"Idempotency-Key": key},
        content_type="multipart/form-data",
    )
    response = client.post(
        "/api/v1/document-analyses",
        data={**_fields(), "files": (io.BytesIO(b"%PDF-1.7\nsecond"), "first.pdf")},
        headers={"Idempotency-Key": key},
        content_type="multipart/form-data",
    )

    assert response.status_code == 409
    assert response.json["error"]["code"] == "idempotency_conflict"
