# Energy Sharing Dashboard

Energy Sharing Dashboard is a small **MVP analytics web application**
built to analyze electricity consumption and photovoltaic (PV)
production in a **multi-tenant residential building**.

The goal of the project is to process **cumulative electricity meter
readings** and transform them into meaningful consumption metrics that
can be explored through a **simple interactive dashboard**.

The application demonstrates how energy data from multiple meters ---
including **tenant meters, a building-level meter, and a PV production
meter** --- can be processed and visualized to provide insights into:

-   building electricity consumption
-   photovoltaic production
-   tenant usage patterns
-   estimated PV self-consumption and surplus

This MVP was implemented within a **4--6 hour time constraint** as part
of an engineering case study, prioritizing **clarity of architecture,
correctness of data processing, and pragmatic engineering trade-offs**.

------------------------------------------------------------------------

# Setup

The project consists of two parts:

-   **Backend API** built with FastAPI
-   **Frontend dashboard** built with React and TypeScript

The frontend communicates with the backend through a **REST API**.

------------------------------------------------------------------------

## Backend

The backend loads and processes the Excel dataset and serves results via
REST. Pipeline and design are described in [Design & Architecture
Overview](#design--architecture-overview).

### Install dependencies

From the `backend/` directory:

```bash
pip install -r requirements.txt
```

### Start the FastAPI server

From the `backend/` directory:

```bash
cd backend
uvicorn app.main:app --reload
```

The backend will start a local development server (default: http://localhost:8000) and expose API endpoints used by the frontend dashboard. The frontend expects the API at `http://localhost:8000` unless you set `VITE_API_URL` in the frontend environment.

### Local Development Setup (PostgreSQL)

When using the database persistence layer:

**Requirements:** PostgreSQL 15+ recommended, Python 3.10+, Node.js 18+

**Environment variables** — example backend `.env`:

```env
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/revolusun
```

**Run PostgreSQL locally**

Install and start PostgreSQL on your machine, then create the database and user to match the URL above (or adjust `DATABASE_URL` to your setup).

-   **Linux (Debian/Ubuntu):** `sudo apt install postgresql postgresql-contrib`, then `sudo -u postgres createuser -s postgres` (or create a dedicated user/db) and `createdb revolusun`.
-   **macOS:** `brew install postgresql@15` and `brew services start postgresql@15`, then `createdb revolusun`.
-   **Windows:** install from [postgresql.org](https://www.postgresql.org/download/windows/) and create database `revolusun` (e.g. via pgAdmin or `psql`).

Ensure the server is listening on `localhost:5432` and that the user/password in `.env` match your local Postgres configuration.


**Run database migrations** (from the `backend/` directory):

```bash
cd backend
alembic upgrade head
```

**Re-import data (full pipeline reset)**

To clear existing analytics data and re-run the full import pipeline (e.g. so data reflects the latest processing logic, such as negative-delta handling):

1. From the `backend/` directory, run:
   ```bash
   python scripts/reset_analytics_data.py
   ```
   This truncates all analytics tables (`raw_meter_readings`, `normalized_meter_readings`, `daily_meter_consumption`, `daily_energy_sharing`, `data_quality_issues`, `import_batches`).

2. Restart the FastAPI server (stop and start `uvicorn app.main:app --reload`).

On startup, the backend sees no existing import for the file named in `DATA_FILE_PATH` and runs the full pipeline again (ingestion → normalization → resampling → quality → sharing). Ensure `DATA_FILE_PATH` in `.env` points to your Excel file (e.g. `../document/Messdaten_Nürnberg_2024-2026.xlsx`) before restarting.

------------------------------------------------------------------------

## Frontend

Run all frontend commands from the **`frontend/`** directory. The
dashboard fetches data from the backend API.

### Install dependencies

From the `frontend/` directory:

``` bash
npm install
```

### Start the development server

From the `frontend/` directory:

``` bash
npm run dev
```

------------------------------------------------------------------------

# Design & Architecture Overview

------------------------------------------------------------------------

## Approach Summary

Short overview of the problem, scope, and main decisions. Details follow
in the sections below.

**Problem.** Data is **cumulative meter readings** (running totals), so
consumption = difference between consecutive readings. The dataset mixes
tenant, building, and PV meters with irregular timestamps. Priority:
turn this into **clean daily consumption** and build a dashboard on top.
See [Problem Understanding](#problem-understanding) for dataset details.

**Scope.** Within a 4–6 hour time box we aimed for a **minimal
end-to-end app**: Excel → pipeline → database → REST API → frontend.
We left out login, real-time updates, and advanced analytics to deliver
a working app with meaningful charts. See [MVP Scope](#mvp-scope) for
in/out of scope.

**Decisions (details in later sections).**

-   **Staged pipeline:** Ingest → normalize → daily deltas → quality
    checks → PV allocation. One job per stage; see [Backend Processing
    with Database](#backend-processing-with-database).
-   **PostgreSQL for persistence:** Raw and derived data stored so we
    can re-run, compare, and inspect; see [Database & Persistence
    Strategy](#database--persistence-strategy) and [Database
    Schema](#database-schema).
-   **Backend: Python, FastAPI, Pandas** — Excel + time-series + REST;
    see [Technology Stack and Rationale](#technology-stack-and-rationale).
-   **Frontend: React, TypeScript, Recharts** — modular UI and quick
    charts; same section.
-   **PV allocation: proportional by demand** per day; simple and
    explainable (advanced allocation out of scope).
-   **Trade-offs:** No auth, no real-time, basic filters; focus on
    correct processing and useful visualizations.

------------------------------------------------------------------------

## Problem Understanding

The dataset is **Excel-based cumulative electricity meter readings**;
consumption is derived as the **difference (delta) between consecutive
readings** (see [Approach Summary](#approach-summary)).

Key characteristics:

-   several **tenant electricity meters**
-   a **building-level meter (Summenzähler)** with a **conversion factor
    of 50**
-   a **PV production meter**
-   **irregular timestamps**
-   **different measurement coverage periods for tenants**

Additional challenges:

-   timestamps that are not evenly spaced
-   tenants starting or stopping measurements at different times
-   ensuring that building-level consumption aligns with tenant usage
    and PV production

The pipeline therefore **cleans, normalizes, and aggregates to daily
consumption** before the dashboard can use it.

------------------------------------------------------------------------

## MVP Scope

The MVP focuses on building a minimal but functional **energy analytics
pipeline**.

### Implemented

-   Excel dataset ingestion
-   conversion of cumulative readings into interval consumption values
-   aggregation of consumption and production metrics
-   REST API for data retrieval
-   interactive dashboard visualizations
-   basic data quality indicators

### Out of Scope

Due to the **4--6 hour development constraint**, several features were
intentionally excluded:

-   authentication and authorization
-   real-time data processing
-   advanced PV allocation algorithms
-   sophisticated anomaly detection
-   complex UI filtering and controls

The focus was on demonstrating **core analytical capabilities rather
than a production-ready platform**.

------------------------------------------------------------------------

## Technology Stack and Rationale

The chosen technology stack prioritizes **fast development, clarity, and
strong support for data processing**. See the [Technology Decision Matrix](#technology-decision-matrix) below for alternatives considered.

### Backend

-   **Python**
-   **FastAPI**
-   **Pandas**

Python and Pandas provide excellent tools for transforming and analyzing
tabular energy datasets.

FastAPI provides a lightweight framework for exposing the processed data
via REST endpoints.

### Frontend

-   **React**
-   **TypeScript**
-   **Vite**
-   **Recharts**

React enables building modular UI components, while TypeScript improves
maintainability through static typing.

Vite provides fast development startup times, and Recharts allows rapid
implementation of dashboard charts.

------------------------------------------------------------------------

### Technology Decision Matrix

#### Backend Framework Comparison

| Option | Pros | Cons | Decision |
|--------|------|------|----------|
| **FastAPI** | Lightweight, fast API development, strong typing support, ideal for data services | Smaller ecosystem compared to Django | **Chosen** |
| Django | Mature framework, built-in ORM and admin tools | Heavy framework for a simple data processing API | Not chosen |
| Node.js (Express) | Flexible JavaScript ecosystem | Less convenient for data-heavy processing | Not chosen |

FastAPI was selected because the backend primarily acts as a **thin API layer on top of data processing logic**. Using Python also enables leveraging **Pandas**, which simplifies manipulation of energy datasets.

#### Frontend Framework Comparison

| Option | Pros | Cons | Decision |
|--------|------|------|----------|
| **React + TypeScript** | Large ecosystem, component-based architecture, strong tooling | Slightly more setup complexity | **Chosen** |
| Vue | Simpler learning curve | Smaller ecosystem for analytics dashboards | Not chosen |
| Vanilla JavaScript | Minimal dependencies | Harder to scale and maintain | Not chosen |

React was selected due to its **mature ecosystem for building interactive dashboards** and strong compatibility with charting libraries.

#### Chart Library Comparison

| Option | Pros | Cons | Decision |
|--------|------|------|----------|
| **Recharts** | React-native components, easy integration, fast to implement | Less customization than D3 | **Chosen** |
| Chart.js | Popular and simple chart library | Less React-focused architecture | Not chosen |
| D3.js | Extremely powerful visualization capabilities | Complex and time-consuming to implement | Not chosen |

Recharts was chosen because it allows **rapid implementation of dashboard charts within the MVP time constraint**.

------------------------------------------------------------------------

## System Architecture

The system follows a **client--server architecture** with a **relational
persistence layer**.

    Excel Dataset
          ↓
    Backend (FastAPI)
          ↓
    Pandas ingestion + cleaning
          ↓
    Raw readings persisted in PostgreSQL
          ↓
    Normalization and daily delta computation
          ↓
    Derived analytics tables persisted in PostgreSQL
          ↓
    FastAPI endpoints query persisted results
          ↓
    React Dashboard

### Data Flow

1.  The backend loads the Excel dataset.
2.  Pandas ingests and cleans the data; raw readings are persisted in PostgreSQL.
3.  Normalization and daily delta computation produce derived analytics tables in PostgreSQL.
4.  FastAPI exposes data by querying persisted tables through REST endpoints.
5.  The React frontend fetches the data.
6.  The dashboard visualizes the data using charts.

This architecture keeps **data processing logic isolated in the
backend**, **persistence and traceability in PostgreSQL**, and the
frontend focused on visualization.

------------------------------------------------------------------------

## Database & Persistence Strategy

For this MVP, the application uses a **relational persistence layer**
instead of keeping all processed data only in memory.

### Chosen stack

-   **PostgreSQL**
-   **SQLAlchemy 2.0**
-   **Alembic**
-   **Pandas** for ingestion and transformation
-   **FastAPI** for serving the processed analytics

### Why a database is used in this MVP

Although the source dataset is a single Excel file, persisting the
imported and derived data provides important engineering benefits:

-   **Traceability**: preserve what was imported from the original file
-   **Reproducibility**: compare processing results across runs or logic changes
-   **Debuggability**: inspect raw, normalized, and derived records directly
-   **Clear separation of concerns**: import pipeline, analytics pipeline, and API layer stay decoupled
-   **Scalability path**: the design can evolve toward multi-building or repeated imports without restructuring the whole app

### Architectural decision

**Pandas** does the transformations; **PostgreSQL** stores raw and
derived data. Flow as in [System Architecture](#system-architecture):
Excel → Pandas → PostgreSQL → FastAPI → React. The pipeline stays
explicit and inspectable.

------------------------------------------------------------------------

## Database Schema

The database is modeled in layers so that both the raw import and the
processed outputs remain available.

### 1. `import_batches`

Tracks each dataset import.

Suggested fields: `id`, `filename`, `uploaded_at`, `status`, `notes`

Purpose: import traceability, dataset versioning, reproducibility of results.

### 2. `raw_meter_readings`

Stores imported rows close to the original Excel structure.

Suggested fields: `id`, `import_batch_id`, `source_sheet`, `meter_id`,
`meter_type` (`tenant`, `building_total`, `pv`), `tenant_id` (nullable),
`serial_number`, `timestamp`, `raw_value`, `conversion_factor`,
`obis_code` (nullable), `created_at`

Purpose: preserve the original imported readings, support import
debugging, keep a clear audit trail from source file to processed outputs.

### 3. `normalized_meter_readings`

Stores cleaned cumulative values after standardization.

Suggested fields: `id`, `import_batch_id`, `meter_id`, `meter_type`,
`tenant_id` (nullable), `timestamp`, `cumulative_kwh`

Purpose: canonical cleaned source of truth for downstream analytics.

### 4. `daily_meter_consumption`

Stores derived daily deltas from cumulative readings.

Suggested fields: `id`, `import_batch_id`, `meter_id`, `meter_type`,
`tenant_id` (nullable), `date`, `delta_kwh`, `is_valid`,
`quality_flag` (nullable)

Purpose: support all dashboard consumption charts, preserve data-quality
decisions at the derived level.

### 5. `daily_energy_sharing`

Stores the result of the proportional PV allocation model.

Suggested fields: `id`, `import_batch_id`, `date`, `tenant_id`,
`tenant_demand_kwh`, `allocated_pv_kwh`, `grid_import_kwh`,
`self_sufficiency_ratio`

Purpose: make the energy-sharing simulation persistent and inspectable,
simplify API queries for tenant-level sharing views.

### 6. `data_quality_issues`

Stores detected quality problems during processing.

Suggested fields: `id`, `import_batch_id`, `issue_type`, `meter_id`
(nullable), `tenant_id` (nullable), `date` (nullable), `severity`,
`message`

Examples: negative delta, missing day, inconsistent coverage, tenant sum
vs building total mismatch.

Purpose: centralize quality reporting, support trust and transparency
in the dashboard.

------------------------------------------------------------------------

## Backend Processing with Database

The backend processes the dataset in explicit stages:

### Stage 1 — Import

-   read Excel sheets with Pandas
-   parse tenant sheets, building total meter, and PV meter
-   write original rows into `raw_meter_readings`
-   create an `import_batches` entry

### Stage 2 — Normalize

-   standardize meter types and identifiers
-   apply conversion factors
-   write cleaned cumulative values into `normalized_meter_readings`

### Stage 3 — Derive daily consumption

-   sort readings by meter and timestamp
-   compute deltas from cumulative values
-   flag negative deltas (anomalies); exclude them from daily totals
-   aggregate only valid deltas to daily values
-   persist results in `daily_meter_consumption`

Negative deltas can occur due to meter resets, data corruption, or timestamp inconsistencies. Since cumulative energy meters cannot physically decrease, negative deltas are treated as anomalies. These values are flagged in the data quality checks and excluded from consumption aggregation.

### Stage 4 — Compute energy-sharing outputs

-   compute daily tenant demand
-   compute proportional PV allocation
-   derive grid import and self-sufficiency
-   persist results in `daily_energy_sharing`

### Stage 5 — Persist quality issues

-   store quality findings in `data_quality_issues`

### Stage 6 — Serve APIs

-   query persisted derived tables instead of recomputing on each request

This keeps runtime API logic simple and improves reliability.

------------------------------------------------------------------------

## Suggested SQLAlchemy Models and Migration Strategy

The backend implements the tables described in [Database
Schema](#database-schema) as SQLAlchemy ORM models under `app/models/`.
Use **Alembic** for schema versioning:

```bash
alembic revision --autogenerate -m "create initial analytics schema"
alembic upgrade head
```

Schema evolution stays explicit and versioned.

------------------------------------------------------------------------

## API Design Impact

Endpoints query the persisted derived tables (see [Backend Processing
with Database](#backend-processing-with-database), Stage 6) instead of
recomputing on each request. Examples:

-   `/api/summary` → aggregate from `daily_meter_consumption` and `daily_energy_sharing`
-   `/api/timeseries/building` → query daily building and PV records
-   `/api/tenants/comparison` → aggregate tenant metrics from derived daily data
-   `/api/sharing` → query `daily_energy_sharing`
-   `/api/quality` → query `data_quality_issues`

------------------------------------------------------------------------

## Data Processing Strategy

The concrete pipeline is described in [Backend Processing with
Database](#backend-processing-with-database). In short: load Excel, sort
by meter and timestamp, compute deltas from cumulative values, apply the
**building-level conversion factor**, aggregate to daily consumption.
Irregular timestamps are normalized to daily granularity without
interpolation, so we avoid assumptions about missing data.

------------------------------------------------------------------------

## Key Metrics and Insights

The dashboard generates several metrics that help analyze energy usage
patterns.

### Total PV Production

Total electricity generated by the photovoltaic system.

### Building Consumption

Total electricity consumption recorded by the building-level meter.

### Tenant Consumption Comparison

Visualization comparing consumption across tenants.

### Estimated PV Self-Consumption

Estimated amount of PV energy consumed within the building.

### Estimated PV Surplus Generation

PV production that likely exceeded building demand.

These metrics help reveal:

-   daily energy demand patterns
-   tenant consumption differences
-   interaction between PV generation and building consumption

------------------------------------------------------------------------

# Assumptions

Key assumptions for this MVP:

-   consumption is derived from **deltas between consecutive cumulative
    readings**; aggregation is at **daily granularity**
-   PV self-consumption is estimated from **overlap between PV
    production and building demand**; building-level conversion factor
    is applied consistently
-   imports are versioned via `import_batches`; raw rows are preserved,
    then transformed and persisted in PostgreSQL; the API reads from
    these persisted tables (no per-request recomputation)

These keep the implementation manageable while still giving meaningful
insights.

------------------------------------------------------------------------

# Limitations

See [MVP Scope](#mvp-scope) (Out of Scope) for features not
implemented. Additional limitations:

-   irregular timestamps are not interpolated; PV allocation is
    simplified; anomaly detection is minimal; dashboard filtering is
    basic
-   schema and import workflow assume a **single-building MVP** and a
    known Excel structure; analytics are precomputed at import, not
    incrementally updated
-   relational storage is used for MVP scale; production-scale
    smart-meter ingestion might benefit from a time-series–optimized
    store

The MVP demonstrates **core data transformation and visualization**
rather than a full production system.

------------------------------------------------------------------------

# Future Improvements

With additional development time, the following improvements could be
implemented:

### Improved Time-Series Handling

-   interpolation of irregular intervals
-   more robust resampling strategies

### Advanced PV Allocation

-   more accurate distribution of PV generation across tenants
-   modeling of self-consumption and grid export

### Data Quality Monitoring

-   anomaly detection for faulty meters
-   automated data validation rules

### Persistent Storage and Import Workflow

-   support repeated dataset uploads through an admin import workflow
-   compare multiple import batches and processing versions
-   support multiple buildings and projects in the same schema
-   introduce background jobs for import and analytics recomputation
-   evaluate TimescaleDB or another time-series optimized storage layer for production-scale ingestion

### Enhanced Dashboard

-   tenant filtering
-   customizable time ranges
-   additional analytics views
-   improved visualization capabilities

These improvements would transform the MVP into a **more robust energy
analytics platform**.

