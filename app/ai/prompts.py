from dataclasses import dataclass

from app.ai.ports import AIPurpose, PromptReference
from app.analysis.contracts import SCHEMA_VERSION


@dataclass(frozen=True)
class AnalysisPrompt:
    reference: PromptReference
    instructions: str


class StaticPromptRegistry:
    def resolve(self, purpose: AIPurpose) -> AnalysisPrompt:
        if purpose is not AIPurpose.DOCUMENT_ANALYSIS:
            raise ValueError("unsupported prompt purpose")
        return AnalysisPrompt(
            reference=PromptReference("doxary.document_analysis", "2", purpose, SCHEMA_VERSION),
            instructions=(
                "Analyze only the supplied document. Extract only grounded sender, type, dates, "
                "deadlines, appointments, amounts, required documents, practical actions, quality "
                "issues and uncertainty. Prefer partial or unavailable over invention. Do not give "
                "legal advice or calculate unstated legal deadlines. Set analysis_status to "
                "complete only when a matching explanation is present; otherwise use partial or "
                "unavailable. For every normalized date or due_date, emit only a machine-readable "
                "ISO calendar date (YYYY-MM-DD), or an ISO datetime at UTC/naive midnight; never "
                "emit natural-language or locale-formatted dates. Put human-readable wording in "
                "source_text and use uncertainty when a date is ambiguous. Appointment times must "
                "be offset-free ISO times without timezone information. For each amount value, "
                "emit only a JSON number using a decimal point where needed; never include a "
                "currency symbol/code, thousands separators, qualifiers, ranges, or prose. Put "
                "the currency in currency. Omit an amount when no reliable numeric value exists."
            ),
        )
