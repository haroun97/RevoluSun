"""Stage 1: Excel ingestion into raw_meter_readings."""
import re
from datetime import datetime
from pathlib import Path

import pandas as pd
from sqlalchemy.orm import Session

from app.models import ImportBatch, RawMeterReading

# Building-level meter conversion factor per README
BUILDING_CONVERSION_FACTOR = 50.0
DEFAULT_CONVERSION_FACTOR = 1.0

# Sheet name patterns
TENANT_SHEET_PATTERN = re.compile(r"^Kunde\s*(\d+)$", re.IGNORECASE)
BUILDING_SHEET_NAMES = ("Summenzähler", "Summe", "Building", "building_total")
PV_SHEET_NAMES = ("PV", "pv", "Photovoltaik", "Solar")

# Column name variants for timestamp and value
TIMESTAMP_COLS = ("timestamp", "Timestamp", "Zeit", "Datum", "Date", "time", "datetime")
VALUE_COLS = ("value", "Value", "Wert", "Reading", "raw_value", "kwh", "cumulative")


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
    # Fallback: first numeric column that is not an index
    for c in df.columns:
        if pd.api.types.is_numeric_dtype(df[c]):
            return c
    return None


def _parse_timestamp(ts: object) -> datetime | None:
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
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def load_excel_sheets(path: Path) -> dict[str, pd.DataFrame]:
    """Load all sheets from Excel. Keys = sheet names."""
    xl = pd.ExcelFile(path, engine="openpyxl")
    return {name: xl.parse(name) for name in xl.sheet_names}


def classify_sheet(name: str) -> tuple[str, str | None] | None:
    """Return (meter_type, tenant_id_or_None) or None if sheet is ignored."""
    name = name.strip()
    m = TENANT_SHEET_PATTERN.match(name)
    if m:
        return ("tenant", f"Kunde{m.group(1)}")
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
    """Parse DataFrame and insert raw readings. Returns count inserted."""
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
    """Load Excel, create import_batch, persist raw rows. Raises on fatal errors."""
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
