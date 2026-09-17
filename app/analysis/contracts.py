from datetime import date, time
from decimal import Decimal
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

SCHEMA_VERSION = "analysis_result.v1"


class ContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class AnalysisStatus(StrEnum):
    COMPLETE = "complete"
    PARTIAL = "partial"
    UNAVAILABLE = "unavailable"


class ActionRequirement(StrEnum):
    YES = "yes"
    NO = "no"
    UNCERTAIN = "uncertain"


class Urgency(StrEnum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"
    UNCERTAIN = "uncertain"


class PracticalState(StrEnum):
    INFORMATIONAL = "informational"
    ACTION_REQUIRED = "action_required"
    APPOINTMENT = "appointment"
    PAYMENT = "payment"
    DOCUMENTS_REQUIRED = "documents_required"


class QualityReason(StrEnum):
    BLURRY_IMAGE = "blurry_image"
    PAGE_CUT_OFF = "page_cut_off"
    UNREADABLE_TEXT = "unreadable_text"
    MISSING_PAGES = "missing_pages"
    UNSUPPORTED_FILE = "unsupported_file"
    CORRUPT_FILE = "corrupt_file"
    INSUFFICIENT_CONTENT = "insufficient_content"


class AmountDirection(StrEnum):
    PAY = "pay"
    RECEIVE = "receive"
    UNKNOWN = "unknown"


class UncertaintyCode(StrEnum):
    AMBIGUOUS_DATE = "ambiguous_date"
    SENDER_UNCLEAR = "sender_unclear"
    WORDING_UNCLEAR = "wording_unclear"
    MISSING_CONTEXT = "missing_context"
    EXTRACTION_UNCERTAIN = "extraction_uncertain"


class ExplanationStyle(StrEnum):
    STANDARD = "standard"
    SIMPLE = "simple"


class Provenance(StrEnum):
    ANALYSIS = "analysis"
    USER = "user"
    SYSTEM = "system"


NonEmptyText = Annotated[str, Field(min_length=1)]


class EvidenceReference(ContractModel):
    reference_id: NonEmptyText
    file_id: str | None = None
    page_number: int | None = Field(default=None, ge=1)
    page_index: int | None = Field(default=None, ge=0)
    location: str | None = Field(default=None, max_length=200)
    excerpt: str | None = Field(default=None, max_length=1000)
    provenance: Provenance = Provenance.ANALYSIS


class Uncertainty(ContractModel):
    code: UncertaintyCode
    message: NonEmptyText
    evidence_reference_ids: list[NonEmptyText] = Field(default_factory=list)


class QualityIssue(ContractModel):
    reason: QualityReason
    message: NonEmptyText | None = None
    evidence_reference_ids: list[NonEmptyText] = Field(default_factory=list)


class ClassificationSuggestion(ContractModel):
    sender_organization: str | None = Field(default=None, min_length=1)
    document_type: str | None = Field(default=None, min_length=1)
    evidence_reference_ids: list[NonEmptyText] = Field(default_factory=list)
    uncertainties: list[Uncertainty] = Field(default_factory=list)


class DocumentDate(ContractModel):
    value: date | None = None
    source_text: str | None = Field(default=None, max_length=200)
    description: str | None = Field(default=None, max_length=300)
    evidence_reference_ids: list[NonEmptyText] = Field(default_factory=list)
    uncertainties: list[Uncertainty] = Field(default_factory=list)

    @model_validator(mode="after")
    def has_date_or_source_text(self) -> "DocumentDate":
        if self.value is None and not self.source_text:
            raise ValueError("a document date needs a normalized value or source_text")
        return self


class Deadline(ContractModel):
    description: NonEmptyText
    value: date | None = None
    source_text: str | None = Field(default=None, max_length=300)
    consequence: str | None = Field(default=None, max_length=500)
    evidence_reference_ids: list[NonEmptyText] = Field(default_factory=list)
    uncertainties: list[Uncertainty] = Field(default_factory=list)

    @model_validator(mode="after")
    def has_date_or_source_text(self) -> "Deadline":
        if self.value is None and not self.source_text:
            raise ValueError("a deadline needs a normalized value or source_text")
        return self


class Appointment(ContractModel):
    purpose: NonEmptyText
    appointment_date: date | None = None
    appointment_time: time | None = None
    timezone: str | None = Field(default=None, max_length=64)
    location: str | None = Field(default=None, max_length=300)
    evidence_reference_ids: list[NonEmptyText] = Field(default_factory=list)
    uncertainties: list[Uncertainty] = Field(default_factory=list)


class Amount(ContractModel):
    value: Decimal = Field(max_digits=20, decimal_places=8)
    currency: Annotated[str, Field(min_length=3, max_length=3)]
    purpose: NonEmptyText
    direction: AmountDirection = AmountDirection.UNKNOWN
    due_date: date | None = None
    evidence_reference_ids: list[NonEmptyText] = Field(default_factory=list)
    uncertainties: list[Uncertainty] = Field(default_factory=list)

    @field_validator("currency")
    @classmethod
    def uppercase_currency(cls, value: str) -> str:
        return value.upper()


class RequiredDocument(ContractModel):
    description: NonEmptyText
    explicitly_required: bool | None = None
    due_date: date | None = None
    evidence_reference_ids: list[NonEmptyText] = Field(default_factory=list)
    uncertainties: list[Uncertainty] = Field(default_factory=list)


class SuggestedTask(ContractModel):
    title: NonEmptyText
    due_date: date | None = None
    instructions: str | None = Field(default=None, max_length=1000)
    linked_deadline_index: int | None = Field(default=None, ge=0)
    evidence_reference_ids: list[NonEmptyText] = Field(default_factory=list)
    uncertainties: list[Uncertainty] = Field(default_factory=list)


class ExtractedFacts(ContractModel):
    document_date: DocumentDate | None = None
    deadlines: list[Deadline] = Field(default_factory=list)
    appointments: list[Appointment] = Field(default_factory=list)
    amounts: list[Amount] = Field(default_factory=list)
    required_documents: list[RequiredDocument] = Field(default_factory=list)
    suggested_tasks: list[SuggestedTask] = Field(default_factory=list)


class Explanation(ContractModel):
    language: Annotated[str, Field(min_length=2, max_length=35)]
    style: ExplanationStyle
    summary: NonEmptyText
    body: NonEmptyText
    next_actions: list[NonEmptyText] = Field(default_factory=list)


class AnalysisResult(ContractModel):
    """Doxary-owned, provider-neutral structured analysis contract v1."""

    schema_version: str = SCHEMA_VERSION
    analysis_status: AnalysisStatus
    client_document_id: NonEmptyText
    detected_language: Annotated[str, Field(min_length=2, max_length=35)] = "undetermined"
    classification: ClassificationSuggestion | None = None
    action_required: ActionRequirement = ActionRequirement.UNCERTAIN
    urgency: Urgency = Urgency.UNCERTAIN
    practical_states: list[PracticalState] = Field(default_factory=list)
    extracted_facts: ExtractedFacts = Field(default_factory=ExtractedFacts)
    explanation: Explanation | None = None
    source_references: list[EvidenceReference] = Field(default_factory=list)
    uncertainties: list[Uncertainty] = Field(default_factory=list)
    quality_issues: list[QualityIssue] = Field(default_factory=list)

    @field_validator("schema_version")
    @classmethod
    def require_supported_schema(cls, value: str) -> str:
        if value != SCHEMA_VERSION:
            raise ValueError(f"unsupported analysis schema version: {value}")
        return value

    @model_validator(mode="after")
    def require_explanation_for_usable_result(self) -> "AnalysisResult":
        if self.analysis_status is AnalysisStatus.COMPLETE and self.explanation is None:
            raise ValueError("complete analysis requires an explanation")
        return self
