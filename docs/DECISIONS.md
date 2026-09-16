# Architecture decisions and open questions

## Confirmed decisions

### D-001 — Async analysis operations

Document analysis uses an asynchronous operation resource: submission returns `202` with `operation_id`; clients poll status/result. This handles multi-page input, mobile interruption, retries, idempotency, and provider latency. A later bounded synchronous optimization may be additive but cannot replace the durable contract.

### D-002 — Local-first server boundary

The backend does not own permanent MVP Documents or original files. `client_document_id` is client-side correlation only; follow-up context, if persisted, has its own expiring identity. The server persists only operational responsibilities.

### D-003 — Structured, provider-neutral AI boundary

Providers are behind infrastructure adapters. Validated versioned product schemas—not raw provider JSON—cross the API boundary. Facts are distinct from language/style-dependent explanation and uncertainty wins over fabrication.

### D-004 — Operations, attempts, and ledger separation

One user-visible operation may contain multiple provider attempts. Per-attempt privacy-safe usage/cost records are append-oriented and retain pricing snapshots. Repository methods do not independently commit.

### D-005 — Hosting and commercialization deferred

Hosting, account auth, exact quota/credit economics, reward advertising, billing, and permanent storage are not decided or implemented. Doxary is a dedicated modular monolith, not a generic multi-app platform.

### D-006 — Phase 1 process health and immutable pricing evidence

`GET /api/v1/health` reports process liveness only; it does not claim database readiness. This keeps the initial health contract honest without creating a deployment-specific readiness system. Usage cost is stored as exact decimal plus a canonical immutable price-input snapshot per append-only event, rather than a reference to mutable current pricing. PostgreSQL is production-targeted; SQLite is restricted to fast normal tests, with PostgreSQL validation remaining an explicit local/CI step.

### D-007 — Validated JSON/JSONB temporary operation results

Phase 2.1 stores one validated, versioned `AnalysisResult` payload per operation in `operation_results`, using PostgreSQL JSONB (portable JSON elsewhere), mandatory expiry, and a unique operation relationship. The application boundary accepts only typed Pydantic models and revalidates payloads on reads. This avoids premature normalization of nested facts while preserving a real product contract. OperationResult is temporary delivery state and is deliberately separate from Phase 3 FollowUpContext.

### D-008 — Local temporary intake and metadata-only database record

Phase 2.2 accepts one PDF or ordered images through `POST /api/v1/document-analyses`, validates magic bytes and bounded limits, writes files through the `TemporaryDocumentStore` port, and records only storage reference/metadata in `temporary_inputs`. The initial adapter uses an operation-isolated local filesystem path; server-generated names prevent traversal/collision. A compensating delete handles database/storage failures. Shared/object storage is adopted only when multi-host workers, non-shared container disks, or horizontal scaling make local storage inadequate. No worker or provider call exists yet.

### D-009 — PostgreSQL worker with leases, no external queue

Phase 2.3 uses PostgreSQL row locking (`FOR UPDATE SKIP LOCKED`) as the MVP durable queue. Claims carry a worker ID and bounded lease; stale leases are reclaimable and attempt history drives a finite retry budget. The worker runs as `python -m app.worker`, outside Flask request lifetimes, and does not fabricate provider results. Redis/Celery/cloud queues remain deferred until throughput, contention, or distributed-runtime evidence justifies adoption.

### D-010 — Opt-in Responses API provider execution

Phase 2.4 keeps provider execution behind the worker executor boundary. OpenAI is enabled explicitly, the SDK uses no implicit retries, and temporary provider file resources are deleted after a request where possible. Public status/result delivery remains Phase 2.5.

### D-011 — Explicit provider privacy and telemetry boundaries

Document-analysis Responses requests set `store=False`. The provider transport schema contains model-generated fields only; Doxary injects server-owned `client_document_id` and `schema_version` before validating its authoritative `AnalysisResult v1` contract. Usage/latency and known Decimal cost are recorded even when post-response mapping fails. Unpriced models retain usage with null cost rather than fabricated pricing; pricing snapshots are immutable telemetry evidence, not billing.

### D-012 — Public operation polling and temporary result delivery

Phase 2.5 exposes `GET /api/v1/operations/{operation_id}` as a read-only, idempotent v1 resource. It maps internal states to four public statuses, returns only revalidated `AnalysisResult v1` on success, uses provider-neutral failures, and fails closed for missing/corrupt or expired results. Responses are private and `no-store`; authentication, ownership, quotas, rate limiting, push delivery, and regeneration remain deferred.

### D-014 - Explicit transport/domain normalization boundary

Provider structured output uses a transport schema weaker than Pydantic domain constraints. Doxary normalizes only enumerated date/time paths using documented, conservative ISO rules, then performs authoritative `AnalysisResult v1` validation. Ambiguous values fail closed; provider output and document-derived values are never logged. The truncated staging `required_documents` diagnostic remains of unknown nested cause.

### D-013 - One-host Compose staging topology

Phase 2.7a prepares one Ubuntu host with API and worker sharing one image, PostgreSQL 16, an internal Compose network, and named PostgreSQL/temporary-input volumes. The API binds loopback port 8000 for a future host reverse proxy. Shared local temporary storage is an MVP constraint; split hosts, horizontal scaling, non-shared disks, or stronger durability trigger object-storage evaluation. No remote provisioning, TLS, Redis, or object storage is included.

## Open questions (intentionally unresolved)

- Initial provider and exact model/configuration; regional/provider processing terms.
- Production upload/file/page/request limits and malware-scanning approach.
- Temporary-file and follow-up-context retention durations and backup/deletion policy.
- Anonymous/device-scoped abuse-control mechanism and thresholds.
- Pricing, free allowance, entitlement sources, and any reward-credit economics.
- Hosting/runtime platform, data residency, and operational deployment design.
- Exact legal/privacy disclosures, lawful basis, DPA/DPIA conclusions.
- Whether/when a non-sensitive capabilities endpoint is needed by Flutter.
