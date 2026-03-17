"""
Query helpers for the API: read from the database and return data for the dashboard.

All functions take a database session and usually the latest import batch.
They aggregate from daily_meter_consumption, daily_energy_sharing, and
data_quality_issues. Optional start_date/end_date filter the date range.
"""
from datetime import date, timedelta
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.constants import (
    canonical_tenant_id,
    coverage_entry_sort_key,
    get_missing_tenant_ids,
    tenant_id_sort_key,
)
from app.models import (
    DailyEnergySharing,
    DailyMeterConsumption,
    DataQualityIssue,
    ImportBatch,
)


def _parse_date(s: str | None) -> date | None:
    """Parse ISO date string to date, or return None."""
    if not s or not s.strip():
        return None
    try:
        return date.fromisoformat(s.strip())
    except ValueError:
        return None


def get_latest_batch_id(session: Session) -> int | None:
    """Return the most recent import batch id (by upload time), or None if no data."""
    r = session.scalar(select(ImportBatch.id).order_by(ImportBatch.uploaded_at.desc()).limit(1))
    return r


def get_date_range(session: Session, batch_id: int | None = None) -> tuple[date | None, date | None]:
    """Return the earliest and latest date in daily consumption for this batch (for UI date picker)."""
    if batch_id is None:
        batch_id = get_latest_batch_id(session)
    if batch_id is None:
        return None, None
    row = session.execute(
        select(
            func.min(DailyMeterConsumption.date),
            func.max(DailyMeterConsumption.date),
        ).where(DailyMeterConsumption.import_batch_id == batch_id)
    ).one()
    return (row[0], row[1])


def summary_from_db(
    session: Session,
    batch_id: int | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
) -> dict | None:
    """Build the summary KPIs: building consumption, PV total, self-consumption %, surplus %, tenant count, quality alert count."""
    if batch_id is None:
        batch_id = get_latest_batch_id(session)
    if batch_id is None:
        return None

    # Building total consumption (only valid deltas; negative deltas excluded)
    b_cond = [
        DailyMeterConsumption.import_batch_id == batch_id,
        DailyMeterConsumption.meter_type == "building_total",
        DailyMeterConsumption.is_valid.is_(True),
    ]
    if start_date is not None:
        b_cond.append(DailyMeterConsumption.date >= start_date)
    if end_date is not None:
        b_cond.append(DailyMeterConsumption.date <= end_date)
    b = session.execute(
        select(func.coalesce(func.sum(DailyMeterConsumption.delta_kwh), 0)).where(*b_cond)
    ).scalar()
    building_total = float(b or 0)

    # PV total (only valid deltas; negative deltas excluded)
    pv_cond = [
        DailyMeterConsumption.import_batch_id == batch_id,
        DailyMeterConsumption.meter_type == "pv",
        DailyMeterConsumption.is_valid.is_(True),
    ]
    if start_date is not None:
        pv_cond.append(DailyMeterConsumption.date >= start_date)
    if end_date is not None:
        pv_cond.append(DailyMeterConsumption.date <= end_date)
    pv = session.execute(
        select(func.coalesce(func.sum(DailyMeterConsumption.delta_kwh), 0)).where(*pv_cond)
    ).scalar()
    pv_total = float(pv or 0)

    # Self-consumed: sum of allocated_pv from sharing (with date filter)
    sharing_cond = [DailyEnergySharing.import_batch_id == batch_id]
    if start_date is not None:
        sharing_cond.append(DailyEnergySharing.date >= start_date)
    if end_date is not None:
        sharing_cond.append(DailyEnergySharing.date <= end_date)
    allocated = session.execute(
        select(func.coalesce(func.sum(DailyEnergySharing.allocated_pv_kwh), 0)).where(*sharing_cond)
    ).scalar()
    self_consumed = float(allocated or 0)
    surplus = max(0, pv_total - self_consumed) if pv_total else 0
    self_ratio = (self_consumed / pv_total * 100) if pv_total else 0
    surplus_ratio = (surplus / pv_total * 100) if pv_total else 0

    # Active tenants (distinct tenant_id in daily_consumption)
    tenant_cond = [
        DailyMeterConsumption.import_batch_id == batch_id,
        DailyMeterConsumption.meter_type == "tenant",
        DailyMeterConsumption.tenant_id.isnot(None),
    ]
    if start_date is not None:
        tenant_cond.append(DailyMeterConsumption.date >= start_date)
    if end_date is not None:
        tenant_cond.append(DailyMeterConsumption.date <= end_date)
    tenants = session.execute(
        select(func.count(func.distinct(DailyMeterConsumption.tenant_id))).where(*tenant_cond)
    ).scalar()
    active_tenants = int(tenants or 0)

    # Quality alerts count (no date filter)
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


