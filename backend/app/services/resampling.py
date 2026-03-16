"""Stage 3: Derive daily consumption from normalized cumulative readings.

Negative deltas: Cumulative energy meters cannot physically decrease. A negative
delta (current_reading - previous_reading < 0) is invalid and can be caused by meter
reset, data corruption, unsorted timestamps, or wrong conversion factor. We do NOT
use abs(delta) and we do NOT sum negative deltas into consumption. Invalid deltas
are flagged as anomalies (is_valid=False, quality_flag='negative_delta') and
excluded from the daily aggregate; anomaly info remains available for data-quality
reports.
"""
from datetime import date

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import DailyMeterConsumption, NormalizedMeterReading


def run_resampling(session: Session, import_batch_id: int) -> int:
    """For each meter, sort by meter_id and timestamp, compute deltas, aggregate only
    valid (non-negative) deltas to daily, persist. Negative deltas are flagged but
    excluded from aggregation. Returns count of daily rows."""
    stmt = select(NormalizedMeterReading).where(
        NormalizedMeterReading.import_batch_id == import_batch_id
    ).order_by(NormalizedMeterReading.meter_id, NormalizedMeterReading.timestamp)
    rows = session.scalars(stmt).all()
    if not rows:
        return 0

    df = pd.DataFrame([
        {
            "meter_id": r.meter_id,
            "meter_type": r.meter_type,
            "tenant_id": r.tenant_id if r.tenant_id is not None else pd.NA,
            "timestamp": r.timestamp,
            "cumulative_kwh": r.cumulative_kwh,
        }
        for r in rows
    ])
    df["timestamp"] = pd.to_datetime(df["timestamp"]).dt.tz_localize(None)
    df["date"] = df["timestamp"].dt.date

    count = 0
    for (meter_id, meter_type, tenant_id), group in df.groupby(["meter_id", "meter_type", "tenant_id"], dropna=False):
        group = group.sort_values("timestamp")
        prev_cumulative = None
        daily_deltas: dict[date, float] = {}
        daily_invalid: dict[date, bool] = {}
        daily_flag: dict[date, str | None] = {}

        for _, r in group.iterrows():
            cum = r["cumulative_kwh"]
            dt = r["date"]
            if prev_cumulative is not None:
                delta = cum - prev_cumulative
                if dt not in daily_deltas:
                    daily_deltas[dt] = 0.0
                    daily_invalid[dt] = False
                    daily_flag[dt] = None
                if delta >= 0:
                    daily_deltas[dt] += delta
                else:
                    # Do not add negative delta to consumption; flag for data-quality report
                    daily_invalid[dt] = True
                    daily_flag[dt] = "negative_delta"
            prev_cumulative = cum

        for d, delta in daily_deltas.items():
            rec = DailyMeterConsumption(
                import_batch_id=import_batch_id,
                meter_id=meter_id,
                meter_type=meter_type,
                tenant_id=tenant_id if pd.notna(tenant_id) else None,
                date=d,
                delta_kwh=round(delta, 6),
                is_valid=not daily_invalid.get(d, False),
                quality_flag=daily_flag.get(d),
            )
            session.add(rec)
            count += 1

    return count
