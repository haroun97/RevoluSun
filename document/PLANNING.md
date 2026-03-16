# RevoluSUN Energy Sharing Dashboard — Implementation Plan

This document tracks progress of the MVP implementation. It maps README requirements to the codebase and records completion status.

---

## 1. Repo analysis & implementation mapping

### 1.1 Current state

| Area | Status | Notes |
|------|--------|--------|
| Backend | ✅ Done | FastAPI, models, pipeline, API, tests |
| Frontend | ✅ Done | React + TypeScript + Vite; dashboard uses real API |
| Types | Present | `frontend/src/types/energy.ts` — KpiData, TimeSeriesPoint, TenantData, etc. |
| Excel dataset | ✅ Ready | `document/Messdaten_Nürnberg_2024-2026.xlsx`; `backend/.env` / `.env.example` use `DATA_FILE_PATH=../document/Messdaten_Nürnberg_2024-2026.xlsx` |

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
- `backend/tests/test_conversion_factor.py`, `test_delta_calculation.py`, `test_energy_sharing.py`, `test_missing_tenants.py`

**Frontend (updated):**
- `frontend/src/api/client.ts`, `frontend/src/api/energyApi.ts` (new)
- `frontend/src/pages/DashboardPage.tsx` (fetches from API + loading/error states)

**Data & config:**
- `document/Messdaten_Nürnberg_2024-2026.xlsx` — Nürnberg measurement data (Kunde1–Kunde13, Summenzähler, PV-Zähler)
- `backend/.env.example` — includes `DATA_FILE_PATH=../document/Messdaten_Nürnberg_2024-2026.xlsx`

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
| **4** | Backend running; pipeline imported Nürnberg Excel |
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

---

## 9. Improvement plan: date range, filters & chart clarity

**Status:** Implemented (see below). Plan was executed after permission.

This section documents the full improvement plan to fix unclear energy charts, missing date selection, and misleading KPI labels. Tasks are ordered by dependency; the **first task that must be done** is **9.1 (Backend: date params and filtering)**.

### 9.1 Context: what’s wrong today

| Issue | Root cause |
|--------|------------|
| Energy charts show very dense, unclear data | Full 1.5 years of daily data (Aug 2024–Mar 2026) with no date filter; no aggregation. |
| “Which date is selected by default?” | No date is selected; FilterBar shows hardcoded “Jun 1 – Aug 29, 2024” that does nothing. |
| User cannot select a date/range to filter data | No date/range picker, no date state, no date query params on any API. |
| Daily / Weekly / Monthly has no effect | Frontend always sends `granularity=daily`; backend accepts but never uses granularity (always returns daily). |
| KPI labels say “90-day” but numbers are full-period | Backend summary aggregates over all dates; labels are misleading. |
| Reset button does nothing | No handler; date/granularity state not reset. |

### 9.2 Goal

- One **global date range** that drives all charts and KPIs.
- User can **select** that range (presets or picker); “default” is explicit (e.g. last 90 days or Jun–Aug 2024).
- **Granularity** actually changes the data: weekly/monthly aggregation for timeseries when range is wide.
- Charts show **meaningful, readable** data; KPI labels match the selected period.

### 9.3 Task list (order and dependencies)

**Do first (no dependency on other tasks in this plan):**

- [x] **9.1 — Backend: add date params and filtering**  
  - Add optional query params `start_date` and `end_date` (ISO date strings) to:  
    `GET /api/summary`, `GET /api/timeseries/building`, `GET /api/tenants/comparison`, `GET /api/tenants/timeseries/{tenant_id}`, `GET /api/sharing`.  
  - In `app/services/analytics.py` (and any route logic): filter all queries by `date >= start_date` and `date <= end_date` when params are provided.  
  - If omitted, keep current behaviour (full range).  
  - **Files:** `backend/app/api/routes.py`, `backend/app/services/analytics.py`.  
  - **Must be done first** so the frontend has something to call with a date range.

**Depends on 9.1:**

