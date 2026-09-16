"""Add temporary document input metadata.

Revision ID: 20260916_0003
Revises: 20260916_0002
Create Date: 2026-09-16
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "20260916_0003"
down_revision = "20260916_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    metadata_type = sa.JSON().with_variant(JSONB(), "postgresql")
    op.create_table(
        "temporary_inputs",
        sa.Column("operation_id", sa.String(length=36), nullable=False),
        sa.Column("input_kind", sa.String(length=16), nullable=False),
        sa.Column("storage_reference", sa.String(length=128), nullable=False),
        sa.Column("file_metadata", metadata_type, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["operation_id"], ["operations.operation_id"]),
        sa.PrimaryKeyConstraint("operation_id"),
        sa.UniqueConstraint("operation_id", name="uq_temporary_inputs_operation_id"),
        sa.UniqueConstraint("storage_reference", name="uq_temporary_inputs_storage_reference"),
    )
    op.create_index("ix_temporary_inputs_expires_at", "temporary_inputs", ["expires_at"])


def downgrade() -> None:
    op.drop_table("temporary_inputs")
