from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database.metadata import Base

result_json_type = JSON().with_variant(JSONB(), "postgresql")


class OperationResultRecord(Base):
    __tablename__ = "operation_results"
    __table_args__ = (
        UniqueConstraint("operation_id", name="uq_operation_results_operation_id"),
        Index("ix_operation_results_expires_at", "expires_at"),
    )

    operation_result_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    operation_id: Mapped[str] = mapped_column(ForeignKey("operations.operation_id"), nullable=False)
    schema_version: Mapped[str] = mapped_column(String(64), nullable=False)
    result_payload: Mapped[dict] = mapped_column(result_json_type, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
