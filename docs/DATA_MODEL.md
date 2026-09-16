# Server-side data model

This model covers server responsibilities only. It deliberately does **not** contain Organizations, Cases, local Documents, document files, local analyses, tasks, deadlines, or appointments.

## Entities

| Entity | Purpose and key fields | Relationship / retention | First need |
|---|---|---|---|
| `operations` | Logical user-visible work: `operation_id`, request correlation, `client_document_id` where relevant, type, status, timestamps, failure category, idempotency reference, retry summary, prompt/model/config/schema references. | One-to-many attempts; metadata only, no original file/content. Retention policy required. | Phase 1 foundation |
| `operation_attempts` | A provider processing attempt: `attempt_id`, operation ID, ordinal, provider/config IDs, prompt/schema versions, timestamps, outcome, retry reason, latency. | Belongs to an operation; referenced by usage events. Retention aligned with operational/audit policy. | Phase 1 foundation |
| `usage_events` | Append-oriented cost/usage ledger: `usage_event_id`, operation/attempt/request IDs, operation type, provider/model config, prompt/schema, token/page metrics, cost/currency/pricing snapshot, latency, outcome, timestamp. | One event per provider-reported/calculated accounting record; never raw content. Long enough for financial/operational reporting; exact policy open. | Phase 1 foundation |
| `idempotency_records` | Prevent duplicate costly mutation: scoped key fingerprint, request fingerprint, operation/result reference, creation/expiry, completion state. | Does not use document identity as its primary key. Bounded configurable replay window. | Phase 1 foundation |
| `follow_up_contexts` | Minimal retained context: `follow_up_context_id`, structured-analysis context/summary, selected evidence snippets, context version, created/expiry/deletion timestamps. | Never original image/PDF; explicit deletion and automatic expiry. | Phase 3 |
| entitlement ledger/reservations | Future permission/reservation/consumption record with source and expiration. | Must support atomic reservation/consume/release; commercial policy unknown. | Phase 4 |

`client_document_id` is correlation metadata, not a foreign key to a server Documents table. IDs are UUIDv7 or comparably opaque, non-guessable IDs; externally visible IDs never encode sensitive information. `server_resource_id` is reserved for a future explicitly synced resource and is not needed by these tables.

## Data integrity and lifecycle

Operation status is separate from local Document state. Attempts make retries/fallbacks auditable without exposing multiple attempts as multiple user operations. Usage is append-oriented: corrections are compensating records, not destructive rewrites. Pricing snapshots/version identifiers are stored on every event so historical totals do not change when pricing configuration changes.

Phase 1 creates the first four tables in forward migration `20260916_0001`. `operations.operation_id`, attempt IDs, usage event IDs, and idempotency IDs are opaque UUID values rather than sequential public keys. `operation_attempts` enforces unique positive `attempt_number` per operation. `idempotency_records` enforces unique `(scope, key_hash)` and carries an indexed expiry. All relations are to backend operation/attempt rows only, never Flutter product tables.

`usage_events.cost_amount` is `NUMERIC(20, 8)`, never binary floating point. Each event stores a canonical, immutable `pricing_snapshot_json` with the actual price inputs used for its calculation; mutable current pricing configuration is not required to interpret historical cost.
