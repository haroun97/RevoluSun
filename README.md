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

The backend is responsible for:

-   loading and processing the Excel dataset
-   converting cumulative readings into consumption intervals
-   computing aggregated metrics
-   exposing data through REST endpoints

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

**Alternatively: run PostgreSQL with Docker**

If you prefer not to install PostgreSQL locally:

```bash
docker run --name revolusun-postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=revolusun \
  -p 5432:5432 \
  -d postgres:15
```

**Run database migrations** (from the `backend/` directory):

```bash
cd backend
alembic upgrade head
```

**Additional backend dependencies** (add to backend environment if not present):

-   `sqlalchemy`, `alembic`, `psycopg[binary]`, `python-dotenv`
-   Optional: `pandas`, `openpyxl`

------------------------------------------------------------------------

## Frontend

The frontend provides a simple dashboard interface for visualizing the
processed energy data.

### Install dependencies

``` bash
npm install
```

### Start the development server

``` bash
npm run dev
```

The frontend will start a local development server and communicate with
the backend REST API to fetch data.

------------------------------------------------------------------------

# Design & Architecture Overview

This section explains the core architectural decisions made while
building the MVP.

The implementation prioritizes:

-   clear data processing logic
-   simple system architecture
-   quick development within a limited time window

------------------------------------------------------------------------

## Problem Understanding

The dataset consists of **Excel sheets containing cumulative electricity
meter readings**.

Key characteristics of the dataset include:

-   several **tenant electricity meters**
-   a **building-level meter (Summenzähler)** with a **conversion factor
    of 50**
-   a **PV production meter**
-   **irregular timestamps**
-   **different measurement coverage periods for tenants**
-   readings recorded as **cumulative totals rather than direct
    consumption values**

Because the readings are cumulative counters, they cannot be analyzed
directly.

To derive energy consumption, the system must compute the **difference
(delta) between consecutive readings**.

Additional challenges include:

-   timestamps that are not evenly spaced
-   tenants starting or stopping measurements at different times
-   ensuring that building-level consumption aligns with tenant usage
    and PV production

Before meaningful insights can be generated, the dataset must be
**cleaned, normalized, and transformed into interval consumption
values**.

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
strong support for data processing**.

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

  -----------------------------------------------------------------------
  Option            Pros              Cons              Decision
  ----------------- ----------------- ----------------- -----------------
  FastAPI           Lightweight, fast Smaller ecosystem **Chosen**
                    API development,  compared to       
                    strong typing     Django            
                    support, ideal                      
                    for data services                   

  Django            Mature framework, Heavy framework   Not chosen
                    built-in ORM and  for a simple data 
                    admin tools       processing API    

  Node.js (Express) Flexible          Less convenient   Not chosen
                    JavaScript        for data-heavy    
                    ecosystem         processing        
  -----------------------------------------------------------------------

FastAPI was selected because the backend primarily acts as a **thin API
layer on top of data processing logic**.

Using Python also enables leveraging **Pandas**, which simplifies
manipulation of energy datasets.

------------------------------------------------------------------------

#### Frontend Framework Comparison

  -----------------------------------------------------------------------
  Option            Pros              Cons              Decision
  ----------------- ----------------- ----------------- -----------------
  React +           Large ecosystem,  Slightly more     **Chosen**
  TypeScript        component-based   setup complexity  
                    architecture,                       
                    strong tooling                      

  Vue               Simpler learning  Smaller ecosystem Not chosen
                    curve             for analytics     
                                      dashboards        

  Vanilla           Minimal           Harder to scale   Not chosen
  JavaScript        dependencies      and maintain      
  -----------------------------------------------------------------------

React was selected due to its **mature ecosystem for building
interactive dashboards** and strong compatibility with charting
libraries.

------------------------------------------------------------------------

#### Chart Library Comparison

  -----------------------------------------------------------------------
  Option            Pros              Cons              Decision
  ----------------- ----------------- ----------------- -----------------
  Recharts          React-native      Less              **Chosen**
                    components, easy  customization     
                    integration, fast than D3           
                    to implement                        

  Chart.js          Popular and       Less              Not chosen
                    simple chart      React-focused     
                    library           architecture      

  D3.js             Extremely         Complex and       Not chosen
                    powerful          time-consuming to 
                    visualization     implement         
                    capabilities                        
  -----------------------------------------------------------------------

