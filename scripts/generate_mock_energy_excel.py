#!/usr/bin/env python3
"""
Generate a mock Excel file for the RevoluSUN Energy Sharing case study.

Matches:
- Case study PDF: Kunde1–Kunde13 (Kunde7 missing), Summenzähler (factor 50), PV-Zähler.
- Columns: Seriennummer (optional), Zeit (timestamp), Wert (cumulative kWh); Kunde13 has OBIS-Code.
- Backend ingestion: sheet names and column names (Zeit, Wert) compatible with app/services/ingestion.py.

Output: data/mock_energy_data.xlsx (or path given as first argument).
"""

import random
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd

# --- Config ---
START_DATE = date(2024, 6, 1)
NUM_DAYS = 92
# Tenant sheet names: Kunde1–Kunde13 excluding Kunde7 (per case study)
TENANT_SHEETS = [f"Kunde{i}" for i in [1, 2, 3, 4, 5, 6, 8, 9, 10, 11, 12, 13]]
BUILDING_SHEET = "Summenzähler"
PV_SHEET = "PV"
# Building meter: displayed value = raw_value * 50 (so we store raw = actual_kwh / 50)
BUILDING_FACTOR = 50


def _daily_consumption_kwh(tenant_idx: int, day_offset: int, is_weekend: bool) -> float:
    """Realistic daily consumption per tenant (kWh)."""
    base = 8 + (tenant_idx % 5) * 4 + random.uniform(-1.5, 1.5)
    if is_weekend:
        base *= 0.85
    return max(0.1, round(base, 2))


def _daily_pv_kwh(day_offset: int, is_weekend: bool) -> float:
    """PV generation (kWh) – higher in summer, some variance."""
    # June–Aug: roughly 30–70 kWh/day
    month = (START_DATE + timedelta(days=day_offset)).month
    base = 35 + (month - 5) * 5 + random.uniform(-8, 12)
    if random.random() < 0.15:  # cloudy
        base *= 0.3
    return max(0, round(base, 2))


def _tenant_coverage(tenant_idx: int) -> tuple[int, int]:
    """Return (first_day_offset, last_day_offset) for this tenant (irregular coverage)."""
    # Some tenants start later or end earlier (case study: different coverage periods)
    n = NUM_DAYS
    if tenant_idx == 0:
        return 0, n - 1
    if tenant_idx == 1:
        return 5, n - 1  # starts 5 days later
    if tenant_idx == 2:
        return 0, n - 6  # ends 5 days earlier
    if tenant_idx in (3, 4):
        return 2, n - 3
    return 0, n - 1


def _maybe_skip_day(tenant_idx: int, day_offset: int) -> bool:
    """Occasional gap (missing day) for some meters."""
    if tenant_idx not in (1, 4):
        return False
    # 2–3 missing days per meter
    return (day_offset + tenant_idx * 17) % 31 in (0, 15)


def generate_tenant_sheet(name: str, tenant_idx: int, include_obis: bool) -> pd.DataFrame:
    """One sheet: Seriennummer, Zeit, Wert (cumulative kWh). Kunde13: add OBIS-Code."""
    start_off, end_off = _tenant_coverage(tenant_idx)
    serial = f"SN-T-{1000 + tenant_idx}"
    base_cumulative = 1000.0 + tenant_idx * 500 + random.uniform(0, 200)
    rows = []
    cum = base_cumulative
    for d in range(start_off, end_off + 1):
        if _maybe_skip_day(tenant_idx, d):
            continue
        dt = datetime.combine(START_DATE + timedelta(days=d), datetime.min.time())
        is_weekend = (START_DATE + timedelta(days=d)).weekday() >= 5
        daily = _daily_consumption_kwh(tenant_idx, d, is_weekend)
        cum += daily
        row = {"Seriennummer": serial, "Zeit": dt, "Wert": round(cum, 4)}
        if include_obis:
            row["OBIS-Code"] = "1-0:1.8.0"
        rows.append(row)
    df = pd.DataFrame(rows)
    return df


def generate_building_sheet_simple() -> pd.DataFrame:
    """Summenzähler: daily cumulative raw dial value. Actual kWh = Wert * 50."""
    cum_actual_kwh = 0.0
    base_raw = 1000.0  # starting dial reading (raw)
    rows = []
    for d in range(NUM_DAYS):
        dt = datetime.combine(START_DATE + timedelta(days=d), datetime.min.time())
        is_weekend = (START_DATE + timedelta(days=d)).weekday() >= 5
        daily_kwh = 120 + random.uniform(-25, 35)
        if is_weekend:
            daily_kwh *= 0.9
        cum_actual_kwh += daily_kwh
        raw_value = base_raw + cum_actual_kwh / BUILDING_FACTOR
        rows.append({"Zeit": dt, "Wert": round(raw_value, 4)})
    return pd.DataFrame(rows)


def generate_pv_sheet() -> pd.DataFrame:
    """PV-Zähler: daily cumulative generation (kWh)."""
    cum = 0.0
    rows = []
    for d in range(NUM_DAYS):
        dt = datetime.combine(START_DATE + timedelta(days=d), datetime.min.time())
        daily = _daily_pv_kwh(d, (START_DATE + timedelta(days=d)).weekday() >= 5)
        cum += daily
        rows.append({"Zeit": dt, "Wert": round(cum, 4)})
    return pd.DataFrame(rows)


def main() -> None:
    out_dir = Path(__file__).resolve().parent.parent / "data"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "mock_energy_data.xlsx"
    if len(sys.argv) > 1:
        out_path = Path(sys.argv[1]).resolve()

    random.seed(42)
    with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
        for idx, name in enumerate(TENANT_SHEETS):
            df = generate_tenant_sheet(name, idx, include_obis=(name == "Kunde13"))
            df.to_excel(writer, sheet_name=name, index=False)
        generate_building_sheet_simple().to_excel(writer, sheet_name=BUILDING_SHEET, index=False)
        generate_pv_sheet().to_excel(writer, sheet_name=PV_SHEET, index=False)

    print(f"Written: {out_path}")
    print(f"Sheets: {TENANT_SHEETS + [BUILDING_SHEET, PV_SHEET]}")


if __name__ == "__main__":
    main()
