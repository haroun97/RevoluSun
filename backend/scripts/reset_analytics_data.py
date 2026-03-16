#!/usr/bin/env python3
"""Truncate all analytics tables so the next backend startup will re-import DATA_FILE_PATH."""
import os
import sys

# Run from backend/ so app is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text

from app.db.session import engine

# Child tables first, then import_batches (FK references)
TABLES = (
    "raw_meter_readings",
    "normalized_meter_readings",
    "daily_meter_consumption",
    "daily_energy_sharing",
    "data_quality_issues",
    "import_batches",
)


def main() -> None:
    with engine.connect() as conn:
        conn.execute(
            text("TRUNCATE TABLE " + ", ".join(TABLES) + " RESTART IDENTITY CASCADE;")
        )
        conn.commit()
    print("Analytics tables truncated. Restart backend to re-import DATA_FILE_PATH.")


if __name__ == "__main__":
    main()
