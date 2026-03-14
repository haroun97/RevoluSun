"""NormalizedMeterReading ORM model."""
from datetime import datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class NormalizedMeterReading(Base):
    __tablename__ = "normalized_meter_readings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    import_batch_id: Mapped[int] = mapped_column(ForeignKey("import_batches.id"), nullable=False)
    meter_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    meter_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    tenant_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    cumulative_kwh: Mapped[float] = mapped_column(Float, nullable=False)

    import_batch = relationship("ImportBatch", back_populates="normalized_readings")
