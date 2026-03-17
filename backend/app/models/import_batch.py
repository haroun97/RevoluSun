"""
One row per Excel import run.

Tracks which file was imported and when. All raw readings, normalized readings,
daily consumption, sharing, and quality issues for that run link back to this batch.
"""
from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ImportBatch(Base):
    """One import run (e.g. one Excel file loaded)."""

    __tablename__ = "import_batches"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    status: Mapped[str] = mapped_column(String(64), nullable=False, default="completed")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Links to all data produced by this import
    raw_readings = relationship("RawMeterReading", back_populates="import_batch")
    normalized_readings = relationship("NormalizedMeterReading", back_populates="import_batch")
    daily_consumption = relationship("DailyMeterConsumption", back_populates="import_batch")
    daily_sharing = relationship("DailyEnergySharing", back_populates="import_batch")
    quality_issues = relationship("DataQualityIssue", back_populates="import_batch")
