"""
Database connection and session handling.

Creates the PostgreSQL engine from DATABASE_URL and provides a session factory.
API routes and the import pipeline use get_db() to get a session, do work, then close it.
"""
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.db.base import Base


def get_engine():
    """Create the SQLAlchemy engine from DATABASE_URL (one engine per process)."""
    settings = get_settings()
    return create_engine(
        settings.database_url,
        pool_pre_ping=True,  # Check connection is alive before using
        echo=False,
    )


engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Provide a database session for one request or one pipeline run.

    The session is closed automatically when the caller is done (e.g. after
    the API handler returns). Use this in FastAPI dependencies.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    Create all tables if they do not exist.

    Normally we use Alembic migrations for schema changes; this is a fallback
    so the app can start even without running migrations first.
    """
    Base.metadata.create_all(bind=engine)
