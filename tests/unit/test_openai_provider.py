import json
from decimal import Decimal
from types import SimpleNamespace

import httpx
import pytest
from app.ai.openai_provider import (
    OpenAIAnalysisExecutor,
    PricingSnapshot,
    _parse_transport_result,
    _safe_failure_diagnostic,
    _safe_validation_diagnostic,
    structured_output_format,
)
from app.analysis.contracts import AnalysisResult
from app.intake.domain.input import DocumentInput, InputFile, InputKind
from openai import BadRequestError
from pydantic import ValidationError


class FakeResponses:
    def __init__(self, result=None, error=None, output_text=None):
        self.result, self.error, self.output_text = result, error, output_text

    def create(self, **kwargs):
        self.kwargs = kwargs
        if self.error:
            raise self.error
        return SimpleNamespace(
            output_text=(
                self.output_text
                if self.output_text is not None
                else self.result.model_dump_json()
                if self.result
                else "{}"
            ),
            usage=SimpleNamespace(input_tokens=2, output_tokens=3),
        )


class FakeClient:
    def __init__(self, result=None, error=None, output_text=None):
        self.responses = FakeResponses(result, error, output_text)
        self.deleted = []
        self.files = SimpleNamespace(
            create=lambda **kwargs: SimpleNamespace(id="file-test"),
            delete=lambda value: self.deleted.append(value),
        )


def _document(kind=InputKind.IMAGES):
    return DocumentInput(
        kind=kind,
        client_document_id="doc",
        output_language="de",
        output_style="standard",
        files=(InputFile(b"data", "image/png", "one.png", 0, "digest"),),
    )


def _result():
    return AnalysisResult(
        analysis_status="complete",
        client_document_id="doc",
        explanation={"language": "de", "style": "standard", "summary": "ok", "body": "ok"},
    )


def test_adapter_returns_only_validated_result():
    adapter = OpenAIAnalysisExecutor("test", "test-model", 1, client=FakeClient(_result()))
    outcome = adapter.execute(_document())
    assert outcome.kind == "success" and outcome.result.schema_version == "analysis_result.v1"
    assert outcome.provider_id == "openai" and outcome.model_config_id == "test-model"


def test_adapter_classifies_timeout_and_rejects_missing_structured_result():
    timeout = OpenAIAnalysisExecutor("test", "model", 1, client=FakeClient(error=TimeoutError()))
    assert timeout.execute(_document()).failure_code == "provider_timeout"
    invalid = OpenAIAnalysisExecutor("test", "model", 1, client=FakeClient())
    assert invalid.execute(_document()).failure_code == "structured_output_invalid"


def test_pricing_uses_decimal_costs():
    from decimal import Decimal

    snapshot = PricingSnapshot(
        "openai", "model", "test", Decimal("1"), Decimal("0.5"), Decimal("2")
    )
    assert snapshot.estimate(100, 20, 50) == Decimal("0.00019")


def test_pdf_uses_provider_file_and_cleans_it_up():
    client = FakeClient(_result())
    outcome = OpenAIAnalysisExecutor("test", "test-model", 1, client=client).execute(
        _document(InputKind.PDF)
    )
    assert outcome.kind == "success"
    assert client.deleted == ["file-test"]


def test_images_are_sent_in_page_order_with_preferences_and_prompt_metadata():
    client = FakeClient(_result())
    document = DocumentInput(
        kind=InputKind.IMAGES,
        client_document_id="doc",
        output_language="ar",
        output_style="simple",
        files=(
            InputFile(b"second", "image/png", "2.png", 1, "b"),
            InputFile(b"first", "image/jpeg", "1.jpg", 0, "a"),
        ),
    )
    outcome = OpenAIAnalysisExecutor("test", "test-model", 1, client=client).execute(document)
    user = client.responses.kwargs["input"][1]["content"]
    assert "ar" in user[0]["text"] and "simple" in user[0]["text"]
    assert [item["image_url"].split(",", 1)[1] for item in user[1:]] == ["Zmlyc3Q=", "c2Vjb25k"]
    assert client.responses.kwargs["text"]["format"]["type"] == "json_schema"
    assert outcome.prompt_id == "doxary.document_analysis" and outcome.prompt_version == "2"
    assert client.responses.kwargs["store"] is False


