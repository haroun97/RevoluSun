"""Stage 5: Proportional PV allocation per day -> daily_energy_sharing.

Uses only valid daily consumption rows (is_valid=True); negative deltas are excluded
from PV and tenant demand so allocation is based on physically plausible values.
"""
from datetime import date

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import DailyEnergySharing, DailyMeterConsumption


def run_sharing(session: Session, import_batch_id: int) -> int:
    """Per day: tenant_demand_i, pv_total, total_tenant_demand; allocated_pv_i = min(demand_i, pv_total * demand_i/total_demand); persist. Returns count.
    Only valid (non-negative) deltas are included in PV and tenant demand."""
    stmt = select(DailyMeterConsumption).where(
        DailyMeterConsumption.import_batch_id == import_batch_id,
        DailyMeterConsumption.is_valid.is_(True),
    )
    rows = session.scalars(stmt).all()
    if not rows:
        return 0

    df = pd.DataFrame([
        {
            "date": r.date,
            "meter_id": r.meter_id,
            "meter_type": r.meter_type,
            "tenant_id": r.tenant_id,
            "delta_kwh": r.delta_kwh,
        }
        for r in rows
    ])

    pv_daily = df[df["meter_type"] == "pv"].groupby("date")["delta_kwh"].sum()
    tenant_daily = df[df["meter_type"] == "tenant"].groupby(["date", "tenant_id"])["delta_kwh"].sum()

    count = 0
    for d in pv_daily.index:
        pv_total = max(0.0, pv_daily.get(d, 0.0))
        try:
            tenants_on_date = tenant_daily.loc[d]
        except KeyError:
            continue
        if isinstance(tenants_on_date, pd.Series):
            tenant_demands = tenants_on_date.to_dict()
        else:
            tenant_demands = {tenants_on_date.name: float(tenants_on_date)}

        total_demand = sum(max(0, v) for v in tenant_demands.values())
        if total_demand <= 0:
            for tid, demand in tenant_demands.items():
                session.add(DailyEnergySharing(
                    import_batch_id=import_batch_id,
                    date=d,
                    tenant_id=tid,
                    tenant_demand_kwh=demand,
                    allocated_pv_kwh=0.0,
                    grid_import_kwh=demand,
                    self_sufficiency_ratio=0.0,
                ))
                count += 1
            continue

        for tenant_id, tenant_demand in tenant_demands.items():
            tenant_demand = max(0.0, tenant_demand)
            allocated_pv = min(tenant_demand, pv_total * tenant_demand / total_demand)
            grid_import = tenant_demand - allocated_pv
            ratio = (allocated_pv / tenant_demand) if tenant_demand > 0 else 0.0
            session.add(DailyEnergySharing(
                import_batch_id=import_batch_id,
                date=d,
                tenant_id=tenant_id,
                tenant_demand_kwh=round(tenant_demand, 6),
                allocated_pv_kwh=round(allocated_pv, 6),
                grid_import_kwh=round(grid_import, 6),
                self_sufficiency_ratio=round(ratio, 6),
            ))
            count += 1

    return count