- [x] **9.2 — Backend: implement granularity for timeseries**  
  - In `building_timeseries()` (and, if exposed, any tenant date-level timeseries): use the existing `granularity` argument.  
  - For `weekly`: aggregate daily rows by week (e.g. week start Monday or Sunday); return one point per week (sum of building_consumption, pv_generation, self_consumed, surplus).  
  - For `monthly`: aggregate by month; return one point per month.  
  - Keep `daily` as current behaviour (one point per day).  
  - **Files:** `backend/app/services/analytics.py`.  
  - **Depends on:** 9.1 (so that filtered daily data is then aggregated by week/month).

- [x] **9.3 — Frontend: global date range state and API params**  
  - Add state for the selected date range, e.g. `dateRange: { start: string, end: string }` (ISO dates) in `DashboardPage.tsx` (or a small context/store).  
  - Default range: e.g. last 90 days from the latest date in the dataset, or a fixed window like 2024-06-01 to 2024-08-29.  
  - Pass `start_date` and `end_date` into every API call that supports them: `fetchSummary`, `fetchBuildingTimeseries`, `fetchTenants` (and underlying comparison + tenant timeseries), `fetchSharing`.  
  - Update `energyApi.ts`: add `start_date`/`end_date` to request URLs (e.g. `?start_date=...&end_date=...`).  
  - **Files:** `frontend/src/pages/DashboardPage.tsx`, `frontend/src/api/energyApi.ts`.  
  - **Depends on:** 9.1 (backend must accept and apply the params).

- [x] **9.4 — Frontend: FilterBar controls range and granularity**  
  - Replace the hardcoded “Jun 1 – Aug 29, 2024” with a real control: either a date range picker (e.g. calendar popover with start/end) or presets (“Last 30 days”, “Last 90 days”, “Jun – Aug 2024”, “Full period”) that set the global range.  
  - Wire FilterBar to the global date range state (and granularity state).  
  - Implement **Reset**: set range and granularity back to the chosen default (e.g. last 90 days, daily).  
  - **Files:** `frontend/src/components/filters/FilterBar.tsx`, `frontend/src/pages/DashboardPage.tsx`.  
  - **Depends on:** 9.3 (state and wiring must exist).

- [x] **9.5 — Frontend: pass granularity to building timeseries**  
  - In `energyApi.ts`, pass the selected `granularity` into the building timeseries request: `GET /api/timeseries/building?granularity=weekly` (or daily/monthly) instead of always `daily`.  
  - Ensure `DashboardPage` uses the same granularity state for this call.  
  - **Files:** `frontend/src/api/energyApi.ts`, `frontend/src/pages/DashboardPage.tsx`.  
  - **Depends on:** 9.2 (backend must implement granularity).

- [x] **9.6 — Frontend: KPI labels match selected period**  
  - Change KPI card labels so they reflect the selected range: e.g. “Total demand (selected period)” or “90-day demand” only when the selected range is 90 days.  
  - **Files:** `frontend/src/pages/DashboardPage.tsx` (and any KPI/subtitle strings).  
  - **Depends on:** 9.3 (range is available in the UI).

**Optional / later:**

- [ ] **9.7 — Tenant trend chart: range and sampling** (skipped; tenant data already filtered by selected range)  
  - Ensure tenant trends use the same global date range (already true if tenants are fetched with date params from 9.3).  
  - Optionally replace “every 3 days” sampling with proper aggregation (e.g. one point per week when range is long) so the trend chart is readable.  
  - **Files:** `frontend/src/components/charts/TenantTrendChart.tsx`, backend if tenant timeseries is aggregated by week/month.  
  - **Depends on:** 9.3, optionally 9.2 if backend exposes weekly/monthly tenant series.

### 9.4 Execution order summary

| Order | Task ID | Task | Blocked by |
|-------|---------|------|-------------|
| **1** | **9.1** | Backend: add date params and filtering | — **(do this first)** |
| 2 | 9.2 | Backend: implement granularity for timeseries | 9.1 |
| 3 | 9.3 | Frontend: global date range state and API params | 9.1 |
| 4 | 9.4 | Frontend: FilterBar controls range and granularity | 9.3 |
| 5 | 9.5 | Frontend: pass granularity to building timeseries | 9.2 |
| 6 | 9.6 | Frontend: KPI labels match selected period | 9.3 |
| 7 | 9.7 | (Optional) Tenant trend chart range/sampling | 9.3, optionally 9.2 |

