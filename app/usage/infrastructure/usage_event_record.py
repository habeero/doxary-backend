from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database.metadata import Base


class UsageEventRecord(Base):
    __tablename__ = "usage_events"

    usage_event_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    request_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    operation_id: Mapped[str] = mapped_column(
        ForeignKey("operations.operation_id"), nullable=False, index=True
    )
    attempt_id: Mapped[str | None] = mapped_column(
        ForeignKey("operation_attempts.attempt_id"), nullable=True, index=True
    )
    operation_type: Mapped[str] = mapped_column(String(32), nullable=False)
    provider_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    model_config_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    prompt_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    prompt_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    output_schema_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    input_units: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_units: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cached_units: Mapped[int | None] = mapped_column(Integer, nullable=True)
    input_page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    outcome: Mapped[str | None] = mapped_column(String(32), nullable=True)
    cost_amount: Mapped[Decimal | None] = mapped_column(Numeric(20, 8), nullable=True)
    currency: Mapped[str | None] = mapped_column(String(3), nullable=True)
    pricing_snapshot_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
