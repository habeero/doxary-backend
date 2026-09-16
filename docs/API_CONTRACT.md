# API contract

Future HTTP APIs are versioned under `/api/v1`. JSON uses `lower_snake_case`; externally visible IDs are opaque; timestamps are ISO-8601 with offsets; date-only values remain dates; product payloads carry explicit schema versions. Additive compatible change is preferred within v1. Future collections use cursor pagination: `?limit=&cursor=` and `{items, next_cursor}`.

## Identifiers

| Identifier | Meaning |
|---|---|
| `client_document_id` | Stable client-generated ID for a local Doxary Document. Correlates requests/results only; never implies server Document persistence. |
| `request_id` | One HTTP request’s observability correlation ID, accepted/generated via `X-Request-ID` and returned safely. |
| `operation_id` | Server ID for one logical processing operation, used to poll operation status. |
| `server_resource_id` | Reserved for future persisted/synced server product resources; unused for MVP Documents. |
| `follow_up_context_id` | Dedicated ID for minimal, expiring server follow-up context; neither a Document nor server resource ID. |

## Directional endpoints

| Endpoint | Directional contract |
|---|---|
| `GET /health` | Minimal liveness/readiness response; no sensitive diagnostics. |
| `POST /documents/analyze` | Multipart logical-document upload: required client ID, language/style preference, ordered file/page parts, and `Idempotency-Key`; returns `202` operation. |
| `GET /operations/{operation_id}` | Returns status and, on terminal success/partial state, validated product result. |
| `POST /assistant/questions` | Takes minimum client-scoped context plus question; returns validated answer or operation. |
| `POST /assistant/reply-drafts` | Takes scoped context and drafting intent; returns validated German draft or operation. |
| `DELETE /follow-up-contexts/{follow_up_context_id}` | Explicitly deletes retained follow-up context; idempotent deletion semantics to be specified. |
| `GET /capabilities` | Optional, non-sensitive enabled capability/schema information; only add when Flutter needs runtime negotiation. |

Analysis accepts one image, multiple ordered images/pages, or one PDF as a logical Document. It must validate allowed MIME and practical file signature/content, declared/actual size, request size, page/file count, malformed/corrupt input, safe generated filenames, and bounded temporary lifecycle. Exact production limits are configuration policy and intentionally unset in Phase 0. Filename extensions alone are never trusted.

## Operation response, idempotency, and errors

`POST /documents/analyze` is asynchronous by default: `202 {operation_id, status, request_id}`. Polling returns operation lifecycle status and an analysis envelope only when available. The client supplies a high-entropy `Idempotency-Key` for costly/mutating operations. Scope it by caller/device abuse-control scope plus route; bind it to a canonical request fingerprint; persist its result/operation for a configurable bounded replay window. A key reused for materially different input is rejected. It is not a document ID or request ID.

All errors use:

```json
{"error":{"code":"...","message":"...","retryable":false,"details":{}},"request_id":"..."}
```

`details` is only safe field-level feedback. The response never exposes stack traces, provider payloads, secrets, or raw content. HTTP mappings include 400 validation/malformed input, 404 operation/context absent or expired, 409 idempotency conflict, 413 size limit, 415 unsupported media, 422 insufficient document quality, 429 rate/quota limit, 503 capability/provider unavailable or timeout, and 500 unexpected failure. See `OPERATIONS.md` for product versus infrastructure states.

Stable error codes are intentionally typed rather than provider-derived: `validation_error`, `unsupported_media`, `malformed_file`, `corrupt_file`, `document_quality_insufficient`, `capability_unavailable`, `quota_exceeded`, `rate_limited`, `provider_timeout`, `provider_unavailable`, `provider_failure`, `structured_output_invalid`, `operation_not_found`, `operation_expired`, `context_not_found`, `context_expired`, and `internal_error`. Error messages are user-safe; retryability is set from the normalized category and current operation state, not copied from a provider message.
