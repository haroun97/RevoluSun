"""
Data quality findings: negative deltas, missing days, tenant/building mismatches, etc.

Each row is one issue (e.g. "negative delta on meter X on date Y"). The dashboard
uses this for the Data Quality view and alert counts.
"""
from datetime import date

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class DataQualityIssue(Base):
    """One quality issue (e.g. negative delta, missing tenant) for this import batch."""

    __tablename__ = "data_quality_issues"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    import_batch_id: Mapped[int] = mapped_column(ForeignKey("import_batches.id"), nullable=False)
    issue_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    meter_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    tenant_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    severity: Mapped[str] = mapped_column(String(32), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)

    import_batch = relationship("ImportBatch", back_populates="quality_issues")
