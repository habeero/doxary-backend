from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database.metadata import Base


class OperationAttemptRecord(Base):
    __tablename__ = "operation_attempts"
    __table_args__ = (
        UniqueConstraint("operation_id", "attempt_number", name="uq_operation_attempt_number"),
        CheckConstraint("attempt_number > 0", name="ck_attempt_number_positive"),
    )

    attempt_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    operation_id: Mapped[str] = mapped_column(
        ForeignKey("operations.operation_id"), nullable=False, index=True
    )
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    provider_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    model_config_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    prompt_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    prompt_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    output_schema_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    outcome: Mapped[str | None] = mapped_column(String(32), nullable=True)
    failure_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    retry_reason: Mapped[str | None] = mapped_column(String(128), nullable=True)