def _week_start(d: date) -> date:
    """Monday as week start."""
    return d - timedelta(days=d.weekday())


def _month_start(d: date) -> date:
    return d.replace(day=1)


def building_timeseries(
    session: Session,
    batch_id: int | None,
    granularity: str = "daily",
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[dict]:
    """Building consumption, PV, self-consumed, surplus per date (or per week/month)."""
    if batch_id is None:
        batch_id = get_latest_batch_id(session)
    if batch_id is None:
        return []

    b_cond = [
        DailyMeterConsumption.import_batch_id == batch_id,
        DailyMeterConsumption.meter_type == "building_total",
        DailyMeterConsumption.is_valid.is_(True),
    ]
    pv_cond = [
        DailyMeterConsumption.import_batch_id == batch_id,
        DailyMeterConsumption.meter_type == "pv",
        DailyMeterConsumption.is_valid.is_(True),
    ]
    sh_cond = [DailyEnergySharing.import_batch_id == batch_id]
    if start_date is not None:
        b_cond.append(DailyMeterConsumption.date >= start_date)
        pv_cond.append(DailyMeterConsumption.date >= start_date)
        sh_cond.append(DailyEnergySharing.date >= start_date)
    if end_date is not None:
        b_cond.append(DailyMeterConsumption.date <= end_date)
        pv_cond.append(DailyMeterConsumption.date <= end_date)
        sh_cond.append(DailyEnergySharing.date <= end_date)

    building = session.execute(
        select(DailyMeterConsumption.date, func.sum(DailyMeterConsumption.delta_kwh).label("kwh")).where(
            *b_cond
        ).group_by(DailyMeterConsumption.date)
    ).all()

    pv = session.execute(
        select(DailyMeterConsumption.date, func.sum(DailyMeterConsumption.delta_kwh).label("kwh")).where(
            *pv_cond
        ).group_by(DailyMeterConsumption.date)
    ).all()

    sharing = session.execute(
        select(
            DailyEnergySharing.date,
            func.sum(DailyEnergySharing.allocated_pv_kwh).label("allocated"),
        ).where(*sh_cond).group_by(DailyEnergySharing.date)
    ).all()

    b_by_date = {d: kwh for d, kwh in building}
    pv_by_date = {d: kwh for d, kwh in pv}
    alloc_by_date = {d: a for d, a in sharing}
    all_dates = sorted(set(b_by_date) | set(pv_by_date))

    if granularity == "weekly":
        buckets: dict[date, dict[str, float]] = {}
        for d in all_dates:
            bucket = _week_start(d)
            if bucket not in buckets:
                buckets[bucket] = {"building_consumption": 0, "pv_generation": 0, "self_consumed_pv": 0, "surplus_pv": 0}
            b_val = float(b_by_date.get(d, 0))
            pv_val = float(pv_by_date.get(d, 0))
            self_val = float(alloc_by_date.get(d, 0))
            buckets[bucket]["building_consumption"] += b_val
            buckets[bucket]["pv_generation"] += pv_val
            buckets[bucket]["self_consumed_pv"] += self_val
            buckets[bucket]["surplus_pv"] += max(0, pv_val - self_val)
        out = [
            {
                "date": b.isoformat(),
                "building_consumption": round(v["building_consumption"], 4),
                "pv_generation": round(v["pv_generation"], 4),
                "self_consumed_pv": round(v["self_consumed_pv"], 4),
                "surplus_pv": round(v["surplus_pv"], 4),
            }
            for b, v in sorted(buckets.items())
        ]
        return out
    if granularity == "monthly":
        buckets = {}
        for d in all_dates:
            bucket = _month_start(d)
            if bucket not in buckets:
                buckets[bucket] = {"building_consumption": 0, "pv_generation": 0, "self_consumed_pv": 0, "surplus_pv": 0}
            b_val = float(b_by_date.get(d, 0))
            pv_val = float(pv_by_date.get(d, 0))
            self_val = float(alloc_by_date.get(d, 0))
            buckets[bucket]["building_consumption"] += b_val
            buckets[bucket]["pv_generation"] += pv_val
            buckets[bucket]["self_consumed_pv"] += self_val
            buckets[bucket]["surplus_pv"] += max(0, pv_val - self_val)
        out = [
            {
                "date": b.isoformat(),
                "building_consumption": round(v["building_consumption"], 4),
                "pv_generation": round(v["pv_generation"], 4),
                "self_consumed_pv": round(v["self_consumed_pv"], 4),
                "surplus_pv": round(v["surplus_pv"], 4),
            }
            for b, v in sorted(buckets.items())
        ]
        return out

    # daily
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


def tenants_comparison(
    session: Session,
    batch_id: int | None,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[dict]:
    """Per tenant: total_consumption, average_daily_consumption, average_weekly_consumption, active_days."""
    if batch_id is None:
        batch_id = get_latest_batch_id(session)
    if batch_id is None:
        return []

    cond = [
        DailyMeterConsumption.import_batch_id == batch_id,
        DailyMeterConsumption.meter_type == "tenant",
        DailyMeterConsumption.tenant_id.isnot(None),
        DailyMeterConsumption.is_valid.is_(True),
    ]
    if start_date is not None:
        cond.append(DailyMeterConsumption.date >= start_date)
    if end_date is not None:
        cond.append(DailyMeterConsumption.date <= end_date)
    rows = session.execute(
        select(
            DailyMeterConsumption.tenant_id,
            func.sum(DailyMeterConsumption.delta_kwh).label("total"),
            func.count(DailyMeterConsumption.id).label("days"),
        ).where(*cond).group_by(DailyMeterConsumption.tenant_id)
    ).all()

    items = [
        {
            "tenant_id": tid,
            "total_consumption": round(float(total), 2),
            "average_daily_consumption": round(float(total) / days, 2) if days else 0,
            "average_weekly_consumption": round((float(total) / days) * 7, 2) if days else 0,
            "active_days": int(days),
        }
        for tid, total, days in rows
    ]
    # Collapse duplicates: Kunde01 and Kunde1 -> one row with canonical tenant_id and summed metrics
    by_canonical: dict[str, list[dict]] = {}
    for it in items:
        can = canonical_tenant_id(it["tenant_id"])
        if can not in by_canonical:
            by_canonical[can] = []
        by_canonical[can].append(it)
    collapsed = []
    for can, group in by_canonical.items():
        total_sum = sum(x["total_consumption"] for x in group)
        days_sum = sum(x["active_days"] for x in group)
        collapsed.append({
            "tenant_id": can,
            "total_consumption": round(total_sum, 2),
            "average_daily_consumption": round(total_sum / days_sum, 2) if days_sum else 0,
            "average_weekly_consumption": round((total_sum / days_sum) * 7, 2) if days_sum else 0,
            "active_days": int(days_sum),
        })
    collapsed.sort(key=lambda x: tenant_id_sort_key(x["tenant_id"]))
    return collapsed


def tenant_timeseries(
    session: Session,
    tenant_id: str,
    batch_id: int | None,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[dict]:
    """Date and consumption for one tenant."""
    if batch_id is None:
        batch_id = get_latest_batch_id(session)
    if batch_id is None:
        return []

    cond = [
        DailyMeterConsumption.import_batch_id == batch_id,
        DailyMeterConsumption.meter_type == "tenant",
        DailyMeterConsumption.tenant_id == tenant_id,
        DailyMeterConsumption.is_valid.is_(True),
    ]
    if start_date is not None:
        cond.append(DailyMeterConsumption.date >= start_date)
    if end_date is not None:
        cond.append(DailyMeterConsumption.date <= end_date)
    rows = session.execute(
        select(DailyMeterConsumption.date, DailyMeterConsumption.delta_kwh).where(
            *cond
        ).order_by(DailyMeterConsumption.date)
    ).all()

    return [{"date": d.isoformat(), "consumption": round(float(kwh), 4)} for d, kwh in rows]


def sharing_aggregates(
    session: Session,
    batch_id: int | None,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[dict]:
    """Per tenant: demand, allocated_pv, grid_import, self_sufficiency_ratio (aggregated over selected days)."""
    if batch_id is None:
        batch_id = get_latest_batch_id(session)
    if batch_id is None:
        return []

    cond = [DailyEnergySharing.import_batch_id == batch_id]
    if start_date is not None:
        cond.append(DailyEnergySharing.date >= start_date)
    if end_date is not None:
        cond.append(DailyEnergySharing.date <= end_date)
    rows = session.execute(
        select(
            DailyEnergySharing.tenant_id,
            func.sum(DailyEnergySharing.tenant_demand_kwh).label("demand"),
            func.sum(DailyEnergySharing.allocated_pv_kwh).label("allocated"),
            func.sum(DailyEnergySharing.grid_import_kwh).label("grid"),
        ).where(*cond).group_by(DailyEnergySharing.tenant_id)
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
    # Collapse duplicates by canonical tenant_id (Kunde01 + Kunde1 -> one row)
    by_canonical: dict[str, list[dict]] = {}
    for it in out:
        can = canonical_tenant_id(it["tenant_id"])
        if can not in by_canonical:
            by_canonical[can] = []
        by_canonical[can].append(it)
    collapsed = []
    for can, group in by_canonical.items():
        demand_sum = sum(x["demand"] for x in group)
        allocated_sum = sum(x["allocated_pv"] for x in group)
        grid_sum = sum(x["grid_import"] for x in group)
        ratio = (allocated_sum / demand_sum * 100) if demand_sum > 0 else 0
        collapsed.append({
            "tenant_id": can,
            "demand": round(demand_sum, 2),
            "allocated_pv": round(allocated_sum, 2),
            "grid_import": round(grid_sum, 2),
            "self_sufficiency_ratio": round(ratio, 2),
        })
    collapsed.sort(key=lambda x: tenant_id_sort_key(x["tenant_id"]))
    return collapsed


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

    coverage_ranges.sort(key=coverage_entry_sort_key)

    # Tenants expected (Kunde1–Kunde13) but with no data in this batch (e.g. Kunde7 missing from workbook)
    present_tenants = session.execute(
        select(DailyMeterConsumption.tenant_id).where(
            DailyMeterConsumption.import_batch_id == batch_id,
            DailyMeterConsumption.meter_type == "tenant",
            DailyMeterConsumption.tenant_id.isnot(None),
        ).distinct()
    ).scalars().all()
    missing_tenants = get_missing_tenant_ids([t for t in present_tenants if t])

    return {
        "negative_deltas": negative,
        "missing_days": missing,
        "coverage_ranges": coverage_ranges,
        "consistency_checks": consistency_checks,
        "missing_tenants": missing_tenants,
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
