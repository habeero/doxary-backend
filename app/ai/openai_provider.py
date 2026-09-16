import base64
import json
import logging
from dataclasses import dataclass
from datetime import date, datetime, time
from decimal import Decimal
from io import BytesIO
from time import monotonic

from app.ai.ports import AIPurpose
from app.ai.prompts import StaticPromptRegistry
from app.analysis.contracts import SCHEMA_VERSION, AnalysisResult
from app.core.errors.diagnostics import bound_diagnostic
from app.intake.domain.input import DocumentInput, InputKind
from app.worker.runtime import ExecutionOutcome

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class PricingSnapshot:
    provider: str
    model: str
    version: str
    input_per_million: Decimal
    cached_input_per_million: Decimal
    output_per_million: Decimal
    currency: str = "USD"

    def estimate(self, input_tokens: int, cached_tokens: int, output_tokens: int) -> Decimal:
        uncached = max(input_tokens - cached_tokens, 0)
        return (
            Decimal(uncached) * self.input_per_million
            + Decimal(cached_tokens) * self.cached_input_per_million
            + Decimal(output_tokens) * self.output_per_million
        ) / Decimal(1_000_000)


class OpenAIAnalysisExecutor:
    """OpenAI Responses adapter; only normalized results leave this module."""

    def __init__(
        self,
        api_key: str,
        model: str,
        timeout_seconds: float,
        *,
        reasoning_effort: str | None = None,
        client=None,
    ):
        from openai import OpenAI

        self._client = client or OpenAI(api_key=api_key, timeout=timeout_seconds, max_retries=0)
        self._model, self._reasoning_effort = model, reasoning_effort

    def execute(self, document: DocumentInput) -> ExecutionOutcome:
        prompt = StaticPromptRegistry().resolve(AIPurpose.DOCUMENT_ANALYSIS)
        content = [
            {
                "type": "input_text",
                "text": f"Explain in {document.output_language}, style {document.output_style}.",
            }
        ]
        uploaded = []
        try:
            if document.kind is InputKind.PDF:
                item = document.files[0]
                uploaded_file = self._client.files.create(
                    file=(item.original_filename, BytesIO(item.content)), purpose="user_data"
                )
                uploaded.append(uploaded_file.id)
                content.append({"type": "input_file", "file_id": uploaded_file.id})
            else:
                for item in sorted(document.files, key=lambda value: value.page_index or 0):
                    encoded = base64.b64encode(item.content).decode("ascii")
                    content.append(
                        {
                            "type": "input_image",
                            "image_url": f"data:{item.media_type};base64,{encoded}",
                        }
                    )
            kwargs = {
                "model": self._model,
                "store": False,
                "input": [
                    {"role": "system", "content": prompt.instructions},
                    {"role": "user", "content": content},
                ],
                "text": {"format": structured_output_format()},
            }
            if self._reasoning_effort:
                kwargs["reasoning"] = {"effort": self._reasoning_effort}
            started = monotonic()
            response = self._client.responses.create(**kwargs)
            latency_ms = int((monotonic() - started) * 1000)
            usage = getattr(response, "usage", None)
            telemetry = {
                "usage": usage,
                "latency_ms": latency_ms,
                "cached_units": _cached_tokens(usage),
                "cost_amount": _estimate_cost(self._model, usage),
                "currency": "USD" if _pricing_for(self._model) else None,
                "pricing_snapshot": _pricing_payload(self._model),
                "input_page_count": len(document.files),
            }
            try:
                result = _parse_transport_result(response.output_text, document)
            except Exception as error:
                diagnostic = getattr(
                    error, "_doxary_diagnostic", None
                ) or _safe_validation_diagnostic(error)
                log.warning(
                    "openai structured output failed Doxary validation",
                    extra={
                        "provider": "openai",
                        "model": self._model,
                        "provider_diagnostic": diagnostic,
                    },
                )
                return ExecutionOutcome(
                    "failure",
                    "structured_output_invalid",
                    False,
                    provider_id="openai",
                    model_config_id=self._model,
                    prompt_id=prompt.reference.identifier,
                    prompt_version=prompt.reference.version,
                    output_schema_version=prompt.reference.output_schema_version,
                    failure_diagnostic=diagnostic,
                    **telemetry,
                )
            return ExecutionOutcome(
                "success",
                result=result,
                provider_id="openai",
                model_config_id=self._model,
                prompt_id=prompt.reference.identifier,
                prompt_version=prompt.reference.version,
                output_schema_version=result.schema_version,
                **telemetry,
            )
        except Exception as error:
            code = _failure_code(error)
            diagnostic = _safe_failure_diagnostic(error)
            log.warning(
                "openai response request failed",
                extra={
                    "provider": "openai",
                    "model": self._model,
                    "failure_code": code,
                    "provider_diagnostic": diagnostic,
                },
            )
            return ExecutionOutcome(
                "failure",
                code,
                code in {"provider_timeout", "provider_unavailable", "rate_limited"},
                provider_id="openai",
                model_config_id=self._model,
                prompt_id=prompt.reference.identifier,
                prompt_version=prompt.reference.version,
                output_schema_version=prompt.reference.output_schema_version,
                failure_diagnostic=diagnostic,
            )
        finally:
            for file_id in uploaded:
                try:
                    self._client.files.delete(file_id)
                except Exception:
                    pass


