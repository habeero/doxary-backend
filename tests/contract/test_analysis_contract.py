from decimal import Decimal

import pytest
from app.analysis.contracts import (
    ActionRequirement,
    Amount,
    AnalysisResult,
    AnalysisStatus,
    Explanation,
    ExplanationStyle,
    PracticalState,
    QualityIssue,
    QualityReason,
    Uncertainty,
    UncertaintyCode,
    Urgency,
)
from pydantic import ValidationError


def complete_result(**overrides) -> AnalysisResult:
    values = {
        "analysis_status": AnalysisStatus.COMPLETE,
        "client_document_id": "client-document-1",
        "explanation": Explanation(
            language="ar",
            style=ExplanationStyle.STANDARD,
            summary="ملخص واضح",
            body="شرح واضح للمستند",
        ),
    }
    values.update(overrides)
    return AnalysisResult(**values)


def test_minimal_complete_result_is_typed_and_versioned():
    result = complete_result()

    assert result.schema_version == "analysis_result.v1"
    assert result.analysis_status is AnalysisStatus.COMPLETE
    assert result.extracted_facts.deadlines == []


def test_partial_and_unavailable_results_allow_missing_explanation():
    assert (
        AnalysisResult(
            analysis_status=AnalysisStatus.PARTIAL, client_document_id="doc"
        ).analysis_status
        is AnalysisStatus.PARTIAL
    )
    assert (
        AnalysisResult(
            analysis_status=AnalysisStatus.UNAVAILABLE, client_document_id="doc"
        ).analysis_status
        is AnalysisStatus.UNAVAILABLE
    )


def test_nonexclusive_states_arabic_simple_german_and_exact_amount():
    result = complete_result(
        practical_states=[PracticalState.ACTION_REQUIRED, PracticalState.PAYMENT],
        action_required=ActionRequirement.YES,
        urgency=Urgency.HIGH,
        explanation=Explanation(
            language="de", style=ExplanationStyle.SIMPLE, summary="Kurz", body="Einfach erklärt"
        ),
    )
    result.extracted_facts.amounts.append(
        Amount(value=Decimal("12.34000000"), currency="eur", purpose="Gebühr")
    )

    assert result.explanation.language == "de"
    assert result.explanation.style is ExplanationStyle.SIMPLE
    assert result.extracted_facts.amounts[0].value == Decimal("12.34000000")
    assert result.extracted_facts.amounts[0].currency == "EUR"


def test_evidence_uncertainty_and_quality_are_typed():
    result = complete_result(
        uncertainties=[Uncertainty(code=UncertaintyCode.AMBIGUOUS_DATE, message="Datum unklar")],
        quality_issues=[QualityIssue(reason=QualityReason.BLURRY_IMAGE, message="Bild unscharf")],
    )

    assert result.uncertainties[0].code is UncertaintyCode.AMBIGUOUS_DATE
    assert result.quality_issues[0].reason is QualityReason.BLURRY_IMAGE


def test_invalid_status_nested_value_and_schema_version_are_rejected():
    with pytest.raises(ValidationError):
        AnalysisResult(analysis_status="invented", client_document_id="doc")
    with pytest.raises(ValidationError):
        complete_result(schema_version="analysis_result.v2")
    with pytest.raises(ValidationError):
        complete_result(explanation={"language": "ar", "style": "standard"})
