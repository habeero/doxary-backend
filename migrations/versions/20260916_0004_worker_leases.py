"""Add durable worker lease and retry metadata."""

import sqlalchemy as sa
from alembic import op

revision = "20260916_0004"
down_revision = "20260916_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("operations", sa.Column("worker_id", sa.String(length=128), nullable=True))
    op.add_column("operations", sa.Column("claimed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        "operations", sa.Column("lease_expires_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "operations", sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.create_index("ix_operations_worker_id", "operations", ["worker_id"])
    op.create_index("ix_operations_lease_expires_at", "operations", ["lease_expires_at"])
    op.create_index("ix_operations_next_attempt_at", "operations", ["next_attempt_at"])


def downgrade() -> None:
    op.drop_index("ix_operations_next_attempt_at", table_name="operations")
    op.drop_index("ix_operations_lease_expires_at", table_name="operations")
    op.drop_index("ix_operations_worker_id", table_name="operations")
    op.drop_column("operations", "next_attempt_at")
    op.drop_column("operations", "lease_expires_at")
    op.drop_column("operations", "claimed_at")
    op.drop_column("operations", "worker_id")