def test_transport_schema_is_strict_and_removes_unsupported_domain_constraints():
    format_config = structured_output_format()
    rendered = str(format_config)
    assert "'strict': True" in rendered
    assert "'default'" not in rendered
    assert "'minLength'" not in rendered
    assert "'format'" not in rendered
    assert "client_document_id" not in format_config["schema"]["properties"]
    assert "client_document_id" not in format_config["schema"]["required"]
    assert "schema_version" not in format_config["schema"]["properties"]
    assert "schema_version" not in format_config["schema"]["required"]
    defs = format_config["schema"]["$defs"]
    assert defs["Amount"]["properties"]["direction"]["enum"] == [
        "pay",
        "receive",
        "unknown",
    ]
    assert defs["Amount"]["properties"]["value"] == {
        "type": "number",
        "description": (
            "Canonical monetary number only. Do not include currency, thousands "
            "separators, qualifiers, ranges, or prose."
        ),
    }
    assert "YYYY-MM-DD" in defs["Deadline"]["properties"]["value"]["description"]
    assert "no timezone" in defs["Appointment"]["properties"]["appointment_time"]["description"]


def test_failure_diagnostic_contains_only_safe_technical_fields():
    error = type(
        "BadRequestError",
        (Exception,),
        {"status_code": 400, "code": "invalid_json_schema", "request_id": "req-safe"},
    )()
    outcome = OpenAIAnalysisExecutor("test", "model", 1, client=FakeClient(error=error)).execute(
        _document()
    )
    assert outcome.failure_code == "provider_failure"
    assert "status_code=400" in outcome.failure_diagnostic
    assert "invalid_json_schema" in outcome.failure_diagnostic


def test_bad_request_diagnostic_reads_allowlisted_nested_sdk_metadata_only():
    request = httpx.Request("POST", "https://api.test")
    error = BadRequestError(
        "SECRET_PROVIDER_MESSAGE",
        response=httpx.Response(
            400,
            request=request,
            headers={"x-request-id": "req_nested"},
        ),
        body={
            "error": {
                "type": "invalid_request_error",
                "code": "invalid_schema",
                "param": "text.format",
                "message": "SECRET_NESTED_MESSAGE",
                "metadata": {"document_text": "SECRET_DOCUMENT"},
            },
            "unexpected": {"raw": "SECRET_RAW_BODY"},
        },
    )

    diagnostic = _safe_failure_diagnostic(error)

    assert "status_code=400" in diagnostic
    assert "type=invalid_request_error" in diagnostic
    assert "code=invalid_schema" in diagnostic
    assert "param=text.format" in diagnostic
    assert "request_id=req_nested" in diagnostic
    assert "SECRET" not in diagnostic
    assert "message" not in diagnostic
    assert len(diagnostic) <= 128


def test_failure_diagnostic_ignores_non_scalar_nested_provider_metadata():
    error = type(
        "BadRequestLike",
        (Exception,),
        {
            "status_code": 400,
            "body": {
                "error": {
                    "type": {"nested": "invalid_request_error"},
                    "code": ["invalid_schema"],
                    "param": object(),
                }
            },
        },
    )()

    diagnostic = _safe_failure_diagnostic(error)

    assert diagnostic == "exception=BadRequestLike,status_code=400"
    assert len(diagnostic) <= 128


def test_local_document_id_is_injected_before_domain_validation():
    payload = _result().model_dump()
    payload.pop("client_document_id")
    payload["schema_version"] = "untrusted-version"
    parsed = _parse_transport_result(json.dumps(payload), _document())
    assert parsed.client_document_id == "doc"
    assert parsed.schema_version == "analysis_result.v1"


