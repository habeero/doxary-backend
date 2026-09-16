"""Create Phase 1 backend-owned persistence.

Revision ID: 20260916_0001
Revises:
Create Date: 2026-09-16
"""

import sqlalchemy as sa
from alembic import op

revision = "20260916_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "operations",
        sa.Column("operation_id", sa.String(length=36), nullable=False),
        sa.Column("request_id", sa.String(length=36), nullable=False),
        sa.Column("client_document_id", sa.String(length=128), nullable=True),
        sa.Column("operation_type", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failure_code", sa.String(length=64), nullable=True),
        sa.CheckConstraint(
            "operation_type IN ('document_analysis', 'document_question', "
            "'reply_draft', 'reanalysis')",
            name="ck_operations_type",
        ),
        sa.CheckConstraint(
            "status IN ('accepted', 'processing', 'succeeded', 'partial', "
            "'failed', 'cancelled', 'expired')",
            name="ck_operations_status",
        ),
        sa.PrimaryKeyConstraint("operation_id"),
    )
    op.create_index("ix_operations_request_id", "operations", ["request_id"])
    op.create_index("ix_operations_client_document_id", "operations", ["client_document_id"])
    op.create_table(
        "operation_attempts",
        sa.Column("attempt_id", sa.String(length=36), nullable=False),
        sa.Column("operation_id", sa.String(length=36), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("provider_id", sa.String(length=64), nullable=True),
        sa.Column("model_config_id", sa.String(length=128), nullable=True),
        sa.Column("prompt_id", sa.String(length=128), nullable=True),
        sa.Column("prompt_version", sa.String(length=64), nullable=True),
        sa.Column("output_schema_version", sa.String(length=64), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("outcome", sa.String(length=32), nullable=True),
        sa.Column("failure_code", sa.String(length=64), nullable=True),
        sa.Column("retry_reason", sa.String(length=128), nullable=True),
        sa.CheckConstraint("attempt_number > 0", name="ck_attempt_number_positive"),
        sa.ForeignKeyConstraint(["operation_id"], ["operations.operation_id"]),
        sa.PrimaryKeyConstraint("attempt_id"),
        sa.UniqueConstraint("operation_id", "attempt_number", name="uq_operation_attempt_number"),
    )
    op.create_index("ix_operation_attempts_operation_id", "operation_attempts", ["operation_id"])
    op.create_table(
        "idempotency_records",
        sa.Column("idempotency_record_id", sa.String(length=36), nullable=False),
        sa.Column("scope", sa.String(length=128), nullable=False),
        sa.Column("key_hash", sa.String(length=64), nullable=False),
        sa.Column("request_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("request_id", sa.String(length=36), nullable=False),
        sa.Column("operation_id", sa.String(length=36), nullable=True),
        sa.Column("state", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["operation_id"], ["operations.operation_id"]),
        sa.PrimaryKeyConstraint("idempotency_record_id"),
        sa.UniqueConstraint("scope", "key_hash", name="uq_idempotency_scope_key"),
    )
    op.create_index("ix_idempotency_records_expires_at", "idempotency_records", ["expires_at"])
    op.create_table(
        "usage_events",
        sa.Column("usage_event_id", sa.String(length=36), nullable=False),
        sa.Column("request_id", sa.String(length=36), nullable=True),
        sa.Column("operation_id", sa.String(length=36), nullable=False),
        sa.Column("attempt_id", sa.String(length=36), nullable=True),
        sa.Column("operation_type", sa.String(length=32), nullable=False),
        sa.Column("provider_id", sa.String(length=64), nullable=True),
        sa.Column("model_config_id", sa.String(length=128), nullable=True),
        sa.Column("prompt_id", sa.String(length=128), nullable=True),
        sa.Column("prompt_version", sa.String(length=64), nullable=True),
        sa.Column("output_schema_version", sa.String(length=64), nullable=True),
        sa.Column("input_units", sa.Integer(), nullable=True),
        sa.Column("output_units", sa.Integer(), nullable=True),
        sa.Column("cached_units", sa.Integer(), nullable=True),
        sa.Column("input_page_count", sa.Integer(), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("outcome", sa.String(length=32), nullable=True),
        sa.Column("cost_amount", sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=True),
        sa.Column("pricing_snapshot_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["attempt_id"], ["operation_attempts.attempt_id"]),
        sa.ForeignKeyConstraint(["operation_id"], ["operations.operation_id"]),
        sa.PrimaryKeyConstraint("usage_event_id"),
    )
    op.create_index("ix_usage_events_request_id", "usage_events", ["request_id"])
    op.create_index("ix_usage_events_operation_id", "usage_events", ["operation_id"])
    op.create_index("ix_usage_events_attempt_id", "usage_events", ["attempt_id"])


def downgrade() -> None:
    op.drop_table("usage_events")
    op.drop_table("idempotency_records")
    op.drop_table("operation_attempts")
    op.drop_table("operations")
