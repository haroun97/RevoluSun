# Energy data

The backend loads measurement data from a single Excel file configured via `DATA_FILE_PATH` in `backend/.env`.

## Dataset (Nürnberg)

- **File:** `document/Messdaten_Nürnberg_2024-2026.xlsx` (anonymized measurement data from a multi-family house in Nuremberg).
- **Sheets:** Kunde1–Kunde13 (tenant meters), Summenzähler (building total, conversion factor 50), PV-Zähler (PV generation).
- **Columns:** `timestamp`, `value` (and optional `measuring_point__serial`, `obis_code`, `measuring_point__conversion_factor`).
- **Date range:** 2024-08-16 to 2026-03-06.

## Using with the backend

Set in `backend/.env`:

```env
DATA_FILE_PATH=../document/Messdaten_Nürnberg_2024-2026.xlsx
```

On startup, the backend imports this file once per filename (idempotent by filename).
