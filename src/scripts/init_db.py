"""
Database initialization script
"""
import os
import sys
from pathlib import Path

# Add the parent directory to the path so we can import from src
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import logging

from src.config import DATABASE_URL, DATABASE_PATH
from src.api.models import Base
from src.api.database import engine
from src.logger import setup_logger

# Setup logger
logger = setup_logger(__name__)

def init_db():
    """
    Initialize the database by creating all tables
    """
    try:
        # Create database directory if it doesn't exist
        if DATABASE_URL.startswith('sqlite'):
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
