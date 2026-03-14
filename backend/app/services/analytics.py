"""Query helpers for API: aggregate from persisted tables."""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    DailyEnergySharing,
    DailyMeterConsumption,
    DataQualityIssue,
    ImportBatch,
)


def get_latest_batch_id(session: Session) -> int | None:
    """Return latest import_batch id by uploaded_at, or None."""
    r = session.scalar(select(ImportBatch.id).order_by(ImportBatch.uploaded_at.desc()).limit(1))
    return r


def summary_from_db(session: Session, batch_id: int | None = None) -> dict | None:
    """Aggregate total building consumption, PV, self-consumption ratio, surplus ratio, active tenants, quality alert count."""
    if batch_id is None:
        batch_id = get_latest_batch_id(session)
    if batch_id is None:
        return None

    # Building total consumption
    b = session.execute(
        select(func.coalesce(func.sum(DailyMeterConsumption.delta_kwh), 0)).where(
            DailyMeterConsumption.import_batch_id == batch_id,
            DailyMeterConsumption.meter_type == "building_total",
        )
    ).scalar()
    building_total = float(b or 0)

    # PV total
    pv = session.execute(
        select(func.coalesce(func.sum(DailyMeterConsumption.delta_kwh), 0)).where(
            DailyMeterConsumption.import_batch_id == batch_id,
            DailyMeterConsumption.meter_type == "pv",
        )
    ).scalar()
    pv_total = float(pv or 0)

    # Self-consumed = min(building, pv) concept: sum of allocated_pv from sharing
    allocated = session.execute(
        select(func.coalesce(func.sum(DailyEnergySharing.allocated_pv_kwh), 0)).where(
            DailyEnergySharing.import_batch_id == batch_id,
        )
    ).scalar()
    self_consumed = float(allocated or 0)
    surplus = max(0, pv_total - self_consumed) if pv_total else 0
    self_ratio = (self_consumed / pv_total * 100) if pv_total else 0
    surplus_ratio = (surplus / pv_total * 100) if pv_total else 0

    # Active tenants (distinct tenant_id in daily_consumption)
    tenants = session.execute(
        select(func.count(func.distinct(DailyMeterConsumption.tenant_id))).where(
            DailyMeterConsumption.import_batch_id == batch_id,
            DailyMeterConsumption.meter_type == "tenant",
            DailyMeterConsumption.tenant_id.isnot(None),
        )
    ).scalar()
    active_tenants = int(tenants or 0)

    # Quality alerts count
    q = session.execute(
        select(func.count(DataQualityIssue.id)).where(
            DataQualityIssue.import_batch_id == batch_id,
        )
    ).scalar()
    quality_alerts = int(q or 0)

    return {
        "total_building_consumption": round(building_total, 2),
        "total_pv_generation": round(pv_total, 2),
        "self_consumption_ratio": round(self_ratio, 2),
        "surplus_pv_ratio": round(surplus_ratio, 2),
        "active_tenants": active_tenants,
        "data_quality_alerts": quality_alerts,
    }


def building_timeseries(session: Session, batch_id: int | None, granularity: str = "daily") -> list[dict]:
    """Daily building consumption, PV, self-consumed, surplus per date."""
    if batch_id is None:
        batch_id = get_latest_batch_id(session)
    if batch_id is None:
        return []

    building = session.execute(
        select(DailyMeterConsumption.date, func.sum(DailyMeterConsumption.delta_kwh).label("kwh")).where(
            DailyMeterConsumption.import_batch_id == batch_id,
            DailyMeterConsumption.meter_type == "building_total",
        ).group_by(DailyMeterConsumption.date)
    ).all()

    pv = session.execute(
        select(DailyMeterConsumption.date, func.sum(DailyMeterConsumption.delta_kwh).label("kwh")).where(
            DailyMeterConsumption.import_batch_id == batch_id,
            DailyMeterConsumption.meter_type == "pv",
        ).group_by(DailyMeterConsumption.date)
    ).all()

    sharing = session.execute(
        select(
            DailyEnergySharing.date,
            func.sum(DailyEnergySharing.allocated_pv_kwh).label("allocated"),
        ).where(
            DailyEnergySharing.import_batch_id == batch_id,
        ).group_by(DailyEnergySharing.date)
    ).all()

    b_by_date = {d: kwh for d, kwh in building}
    pv_by_date = {d: kwh for d, kwh in pv}
    alloc_by_date = {d: a for d, a in sharing}
    all_dates = sorted(set(b_by_date) | set(pv_by_date))
    out = []
    for d in all_dates:
        b_val = float(b_by_date.get(d, 0))
        pv_val = float(pv_by_date.get(d, 0))
        self_val = float(alloc_by_date.get(d, 0))
        surplus_val = max(0, pv_val - self_val)
        out.append({
            "date": d.isoformat(),
            "building_consumption": round(b_val, 4),
            "pv_generation": round(pv_val, 4),
            "self_consumed_pv": round(self_val, 4),
            "surplus_pv": round(surplus_val, 4),
        })
    return out


