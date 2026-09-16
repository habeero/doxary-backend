# Backend roadmap

Phases 2.4 and 2.5 are implemented: opt-in OpenAI Responses analysis, versioned prompts, strict transport/domain validation, temporary provider telemetry, explicit `store=False`, terminal temporary-input cleanup, and public operation polling/result delivery. Phase 2.6 remains Flutter integration. Pricing catalog/snapshot maintenance, user billing, credits, and monetization remain later operational/product work.

Phase 2.5 public polling and temporary result delivery is implemented. A one-host Phase 2.7 staging deployment is live and has passed backend synthetic E2E validation; Phase 2.6 remains Flutter integration. Phase 3 remains questions, bounded context, and reply drafts. Authentication/ownership, quotas/rate limiting, push delivery, cloud storage, and reanalysis remain deferred.

The verified Phase 2.7 staging slice includes a Germany-hosted Hetzner Ubuntu host, Docker Compose, Caddy HTTPS, non-public PostgreSQL/worker networking, temporary-volume initialization, migrations, health checks, and a successful real backend AI E2E. Production readiness remains pending Flutter-to-staging E2E, comprehensive backups and tested restore, production domain/configuration, host hardening, abuse controls, Caddy/access-log privacy review, provider privacy/data-processing review, pricing/cost policy, and final staging-to-production checks.

- **Phase 0 — current:** authoritative architecture and documentation only.
- **Phase 1 — Flask foundation:** implemented application factory, typed config, PostgreSQL-oriented SQLAlchemy/Alembic foundation, API v1 process health/error/correlation/log-redaction, operation/attempt/usage/idempotency persistence, provider-neutral AI interfaces, and tests. No real provider.
- **Phase 2 — AI document analysis:** temporary uploads, initial provider adapter, vision/document analysis, structured validation, quality outcomes, operation attempts, usage/cost, prompt/model routing, and Flutter contract integration.
- **Phase 2.1 — analysis contract and temporary results:** implemented typed provider-neutral `AnalysisResult v1`, validated temporary `OperationResult` persistence, and the forward migration/tests needed for later result delivery. Uploads, workers, and providers remain deferred to subsequent Phase 2 increments.
- **Phase 2.2 — document intake and temporary storage:** implemented multipart submission validation, ordered PDF/image intake, local temporary storage, operation/idempotency creation, temporary input metadata, expiry cleanup primitive, and tests. Worker execution remains Phase 2.3; provider execution remains Phase 2.4.
- **Phase 3 — document-scoped assistant:** bounded follow-up context, questions, German reply drafts, deletion/expiry, and cost tracking.
- **Phase 4 — quotas/credits enforcement:** free allowance, configurable credits, possible future reward-credit integration, and paid entitlement integration only after product decisions.
- **Later when justified:** accounts, sync, permanent cloud storage, cross-device state, broader integrations, and extraction of backend components only after genuine multi-application reuse is proven.

No dates or hosting platform are promised.

## Cross-project Phase 2 delivery sequence

- **Phase 2.6 â€” Flutter integration:** Flutter owns the real-client upload, polling, result mapping, and local persistence path; the backend contract remains stable. Local end-to-end validation is required before deployment.
- **Phase 2.7 — Staging deployment (partially verified):** the one-host Compose deployment, Caddy HTTPS endpoint, private database/worker networking, temporary-volume initialization, migrations, health, and backend AI E2E are verified. Flutter-to-staging validation, backup/restore, production configuration, hardening, abuse controls, provider privacy review, pricing policy, and final operational checks remain pending.
- **Phase 2.8 â€” Real-device and beta testing (deferred):** developer real-phone testing, then 2-3 informed trusted testers and later a broader closed beta, collecting quality, cost, latency, and failure evidence without adding document-content telemetry.
- **Phase 2.9 â€” Beta hardening/release preparation (deferred):** observed-failure fixes, privacy/disclosure review, operational limits, monitoring, release checklist, and Play testing/release readiness.
- **Phase 3 â€” Document-scoped assistant (deferred):** questions, bounded `FollowUpContext`, and German reply drafting.

The local filesystem adapter is intentionally an MVP runtime assumption. Shared/object storage becomes an adoption decision if API and worker run on different hosts, containers lack shared ephemeral disks, or horizontal scaling requires it; that trigger is deferred rather than ignored.
