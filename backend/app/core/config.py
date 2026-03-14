"""Application configuration from environment."""
import os
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Backend settings from env."""

    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/revolusun"
    data_file_path: str = ""

    model_config = {"env_file": ".env", "extra": "ignore"}


def get_settings() -> Settings:
    return Settings(
        database_url=os.getenv("DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/revolusun"),
        data_file_path=os.getenv("DATA_FILE_PATH", ""),
    )


def get_data_file_path() -> Path | None:
    """Return path to Excel file if set and exists."""
    path = get_settings().data_file_path.strip()
    if not path:
        return None
    p = Path(path)
    return p if p.is_file() else None
