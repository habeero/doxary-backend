# Staging deployment (Phase 2.7a)

One Ubuntu host in Germany runs `postgres` (PostgreSQL 16), `api` (Gunicorn), and `worker` (`python -m app.worker`) from one application image. Compose uses an internal network, named `doxary_postgres` and `doxary_temporary` volumes, and binds API port `127.0.0.1:8000` for a future host-level reverse proxy. PostgreSQL is not publicly exposed; TLS, DNS, and proxy installation are deferred.

The shared temporary volume is valid only while API and worker remain on one host. Split hosts, horizontal scaling, non-shared disks, or stronger durability trigger object-storage evaluation. Temporary files remain bounded and are deleted by existing expiry/terminal cleanup; they are not permanent storage.

## Configuration and migration

Copy `.env.example` to ignored `.env`; set a strong `POSTGRES_PASSWORD` and the existing `DOXARY_*` settings. Keep `DOXARY_OPENAI_API_KEY` runtime-only; AI-disabled smoke tests are the default. In staging the database URL must address the Compose DNS name `postgres`. Never bake or print secrets.

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

Phase 2.7b manually provisions/hardens Hetzner Ubuntu in Germany; 2.7c installs proxy/DNS/HTTPS; 2.7d deploys this stack and secrets; 2.7e performs operational/backup verification; 2.7f connects Flutter. None is implemented here.