def test_transport_rejects_invalid_amount_direction_as_structured_output_invalid():
    payload = _result().model_dump(mode="json")
    payload.pop("client_document_id")
    payload["extracted_facts"] = {
        "amounts": [
            {
                "value": "12.50",
                "currency": "EUR",
                "purpose": "Fee",
                "direction": "threshold",
            }
        ]
    }

    with pytest.raises(ValidationError) as captured:
        _parse_transport_result(json.dumps(payload), _document())

    assert "amounts" in str(captured.value)
    assert "direction" in str(captured.value)
    outcome = OpenAIAnalysisExecutor(
        "test",
        "test-model",
        1,
        client=FakeClient(output_text=json.dumps(payload)),
    ).execute(_document())
    assert outcome.failure_code == "structured_output_invalid"


def _transport_payload_with_amounts(amounts: list[dict]) -> dict:
    payload = _result().model_dump(mode="json")
    payload.pop("client_document_id")
    payload["extracted_facts"] = {"amounts": amounts}
    return payload


def test_numeric_transport_amounts_validate_as_decimals():
    payload = _transport_payload_with_amounts(
        [
            {"value": 1200, "currency": "EUR", "purpose": "Invoice"},
            {"value": 1234.56, "currency": "EUR", "purpose": "Fee"},
            {"value": -12.5, "currency": "EUR", "purpose": "Refund"},
        ]
    )

    parsed = _parse_transport_result(json.dumps(payload), _document())

    assert [amount.value for amount in parsed.extracted_facts.amounts] == [
        Decimal("1200"),
        Decimal("1234.56"),
        Decimal("-12.5"),
    ]


@pytest.mark.parametrize(
    "value",
    ["1.234,56", "EUR 1,234.56", "ca. 1200", "1.200 bis 1.500", "unknown", None],
)
def test_transport_rejects_non_numeric_or_null_amount_values(value):
    payload = _transport_payload_with_amounts(
        [{"value": value, "currency": "EUR", "purpose": "Amount"}]
    )

    with pytest.raises(ValidationError):
        _parse_transport_result(json.dumps(payload), _document())


def test_multi_image_provider_output_with_numeric_amounts_is_one_valid_result():
    document = DocumentInput(
        kind=InputKind.IMAGES,
        client_document_id="doc",
        output_language="de",
        output_style="standard",
        files=(
            InputFile(b"second", "image/png", "2.png", 1, "b"),
            InputFile(b"first", "image/jpeg", "1.jpg", 0, "a"),
        ),
    )
    payload = _transport_payload_with_amounts(
        [
            {"value": 12, "currency": "EUR", "purpose": "First"},
            {"value": 12.5, "currency": "EUR", "purpose": "Second"},
            {"value": -1, "currency": "EUR", "purpose": "Third"},
        ]
    )
    client = FakeClient(output_text=json.dumps(payload))

    outcome = OpenAIAnalysisExecutor("test", "test-model", 1, client=client).execute(document)

    assert outcome.kind == "success"
    assert [amount.value for amount in outcome.result.extracted_facts.amounts] == [
        Decimal("12"),
        Decimal("12.5"),
        Decimal("-1"),
    ]
    user = client.responses.kwargs["input"][1]["content"]
    assert [item["image_url"].split(",", 1)[1] for item in user[1:]] == [
        "Zmlyc3Q=",
        "c2Vjb25k",
    ]


def test_validation_diagnostic_retains_only_error_path_and_category():
    try:
        AnalysisResult.model_validate({})
    except Exception as error:
        diagnostic = _safe_validation_diagnostic(error)
    assert diagnostic.startswith("VE;")
    assert "analysis_status:missing" in diagnostic
    assert ";" in diagnostic


def test_complete_partial_and_unavailable_transport_payloads_map_through_contract():
    for status in ("complete", "partial", "unavailable"):
        payload = _result().model_dump()
        payload.pop("client_document_id")
        payload["schema_version"] = "wrong"
        payload["analysis_status"] = status
        if status != "complete":
            payload["explanation"] = None
        parsed = _parse_transport_result(json.dumps(payload), _document())
        assert parsed.analysis_status.value == status


