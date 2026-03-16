#!/usr/bin/env python3
"""Inspect Excel sheet columns and first/last rows for Summenzähler and PV to verify we read correct columns."""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

excel_path = Path(__file__).resolve().parent.parent.parent / "document" / "Messdaten_Nürnberg_2024-2026.xlsx"
xl = pd.ExcelFile(excel_path, engine="openpyxl")

for name in ["Summenzähler", "PV-Zähler"]:
    if name not in xl.sheet_names:
        continue
    df = xl.parse(name)
    print(f"=== {name} ===")
    print("Columns:", list(df.columns))
    print("Dtypes:", df.dtypes.to_dict())
    print("First 5 rows:")
    print(df.head().to_string())
    print("Last 5 rows:")
    print(df.tail().to_string())
    print("Sample around row 400 (if exists):")
    if len(df) >= 400:
        print(df.iloc[398:403].to_string())
    print()
