# Doxary backend

This is the dedicated backend for Doxary, a local-first assistant that helps people understand German administrative and formal documents. The Flutter client remains the durable MVP owner of product documents and related state. The backend will temporarily process requested uploads, coordinate AI-capable providers behind server boundaries, validate structured output, and record privacy-safe operational usage.

**Current status: Backend Phase 0 — architecture and documentation only.** No Flask application, dependencies, SQLAlchemy/Alembic setup, Docker files, provider integration, database migration, or deployment configuration is included.

Start with [Product context](docs/PRODUCT_CONTEXT.md), then [Architecture](docs/ARCHITECTURE.md), [API contract](docs/API_CONTRACT.md), and [Decisions](docs/DECISIONS.md). Each concern has one authoritative document, listed in [Architecture](docs/ARCHITECTURE.md#documentation-authority).

The intended future stack is a Python/Flask modular monolith with PostgreSQL, SQLAlchemy, and Alembic. Those are directional architecture decisions, not implemented dependencies in this phase.