def test_transport_normalizes_iso_datetime_for_date_fields_without_weakening_contract():
    payload = _result().model_dump()
    payload.pop("client_document_id")
    payload["extracted_facts"] = {
        "deadlines": [{"description": "Reply", "value": "2026-09-30T00:00:00Z"}],
        "required_documents": [{"description": "Passport"}],
    }
    parsed = _parse_transport_result(json.dumps(payload), _document())
    assert parsed.extracted_facts.deadlines[0].value.isoformat() == "2026-09-30"


def test_transport_rejects_ambiguous_date_and_malformed_required_document():
    payload = _result().model_dump()
    payload.pop("client_document_id")
    payload["extracted_facts"] = {
        "deadlines": [{"description": "Reply", "value": "09/30/2026"}],
        "required_documents": [{"due_date": "2026-09-30"}],
    }
    with pytest.raises((ValidationError, ValueError)):
        _parse_transport_result(json.dumps(payload), _document())


@pytest.mark.parametrize(
    ("collection", "entry", "attribute"),
    [
        (
            "appointments",
            {"purpose": "Call", "appointment_date": "2026-10-01", "appointment_time": "09:30"},
            "appointment_date",
        ),
        (
            "amounts",
            {"value": "12.50", "currency": "EUR", "purpose": "Fee", "due_date": "2026-10-02"},
            "due_date",
        ),
        ("required_documents", {"description": "Passport", "due_date": "2026-10-03"}, "due_date"),
        ("suggested_tasks", {"title": "Reply", "due_date": "2026-10-04"}, "due_date"),
    ],
)
def test_each_explicit_date_time_path_maps_without_generic_value_normalization(
    collection, entry, attribute
):
    payload = _result().model_dump()
    payload.pop("client_document_id")
    payload["extracted_facts"] = {collection: [entry]}
    parsed = _parse_transport_result(json.dumps(payload), _document())
    assert (
        getattr(parsed.extracted_facts.__getattribute__(collection)[0], attribute).isoformat()
        == entry[attribute]
    )
    if collection == "amounts":
        assert str(parsed.extracted_facts.amounts[0].value) == "12.50"


def test_timezone_bearing_date_and_time_are_not_silently_reinterpreted():
    payload = _result().model_dump()
    payload.pop("client_document_id")
    payload["extracted_facts"] = {
        "deadlines": [{"description": "Reply", "value": "2026-09-30T23:30:00+02:00"}],
        "appointments": [{"purpose": "Call", "appointment_time": "09:30+02:00"}],
    }
    with pytest.raises(ValueError):
        _parse_transport_result(json.dumps(payload), _document())


def test_date_datetime_diagnostic_reports_shape_without_value():
    payload = _result().model_dump()
    payload.pop("client_document_id")
    payload["extracted_facts"] = {
        "deadlines": [{"description": "Reply", "value": "30/09/2026"}],
        "required_documents": [{"description": "Passport", "due_date": "30/09/2026"}],
        "suggested_tasks": [{"title": "Reply", "due_date": "30/09/2026"}],
    }
    with pytest.raises(ValidationError) as captured:
        _parse_transport_result(json.dumps(payload), _document())
    diagnostic = captured.value._doxary_diagnostic
    assert "dl0v:dd" in diagnostic
    assert "rd0d:dd" in diagnostic
    assert "st0d:dd" in diagnostic
    assert len(diagnostic) <= 128
    assert "t=s,d=0,dt=0,z=0,m=0" in diagnostic
    assert "30/09/2026" not in diagnostic


def test_source_text_preserves_human_wording_without_normalizing_the_date():
    payload = _result().model_dump()
    payload.pop("client_document_id")
    payload["extracted_facts"] = {
        "deadlines": [{"description": "Reply", "value": None, "source_text": "Ende September"}]
    }
    parsed = _parse_transport_result(json.dumps(payload), _document())
    assert parsed.extracted_facts.deadlines[0].source_text == "Ende September"
