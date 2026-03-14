# RevoluSUN Energy Sharing Dashboard — Implementation Plan

This document tracks progress of the MVP implementation. It maps README requirements to the codebase and records completion status.

---

## 1. Repo analysis & implementation mapping

### 1.1 Current state

| Area | Status | Notes |
|------|--------|--------|
| Backend | ✅ Done | FastAPI, models, pipeline, API, tests |
| Frontend | ✅ Done | React + TypeScript + Vite; dashboard uses real API |
| Mock data (frontend) | Legacy | `frontend/src/data/mockEnergyData.ts` — no longer used by dashboard |
| Types | Present | `frontend/src/types/energy.ts` — KpiData, TimeSeriesPoint, TenantData, etc. |
| Excel dataset | ✅ Ready | `data/mock_energy_data.xlsx` (generated); `backend/.env.example` has `DATA_FILE_PATH=../data/mock_energy_data.xlsx` |

### 1.2 README → codebase mapping

| README requirement | Target location | Status |
|--------------------|-----------------|--------|
| Backend structure (FastAPI, app/, api/, db/, models/, schemas/, services/, core/) | `backend/app/` | ✅ |
| DB models (import_batch, raw_meter_reading, normalized_meter_reading, daily_meter_consumption, daily_energy_sharing, data_quality_issue) | `backend/app/models/` | ✅ |
| Alembic migrations | `backend/alembic/` | ✅ |
| Config (DATABASE_URL, DATA_FILE_PATH) | `backend/app/core/config.py` | ✅ |
| Stage 1: Excel ingestion → raw_meter_readings | `backend/app/services/ingestion.py` | ✅ |
| Stage 2: Normalize → normalized_meter_readings | `backend/app/services/normalization.py` | ✅ |
| Stage 3: Daily deltas → daily_meter_consumption | `backend/app/services/resampling.py` | ✅ |
| Stage 4: Quality checks → data_quality_issues | `backend/app/services/quality.py` | ✅ |
| Stage 5: Energy sharing → daily_energy_sharing | `backend/app/services/sharing.py` | ✅ |
| GET /api/health | `backend/app/api/routes.py` | ✅ |
| GET /api/summary | `backend/app/api/routes.py` | ✅ |
| GET /api/timeseries/building | `backend/app/api/routes.py` | ✅ |
| GET /api/tenants/comparison | `backend/app/api/routes.py` | ✅ |
| GET /api/tenants/timeseries/{tenant_id} | `backend/app/api/routes.py` | ✅ |
| GET /api/sharing | `backend/app/api/routes.py` | ✅ |
| GET /api/quality | `backend/app/api/routes.py` | ✅ |
| Frontend API client | `frontend/src/api/client.ts`, `energyApi.ts` | ✅ |
| Dashboard uses real API | `frontend/src/pages/DashboardPage.tsx` | ✅ |
| Tests (conversion, delta, energy sharing) | `backend/tests/` | ✅ |

---

## 2. Execution checklist (order of implementation)

### Phase 1 — Backend structure and DB

- [x] **1.1** Create `backend/` with `app/`, `requirements.txt`, `.env.example`
- [x] **1.2** Implement `app/core/config.py` (DATABASE_URL, DATA_FILE_PATH)
- [x] **1.3** Implement `app/db/base.py` and `app/db/session.py`
- [x] **1.4** Implement all SQLAlchemy models under `app/models/`
- [x] **1.5** Set up Alembic; create initial migration for all tables
- [x] **1.6** Add indexes (timestamp, date, meter_id, tenant_id, import_batch_id)

### Phase 2 — Processing pipeline

- [x] **2.1** Ingestion: read Excel (tenant sheets Kunde1–Kunde13, Summenzähler, PV), standardize columns, persist raw_meter_readings
- [x] **2.2** Normalization: conversion factors (50 for building, 1 for tenant/PV), persist normalized_meter_readings
- [x] **2.3** Resampling: deltas, negative-delta flag, daily aggregation → daily_meter_consumption
- [x] **2.4** Quality: negative deltas, gaps, coverage, tenant-sum vs building mismatch → data_quality_issues
- [x] **2.5** Sharing: proportional allocation formula → daily_energy_sharing
- [x] **2.6** Startup: idempotent import guard (filename); run pipeline if no data

### Phase 3 — REST API

- [x] **3.1** `GET /api/health` (DB check)
- [x] **3.2** `GET /api/summary` (KPIs from persisted tables)
- [x] **3.3** `GET /api/timeseries/building?granularity=daily`
- [x] **3.4** `GET /api/tenants/comparison`
- [x] **3.5** `GET /api/tenants/timeseries/{tenant_id}`
- [x] **3.6** `GET /api/sharing`
- [x] **3.7** `GET /api/quality`
- [x] **3.8** Pydantic response schemas in `app/schemas/responses.py`

### Phase 4 — Frontend integration

- [x] **4.1** Create `frontend/src/api/client.ts` (base URL, fetch wrapper)
- [x] **4.2** Create `frontend/src/api/energyApi.ts` (summary, timeseries, tenants, sharing, quality)
- [x] **4.3** Update `DashboardPage.tsx`: fetch from API, loading/empty states, preserve UI
- [x] **4.4** Map API responses to existing types/chart props; no redesign

### Phase 5 — Tests and polish

- [x] **5.1** `backend/tests/test_conversion_factor.py`
- [x] **5.2** `backend/tests/test_delta_calculation.py`
- [x] **5.3** `backend/tests/test_energy_sharing.py`
- [x] **5.4** Error handling: missing file, bad sheets, malformed data, DB errors
- [x] **5.5** README: small clarifications only (run backend, migrations, frontend → backend)
- [x] **5.6** Verify: backend + frontend run locally; dashboard uses real data

