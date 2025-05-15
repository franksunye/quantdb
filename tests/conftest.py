"""
Pytest configuration file with shared fixtures
"""
import sys
from pathlib import Path
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

# Add the parent directory to the path so we can import from src
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.api.main import app, mcp_interpreter
from src.api.database import get_db, Base
from src.api.models import Asset, Price
from src.cache.cache_engine import CacheEngine
from src.cache.freshness_tracker import FreshnessTracker
from src.cache.akshare_adapter import AKShareAdapter
from datetime import date, timedelta

# Use a file-based SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./database/test_db.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create test client
client = TestClient(app)

# Override the get_db dependency
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

# Apply the override to the app
app.dependency_overrides[get_db] = override_get_db

# Create a fixture to initialize the database before all tests
@pytest.fixture(scope="session", autouse=True)
def initialize_test_db():
    """Initialize the test database before all tests"""
    # Create all tables
    Base.metadata.create_all(bind=engine)
    yield
    # Clean up after all tests
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def test_db():
    """
    Get a database session for testing.
    This fixture assumes the database has already been initialized with test data.
    """
    db = TestingSessionLocal()

    # Set the database for the MCP interpreter if needed
    if hasattr(mcp_interpreter, 'set_db'):
        mcp_interpreter.set_db(db)

    yield db

    # Clean up
    db.close()

@pytest.fixture
def mock_cache_components():
    """
    Create mock cache components for testing.
    """
    from unittest.mock import MagicMock

    mock_cache_engine = MagicMock(spec=CacheEngine)
    mock_freshness_tracker = MagicMock(spec=FreshnessTracker)
    mock_akshare_adapter = MagicMock(spec=AKShareAdapter)

    # Configure mock cache engine
    mock_cache_engine.generate_key.return_value = "test_cache_key"
    mock_cache_engine.get.return_value = None  # Default to cache miss

    # Configure mock freshness tracker
    mock_freshness_tracker.is_fresh.return_value = False  # Default to not fresh

    return {
        "cache_engine": mock_cache_engine,
        "freshness_tracker": mock_freshness_tracker,
        "akshare_adapter": mock_akshare_adapter
    }
