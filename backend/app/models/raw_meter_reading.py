"""RawMeterReading ORM model."""
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class RawMeterReading(Base):
    __tablename__ = "raw_meter_readings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    import_batch_id: Mapped[int] = mapped_column(ForeignKey("import_batches.id"), nullable=False)
    source_sheet: Mapped[str] = mapped_column(String(128), nullable=False)
    meter_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    meter_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)  # tenant | building_total | pv
    tenant_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    serial_number: Mapped[str | None] = mapped_column(String(128), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    raw_value: Mapped[float] = mapped_column(Float, nullable=False)
    conversion_factor: Mapped[float] = mapped_column(Float, nullable=False)
    obis_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    import_batch = relationship("ImportBatch", back_populates="raw_readings")
