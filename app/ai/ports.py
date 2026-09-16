from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol


class AIPurpose(StrEnum):
    DOCUMENT_ANALYSIS = "document_analysis"
    DOCUMENT_QUESTION = "document_question"
    REPLY_DRAFT = "reply_draft"
    REANALYSIS = "reanalysis"


@dataclass(frozen=True)
class PromptReference:
    identifier: str
    version: str
    purpose: AIPurpose
    output_schema_version: str


class AIProvider(Protocol):
    """Future normalized provider boundary; deliberately no implementation in Phase 1."""


class ModelRouter(Protocol):
    def select_config(self, purpose: AIPurpose) -> str: ...


class PromptRegistry(Protocol):
    def resolve(self, purpose: AIPurpose) -> PromptReference: ...


class StructuredOutputValidator(Protocol):
    def validate(self, payload: object, schema_version: str) -> object: ...
