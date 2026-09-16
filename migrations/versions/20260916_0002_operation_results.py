"""Add temporary validated operation results.

Revision ID: 20260916_0002
Revises: 20260916_0001
Create Date: 2026-09-16
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "20260916_0002"
down_revision = "20260916_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    payload_type = sa.JSON().with_variant(JSONB(), "postgresql")
    op.create_table(
        "operation_results",
        sa.Column("operation_result_id", sa.String(length=36), nullable=False),
        sa.Column("operation_id", sa.String(length=36), nullable=False),
        sa.Column("schema_version", sa.String(length=64), nullable=False),
        sa.Column("result_payload", payload_type, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["operation_id"], ["operations.operation_id"]),
        sa.PrimaryKeyConstraint("operation_result_id"),
        sa.UniqueConstraint("operation_id", name="uq_operation_results_operation_id"),
    )
    op.create_index("ix_operation_results_expires_at", "operation_results", ["expires_at"])


def downgrade() -> None:
    op.drop_table("operation_results")
