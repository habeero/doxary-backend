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

## Open questions (intentionally unresolved)

- Initial provider and exact model/configuration; regional/provider processing terms.
- Production upload/file/page/request limits and malware-scanning approach.
- Temporary-file and follow-up-context retention durations and backup/deletion policy.
- Anonymous/device-scoped abuse-control mechanism and thresholds.
- Pricing, free allowance, entitlement sources, and any reward-credit economics.
- Hosting/runtime platform, data residency, and operational deployment design.
- Exact legal/privacy disclosures, lawful basis, DPA/DPIA conclusions.
- Whether/when a non-sensitive capabilities endpoint is needed by Flutter.
