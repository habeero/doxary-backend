# Testing strategy

Phase 2.4 adds configuration, provider-boundary, cost, and worker/provider workflow coverage. Provider tests use a fake Responses client and never call OpenAI. They verify PDF file input and cleanup, ordered image input, prompt/schema selection, validated output, usage/latency, and provider-neutral failures. Workflow tests verify durable result and usage persistence, retry retention, terminal cleanup, and malformed-output rejection. Pricing uses exact `Decimal` arithmetic and an immutable snapshot; unknown models remain unpriced.

The worker's claim transaction commits before executor/network work and a separate transaction persists the terminal outcome. SQLite validates application workflow only. PostgreSQL `FOR UPDATE SKIP LOCKED`, row-lock exclusion, and concurrent claim behavior require the opt-in live PostgreSQL integration tests and are not proven by SQLite.

Provider boundary tests also map handcrafted complete, partial, and unavailable transport payloads through the production injection/validation helper, verify `store=False`, and verify failed provider responses retain usage/cost telemetry without creating results.

Phase 2.4 live validation performed one synthetic image request through the production worker/provider path and verified successful Responses execution, `AnalysisResult v1`, result and usage persistence, and temporary-input cleanup. The configured model had no pricing snapshot, so cost was correctly unavailable. This paid smoke path is opt-in and is not part of normal pytest.

Normal automated tests use fakes/fixtures, not live paid provider calls or real sensitive documents. Fixtures are synthetic or appropriately redacted.

- **Unit/application:** value behavior, normalization, lifecycle transitions, idempotency decisions, routing/prompt selection with fakes, no-fabrication and quality outcomes.
- **Persistence/migrations:** SQLAlchemy repositories where introduced, constraints, operation/attempt/usage relationships, forward migrations, pricing snapshots, and concurrent future credit reservation.
- **API/contract:** typed validation, multipart rules, error envelope, request IDs, idempotency conflicts/replay, status/result compatibility, pagination, and schema version compatibility.
- **AI boundary:** adapter isolation, malformed/unknown/missing structured output, bounded retry/fallback, evidence/uncertainty rules, prompt regression fixtures, and provider timeout/failure mapping.
- **Privacy/security:** log redaction, secret exclusion, upload validation, temporary-file cleanup/orphan recovery, context expiry/deletion, rate limits, and absence of sensitive telemetry.
- **Cost:** per-attempt usage event accuracy, retries/failures, latency, and historical price-snapshot calculation.

Every bug fix receives a focused regression test. Migrations are forward-only, reviewable, and tested against representative upgrade paths; production fixes never depend on dropping/resetting the database. Contract test fixtures protect Flutter compatibility.

Phase 1 tests cover factory configuration, process health, valid/invalid request correlation, typed/sanitized errors, operation lifecycle, privacy-safe formatter allowlisting, operation/attempt/idempotency constraints, exact decimal cost snapshots, and an Alembic upgrade against a temporary SQLite database. SQLite is solely the fast normal-test engine; it does not establish PostgreSQL-specific compatibility. PostgreSQL migration validation is an explicit local/CI step once a local PostgreSQL instance is available, not a hosted or paid test requirement.

Phase 2.1 adds contract tests for minimal complete/partial/unavailable results, empty and non-exclusive fact collections, Arabic and simple-German explanations, exact decimal amounts, evidence, uncertainty, quality reasons, malformed nested values, and schema version rejection. Persistence tests cover validated round trips, operation/result uniqueness, expiry, schema persistence, fail-closed corruption handling, and transaction ownership.

Phase 2.5 API tests cover pending and terminal status delivery, repeated GET idempotency, safe failed responses, unknown operations, expiry (`410`), missing/corrupt results (fail closed), request correlation, and private no-store caching. These use portable persistence; PostgreSQL locking remains covered only by the live integration suite.

Phase 2.7a adds Dockerfile/Compose static validation and a documented local smoke path using AI-disabled synthetic inputs. It must verify build, migration, liveness, shared temporary storage, PostgreSQL volume persistence, and clean restarts where Docker is available; it never makes a paid provider call.
