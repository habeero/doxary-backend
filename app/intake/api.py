import hashlib

from flask import Blueprint, current_app, jsonify, request
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from app.analysis.contracts import ExplanationStyle
from app.core.errors import ApplicationError, ErrorCode
from app.core.request_context.correlation import current_request_id
from app.intake.application.submission import SubmissionService
from app.intake.domain.input import DocumentInput, InputFile, InputKind

intake_blueprint = Blueprint("intake", __name__)


class SubmissionFields(BaseModel):
    model_config = ConfigDict(extra="forbid")

    client_document_id: str = Field(min_length=1, max_length=128)
    output_language: str = Field(min_length=2, max_length=35)
    output_style: ExplanationStyle
    input_kind: InputKind

    @field_validator("output_language")
    @classmethod
    def supported_language(cls, value: str) -> str:
        if value not in {"ar", "de"}:
            raise ValueError("supported output languages are ar and de")
        return value

    @field_validator("output_style")
    @classmethod
    def supported_style(cls, value: ExplanationStyle, info):
        if value is ExplanationStyle.SIMPLE and info.data.get("output_language") != "de":
            raise ValueError("simple style is currently available for German only")
        return value


@intake_blueprint.post("/document-analyses")
def submit_document_analysis():
    idempotency_key = request.headers.get("Idempotency-Key")
    if not idempotency_key:
        raise ApplicationError(ErrorCode.INVALID_MULTIPART, "Idempotency-Key is required.", 400)
    if (
        request.content_length is not None
        and request.content_length > current_app.config["MAX_CONTENT_LENGTH"]
    ):
        raise ApplicationError(ErrorCode.FILE_TOO_LARGE, "The submission is too large.", 413)
    if not request.files:
        raise ApplicationError(ErrorCode.INVALID_MULTIPART, "At least one file is required.", 400)
    try:
        fields = SubmissionFields.model_validate(
            {
                "client_document_id": request.form.get("client_document_id"),
                "output_language": request.form.get("output_language"),
                "output_style": request.form.get("output_style"),
                "input_kind": request.form.get("input_kind"),
            }
        )
    except ValidationError as error:
        raise ApplicationError(
            ErrorCode.INVALID_MULTIPART, "The submission fields are invalid.", 400
        ) from error

    uploaded = request.files.getlist("files")
    if not uploaded:
        raise ApplicationError(
            ErrorCode.INVALID_MULTIPART, "Files must use the repeated 'files' field.", 400
        )
    page_indexes = request.form.getlist("page_indexes")
    settings = current_app.extensions["doxary_container"].settings
    files = _validate_files(
        fields,
        uploaded,
        page_indexes,
        settings.max_file_bytes,
        settings.max_image_pages,
        settings.max_submission_bytes,
    )
    document_input = DocumentInput(
        kind=fields.input_kind,
        client_document_id=fields.client_document_id,
        output_language=fields.output_language,
        output_style=fields.output_style.value,
        files=tuple(files),
    )
    container = current_app.extensions["doxary_container"]
    service = SubmissionService(
        container.session_factory,
        current_app.extensions["doxary_document_store"],
        settings.temporary_input_retention_hours,
    )
    operation = service.submit(document_input, idempotency_key, current_request_id())
    return jsonify(
        {
            "operation_id": operation.operation_id,
            "status": operation.status.value,
            "request_id": current_request_id(),
        }
    ), 202


def _validate_files(
    fields, uploaded, page_indexes, max_file_bytes: int, max_pages: int, max_submission_bytes: int
) -> list[InputFile]:
    if fields.input_kind is InputKind.PDF and len(uploaded) != 1:
        raise ApplicationError(
            ErrorCode.UNSUPPORTED_INPUT_KIND, "A PDF submission must contain exactly one file.", 400
        )
    if fields.input_kind is InputKind.IMAGES and len(uploaded) > max_pages:
        raise ApplicationError(ErrorCode.TOO_MANY_PAGES, "Too many image pages.", 413)
    if fields.input_kind is InputKind.IMAGES and len(page_indexes) != len(uploaded):
        raise ApplicationError(
            ErrorCode.CONFLICTING_PAGE_ORDER, "Each image requires one page_index.", 400
        )
    if fields.input_kind is InputKind.PDF and page_indexes:
        raise ApplicationError(
            ErrorCode.CONFLICTING_PAGE_ORDER, "PDF submissions cannot contain page_indexes.", 400
        )
    indexes = []
    if fields.input_kind is InputKind.IMAGES:
        try:
            indexes = [int(value) for value in page_indexes]
        except ValueError as error:
            raise ApplicationError(
                ErrorCode.CONFLICTING_PAGE_ORDER, "Page indexes must be integers.", 400
            ) from error
        if sorted(indexes) != list(range(len(uploaded))):
            raise ApplicationError(
                ErrorCode.CONFLICTING_PAGE_ORDER,
                "Image page indexes must be contiguous from zero.",
                400,
            )

    total = 0
    result: list[InputFile] = []
    for position, uploaded_file in enumerate(uploaded):
        content = uploaded_file.stream.read(max_file_bytes + 1)
        size = len(content)
        if size == 0:
            raise ApplicationError(ErrorCode.EMPTY_FILE, "Empty files are not accepted.", 400)
        if size > max_file_bytes:
            raise ApplicationError(ErrorCode.FILE_TOO_LARGE, "A file is too large.", 413)
        total += size
        if total > max_submission_bytes:
            raise ApplicationError(ErrorCode.FILE_TOO_LARGE, "The submission is too large.", 413)
        media_type = _detect_media_type(content)
        if fields.input_kind is InputKind.PDF and media_type != "application/pdf":
            raise ApplicationError(
                ErrorCode.UNSUPPORTED_MEDIA, "The file is not a supported PDF.", 415
            )
        if fields.input_kind is InputKind.IMAGES and media_type not in {"image/jpeg", "image/png"}:
            raise ApplicationError(
                ErrorCode.UNSUPPORTED_MEDIA, "Only JPEG and PNG images are supported.", 415
            )
        result.append(
            InputFile(
                content=content,
                media_type=media_type,
                original_filename=uploaded_file.filename or "unnamed",
                page_index=indexes[position] if indexes else None,
                sha256=hashlib.sha256(content).hexdigest(),
            )
        )
    return result


def _detect_media_type(content: bytes) -> str | None:
    if content.startswith(b"%PDF-"):
        return "application/pdf"
    if content.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    return None
