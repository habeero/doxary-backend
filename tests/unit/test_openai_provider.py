import json
from types import SimpleNamespace

from app.ai.openai_provider import (
    OpenAIAnalysisExecutor,
    PricingSnapshot,
    _parse_transport_result,
    _safe_validation_diagnostic,
    structured_output_format,
)
from app.analysis.contracts import AnalysisResult
from app.intake.domain.input import DocumentInput, InputFile, InputKind


class FakeResponses:
    def __init__(self, result=None, error=None):
        self.result, self.error = result, error

    def create(self, **kwargs):
        self.kwargs = kwargs
        if self.error:
            raise self.error
        return SimpleNamespace(
            output_text=self.result.model_dump_json() if self.result else "{}",
            usage=SimpleNamespace(input_tokens=2, output_tokens=3),
        )


class FakeClient:
    def __init__(self, result=None, error=None):
        self.responses = FakeResponses(result, error)
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
    assert outcome.prompt_id == "doxary.document_analysis" and outcome.prompt_version == "1"
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


def test_local_document_id_is_injected_before_domain_validation():
    payload = _result().model_dump()
    payload.pop("client_document_id")
    payload["schema_version"] = "untrusted-version"
    parsed = _parse_transport_result(json.dumps(payload), _document())
    assert parsed.client_document_id == "doc"
    assert parsed.schema_version == "analysis_result.v1"


def test_validation_diagnostic_retains_only_error_path_and_category():
    try:
        AnalysisResult.model_validate({})
    except Exception as error:
        diagnostic = _safe_validation_diagnostic(error)
    assert "exception=ValidationError" in diagnostic
    assert "analysis_status:missing" in diagnostic
    assert "issues=" in diagnostic


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
