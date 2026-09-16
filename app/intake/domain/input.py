from dataclasses import dataclass
from enum import StrEnum


class InputKind(StrEnum):
    PDF = "pdf"
    IMAGES = "images"


@dataclass(frozen=True)
class InputFile:
    content: bytes
    media_type: str
    original_filename: str
    page_index: int | None
    sha256: str


@dataclass(frozen=True)
class DocumentInput:
    kind: InputKind
    client_document_id: str
    output_language: str
    output_style: str
    files: tuple[InputFile, ...]
