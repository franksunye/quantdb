"""
Database connection module for the API
"""
from typing import Union, Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import Session

# Import type hints for adapters
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.db.supabase_adapter import SupabaseAdapter
    from src.db.sqlite_adapter import SQLiteAdapter

from src.config import DATABASE_URL, DB_TYPE

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
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

# Dependency to get DB adapter
def get_db_adapter() -> Union['SupabaseAdapter', 'SQLiteAdapter']:
    """
    Dependency for FastAPI to get a database adapter

    Returns:
        Database adapter instance based on configuration
    """
    from src.db.adapter_factory import create_db_adapter
    return create_db_adapter(DB_TYPE)
