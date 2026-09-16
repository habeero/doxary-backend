# Backend roadmap

Phase 2.4 implements opt-in OpenAI Responses analysis, versioned prompts, strict transport/domain validation, temporary provider telemetry, explicit `store=False`, and terminal temporary-input cleanup. Phase 2.5 still owns public operation polling and result delivery; Phase 2.6 owns Flutter integration. Pricing catalog/snapshot maintenance, user billing, credits, and monetization remain later operational/product work.

Phase 2.5 public polling and temporary result delivery is implemented. Phase 2.6 remains Flutter integration; Phase 3 remains questions, bounded context, and reply drafts. Authentication/ownership, quotas/rate limiting, push delivery, cloud storage, and reanalysis remain deferred.

- **Phase 0 — current:** authoritative architecture and documentation only.
- **Phase 1 — Flask foundation:** implemented application factory, typed config, PostgreSQL-oriented SQLAlchemy/Alembic foundation, API v1 process health/error/correlation/log-redaction, operation/attempt/usage/idempotency persistence, provider-neutral AI interfaces, and tests. No real provider.
- **Phase 2 — AI document analysis:** temporary uploads, initial provider adapter, vision/document analysis, structured validation, quality outcomes, operation attempts, usage/cost, prompt/model routing, and Flutter contract integration.
- **Phase 2.1 — analysis contract and temporary results:** implemented typed provider-neutral `AnalysisResult v1`, validated temporary `OperationResult` persistence, and the forward migration/tests needed for later result delivery. Uploads, workers, and providers remain deferred to subsequent Phase 2 increments.
- **Phase 2.2 — document intake and temporary storage:** implemented multipart submission validation, ordered PDF/image intake, local temporary storage, operation/idempotency creation, temporary input metadata, expiry cleanup primitive, and tests. Worker execution remains Phase 2.3; provider execution remains Phase 2.4.
- **Phase 3 — document-scoped assistant:** bounded follow-up context, questions, German reply drafts, deletion/expiry, and cost tracking.
- **Phase 4 — quotas/credits enforcement:** free allowance, configurable credits, possible future reward-credit integration, and paid entitlement integration only after product decisions.
- **Later when justified:** accounts, sync, permanent cloud storage, cross-device state, broader integrations, and extraction of backend components only after genuine multi-application reuse is proven.

No dates or hosting platform are promised.

The local filesystem adapter is intentionally an MVP runtime assumption. Shared/object storage becomes an adoption decision if API and worker run on different hosts, containers lack shared ephemeral disks, or horizontal scaling requires it; that trigger is deferred rather than ignored.
