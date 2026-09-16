# Architecture

## Direction

The intended implementation is a Python/Flask modular monolith with an application factory, `/api/v1` blueprints, PostgreSQL, SQLAlchemy, Alembic, typed request/response schemas, centralized configuration, typed errors, and structured privacy-safe logging. Dependencies are explicitly composed at bootstrap; no global service locator or magic injection is used.

Phase 1 implements this foundation under `app/`. `bootstrap/app_factory.py` creates an isolated app and invokes the explicit `Container` composition function; imports alone do not create engines or connections. `operations` has a domain model, persistence port, and focused SQLAlchemy adapter. Usage and idempotency are infrastructure-only persistence concerns in this phase, so they do not receive ceremonial domain layers. `ai/ports.py` supplies provider-neutral protocols only.

The directional shape is:

```text
app/
  bootstrap/       composition, configuration, application factory
  core/            errors, IDs, logging, time, common primitives
  health/          feature module
  operations/      processing lifecycle and persistence
  ai/              application ports, routing, prompts, validation
  usage/           append-oriented usage/cost ledger
  assistant/       document-scoped question/reply workflows
  entitlements/    future access boundary only
  api/             API-wide boundary concerns
```

Feature internals use `domain/`, `application/`, `infrastructure/`, and `api/` only where valuable; empty ceremonial directories are prohibited. A blueprint converts HTTP to application inputs and outputs. Application workflows coordinate domain behavior and persistence ports. Infrastructure implements database, filesystem, provider, and external services. Domain/application do not import Flask, SQLAlchemy, Alembic, provider SDKs, or request objects. SQLAlchemy persistence models are infrastructure models, not automatically domain entities; use explicit mapping when a durable domain boundary benefits from it, but do not add mapping ceremony to trivial infrastructure-only records.

## Dependency direction

```text
API/Flask --> application --> domain
     |            |            ^
     v            v            |
 infrastructure adapters --------
```

Provider adapters live in AI infrastructure. Model routing, prompt selection, and output validation are reached through application-facing ports. No provider model name or payload becomes a domain/API product type.

## Documentation authority

| Concern | Authoritative document |
|---|---|
| Product/local-first scope | `PRODUCT_CONTEXT.md` |
| Architecture/dependency direction | this document |
| Server entities/retention | `DATA_MODEL.md` |
| HTTP and identifiers | `API_CONTRACT.md` |
| Provider/prompt/output design | `AI_ARCHITECTURE.md`, `AI_OUTPUT_SCHEMAS.md` |
| Operation behavior | `OPERATIONS.md` |
| Cost ledger | `USAGE_COST.md` |
| Security and privacy | `SECURITY_PRIVACY.md` |
| Runtime configuration | `CONFIGURATION.md` |
| Tests | `TESTING.md` |
| Confirmed decisions/open questions | `DECISIONS.md` |

## Transactions

An application workflow owns a meaningful transaction. Repositories stage reads/writes but do not commit independently. Never hold a database transaction during a long provider call: accept/idempotently create an operation and commit; process externally; then open a short transaction to record the attempt/result/terminal state. Recovery must be safe if a worker crashes between steps. A heavyweight Unit of Work abstraction is not mandated unless several workflows prove the need.

The Phase 1 SQLAlchemy repository and usage ledger intentionally call `Session.add` only. Their caller opens/commits/rolls back the transaction; no provider execution exists yet.