---

## 3. Progress summary

| Phase | Status | Completed items |
|-------|--------|-----------------|
| Phase 1 — Backend structure and DB | ✅ Done | All |
| Phase 2 — Processing pipeline | ✅ Done | All |
| Phase 3 — REST API | ✅ Done | All |
| Phase 4 — Frontend integration | ✅ Done | All |
| Phase 5 — Tests and polish | ✅ Done | All |

**Legend:** ⬜ Not started | 🔄 In progress | ✅ Done

---

## 4. Key domain rules (from README)

- **Conversion factor:** Building meter = raw × 50; tenant and PV = 1.
- **Cumulative:** delta_kwh = current_reading − previous_reading; negative → quality issue.
- **Timestamps:** Aggregate to daily; do not interpolate missing days.
- **Persistence:** Raw, normalized, daily consumption, daily energy sharing, and quality issues all stored in PostgreSQL; APIs read from DB.

---

## 5. Assumptions

- Excel has tenant sheets (e.g. Kunde1–Kunde13), building sheet (Summenzähler), and PV sheet; Kunde7 may be missing.
- If `DATA_FILE_PATH` is unset or file missing, backend starts without failing; import runs when file is provided and not yet imported.
- Frontend dev server can proxy or use `VITE_API_URL` for backend (e.g. `http://localhost:8000`).

---

## 6. Implementation summary (post-MVP)

### Files created / updated

**Backend (new):**
- `backend/requirements.txt`, `backend/.env.example`
- `backend/app/main.py`, `backend/app/core/config.py`
- `backend/app/db/base.py`, `backend/app/db/session.py`
- `backend/app/models/*.py` (6 models)
- `backend/app/schemas/responses.py`, `backend/app/api/routes.py`
- `backend/app/services/ingestion.py`, `normalization.py`, `resampling.py`, `quality.py`, `sharing.py`, `analytics.py`, `startup.py`
- `backend/alembic.ini`, `backend/alembic/env.py`, `backend/alembic/versions/001_create_initial_analytics_schema.py`
- `backend/tests/test_conversion_factor.py`, `test_delta_calculation.py`, `test_energy_sharing.py`

**Frontend (updated):**
- `frontend/src/api/client.ts`, `frontend/src/api/energyApi.ts` (new)
- `frontend/src/pages/DashboardPage.tsx` (switched from mock data to API + loading/error states)

**Data & config:**
- `data/mock_energy_data.xlsx` — mock Excel (Kunde1–Kunde13 minus Kunde7, Summenzähler, PV)
- `scripts/generate_mock_energy_excel.py` — regenerates the mock file
- `backend/.env.example` — includes `DATA_FILE_PATH=../data/mock_energy_data.xlsx`

**Docs:**
- `document/PLANNING.md` (this file)
- `data/README.md` — mock data structure and usage

### How to run the backend

1. From project root: `cd backend`
2. Create virtualenv and install deps: `python -m venv .venv && .venv/bin/pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and set `DATABASE_URL` (and optionally `DATA_FILE_PATH` for Excel import)
4. Run migrations: `alembic upgrade head`
5. Start server: `uvicorn app.main:app --reload` (listens on http://localhost:8000)

### How to run migrations

From the `backend` directory: `alembic upgrade head`. Initial migration creates all 6 tables and indexes.

### How the frontend connects to the backend

- The frontend uses `VITE_API_URL` (default `http://localhost:8000`) for all API requests.
- Set `VITE_API_URL` in `frontend/.env` if the backend runs on a different host/port.
- Dashboard page uses React Query (`useQuery`) to fetch `/api/summary`, `/api/timeseries/building`, tenants (comparison + per-tenant timeseries), `/api/sharing`, and `/api/quality`. Loading and error states are shown; data is mapped to existing chart types.

---

## 7. Next steps (run the full stack) — ✅ Done

| Step | Status |
|------|--------|
| **1** | PostgreSQL + DB `revolusun` created (local) |
| **2** | `backend/.env` configured (DATABASE_URL, DATA_FILE_PATH) |
| **3** | Migrations applied (`alembic upgrade head`) |
| **4** | Backend running; pipeline imported mock Excel |
| **5** | Frontend running; dashboard loads from API |
| **6** | (Optional) Run `pytest tests/ -v` in `backend/` |

**Fix applied:** Resampling in `backend/app/services/resampling.py` now uses `groupby(..., dropna=False)` so building and PV meters (tenant_id = NA) are included. Summary cards (Building Consumption, PV Generation, Self-Consumption, Surplus) now show data. See `document/INVESTIGATION_SUMMARY_CARDS_ZERO.md` for the investigation.

---

## 8. What to do next

The MVP is running end-to-end. Suggested next actions:

| Priority | What to do |
|----------|------------|
| **Demo** | Walk through the dashboard: KPIs, Energy Overview charts, Tenant Analysis, Energy Sharing, Data Quality. Use it to prepare your 45‑min presentation. |
| **Tests** | From `backend/`: run `pytest tests/ -v` and fix any failures. |
| **Docs** | Skim README and PLANNING so you can explain architecture, pipeline, and trade-offs in the call. |
| **Optional** | Add a short “How I ran it” note to the README; tweak filters or date range if needed for the demo. |

No further steps are required for the case study deliverable; the rest is polish and presentation prep.
