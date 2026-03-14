# Mock energy data

- **`mock_energy_data.xlsx`** – Mock Excel dataset for the RevoluSUN Energy Sharing case study and backend ingestion.

## Structure (matches case study PDF + backend)

| Sheet          | Description |
|----------------|-------------|
| Kunde1–Kunde6  | Tenant consumption meters (cumulative kWh). Columns: Seriennummer, Zeit, Wert. |
| Kunde8–Kunde13 | Same (Kunde7 omitted per case study). Kunde13 includes OBIS-Code. |
| Summenzähler   | Building total. **Wert** = raw dial reading; actual kWh = Wert × 50. Columns: Zeit, Wert. |
| PV             | PV generation (cumulative kWh). Columns: Zeit, Wert. |

- **Zeit**: timestamp (one reading per day).
- **Wert**: cumulative meter reading (kWh for tenants and PV; raw value for Summenzähler).
- Coverage differs by tenant (some start later or end earlier); a few days are missing for some meters.

## Regenerating

From the project root:

```bash
backend/.venv/bin/python scripts/generate_mock_energy_excel.py
```

Output: `data/mock_energy_data.xlsx`. Optional: pass a path as first argument.

## Using with the backend

Set in `backend/.env`:

```env
DATA_FILE_PATH=/path/to/project/data/mock_energy_data.xlsx
```

On startup, the backend will import this file once (idempotent by filename).
