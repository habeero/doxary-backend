"""Persist input preferences needed by queued provider execution."""

import sqlalchemy as sa
from alembic import op

revision = "20260916_0005"
down_revision = "20260916_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "temporary_inputs", sa.Column("client_document_id", sa.String(128), nullable=True)
    )
    op.add_column("temporary_inputs", sa.Column("output_language", sa.String(35), nullable=True))
    op.add_column("temporary_inputs", sa.Column("output_style", sa.String(16), nullable=True))


def downgrade() -> None:
    op.drop_column("temporary_inputs", "output_style")
    op.drop_column("temporary_inputs", "output_language")
    op.drop_column("temporary_inputs", "client_document_id")
