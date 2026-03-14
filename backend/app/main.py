"""FastAPI application entry point."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as api_router
from app.db.session import get_db, init_db

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: ensure DB exists; optionally run import pipeline if no data."""
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")


@app.get("/")
def root():
    return {"message": "RevoluSUN Energy Sharing API", "docs": "/docs"}