### 9.5 Suggested default for clarity

- **Default date range:** e.g. last 90 days from the latest date in the data, or a fixed 3‑month window (e.g. Jun 1 – Aug 29, 2024).  
- **Default granularity:** Daily for a 90-day window; consider Weekly or Monthly when the user selects “Full period” so the energy chart stays readable.

---

## 10. Missing Kunde handling (e.g. Kunde7)

**Status:** Implemented.

The case study dataset defines tenant meters Kunde1–Kunde13; **Kunde7 is not present** in the workbook. Treating missing tenants as zero would distort analytics. This section documents the solution: treat expected-but-absent tenants as "not in dataset" and expose that in the API and UI.

### 10.1 Goal

- Do not assume zero consumption for missing tenants.
- Exclude missing tenants from tenant-level analytics (already true: only tenants with data appear).
- Expose which expected tenants have no data (e.g. Kunde7) so users understand coverage.
- Document the policy in the app (one sentence).

### 10.2 Implemented tasks

- [x] **10.1 — Expected tenants constant**  
  - Define `EXPECTED_TENANT_IDS` (Kunde1–Kunde13) in one place.  
  - **File:** `backend/app/core/constants.py`.

- [x] **10.2 — Compute missing tenants**  
  - In `quality_from_db`: get distinct tenant_ids present in `daily_meter_consumption` for the batch; missing = expected − present.  
  - Helper `get_missing_tenant_ids(present)` in constants for testability.  
  - **Files:** `backend/app/core/constants.py`, `backend/app/services/analytics.py`.

- [x] **10.3 — API: expose missing_tenants**  
  - Add `missing_tenants: list[str]` to `GET /api/quality` response.  
  - **Files:** `backend/app/schemas/responses.py`, `backend/app/api/routes.py`.

- [x] **10.4 — Frontend: show missing tenants and doc sentence**  
  - Data Quality section: when `missingTenants.length > 0`, show a note and list (e.g. "Tenants not in dataset: Kunde7").  
  - Footer: one sentence that tenants not in the dataset are excluded; zero is not assumed.  
  - **Files:** `frontend/src/components/charts/DataQualityView.tsx`, `frontend/src/components/layout/Footer.tsx`, `frontend/src/api/energyApi.ts`, `frontend/src/pages/DashboardPage.tsx`.

- [x] **10.5 — Tests**  
  - Unit tests for `EXPECTED_TENANT_IDS` and `get_missing_tenant_ids()` (all present, none present, Kunde7 missing, ignore None).  
  - **File:** `backend/tests/test_missing_tenants.py`.

### 10.3 Files touched

| Area | File |
|------|------|
| Backend | `backend/app/core/constants.py` (new: EXPECTED_TENANT_IDS, get_missing_tenant_ids) |
| Backend | `backend/app/services/analytics.py` (quality_from_db: compute and return missing_tenants) |
| Backend | `backend/app/schemas/responses.py` (QualityResponse.missing_tenants) |
| Backend | `backend/app/api/routes.py` (pass missing_tenants in quality response) |
| Backend | `backend/tests/test_missing_tenants.py` (new) |
| Frontend | `frontend/src/api/energyApi.ts` (QualityDto.missing_tenants, fetchQuality returns missingTenants) |
| Frontend | `frontend/src/pages/DashboardPage.tsx` (pass missingTenants to DataQualityView) |
| Frontend | `frontend/src/components/charts/DataQualityView.tsx` (props missingTenants; show note + list) |
| Frontend | `frontend/src/components/layout/Footer.tsx` (doc sentence) |

---

## 11. Re-import data so current data reflects pipeline fixes (Option A)

**Status:** Documented; no code change (uses existing script).

After pipeline logic changes (e.g. negative-delta handling), existing DB data was produced by the old logic. To re-import so data reflects the fix:

1. From `backend/`: run `python scripts/reset_analytics_data.py` (truncates all analytics tables).
2. Restart the backend; on startup the pipeline runs again for the file in `DATA_FILE_PATH`.

See **README** → "Re-import data (Option A — full pipeline reset)" for the full steps.
