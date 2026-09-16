# Architecture

## Deployment boundary (Phase 2.7a)

Staging uses one shared application image for Gunicorn API and durable worker, PostgreSQL 16.4, an internal Compose network plus an outbound-capable network for API/worker provider access, and named PostgreSQL/temporary-input volumes. Caddy terminates public HTTPS at `https://dox-api.habeero.de` and proxies to the API's host-loopback binding `127.0.0.1:8000`; PostgreSQL and the worker have no public host ports. Redis, object storage, and remote provisioning remain deferred.

## Direction

The intended implementation is a Python/Flask modular monolith with an application factory, `/api/v1` blueprints, PostgreSQL, SQLAlchemy, Alembic, typed request/response schemas, centralized configuration, typed errors, and structured privacy-safe logging. Dependencies are explicitly composed at bootstrap; no global service locator or magic injection is used.

Phase 1 implements this foundation under `app/`. Phase 2.1 adds typed analysis/result boundaries; Phase 2.2 adds `intake/` application/domain ports and local storage/metadata adapters; Phase 2.3 adds the durable worker; Phase 2.4 adds the OpenAI adapter; and Phase 2.5 adds public operation delivery. `bootstrap/app_factory.py` creates an isolated app and invokes the explicit `Container` composition function; imports alone do not create engines or connections. `operations` has domain models, persistence ports, and focused SQLAlchemy adapters. Usage, idempotency, and temporary-input metadata are infrastructure-only persistence concerns, so they do not receive ceremonial domain layers. `ai/ports.py` supplies provider-neutral protocols only.

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

## Phase 2.3 worker

`python -m app.worker` is a separate polling process. PostgreSQL is the durable queue: a short `FOR UPDATE SKIP LOCKED` transaction claims one eligible operation, records its attempt and lease, then commits before loading input or executing. Completion/retry is a second short transaction. Stale leases are reclaimable; defaults are operational values.

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
