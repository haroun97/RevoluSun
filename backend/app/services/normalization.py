"""Stage 2: Normalize raw readings to cumulative_kwh and persist."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import NormalizedMeterReading, RawMeterReading


def run_normalization(session: Session, import_batch_id: int) -> int:
    """Read raw_meter_readings for batch, apply conversion, write normalized_meter_readings. Returns count."""
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
