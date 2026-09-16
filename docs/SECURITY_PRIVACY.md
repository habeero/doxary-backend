# Security and privacy

Doxary may process identity, immigration, employment, health, financial, and housing information. Architecture is not GDPR compliance or legal advice. Before production, verify provider DPA, data residency, retention, roles/lawful basis, DPIA need, privacy notice, deletion behavior, and applicable legal review.

## Phase 2.4 provider data flow

When explicitly enabled, the worker sends a temporary Doxary PDF or ordered images to OpenAI for analysis. The API key remains backend-only and is never logged, persisted, or exposed to Flutter. Raw provider payloads are not retained; structured output is validated before temporary result persistence. Provider retention, legal terms, and regional processing require deployment review.

Document-analysis requests explicitly set `store=False`; this is an application privacy control, not a claim of GDPR compliance.

## Required controls

- Require TLS; keep secrets in secret management, never source control or client apps; disable production debug and stack-trace disclosure.
- Treat uploads as untrusted: request/file/page limits, MIME plus practical signature/content checks, corrupt-file handling, safe generated filenames, isolated temporary storage, least-privilege access, malware-scanning policy, cleanup, and rate/abuse controls.
- Protect provider use with timeouts, bounded retries, rate limiting, quota boundaries, prompt-injection resistance, and validated structured output.
- Minimize follow-up context, exclude originals, make it expirably retained and explicitly deletable, and avoid cross-user exposure when accounts are later added.
- Restrict database/operator access by least privilege; review dependencies and security updates; maintain auditable administrative access where required.

## Logging, metrics, and deletion

Structured logs may contain request/operation ID, route, operation type, duration, status, attempt, model/config and prompt/schema identifiers, aggregate usage, and redacted error category. They must not ordinarily contain uploads, raw document text, names, addresses, account/insurance numbers, income, full prompts, or raw provider output. Metrics use aggregate operational data and are distinct from logs. Retention/cleanup must be observable without sensitive content.

Temporary original files are removed on normal completion, handled failure, expiry, and orphan recovery. Follow-up context supports explicit deletion and automatic expiry. Any future account/sync/cloud-storage deletion behavior—including backups—requires a separately documented policy.

MVP may be anonymous or device-scoped for abuse control only; device identity is not authentication. Technical rate limiting, provider protection, product quota, and upload limits solve different problems. JWT, passwords, OAuth, registration, and recovery are out of Phase 1 scope.

Phase 1 forces production debug off, centralizes secret-bearing configuration, returns a stable sanitized unexpected-error response, and uses an allowlist-based JSON formatter so arbitrary log extra fields such as document text are excluded. It has no upload or file-serving route, no authentication, and no provider integration. This is a security foundation, not a GDPR-compliance claim.

Phase 2.2 receives temporary copies only through the analysis submission route. It validates kind, magic bytes, size, count, page order, and language/style; generates server-owned storage paths; isolates each operation; stores no bytes in PostgreSQL; never serves files publicly; and records only non-content metadata/digests. Client filenames remain metadata and cannot control paths. Validation/storage failures trigger compensating deletion of partial files. Provider transfer does not occur until Phase 2.4. Cleanup is deterministic/expiry-aware but unscheduled; production retention remains an open decision.
