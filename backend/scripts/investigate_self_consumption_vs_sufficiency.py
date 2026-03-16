#!/usr/bin/env python3
"""
Deep investigation: why building self-consumption can be ~0.34% while tenant
self-sufficiency is ~100%. Read-only DB queries to quantify date overlap and sums.
Run from backend/ with DB populated: python scripts/investigate_self_consumption_vs_sufficiency.py
"""
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import func, select

from app.db.session import SessionLocal
from app.models import DailyEnergySharing, DailyMeterConsumption
from app.services.analytics import get_latest_batch_id


def main() -> None:
    db = SessionLocal()
    try:
        batch_id = get_latest_batch_id(db)
        if batch_id is None:
            print("No import batch found. Run pipeline first.")
            return

        # Use a representative range: last 30 days from max date in data
        max_date = db.execute(
            select(func.max(DailyMeterConsumption.date)).where(
                DailyMeterConsumption.import_batch_id == batch_id
            )
        ).scalar()
        if not max_date:
            print("No dates in daily_meter_consumption.")
            return
        end_date = max_date
        start_date = end_date - timedelta(days=29)

        print("=== Self-consumption vs self-sufficiency: deep dive ===\n")
        print(f"Batch ID: {batch_id}")
        print(f"Date range: {start_date} to {end_date} (30 days)\n")

        # --- 1. PV: how many days have valid PV, and total kWh ---
        pv_days = db.execute(
            select(DailyMeterConsumption.date).where(
                DailyMeterConsumption.import_batch_id == batch_id,
                DailyMeterConsumption.meter_type == "pv",
                DailyMeterConsumption.is_valid.is_(True),
                DailyMeterConsumption.date >= start_date,
                DailyMeterConsumption.date <= end_date,
            ).distinct()
        ).scalars().all()
        pv_dates = {d for d in pv_days if d}
        pv_sum = db.execute(
            select(func.coalesce(func.sum(DailyMeterConsumption.delta_kwh), 0)).where(
                DailyMeterConsumption.import_batch_id == batch_id,
                DailyMeterConsumption.meter_type == "pv",
                DailyMeterConsumption.is_valid.is_(True),
                DailyMeterConsumption.date >= start_date,
                DailyMeterConsumption.date <= end_date,
            )
        ).scalar()
        pv_total_kwh = float(pv_sum or 0)
        print(f"1. PV (valid only)")
        print(f"   Distinct dates with valid PV in range: {len(pv_dates)}")
        print(f"   Sum delta_kwh (pv_total in summary):   {pv_total_kwh:.2f} kWh\n")

        # --- 2. Tenant: how many days have at least one tenant ---
        tenant_days = db.execute(
            select(DailyMeterConsumption.date).where(
                DailyMeterConsumption.import_batch_id == batch_id,
                DailyMeterConsumption.meter_type == "tenant",
                DailyMeterConsumption.is_valid.is_(True),
                DailyMeterConsumption.date >= start_date,
                DailyMeterConsumption.date <= end_date,
            ).distinct()
        ).scalars().all()
        tenant_dates = {d for d in tenant_days if d}
        tenant_sum = db.execute(
            select(func.coalesce(func.sum(DailyMeterConsumption.delta_kwh), 0)).where(
                DailyMeterConsumption.import_batch_id == batch_id,
                DailyMeterConsumption.meter_type == "tenant",
                DailyMeterConsumption.is_valid.is_(True),
                DailyMeterConsumption.date >= start_date,
                DailyMeterConsumption.date <= end_date,
            )
        ).scalar()
        tenant_total_kwh = float(tenant_sum or 0)
        print(f"2. Tenants (valid only)")
        print(f"   Distinct dates with at least one tenant: {len(tenant_dates)}")
        print(f"   Sum delta_kwh (total tenant demand):     {tenant_total_kwh:.2f} kWh\n")

        # --- 3. Overlap: dates where we have BOTH PV and tenant data (= allocation days) ---
        overlap_dates = pv_dates & tenant_dates
        print(f"3. Overlap (allocation days)")
        print(f"   Dates with both PV and tenant data: {len(overlap_dates)}")
        print(f"   (Sharing rows exist only for these dates.)\n")

        # --- 4. DailyEnergySharing: sum allocated_pv in range, and per-date breakdown ---
        sharing_rows = db.execute(
            select(
                DailyEnergySharing.date,
                func.sum(DailyEnergySharing.allocated_pv_kwh).label("allocated"),
                func.sum(DailyEnergySharing.tenant_demand_kwh).label("demand"),
                func.sum(DailyEnergySharing.grid_import_kwh).label("grid"),
            ).where(
                DailyEnergySharing.import_batch_id == batch_id,
                DailyEnergySharing.date >= start_date,
                DailyEnergySharing.date <= end_date,
            ).group_by(DailyEnergySharing.date)
        ).all()

        total_allocated = sum(float(r[1]) for r in sharing_rows)
        total_demand_in_sharing = sum(float(r[2]) for r in sharing_rows)
        total_grid = sum(float(r[3]) for r in sharing_rows)
        sharing_dates = {r[0] for r in sharing_rows}
        print(f"4. DailyEnergySharing (in range)")
        print(f"   Distinct dates with sharing rows: {len(sharing_dates)}")
        print(f"   Sum allocated_pv_kwh (self_consumed):   {total_allocated:.2f} kWh")
        print(f"   Sum tenant_demand_kwh:                 {total_demand_in_sharing:.2f} kWh")
        print(f"   Sum grid_import_kwh:                    {total_grid:.2f} kWh\n")

        # --- 5. Ratios ---
        self_ratio = (total_allocated / pv_total_kwh * 100) if pv_total_kwh else 0
        print(f"5. Building-level (summary logic)")
        print(f"   self_consumption_ratio = self_consumed / pv_total * 100")
        print(f"   = {total_allocated:.2f} / {pv_total_kwh:.2f} * 100 = {self_ratio:.2f}%")
        surplus = max(0, pv_total_kwh - total_allocated)
        surplus_ratio = (surplus / pv_total_kwh * 100) if pv_total_kwh else 0
        print(f"   surplus_ratio = {surplus_ratio:.2f}%\n")

        # --- 6. Per-tenant self-sufficiency (same as API) ---
        tenant_agg = db.execute(
            select(
                DailyEnergySharing.tenant_id,
                func.sum(DailyEnergySharing.tenant_demand_kwh).label("demand"),
                func.sum(DailyEnergySharing.allocated_pv_kwh).label("allocated"),
                func.sum(DailyEnergySharing.grid_import_kwh).label("grid"),
            ).where(
                DailyEnergySharing.import_batch_id == batch_id,
                DailyEnergySharing.date >= start_date,
                DailyEnergySharing.date <= end_date,
            ).group_by(DailyEnergySharing.tenant_id)
        ).all()
        print(f"6. Per-tenant (in range)")
        for tid, demand, allocated, grid in tenant_agg:
            d, a, g = float(demand), float(allocated), float(grid)
            ratio = (a / d * 100) if d > 0 else 0
            print(f"   {tid}: demand={d:.2f}, allocated={a:.2f}, grid={g:.2f} -> self_sufficiency={ratio:.2f}%")

        # --- 7. Why ratio is low ---
        print("\n7. Explanation")
        print(f"   PV total is summed over {len(pv_dates)} days in range.")
        print(f"   Allocation (self_consumed) is summed over {len(sharing_dates)} days only (days with both PV and tenant data).")
        if len(pv_dates) > len(sharing_dates):
            print(f"   So {len(pv_dates) - len(sharing_dates)} days have PV but no tenant data -> no allocation on those days.")
            print(f"   Numerator (allocated) is small; denominator (all PV) is large -> low self_consumption_ratio.")
        if sharing_dates and total_demand_in_sharing > 0 and total_allocated >= total_demand_in_sharing - 0.01:
            print(f"   On allocation days, allocated ({total_allocated:.2f}) >= demand ({total_demand_in_sharing:.2f}) -> grid_import ~0 -> tenant self_sufficiency ~100%.")

    finally:
        db.close()


if __name__ == "__main__":
    main()
