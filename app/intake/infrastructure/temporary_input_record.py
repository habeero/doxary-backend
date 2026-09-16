from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database.metadata import Base

metadata_json_type = JSON().with_variant(JSONB(), "postgresql")


class TemporaryInputRecord(Base):
    __tablename__ = "temporary_inputs"
    __table_args__ = (
        UniqueConstraint("operation_id", name="uq_temporary_inputs_operation_id"),
        Index("ix_temporary_inputs_expires_at", "expires_at"),
    )

    operation_id: Mapped[str] = mapped_column(
        ForeignKey("operations.operation_id"), primary_key=True
    )
    input_kind: Mapped[str] = mapped_column(String(16), nullable=False)
    client_document_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    output_language: Mapped[str | None] = mapped_column(String(35), nullable=True)
    output_style: Mapped[str | None] = mapped_column(String(16), nullable=True)
    storage_reference: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    file_metadata: Mapped[list] = mapped_column(metadata_json_type, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
