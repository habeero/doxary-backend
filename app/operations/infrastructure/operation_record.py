from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database.metadata import Base


class OperationRecord(Base):
    __tablename__ = "operations"
    __table_args__ = (
        CheckConstraint(
            "operation_type IN ('document_analysis', 'document_question', "
            "'reply_draft', 'reanalysis')",
            name="ck_operations_type",
        ),
        CheckConstraint(
            "status IN ('accepted', 'processing', 'succeeded', 'partial', "
            "'failed', 'cancelled', 'expired')",
            name="ck_operations_status",
        ),
    )

    operation_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    request_id: Mapped[str] = mapped_column(String(36), index=True)
    client_document_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    operation_type: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failure_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    worker_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    claimed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    lease_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    next_attempt_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
