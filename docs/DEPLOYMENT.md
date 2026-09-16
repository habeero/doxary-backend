# Staging deployment (Phase 2.7a)

One Ubuntu host in Germany runs `postgres` (PostgreSQL 16.4), `api` (Gunicorn), and `worker` (`python -m app.worker`) from one application image. Compose uses `doxary_internal` for private database traffic and a separate outbound-capable network for API/worker provider access, plus named `doxary_postgres` and `doxary_temporary` volumes. Caddy terminates public HTTPS and proxies `https://dox-api.habeero.de` to the API's host-loopback binding `127.0.0.1:8000`. PostgreSQL and the worker have no public host ports.

The current staging endpoint is `https://dox-api.habeero.de`; it is a staging deployment address, not automatically the permanent production API contract.

The verified backend E2E used a synthetic document and completed through Caddy, Gunicorn/Flask, multipart intake, PostgreSQL, the worker, OpenAI Responses, structured-result validation, public polling/result delivery, and terminal cleanup. `OperationResult`, `OperationAttempt`, and `UsageEvent` were persisted; the temporary database lifecycle row was marked deleted and the file was absent from `/var/lib/doxary/tmp`. The configured staging model was `gpt-5.6-luna`; usage was recorded and cost remained unavailable because no pricing snapshot exists for that model.

The shared temporary volume is valid only while API and worker remain on one host. A one-shot `temporary-init` Compose service runs as root, creates `/var/lib/doxary/tmp`, and idempotently assigns UID/GID `100:101`; API and worker depend on its successful completion and remain non-root. Split hosts, horizontal scaling, non-shared disks, or stronger durability trigger object-storage evaluation. Temporary files remain bounded and are deleted by existing expiry/terminal cleanup; they are not permanent storage.

## Configuration and migration

Copy `.env.example` to ignored `.env`; set `POSTGRES_DB`, `POSTGRES_USER`, and a strong `POSTGRES_PASSWORD`, plus the existing `DOXARY_*` settings. Set `DOXARY_DATABASE_URL` explicitly to the Compose DNS name `postgres`. Percent-encode any reserved characters in the URL user/password (or generate a URL-safe password); Compose does not safely URL-encode interpolated credentials. Keep `DOXARY_OPENAI_API_KEY` runtime-only; AI-disabled smoke tests are the default. Never bake or print secrets.

```powershell
docker compose -f compose.staging.yml config
docker compose -f compose.staging.yml build
docker compose -f compose.staging.yml up -d postgres
docker compose -f compose.staging.yml run --rm api alembic upgrade head
docker compose -f compose.staging.yml up -d api worker
docker compose -f compose.staging.yml ps
curl http://127.0.0.1:8000/api/v1/health
docker compose -f compose.staging.yml run --rm api alembic current
```

Migrations are an explicit operator step after PostgreSQL health is confirmed; processes never race migrations. Use forward upgrades only and do not auto-downgrade on rollback. The health endpoint is process liveness, not database readiness; PostgreSQL health is `pg_isready`.

All Doxary-controlled persistent data, temporary files, backups, and customer-derived metadata logs must remain on infrastructure physically hosted in Germany. OpenAI processing is a separate subprocessors/residency question and is not claimed Germany-only.

## Smoke, backup, and restore

With `DOXARY_AI_ENABLED=false`, build/start, migrate, verify health, inspect logs/status, restart PostgreSQL, and confirm the named volume persists. Use only synthetic inputs; verify both containers mount the temporary volume and cleanup remains effective. No paid AI request is automatic.

Keep `pg_dump` backups in Germany and test restore before production:

```powershell
docker compose -f compose.staging.yml exec -T postgres pg_dump -U "$env:POSTGRES_USER" "$env:POSTGRES_DB" > doxary-staging.sql
Get-Content doxary-staging.sql | docker compose -f compose.staging.yml exec -T postgres psql -U "$env:POSTGRES_USER" "$env:POSTGRES_DB"
```

Restore requires explicit operator confirmation of the target database; do not automate destructive restore. Temporary documents are generally not backup data.

The current one-host staging deployment and Caddy HTTPS path have been exercised, including migration, health, temporary-input cleanup, and a real backend analysis flow. Remaining production work includes comprehensive backup/restore verification, production-domain and secret decisions, host hardening, abuse controls, provider privacy review, and Flutter-to-staging validation. This document describes the reproducible Compose shape; it is not a claim that the system is production-ready.
