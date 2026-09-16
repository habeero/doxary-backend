# Configuration

Future runtime configuration is centralized, typed, validated at startup, and injected through composition. Modules must not scatter `os.getenv` calls. Separate development, test, and production configurations; secrets are supplied only by an environment/secret manager, never committed or returned by endpoints.

Expected configuration groups include application environment, database URL, secret material, provider credentials, upload/request/page limits, temporary-file and follow-up-context retention, provider timeouts/retry bounds, rate limits, model-routing configuration, pricing snapshots, and feature flags. Exact production values—especially retention and upload limits—remain open policy decisions and must be explicitly justified before deployment.

Non-sensitive feature/capability configuration may later be exposed only through a deliberately designed client endpoint. Provider credentials, internal routes, price internals, and security settings are never client configuration.
