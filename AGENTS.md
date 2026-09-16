# Doxary backend agent guidance

## Before changing anything

1. Read every applicable `AGENTS.md`, `README.md`, and relevant files under `docs/`.
2. Treat the ADRs in `docs/DECISIONS.md` as authoritative. Record material architecture or contract changes there and update affected documentation in the same change.
3. Resolve unknown product policy by documenting an open question; do not invent a requirement.

Documentation is part of the Definition of Done. After every implementation change, bug fix, refactor, contract or schema change, or architectural decision, review affected documentation and update it in the same change. Update this file for durable engineering rules, `docs/DECISIONS.md` for durable decisions, and `docs/ROADMAP.md` when functionality changes phase or deferral. Deferred capabilities must retain their rationale, intended phase or adoption trigger, and any preparation required now. If reviewed documentation needs no change, say so in the completion report.

## Architecture and boundaries

- Keep a pragmatic Flask modular monolith. HTTP blueprints are thin boundaries; compose dependencies explicitly in bootstrap code.
- Domain and application code must not depend on Flask, SQLAlchemy, Alembic, provider SDKs, or HTTP request objects.
- Keep provider-specific code in infrastructure. Do not expose provider payloads, SDK types, model names, or credentials in client/domain contracts.
- Use classes for identity, state, polymorphism, or meaningful dependency boundaries; prefer pure functions for stateless transformations and validation.
- Do not add global service locators, magic DI, catch-all `services.py`/`utils.py`, ceremonial layer directories, or repositories without a genuine persistence boundary.
- Application workflows own transaction boundaries. Repositories do not independently commit unless explicitly documented and justified.

## Product, data, and security rules

- Preserve local-first ownership: the Flutter client durably owns Organizations, Cases, Documents, files, analyses, corrections, tasks, deadlines, appointments, and preferences in the MVP.
- Never silently introduce permanent server document storage or mirror the Flutter schema. Original uploads are temporary processing artifacts only.
- Never conflate `client_document_id`, `request_id`, `operation_id`, and `server_resource_id`; see `docs/API_CONTRACT.md`.
- Keep follow-up context minimal, bounded, explicitly deletable, and separate from Document storage.
- Never log raw document content, uploads, prompts containing content, raw provider responses, or sensitive identifiers. Never commit secrets.
- Use forward-only Alembic migrations. Never reset or drop a production database to solve a migration issue.
- Add focused regression tests for fixes and preserve privacy-safe usage/cost observability.

## Scope control

- Do not create a generic multi-application platform, accounts, cloud sync, permanent cloud files, billing, or provider integration without an explicit ADR and approved scope.
- Keep `/api/v1` contracts backward compatible where practical; version product schemas explicitly.
