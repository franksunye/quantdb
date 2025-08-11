"""
Database initialization script
"""

import os
import sys
from pathlib import Path

# Add the parent directory to the path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import logging

from core.utils.config import DATABASE_URL, DATABASE_PATH
from core.models import Base
from core.database import engine
from core.utils.logger import get_logger

# Setup logger
logger = get_logger(__name__)


def init_db():
    """
    Initialize the database by creating all tables
    """
    try:
        # Create database directory if it doesn't exist
        if DATABASE_URL.startswith("sqlite"):
            db_dir = os.path.dirname(DATABASE_PATH)
            if not os.path.exists(db_dir):
                os.makedirs(db_dir)
                logger.info(f"Created database directory: {db_dir}")

        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")

        # Test database connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            logger.info(f"Database connection test: {result.fetchone()}")

        return True
    except SQLAlchemyError as e:
        logger.error(f"Error initializing database: {e}")
        return False


if __name__ == "__main__":
    logger.info("Initializing database...")
    success = init_db()
    if success:
        logger.info("Database initialization completed successfully")
    else:
        logger.error("Database initialization failed")
        sys.exit(1)
