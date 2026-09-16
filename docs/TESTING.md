# Testing strategy

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
