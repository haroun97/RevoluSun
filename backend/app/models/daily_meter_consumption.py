"""
Daily consumption per meter: one row = one meter, one day, consumption in kWh.

Computed from normalized cumulative readings: we take the difference (delta) between
consecutive readings and aggregate by day. Negative deltas are flagged (is_valid=False).
"""
from datetime import date

from sqlalchemy import Boolean, Date, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class DailyMeterConsumption(Base):
    """One day's consumption (kWh) for one meter; used for charts and summaries."""

    __tablename__ = "daily_meter_consumption"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    import_batch_id: Mapped[int] = mapped_column(ForeignKey("import_batches.id"), nullable=False)
    meter_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    meter_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    tenant_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    delta_kwh: Mapped[float] = mapped_column(Float, nullable=False)
    is_valid: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    quality_flag: Mapped[str | None] = mapped_column(String(64), nullable=True)

    import_batch = relationship("ImportBatch", back_populates="daily_consumption")
