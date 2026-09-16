# Usage and cost

Usage/cost observability is a first-class server responsibility from the first real provider test. Record an append-oriented event per provider attempt/accounting observation where available: `usage_event_id`, request/operation/attempt IDs, client document correlation only when necessary, operation type, provider identifier, model/config identifier, prompt identifier/version, output schema version, input/output/cached usage, page/input metrics, attempt number, latency, outcome, provider-reported or calculated cost, currency, pricing snapshot/version, and timestamp.

Raw document text, uploads, prompts containing document content, and raw provider responses never enter the ledger. Event identity permits calculations of average, median/P90, by operation/model/config, retries, daily/monthly aggregates, failed-attempt cost, and approximate unit economics. Store the applicable price components or immutable pricing snapshot reference with each event so later price changes do not rewrite historical cost.

Phase 1 uses the smallest viable immutable-evidence approach: each append-only `usage_events` row has an exact `NUMERIC(20,8)` `cost_amount`, ISO currency, and canonical `pricing_snapshot_json` containing the actual input price components/snapshot used at calculation time. It is not a pointer to a mutable current-pricing setting. No pricing-management service is introduced.

The ledger is distinct from quota/entitlement state. Future quota access must atomically reserve, consume, or release permission around an operation so concurrent requests cannot both spend the last credit. Potential sources—monthly allowance, reward, paid entitlement, promotion, admin/test credit—are policy concepts, not Phase 0 implementation; an ad is not permanently one analysis.
