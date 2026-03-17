"""
FastAPI application entry point.

On startup we create tables if needed (init_db) and, if DATA_FILE_PATH is set
and the file has not been imported yet, run the full import pipeline.
All API routes are under the /api prefix (e.g. /api/summary, /api/quality).
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as api_router
from app.db.session import get_db, init_db

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Run on app startup: create DB tables, then optionally load Excel data.

    If DATA_FILE_PATH points to an Excel file and we have no import for it yet,
    we run the full pipeline (ingestion -> normalization -> resampling -> quality -> sharing).
    If that fails we log a warning but the app still starts (so the API is usable).
    """
    init_db()
    try:
        from app.services.startup import ensure_data_loaded
        ensure_data_loaded()
    except Exception as e:
        logger.warning("Startup data load check failed (non-fatal): %s", e)
    yield
    # shutdown: nothing to do


app = FastAPI(
    title="RevoluSUN Energy Sharing API",
    description="REST API for energy analytics dashboard",
    version="1.0.0",
    lifespan=lifespan,
)

# Allow the frontend (e.g. on another port or Vercel) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# All dashboard endpoints live under /api (e.g. GET /api/summary, GET /api/quality)
app.include_router(api_router, prefix="/api")


@app.get("/")
def root():
    """Simple root endpoint; API docs are at /docs."""
    return {"message": "RevoluSUN Energy Sharing API", "docs": "/docs"}
