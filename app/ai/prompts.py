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
            reference=PromptReference("doxary.document_analysis", "1", purpose, SCHEMA_VERSION),
            instructions=(
                "Analyze only the supplied document. Extract only grounded sender, type, dates, "
                "deadlines, appointments, amounts, required documents, practical actions, quality "
                "issues and uncertainty. Prefer partial or unavailable over invention. Do not give "
                "legal advice or calculate unstated legal deadlines. Set analysis_status to "
                "complete only when a matching explanation is present; otherwise use partial or "
                "unavailable."
            ),
        )
