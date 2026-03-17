"""
Stage 4: Run data quality checks and save findings to data_quality_issues.

We look for: (1) negative deltas (already flagged in daily_meter_consumption),
(2) missing days per meter (gaps in the date range), and (3) days where the sum
of tenant consumption does not match the building total (mismatch). Each finding
is stored as one DataQualityIssue row for the dashboard.
"""
from datetime import date

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import DailyMeterConsumption, DataQualityIssue


def run_quality_checks(session: Session, import_batch_id: int) -> int:
    """Run all quality checks for this batch and insert DataQualityIssue rows. Returns number of issues created."""
    stmt = select(DailyMeterConsumption).where(
        DailyMeterConsumption.import_batch_id == import_batch_id
    )
    rows = session.scalars(stmt).all()
    if not rows:
        return 0

    df = pd.DataFrame([
        {
            "meter_id": r.meter_id,
            "meter_type": r.meter_type,
            "tenant_id": r.tenant_id,
            "date": r.date,
            "delta_kwh": r.delta_kwh,
            "is_valid": r.is_valid,
        }
        for r in rows
    ])

    count = 0

    # Negative deltas (already flagged in daily_meter_consumption)
    invalid = df[df["is_valid"] == False]
    for _, r in invalid.iterrows():
        session.add(DataQualityIssue(
            import_batch_id=import_batch_id,
            issue_type="negative_delta",
            meter_id=r["meter_id"],
            tenant_id=r["tenant_id"] if pd.notna(r["tenant_id"]) else None,
            date=r["date"],
            severity="warning",
            message=f"Negative or invalid delta on {r['date']} for meter {r['meter_id']}",
        ))
        count += 1

    # Per-meter coverage: missing days / gaps (simplified: count distinct dates vs min-max range)
    for (meter_id, meter_type, tenant_id), group in df.groupby(["meter_id", "meter_type", "tenant_id"]):
        dates = sorted(group["date"].unique())
        if len(dates) < 2:
            continue
        min_d, max_d = dates[0], dates[-1]
        expected_days = (max_d - min_d).days + 1
        actual_days = len(dates)
        if actual_days < expected_days:
            session.add(DataQualityIssue(
                import_batch_id=import_batch_id,
                issue_type="missing_days",
                meter_id=meter_id,
                tenant_id=tenant_id if pd.notna(tenant_id) else None,
                date=None,
                severity="info",
                message=f"Meter {meter_id}: {expected_days - actual_days} missing days in range {min_d} to {max_d}",
            ))
            count += 1

    # Tenant sum vs building total: compare using only valid deltas (exclude negative deltas)
    valid_df = df[df["is_valid"] == True]
    building = valid_df[valid_df["meter_type"] == "building_total"]
    tenants = valid_df[valid_df["meter_type"] == "tenant"]
    if not building.empty and not tenants.empty:
        b_daily = building.groupby("date")["delta_kwh"].sum()
        t_daily = tenants.groupby("date")["delta_kwh"].sum()
        common_dates = b_daily.index.intersection(t_daily.index)
        for d in common_dates:
            b_val = b_daily.get(d, 0)
            t_val = t_daily.get(d, 0)
            if b_val <= 0:
                continue
            pct = abs(t_val - b_val) / b_val if b_val else 0
            if pct > 0.05:
                session.add(DataQualityIssue(
                    import_batch_id=import_batch_id,
                    issue_type="tenant_building_mismatch",
                    meter_id=None,
                    tenant_id=None,
                    date=d,
                    severity="warning",
                    message=f"On {d}: tenant sum ({t_val:.1f} kWh) deviates >5% from building total ({b_val:.1f} kWh)",
                ))
                count += 1

    return count
