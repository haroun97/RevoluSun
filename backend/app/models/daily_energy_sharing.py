"""DailyEnergySharing ORM model."""
from datetime import date

from sqlalchemy import Date, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class DailyEnergySharing(Base):
    __tablename__ = "daily_energy_sharing"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    import_batch_id: Mapped[int] = mapped_column(ForeignKey("import_batches.id"), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    tenant_demand_kwh: Mapped[float] = mapped_column(Float, nullable=False)
    allocated_pv_kwh: Mapped[float] = mapped_column(Float, nullable=False)
    grid_import_kwh: Mapped[float] = mapped_column(Float, nullable=False)
    self_sufficiency_ratio: Mapped[float] = mapped_column(Float, nullable=False)

    import_batch = relationship("ImportBatch", back_populates="daily_sharing")
