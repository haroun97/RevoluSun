"""Startup: run full pipeline if DATA_FILE_PATH set and no data for that file yet."""
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
    """If DATA_FILE_PATH is set and file exists, and no import for that file exists, run full pipeline."""
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
