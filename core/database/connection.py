"""
Core Database Connection Module

This module provides database connection management and session handling
for the QuantDB core layer.
"""

# Import type hints for adapters (removed deprecated src/ imports)
from typing import TYPE_CHECKING, Generator, Union

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

# Configuration will be imported from core.utils.config
from ..utils.config import DATABASE_URL, DB_TYPE

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    connect_args=(
        {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
    ),
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()


# Dependency to get DB session
def get_db() -> Generator[Session, None, None]:
    """
    Dependency for FastAPI to get a database session

    Returns:
        SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Dependency to get DB adapter (simplified for core architecture)
def get_db_adapter():
    """
    Dependency for FastAPI to get a database adapter

    Note: Simplified for core architecture. Database adapters are now
    handled through the core services layer.
    """
    # Return the engine directly for core architecture
    return engine