def _failure_code(error: Exception) -> str:
    name = type(error).__name__.lower()
    if "timeout" in name:
        return "provider_timeout"
    if "ratelimit" in name:
        return "rate_limited"
    if "auth" in name:
        return "provider_authentication_failed"
    if "connection" in name or "internalserver" in name:
        return "provider_unavailable"
    return "provider_failure"


def _safe_failure_diagnostic(error: Exception) -> str:
    """Keep technical classification, never provider messages or request data."""
    fields = [f"exception={type(error).__name__}"]
    for name in ("status_code", "code", "type", "request_id"):
        value = getattr(error, name, None)
        if value is not None:
            safe = "".join(char for char in str(value) if char.isalnum() or char in "-_.")
            fields.append(f"{name}={safe[:48]}")
    return ",".join(fields)[:128]


_TRANSPORT_UNSUPPORTED_SCHEMA_KEYS = {
    "default",
    "format",
    "minLength",
    "maxLength",
    "pattern",
    "minimum",
    "maximum",
    "exclusiveMinimum",
    "exclusiveMaximum",
    "multipleOf",
    "minItems",
    "maxItems",
}


def structured_output_format() -> dict:
    """Create a strict OpenAI transport schema; Doxary validation remains authoritative."""
    from openai.lib._pydantic import to_strict_json_schema

    schema = _without_transport_unsupported_keywords(to_strict_json_schema(AnalysisResult))
    for server_owned in ("client_document_id", "schema_version"):
        schema["properties"].pop(server_owned, None)
        schema["required"].remove(server_owned)
    return {
        "type": "json_schema",
        "name": "analysis_result_v1",
        "strict": True,
        "schema": schema,
    }


def _without_transport_unsupported_keywords(value):
    if isinstance(value, dict):
        return {
            key: _without_transport_unsupported_keywords(child)
            for key, child in value.items()
            if key not in _TRANSPORT_UNSUPPORTED_SCHEMA_KEYS
        }
    if isinstance(value, list):
        return [_without_transport_unsupported_keywords(child) for child in value]
    return value


def _parse_transport_result(output_text: str, document: DocumentInput) -> AnalysisResult:
    payload = json.loads(output_text)
    if not isinstance(payload, dict):
        raise ValueError("structured response must be an object")
    raw_payload = payload
    payload = _normalize_transport_values(payload)
    # Product correlation is server-owned; it need not be disclosed to the provider.
    payload["client_document_id"] = document.client_document_id
    payload["schema_version"] = SCHEMA_VERSION
    try:
        return AnalysisResult.model_validate(payload)
    except Exception as error:
        error._doxary_diagnostic = _safe_validation_diagnostic(error, raw_payload)
        raise


def _normalize_transport_values(payload: dict) -> dict:
    """Normalize only the explicitly date/time-bearing contract paths.

    OpenAI's transport schema cannot carry Pydantic's date/time ``format``
    constraints. Plain dates and offset-free times are already domain-safe;
    the only datetime compatibility accepted for a date is UTC midnight,
    whose calendar date is unambiguous. All other values remain untouched and
    are rejected by the authoritative domain model.
    """
    normalized = dict(payload)
    facts = normalized.get("extracted_facts")
    if not isinstance(facts, dict):
        return normalized

    document_date = facts.get("document_date")
    if isinstance(document_date, dict) and "value" in document_date:
        document_date = dict(document_date)
        document_date["value"] = _normalize_date(document_date["value"])
        facts = dict(facts)
        facts["document_date"] = document_date

    for collection, date_key in (
        ("deadlines", "value"),
        ("appointments", "appointment_date"),
        ("amounts", "due_date"),
        ("required_documents", "due_date"),
        ("suggested_tasks", "due_date"),
    ):
        entries = facts.get(collection)
        if not isinstance(entries, list):
            continue
        updated = []
        for entry in entries:
            if not isinstance(entry, dict):
                updated.append(entry)
                continue
            item = dict(entry)
            if date_key in item:
                item[date_key] = _normalize_date(item[date_key])
            if collection == "appointments" and "appointment_time" in item:
                item["appointment_time"] = _normalize_time(item["appointment_time"])
            updated.append(item)
        facts = dict(facts)
        facts[collection] = updated
    normalized["extracted_facts"] = facts
    return normalized


