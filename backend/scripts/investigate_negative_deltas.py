#!/usr/bin/env python3
"""
Read-only investigation: load Excel, apply same logic as pipeline (ingestion + normalization + resampling),
report where negative deltas occur and whether we might be excluding real data.
Run from backend/: python scripts/investigate_negative_deltas.py
"""
import re
import sys
from datetime import date, datetime
from pathlib import Path

import pandas as pd

# Run from backend/ so app is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Reuse ingestion column detection
TIMESTAMP_COLS = ("timestamp", "Timestamp", "Zeit", "Datum", "Date", "time", "datetime")
VALUE_COLS = ("value", "Value", "Wert", "Reading", "raw_value", "kwh", "cumulative")
BUILDING_CONVERSION_FACTOR = 50.0
DEFAULT_CONVERSION_FACTOR = 1.0
TENANT_SHEET_PATTERN = re.compile(r"^Kunde\s*(\d+)$", re.IGNORECASE)
BUILDING_SHEET_NAMES = ("Summenzähler", "Summe", "Building", "building_total")
PV_SHEET_NAMES = ("PV", "pv", "Photovoltaik", "Solar")


def _detect_timestamp_column(df: pd.DataFrame) -> str | None:
    for c in TIMESTAMP_COLS:
        if c in df.columns:
            return c
    for c in df.columns:
        if "date" in c.lower() or "zeit" in c.lower() or "time" in c.lower():
            return c
    return None


def _detect_value_column(df: pd.DataFrame) -> str | None:
    for c in VALUE_COLS:
        if c in df.columns:
            return c
    for c in df.columns:
        if "value" in c.lower() or "wert" in c.lower() or "kwh" in c.lower() or "reading" in c.lower():
            return c
    for c in df.columns:
        if pd.api.types.is_numeric_dtype(df[c]):
            return c
    return None


def classify_sheet(name: str) -> tuple[str, str | None] | None:
    name = name.strip()
    m = TENANT_SHEET_PATTERN.match(name)
    if m:
        return ("tenant", f"Kunde{m.group(1)}")
    if any(n in name for n in BUILDING_SHEET_NAMES):
        return ("building_total", None)
    if any(n in name for n in PV_SHEET_NAMES):
        return ("pv", None)
    return None


def main() -> None:
    # Use same path as typical .env
    excel_path = Path(__file__).resolve().parent.parent.parent / "document" / "Messdaten_Nürnberg_2024-2026.xlsx"
    if not excel_path.is_file():
        print(f"Excel not found: {excel_path}")
        sys.exit(1)

    xl = pd.ExcelFile(excel_path, engine="openpyxl")
    print("=== Sheet names ===")
    print(xl.sheet_names)
    print()

    results = []

    for sheet_name in xl.sheet_names:
        classified = classify_sheet(sheet_name)
        if not classified:
            continue
        meter_type, tenant_id = classified
        df = xl.parse(sheet_name)
        ts_col = _detect_timestamp_column(df)
        val_col = _detect_value_column(df)
        if not ts_col or not val_col:
            print(f"  Skip {sheet_name}: no timestamp or value column (cols: {list(df.columns)})")
            continue

        df = df[[ts_col, val_col]].copy()
        df.columns = ["ts", "raw"]
        df["ts"] = pd.to_datetime(df["ts"], errors="coerce")
        df = df.dropna(subset=["ts", "raw"])
        df["raw"] = pd.to_numeric(df["raw"], errors="coerce")
        df = df.dropna(subset=["raw"])
        if df.empty:
            continue

        conv = BUILDING_CONVERSION_FACTOR if meter_type == "building_total" else DEFAULT_CONVERSION_FACTOR
        df["cumulative_kwh"] = df["raw"] * conv
        df["date"] = df["ts"].dt.date
        df = df.sort_values("ts").reset_index(drop=True)

        meter_id = tenant_id or sheet_name
        prev = None
        negative_count = 0
        negative_dates = []
        total_delta_valid = 0.0
        total_delta_if_we_included_negative = 0.0
        readings_per_day = df.groupby("date").size()

        for _, row in df.iterrows():
            cum = row["cumulative_kwh"]
            d = row["date"]
            if prev is not None:
                delta = cum - prev
                total_delta_if_we_included_negative += delta
                if delta >= 0:
                    total_delta_valid += delta
                else:
                    negative_count += 1
                    if len(negative_dates) < 20:  # sample
                        negative_dates.append((d, delta, prev, cum))
            prev = cum

        results.append({
            "sheet": sheet_name,
            "meter_id": meter_id,
            "meter_type": meter_type,
            "rows": len(df),
            "date_min": df["date"].min(),
            "date_max": df["date"].max(),
            "negative_deltas": negative_count,
            "negative_dates_sample": negative_dates,
            "total_kwh_valid_only": total_delta_valid,
            "total_kwh_if_include_negative": total_delta_if_we_included_negative,
            "readings_per_day_max": int(readings_per_day.max()) if len(readings_per_day) else 0,
            "readings_per_day_median": float(readings_per_day.median()) if len(readings_per_day) else 0,
        })

    print("=== Per-sheet summary (sorted by negative_deltas desc) ===")
    for r in sorted(results, key=lambda x: -x["negative_deltas"]):
        print(f"\n--- {r['sheet']} ({r['meter_type']}) ---")
        print(f"  Rows: {r['rows']}, Date range: {r['date_min']} to {r['date_max']}")
        print(f"  Negative deltas: {r['negative_deltas']}")
        print(f"  Total kWh (valid deltas only): {r['total_kwh_valid_only']:.2f}")
        print(f"  Total kWh (if we included negative): {r['total_kwh_if_include_negative']:.2f}")
        print(f"  Readings per day: max={r['readings_per_day_max']}, median={r['readings_per_day_median']}")
        if r["negative_dates_sample"]:
            print(f"  Sample negative delta (date, delta, prev_cum, curr_cum):")
            for d, delta, prev, curr in r["negative_dates_sample"][:5]:
                print(f"    {d}: delta={delta:.2f}, prev={prev:.2f}, curr={curr:.2f}")

    print("\n=== Building_total and PV detail (source of 305 + 383 anomalies) ===")
    for r in results:
        if r["meter_type"] in ("building_total", "pv"):
            print(f"\n{r['meter_id']}: {r['negative_deltas']} negative deltas, "
                  f"valid total={r['total_kwh_valid_only']:.2f} kWh, "
                  f"with negative would be {r['total_kwh_if_include_negative']:.2f} kWh")

    print("\n=== Check: could unsorted timestamps cause false negatives? ===")
    print("Pipeline sorts by timestamp per meter. If Excel had unsorted rows, we'd still sort before delta.")
    print("So negative deltas in this script (after sort) = true decreases in cumulative value (meter reset or error).")

    print("\n=== Conclusion ===")
    total_neg = sum(r["negative_deltas"] for r in results)
    print(f"Total negative deltas across all meters: {total_neg}")
    print("These occur when cumulative value DECREASES (e.g. meter reset). Excluding them from aggregation")
    print("does not 'delete' real data: it avoids counting impossible consumption. On reset days we undercount")
    print("unless we implement reset detection (e.g. treat reset as new series).")


if __name__ == "__main__":
    main()