def tenants_comparison(session: Session, batch_id: int | None) -> list[dict]:
    """Per tenant: total_consumption, average_daily_consumption, active_days."""
    if batch_id is None:
        batch_id = get_latest_batch_id(session)
    if batch_id is None:
        return []

    rows = session.execute(
        select(
            DailyMeterConsumption.tenant_id,
            func.sum(DailyMeterConsumption.delta_kwh).label("total"),
            func.count(DailyMeterConsumption.id).label("days"),
        ).where(
            DailyMeterConsumption.import_batch_id == batch_id,
            DailyMeterConsumption.meter_type == "tenant",
            DailyMeterConsumption.tenant_id.isnot(None),
        ).group_by(DailyMeterConsumption.tenant_id)
    ).all()

    return [
        {
            "tenant_id": tid,
            "total_consumption": round(float(total), 2),
            "average_daily_consumption": round(float(total) / days, 2) if days else 0,
            "active_days": int(days),
        }
        for tid, total, days in rows
    ]


def tenant_timeseries(session: Session, tenant_id: str, batch_id: int | None) -> list[dict]:
    """Date and consumption for one tenant."""
    if batch_id is None:
        batch_id = get_latest_batch_id(session)
    if batch_id is None:
        return []

    rows = session.execute(
        select(DailyMeterConsumption.date, DailyMeterConsumption.delta_kwh).where(
            DailyMeterConsumption.import_batch_id == batch_id,
            DailyMeterConsumption.meter_type == "tenant",
            DailyMeterConsumption.tenant_id == tenant_id,
        ).order_by(DailyMeterConsumption.date)
    ).all()

    return [{"date": d.isoformat(), "consumption": round(float(kwh), 4)} for d, kwh in rows]


def sharing_aggregates(session: Session, batch_id: int | None) -> list[dict]:
    """Per tenant: demand, allocated_pv, grid_import, self_sufficiency_ratio (aggregated over all days)."""
    if batch_id is None:
        batch_id = get_latest_batch_id(session)
    if batch_id is None:
        return []

    rows = session.execute(
        select(
            DailyEnergySharing.tenant_id,
            func.sum(DailyEnergySharing.tenant_demand_kwh).label("demand"),
            func.sum(DailyEnergySharing.allocated_pv_kwh).label("allocated"),
            func.sum(DailyEnergySharing.grid_import_kwh).label("grid"),
        ).where(
            DailyEnergySharing.import_batch_id == batch_id,
        ).group_by(DailyEnergySharing.tenant_id)
    ).all()

    out = []
    for tenant_id, demand, allocated, grid in rows:
        demand_f = float(demand)
        ratio = (float(allocated) / demand_f * 100) if demand_f > 0 else 0
        out.append({
            "tenant_id": tenant_id,
            "demand": round(demand_f, 2),
            "allocated_pv": round(float(allocated), 2),
            "grid_import": round(float(grid), 2),
            "self_sufficiency_ratio": round(ratio, 2),
        })
    return out


def quality_from_db(session: Session, batch_id: int | None) -> dict | None:
    """Quality summary, coverage entries for meters, and issue list."""
    if batch_id is None:
        batch_id = get_latest_batch_id(session)
    if batch_id is None:
        return None

    issues = session.scalars(
        select(DataQualityIssue).where(DataQualityIssue.import_batch_id == batch_id)
    ).all()

    negative = sum(1 for i in issues if i.issue_type == "negative_delta")
    missing = sum(1 for i in issues if i.issue_type == "missing_days")
    consistency_checks = [{"name": "tenant_building_mismatch", "count": sum(1 for i in issues if i.issue_type == "tenant_building_mismatch")}]

    # Build coverage entries from daily_meter_consumption: per meter, active_days and date range
    coverage_rows = session.execute(
        select(
            DailyMeterConsumption.meter_id,
            DailyMeterConsumption.meter_type,
            func.count(DailyMeterConsumption.id).label("active_days"),
            func.min(DailyMeterConsumption.date).label("min_date"),
            func.max(DailyMeterConsumption.date).label("max_date"),
        ).where(
            DailyMeterConsumption.import_batch_id == batch_id,
        ).group_by(DailyMeterConsumption.meter_id, DailyMeterConsumption.meter_type)
    ).all()

    coverage_ranges = []
    for meter_id, meter_type, active_days, min_date, max_date in coverage_rows:
        total_days = (max_date - min_date).days + 1 if min_date and max_date else 0
        coverage_pct = (active_days / total_days * 100) if total_days else 0
        gaps = sum(1 for i in issues if i.issue_type == "missing_days" and i.meter_id == meter_id)
        anomalies = sum(1 for i in issues if i.issue_type == "negative_delta" and i.meter_id == meter_id)
        status = "critical" if anomalies > 0 or coverage_pct < 90 else ("warning" if gaps > 0 or coverage_pct < 98 else "good")
        coverage_ranges.append({
            "meter_id": meter_id,
            "meter_name": meter_id,
            "meter_type": meter_type,
            "active_days": active_days,
            "total_days": total_days,
            "coverage": round(coverage_pct, 1),
            "gaps": gaps,
            "anomalies": anomalies,
            "status": status,
        })

    return {
        "negative_deltas": negative,
        "missing_days": missing,
        "coverage_ranges": coverage_ranges,
        "consistency_checks": consistency_checks,
        "issues": [
            {
                "id": i.id,
                "issue_type": i.issue_type,
                "meter_id": i.meter_id,
                "tenant_id": i.tenant_id,
                "date": i.date.isoformat() if i.date else None,
                "severity": i.severity,
                "message": i.message,
            }
            for i in issues
        ],
    }
