"""
Stage 2: Convert raw readings to kWh and save as normalized readings.

We take each RawMeterReading, multiply raw_value by conversion_factor to get
cumulative_kwh, and write one NormalizedMeterReading per row. This gives a
single unit (kWh) for the next stage (daily deltas).
"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import NormalizedMeterReading, RawMeterReading


def run_normalization(session: Session, import_batch_id: int) -> int:
    """Read all raw readings for this batch, convert to kWh, insert normalized rows. Returns count inserted."""
    stmt = select(RawMeterReading).where(RawMeterReading.import_batch_id == import_batch_id)
    rows = session.scalars(stmt).all()
    count = 0
    for r in rows:
        cumulative_kwh = r.raw_value * r.conversion_factor
        rec = NormalizedMeterReading(
            import_batch_id=import_batch_id,
            meter_id=r.meter_id,
            meter_type=r.meter_type,
            tenant_id=r.tenant_id,
            timestamp=r.timestamp,
            cumulative_kwh=cumulative_kwh,
        )
        session.add(rec)
        count += 1
    return count
