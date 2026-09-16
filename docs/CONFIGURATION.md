# Configuration

Future runtime configuration is centralized, typed, validated at startup, and injected through composition. Modules must not scatter `os.getenv` calls. Separate development, test, and production configurations; secrets are supplied only by an environment/secret manager, never committed or returned by endpoints.

Expected configuration groups include application environment, database URL, secret material, provider credentials, upload/request/page limits, temporary-file and follow-up-context retention, provider timeouts/retry bounds, rate limits, model-routing configuration, pricing snapshots, and feature flags. Exact production values—especially retention and upload limits—remain open policy decisions and must be explicitly justified before deployment.

Non-sensitive feature/capability configuration may later be exposed only through a deliberately designed client endpoint. Provider credentials, internal routes, price internals, and security settings are never client configuration.

Phase 1 implements one Pydantic settings object, loaded once by the application factory with `DOXARY_` environment variables and explicit test overrides. Current settings are environment (`development`, `test`, `production`), database URL, debug/testing, log level, and request-ID header name. Production requires `DOXARY_DATABASE_URL` and forces debug off. Tests supply their own in-memory SQLite URL; PostgreSQL remains the production target. Future setting groups remain documented extension points rather than unused behavior.
