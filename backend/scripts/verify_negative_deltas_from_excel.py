#!/usr/bin/env python3
"""
Standalone verification script: recompute negative deltas directly from the Excel file
and list exactly where they occur (sheet, original row index, timestamp, prev, curr, delta).

Usage (from backend/):

  python scripts/verify_negative_deltas_from_excel.py

This DOES NOT touch the database. It works only on the Excel file
`document/Messdaten_Nürnberg_2024-2026.xlsx`.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


EXCEL_REL_PATH = Path("..") / "document" / "Messdaten_Nürnberg_2024-2026.xlsx"

# Column name variants reused from ingestion logic
TIMESTAMP_COLS = ("timestamp", "Timestamp", "Zeit", "Datum", "Date", "time", "datetime")
VALUE_COLS = ("value", "Value", "Wert", "Reading", "raw_value", "kwh", "cumulative")


def detect_timestamp_column(df: pd.DataFrame) -> str | None:
    for c in TIMESTAMP_COLS:
        if c in df.columns:
            return c
    for c in df.columns:
        name = str(c).lower()
        if "date" in name or "zeit" in name or "time" in name:
            return c
    return None


def detect_value_column(df: pd.DataFrame) -> str | None:
    for c in VALUE_COLS:
        if c in df.columns:
            return c
    for c in df.columns:
        name = str(c).lower()
        if "value" in name or "wert" in name or "kwh" in name or "reading" in name:
            return c
    # Fallback: first numeric column
    for c in df.columns:
        if pd.api.types.is_numeric_dtype(df[c]):
            return c
    return None


def analyse_sheet(name: str, df: pd.DataFrame, conversion_factor: float = 1.0) -> pd.DataFrame:
    """
    Return a DataFrame of all rows where the cumulative value decreases
    after sorting by timestamp.
    Columns in result:
      - sheet
      - original_row (0-based index in Excel sheet)
      - timestamp
      - prev_timestamp
      - prev_cumulative
      - curr_cumulative
      - delta
    """
    ts_col = detect_timestamp_column(df)
    val_col = detect_value_column(df)
    if not ts_col or not val_col:
        return pd.DataFrame()

    # Keep original index so we can point back into the sheet
    df = df[[ts_col, val_col]].copy()
    df.columns = ["timestamp_raw", "value_raw"]
    df["timestamp"] = pd.to_datetime(df["timestamp_raw"], errors="coerce")
    df["value"] = pd.to_numeric(df["value_raw"], errors="coerce")
    df = df.dropna(subset=["timestamp", "value"])
    if df.empty:
        return pd.DataFrame()

    df["cumulative"] = df["value"] * conversion_factor

    # Preserve the original row index from Excel before sort
    df["original_row"] = df.index

    df = df.sort_values("timestamp").reset_index(drop=True)
    df["prev_cumulative"] = df["cumulative"].shift(1)
    df["prev_timestamp"] = df["timestamp"].shift(1)
    df["delta"] = df["cumulative"] - df["prev_cumulative"]

    neg = df[df["delta"] < 0].copy()
    if neg.empty:
        return pd.DataFrame()

    neg.insert(0, "sheet", name)
    cols = [
        "sheet",
        "original_row",
        "timestamp",
        "prev_timestamp",
        "prev_cumulative",
        "cumulative",
        "delta",
    ]
    return neg[cols]


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify negative deltas directly from Excel.")
    parser.add_argument(
        "--excel-path",
        type=str,
        default=str(EXCEL_REL_PATH),
        help="Path to Messdaten_Nürnberg_2024-2026.xlsx (default: ../document/...).",
    )
    parser.add_argument(
        "--output-csv",
        type=str,
        default="negative_deltas_from_excel.csv",
        help="CSV file to write full list of negative deltas.",
    )
    args = parser.parse_args()

    excel_path = Path(args.excel_path).resolve()
    if not excel_path.is_file():
        print(f"Excel not found at {excel_path}")
        return

    print(f"Using Excel file: {excel_path}")

    xl = pd.ExcelFile(excel_path, engine="openpyxl")
    all_neg = []

    # Conversion factors mirror the ingestion logic: 50 for building total, 1 otherwise
    BUILDING_SHEETS = {"Summenzähler", "Summe", "Building", "building_total"}

    for sheet_name in xl.sheet_names:
        df = xl.parse(sheet_name)
        conv = 50.0 if sheet_name in BUILDING_SHEETS else 1.0
        neg = analyse_sheet(sheet_name, df, conversion_factor=conv)
        if not neg.empty:
            first = neg.iloc[0]
            print(
                f"{sheet_name}: {len(neg)} negative deltas "
                f"(first at {first['timestamp']} "
                f"delta={first['delta']:.3f})"
            )
            all_neg.append(neg)
        else:
            print(f"{sheet_name}: 0 negative deltas")

    if not all_neg:
        print("No negative deltas found in any sheet.")
        return

    combined = pd.concat(all_neg, ignore_index=True)
    out_path = Path(args.output_csv).resolve()
    combined.to_csv(out_path, index=False)
    print(f"\nWrote {len(combined)} negative-delta rows to {out_path}")
    print("Columns:")
    print("  sheet, original_row, timestamp, prev_timestamp, prev_cumulative, cumulative, delta")


if __name__ == "__main__":
    main()