Recharts was chosen because it allows **rapid implementation of
dashboard charts within the MVP time constraint**.

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

The application uses **Pandas for transformation** and **PostgreSQL for
persistence**.

Recommended processing flow:

```text
Excel file
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
React dashboard renders API data
```

This keeps the analytics pipeline explicit and inspectable while still
leveraging Python for time-series logic.

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
-   flag negative deltas
-   aggregate to daily values
-   persist results in `daily_meter_consumption`

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

The backend should include SQLAlchemy ORM models for: `ImportBatch`,
`RawMeterReading`, `NormalizedMeterReading`, `DailyMeterConsumption`,
`DailyEnergySharing`, `DataQualityIssue`.

Recommended structure:

```text
backend/
  app/
    db/
      base.py
      session.py
    models/
      import_batch.py
      raw_meter_reading.py
      normalized_meter_reading.py
      daily_meter_consumption.py
      daily_energy_sharing.py
      data_quality_issue.py
```

Use **Alembic** for schema versioning:

```bash
alembic revision --autogenerate -m "create initial analytics schema"
alembic upgrade head
```

Schema evolution stays explicit and versioned.

------------------------------------------------------------------------

## API Design Impact

Because the transformed data is persisted, API endpoints primarily query
derived tables rather than recomputing analytics on each request.

Examples:

-   `/api/summary` → aggregate from `daily_meter_consumption` and `daily_energy_sharing`
-   `/api/timeseries/building` → query daily building and PV records
-   `/api/tenants/comparison` → aggregate tenant metrics from derived daily data
-   `/api/sharing` → query `daily_energy_sharing`
-   `/api/quality` → query `data_quality_issues`

This approach improves clarity and keeps the API layer lightweight.

------------------------------------------------------------------------

## Data Processing Strategy

The dataset contains **cumulative energy readings**, which means
consumption must be derived indirectly.

Key processing steps include:

1.  Loading Excel sheets into Pandas DataFrames
2.  Sorting readings by timestamp
3.  Computing **delta values between consecutive readings**
4.  Applying the **conversion factor for the building-level meter**
5.  Aggregating results into daily consumption metrics

Handling irregular timestamps:

-   timestamps are normalized to daily granularity
-   intervals are preserved rather than interpolated

This approach provides **reliable consumption estimates while avoiding
assumptions about missing data**.

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

Several assumptions were made to simplify the implementation:

-   energy consumption is derived from the difference between cumulative
    readings
-   readings represent consumption between consecutive timestamps
-   aggregation is performed at **daily granularity**
-   PV self-consumption is estimated using **overlap between PV
    production and building demand**
-   the building-level meter conversion factor is applied consistently
-   imported datasets are versioned through `import_batches`
-   raw imported rows are preserved before transformation
-   processed analytics are persisted and served from PostgreSQL
-   Pandas is used for time-series transformations, while PostgreSQL is used for storage and queryable outputs
-   API endpoints read from persisted derived tables rather than recalculating all analytics per request

These assumptions allow meaningful insights while keeping the
implementation manageable.

------------------------------------------------------------------------

# Limitations

Due to the limited development time and dataset complexity, several
limitations exist:

-   irregular timestamps are not interpolated
-   PV allocation across tenants is simplified
-   minimal anomaly detection
-   limited dashboard filtering capabilities
-   the current schema is optimized for a single-building MVP, not yet for a multi-building production platform
-   import workflow assumes a known Excel structure
-   analytics are precomputed during import rather than incrementally updated
-   the database design is relational and suitable for MVP scale, but a specialized time-series architecture may be preferable for production-scale smart-meter ingestion

The MVP focuses on demonstrating **core data transformation and
visualization capabilities** rather than a complete production system.

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

------------------------------------------------------------------------

# Interview Framing

Suggested explanation during the presentation:

> I chose PostgreSQL for persistence because even though the source dataset is small, the application benefits from preserving raw imports, normalized readings, derived daily consumption, allocation results, and quality flags. Pandas handles the transformation pipeline well, while PostgreSQL makes the outputs inspectable, reproducible, and easier to serve through stable APIs. This gives the MVP a cleaner architecture and a credible path toward production.