def _normalize_date(value):
    if not isinstance(value, str):
        return value
    try:
        date.fromisoformat(value)
        return value
    except ValueError:
        pass
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return value
    if parsed.tzinfo is None and parsed.time() == time.min:
        return parsed.date()
    if (
        parsed.tzinfo is not None
        and parsed.utcoffset().total_seconds() == 0
        and parsed.time() == time.min
    ):
        return parsed.date()
    return value


def _normalize_time(value):
    if not isinstance(value, str):
        return value
    try:
        parsed = time.fromisoformat(value)
    except ValueError:
        return value
    if parsed.tzinfo is not None:
        raise ValueError("timezone-bearing appointment times are not supported")
    return parsed


def _safe_validation_diagnostic(error: Exception, payload: dict | None = None) -> str:
    """Validation exception class only; validation inputs may contain document-derived text."""
    diagnostic = f"exception={type(error).__name__}"
    errors = getattr(error, "errors", None)
    if callable(errors):
        safe_issues = []
        for issue in errors()[:6]:
            location = ".".join(str(part) for part in issue.get("loc", ()))
            category = str(issue.get("type", "invalid"))
            metadata = (
                _safe_representation_metadata(payload, issue.get("loc", ())) if payload else ""
            )
            safe_issues.append(f"{location}:{category}{metadata}")
        if safe_issues:
            diagnostic += ",issues=" + "|".join(safe_issues)
    return bound_diagnostic(diagnostic) or "exception=unknown"


def _safe_representation_metadata(payload: dict, location) -> str:
    value = payload
    try:
        for part in location:
            value = value[part] if isinstance(value, (dict, list)) else None
    except (KeyError, IndexError, TypeError):
        value = None
    if isinstance(value, str):
        iso_date = False
        iso_datetime = False
        timezone = False
        midnight = False
        try:
            date.fromisoformat(value)
            iso_date = True
        except ValueError:
            try:
                parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
                iso_datetime = True
                timezone = parsed.tzinfo is not None
                midnight = parsed.time() == time.min
            except ValueError:
                pass
        return (
            f"[type=str,date={int(iso_date)},datetime={int(iso_datetime)},"
            f"tz={int(timezone)},midnight={int(midnight)}]"
        )
    return f"[type={type(value).__name__}]"


def _cached_tokens(usage) -> int | None:
    details = getattr(usage, "prompt_tokens_details", None)
    return (
        getattr(details, "cached_tokens", None)
        if details is not None
        else getattr(usage, "cached_tokens", None)
    )


def _pricing_for(model: str) -> PricingSnapshot | None:
    # Pricing is an explicit, versioned telemetry snapshot. Unknown models are unpriced.
    if model == "gpt-4o-mini":
        return PricingSnapshot(
            "openai", model, "2026-09-dev-1", Decimal("0.15"), Decimal("0.075"), Decimal("0.60")
        )
    return None


def _pricing_payload(model: str) -> dict | None:
    snapshot = _pricing_for(model)
    if snapshot is None:
        return None
    return {
        "provider": snapshot.provider,
        "model": snapshot.model,
        "version": snapshot.version,
        "input_per_million": str(snapshot.input_per_million),
        "cached_input_per_million": str(snapshot.cached_input_per_million),
        "output_per_million": str(snapshot.output_per_million),
        "currency": snapshot.currency,
    }


def _estimate_cost(model: str, usage) -> Decimal | None:
    snapshot = _pricing_for(model)
    if snapshot is None or usage is None:
        return None
    return snapshot.estimate(
        int(getattr(usage, "input_tokens", 0) or 0),
        int(_cached_tokens(usage) or 0),
        int(getattr(usage, "output_tokens", 0) or 0),
    )
