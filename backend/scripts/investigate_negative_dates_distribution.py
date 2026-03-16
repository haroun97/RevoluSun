#!/usr/bin/env python3
"""Distribution of negative-delta dates: are building/PV invalid days clustered (e.g. after Feb 2025)?"""
import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

TIMESTAMP_COLS = ("timestamp", "Timestamp", "Zeit", "Datum", "Date", "time", "datetime")
VALUE_COLS = ("value", "Value", "Wert", "Reading", "raw_value", "kwh", "cumulative")
BUILDING_CONVERSION_FACTOR = 50.0
DEFAULT_CONVERSION_FACTOR = 1.0
BUILDING_SHEET_NAMES = ("Summenzähler", "Summe", "Building", "building_total")
PV_SHEET_NAMES = ("PV", "pv", "Photovoltaik", "Solar")


def _detect_timestamp_column(df):
    for c in TIMESTAMP_COLS:
        if c in df.columns:
            return c
    for c in df.columns:
        if "date" in c.lower() or "zeit" in c.lower() or "time" in c.lower():
            return c
    return None


def _detect_value_column(df):
    for c in VALUE_COLS:
        if c in df.columns:
            return c
    for c in df.columns:
        if "value" in c.lower() or "wert" in c.lower() or "kwh" in c.lower():
            return c
    for c in df.columns:
        if pd.api.types.is_numeric_dtype(df[c]):
            return c
    return None


def main():
    excel_path = Path(__file__).resolve().parent.parent.parent / "document" / "Messdaten_Nürnberg_2024-2026.xlsx"
    xl = pd.ExcelFile(excel_path, engine="openpyxl")

    for sheet_name in ["Summenzähler", "PV-Zähler"]:
        df = xl.parse(sheet_name)
        ts_col = _detect_timestamp_column(df)
        val_col = _detect_value_column(df)
        if not ts_col or not val_col:
            continue
        df = df[[ts_col, val_col]].copy()
        df.columns = ["ts", "raw"]
        df["ts"] = pd.to_datetime(df["ts"], errors="coerce")
        df = df.dropna(subset=["ts", "raw"])
        df["raw"] = pd.to_numeric(df["raw"], errors="coerce")
        df = df.dropna(subset=["raw"])
        conv = 50.0 if "Summen" in sheet_name else 1.0
        df["cumulative_kwh"] = df["raw"] * conv
        df["date"] = df["ts"].dt.date
        df = df.sort_values("ts").reset_index(drop=True)

        prev = None
        negative_dates = []
        for _, row in df.iterrows():
            cum = row["cumulative_kwh"]
            d = row["date"]
            if prev is not None and cum - prev < 0:
                negative_dates.append(d)
            prev = cum

        s = pd.Series(negative_dates)
        print(f"=== {sheet_name}: {len(negative_dates)} negative-delta days ===")
        print("By month (count):")
        print(s.groupby([d.month for d in s]).value_counts().sort_index().head(20) if len(s) else "N/A")
        by_month = pd.Series(negative_dates).apply(lambda d: f"{d.year}-{d.month:02d}")
        print(by_month.value_counts().sort_index())
        print("First 15 negative dates:", sorted(set(negative_dates))[:15])
        print("Last 15 negative dates:", sorted(set(negative_dates))[-15:])
        print()


if __name__ == "__main__":
    main()
