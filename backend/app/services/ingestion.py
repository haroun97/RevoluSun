"""
Stage 1: Read the Excel file and write raw meter readings into the database.

We open each sheet, detect which meter type it is (tenant, building total, or PV),
find the timestamp and value columns, and insert one RawMeterReading per row.
The building-level meter uses a conversion factor (50) from the README; others use 1.0.
"""
import re
from datetime import datetime
from pathlib import Path

import pandas as pd
from sqlalchemy.orm import Session

from app.models import ImportBatch, RawMeterReading

# Building-level meter conversion factor per README (Summenzähler)
BUILDING_CONVERSION_FACTOR = 50.0
DEFAULT_CONVERSION_FACTOR = 1.0

# How we recognize sheet names: tenant = "Kunde N", building = Summenzähler/Summe/..., PV = PV/...
TENANT_SHEET_PATTERN = re.compile(r"^Kunde\s*(\d+)$", re.IGNORECASE)
BUILDING_SHEET_NAMES = ("Summenzähler", "Summe", "Building", "building_total")
PV_SHEET_NAMES = ("PV", "pv", "Photovoltaik", "Solar")

# Possible column names for timestamp and cumulative value (Excel may use German or English)
TIMESTAMP_COLS = ("timestamp", "Timestamp", "Zeit", "Datum", "Date", "time", "datetime")
VALUE_COLS = ("value", "Value", "Wert", "Reading", "raw_value", "kwh", "cumulative")


def _detect_timestamp_column(df: pd.DataFrame) -> str | None:
    """Find the column that holds the reading time (by known names or keywords)."""
    for c in TIMESTAMP_COLS:
        if c in df.columns:
            return c
    for c in df.columns:
        if "date" in c.lower() or "zeit" in c.lower() or "time" in c.lower():
            return c
    return None


def _detect_value_column(df: pd.DataFrame) -> str | None:
    """Find the column that holds the cumulative meter value (by name or first numeric column)."""
    for c in VALUE_COLS:
        if c in df.columns:
            return c
    for c in df.columns:
        if "value" in c.lower() or "wert" in c.lower() or "kwh" in c.lower() or "reading" in c.lower():
            return c
    # Fallback: use the first numeric column
    for c in df.columns:
        if pd.api.types.is_numeric_dtype(df[c]):
            return c
    return None


def _parse_timestamp(ts: object) -> datetime | None:
    """Convert a cell value to a datetime; return None if missing or invalid."""
    if ts is None or (isinstance(ts, float) and pd.isna(ts)):
        return None
    if isinstance(ts, datetime):
        return ts
    if isinstance(ts, pd.Timestamp):
        return ts.to_pydatetime()
    try:
        return pd.to_datetime(ts).to_pydatetime()
    except Exception:
        return None


def _parse_value(v: object) -> float | None:
    """Convert a cell value to float; return None if missing or not a number."""
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def load_excel_sheets(path: Path) -> dict[str, pd.DataFrame]:
    """Load every sheet from the Excel file; returns a dict sheet_name -> DataFrame."""
    xl = pd.ExcelFile(path, engine="openpyxl")
    return {name: xl.parse(name) for name in xl.sheet_names}


def classify_sheet(name: str) -> tuple[str, str | None] | None:
    """Decide if this sheet is tenant, building_total, or pv; return (meter_type, tenant_id or None). Skip unknown sheets."""
    name = name.strip()
    m = TENANT_SHEET_PATTERN.match(name)
    if m:
        # Normalize so "Kunde01" and "Kunde1" both become "Kunde1" (prevents duplicate tenant_ids)
        num = int(m.group(1))
        return ("tenant", f"Kunde{num}")
    if any(n in name for n in BUILDING_SHEET_NAMES):
        return ("building_total", None)
    if any(n in name for n in PV_SHEET_NAMES):
        return ("pv", None)
    return None


def ingest_sheet(
    session: Session,
    import_batch_id: int,
    sheet_name: str,
    meter_type: str,
    tenant_id: str | None,
    df: pd.DataFrame,
) -> int:
    """Read rows from the DataFrame and insert RawMeterReading rows. Returns how many were inserted."""
    ts_col = _detect_timestamp_column(df)
    val_col = _detect_value_column(df)
    if not ts_col or not val_col:
        return 0

    conversion = BUILDING_CONVERSION_FACTOR if meter_type == "building_total" else DEFAULT_CONVERSION_FACTOR
    meter_id = tenant_id or meter_type

    count = 0
    for _, row in df.iterrows():
        ts = _parse_timestamp(row.get(ts_col))
        val = _parse_value(row.get(val_col))
        if ts is None or val is None:
            continue
        rec = RawMeterReading(
            import_batch_id=import_batch_id,
            source_sheet=sheet_name,
            meter_id=meter_id,
            meter_type=meter_type,
            tenant_id=tenant_id,
            serial_number=None,
            timestamp=ts,
            raw_value=val,
            conversion_factor=conversion,
            obis_code=None,
        )
        session.add(rec)
        count += 1
    return count


def run_ingestion(session: Session, file_path: Path) -> ImportBatch:
    """
    Load the Excel file, create one ImportBatch, and insert all raw readings.

    Only sheets we recognize (tenant, building, PV) are imported. Returns the
    new ImportBatch. Caller must commit the session.
    """
    batch = ImportBatch(
        filename=file_path.name,
        status="importing",
        notes=None,
    )
    session.add(batch)
    session.flush()

    sheets = load_excel_sheets(file_path)
    total_rows = 0
    for sheet_name, df in sheets.items():
        if df.empty or len(df) == 0:
            continue
        classified = classify_sheet(sheet_name)
        if not classified:
            continue
        meter_type, tenant_id = classified
        n = ingest_sheet(session, batch.id, sheet_name, meter_type, tenant_id, df)
        total_rows += n

    batch.status = "completed"
    batch.notes = f"Imported {total_rows} raw rows from {len(sheets)} sheets"
    session.add(batch)
    return batch
