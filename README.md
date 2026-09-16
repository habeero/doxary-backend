# Doxary backend

This is the dedicated backend for Doxary, a local-first assistant that helps people understand German administrative and formal documents. The Flutter client remains the durable MVP owner of product documents and related state. The backend will temporarily process requested uploads, coordinate AI-capable providers behind server boundaries, validate structured output, and record privacy-safe operational usage.

**Current status: Backend Phase 2.7 staging-verified.** The repository provides opt-in Responses API execution, structured `AnalysisResult v1` validation, temporary result persistence, provider telemetry, public operation delivery, and a verified one-host Docker Compose staging deployment. Flutter-to-staging validation and production hardening remain pending.

Start with [Product context](docs/PRODUCT_CONTEXT.md), then [Architecture](docs/ARCHITECTURE.md), [API contract](docs/API_CONTRACT.md), and [Decisions](docs/DECISIONS.md). Each concern has one authoritative document, listed in [Architecture](docs/ARCHITECTURE.md#documentation-authority).

The public read-only polling endpoint is `GET /api/v1/operations/{operation_id}`. The staging deployment is reachable through Caddy at `https://dox-api.habeero.de`; the API is bound to host loopback `127.0.0.1:8000`, while PostgreSQL and the worker have no public host ports. Flutter integration remains a separate client milestone.

See [staging deployment](docs/DEPLOYMENT.md) for build, migration, smoke-test, backup, and Germany-hosting requirements.

## Runtime and local development

The supported Python range is 3.12 through 3.14. PostgreSQL is the production database target; normal tests use SQLite only for fast generic persistence checks. Install the project and development tools with:

```powershell
python -m pip install -e ".[dev]"
```

Set `DOXARY_DATABASE_URL` to a PostgreSQL SQLAlchemy URL before running a non-test application. It is mandatory when `DOXARY_APP_ENV=production`; debug remains disabled in production. Run the test suite and checks with:

```powershell
python -m pytest
python -m ruff format --check .
python -m ruff check .
python -m alembic upgrade head
```

For development, construct the factory from `app:create_app`; a WSGI server/hosting choice remains intentionally outside this phase. Alembic uses `DOXARY_DATABASE_URL` only when supplied to its configuration by the invoking environment/tooling; set `sqlalchemy.url` or override it explicitly for local migration runs. Migrations are forward-only in deployment practice; the generated downgrade exists for local development tooling only and must not be used as a production recovery plan.
