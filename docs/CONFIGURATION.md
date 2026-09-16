# Configuration

Pydantic Settings loads an optional local `.env`; operating-system environment variables override it. `.env` is ignored, `.env.example` is safe to track, and production may rely exclusively on environment/secret management. Phase 2.4 adds explicit AI enablement, OpenAI API key, model, reasoning effort, and timeout settings. Enabling AI without a key is a startup configuration error.

Worker defaults are poll interval 2 seconds, lease 300 seconds, maximum attempts 3, and retry delay 5 seconds. These are development/runtime defaults, not final production policy.

`DOXARY_AI_MODEL` selects the runtime provider model; pricing is configured separately as versioned telemetry evidence and is not inferred from the model name. The OpenAI API key is runtime-only secret configuration and is never persisted or exposed.

Future runtime configuration is centralized, typed, validated at startup, and injected through composition. Modules must not scatter `os.getenv` calls. Separate development, test, and production configurations; secrets are supplied only by an environment/secret manager, never committed or returned by endpoints.

Expected configuration groups include application environment, database URL, secret material, provider credentials, upload/request/page limits, temporary-file and follow-up-context retention, provider timeouts/retry bounds, rate limits, model-routing configuration, pricing snapshots, and feature flags. Exact production values—especially retention and upload limits—remain open policy decisions and must be explicitly justified before deployment.

Non-sensitive feature/capability configuration may later be exposed only through a deliberately designed client endpoint. Provider credentials, internal routes, price internals, and security settings are never client configuration.

Phase 1 implements one Pydantic settings object, loaded once by the application factory with `DOXARY_` environment variables and explicit test overrides. Current settings are environment (`development`, `test`, `production`), database URL, debug/testing, log level, and request-ID header name. Production requires `DOXARY_DATABASE_URL` and forces debug off. Tests supply their own in-memory SQLite URL; PostgreSQL remains the production target. Future setting groups remain documented extension points rather than unused behavior.

Phase 2.2 adds safe development/test defaults for temporary input root (`.doxary-tmp`), per-file size (10 MiB), total submission size (25 MiB), image pages (20), and temporary retention (24 hours). These are configuration defaults, not final production policy; exact limits and retention remain open and should be reviewed before deployment. Flask enforces the total request limit before the endpoint processes the body.
