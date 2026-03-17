"""
Startup: run the full import pipeline when the app starts if needed.

If DATA_FILE_PATH points to an Excel file and we have not yet imported that file
(no ImportBatch with that filename), we run: ingestion -> normalization ->
resampling -> quality -> sharing. Each step is committed so the DB stays consistent.
"""
import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_data_file_path
from app.db.session import SessionLocal
from app.models import ImportBatch
from app.services.ingestion import run_ingestion
from app.services.normalization import run_normalization
from app.services.resampling import run_resampling
from app.services.quality import run_quality_checks
from app.services.sharing import run_sharing

logger = logging.getLogger(__name__)


def ensure_data_loaded() -> None:
    """
    Run the full import pipeline once if DATA_FILE_PATH is set and the file is not yet imported.

    We check if an ImportBatch with the same filename already exists. If yes, we skip.
    If no, we run all five stages (ingestion, normalization, resampling, quality, sharing)
    and commit after each stage.
    """
    path = get_data_file_path()
    if not path:
        logger.info("DATA_FILE_PATH not set or file missing; skipping import.")
        return

    db: Session = SessionLocal()
    try:
        existing = db.scalar(
            select(ImportBatch).where(ImportBatch.filename == path.name).limit(1)
        )
        if existing:
            logger.info("Data already imported for this dataset; skipping.")
            return

        logger.info("Running ingestion pipeline for %s", path)
        batch = run_ingestion(db, path)
        db.commit()
        run_normalization(db, batch.id)
        db.commit()
        run_resampling(db, batch.id)
        db.commit()
        run_quality_checks(db, batch.id)
        db.commit()
        run_sharing(db, batch.id)
        db.commit()
        logger.info("Import pipeline completed for batch id=%s", batch.id)
    except Exception as e:
        logger.exception("Import pipeline failed: %s", e)
        db.rollback()
        raise
    finally:
        db.close()
