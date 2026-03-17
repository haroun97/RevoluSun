"""
Application configuration loaded from environment variables.

This module reads DATABASE_URL and DATA_FILE_PATH so the backend knows
where to store data and which Excel file to import on startup.
"""
import os
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    All config the app needs, read from env (or .env file).

    - database_url: PostgreSQL connection string (used by SQLAlchemy).
    - data_file_path: Path to the Excel meter data file; if set and the file
      exists, the startup pipeline will import it when the DB has no data yet.
    """

    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/revolusun"
    data_file_path: str = ""

    model_config = {"env_file": ".env", "extra": "ignore"}


def get_settings() -> Settings:
    """Build settings from current environment (env vars override defaults)."""
    return Settings(
        database_url=os.getenv("DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/revolusun"),
        data_file_path=os.getenv("DATA_FILE_PATH", ""),
    )


def get_data_file_path() -> Path | None:
    """
    Return the path to the Excel data file if it is set and the file exists.

    Returns None when DATA_FILE_PATH is empty or the path is not a file.
    The import pipeline uses this to decide whether to run on startup.
    """
    path = get_settings().data_file_path.strip()
    if not path:
        return None
    p = Path(path)
    return p if p.is_file() else None
