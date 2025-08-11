"""
Pytest configuration file with shared fixtures
"""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Add the parent directory to the path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from datetime import date, timedelta

from api.main import app  # , mcp_interpreter  # MCP功能已归档
from core.cache.akshare_adapter import AKShareAdapter
from core.database import Base, get_db
from core.models import Asset, DailyStockData

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
    # Drop and recreate all tables to ensure clean state
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    # Add test data
    db = TestingSessionLocal()
    try:
        # Add test assets
        test_assets = [
            Asset(
                symbol="000001",
                name="平安银行",
                isin="CNE000000040",
                asset_type="stock",
                exchange="SZSE",
                currency="CNY",
            ),
            Asset(
                symbol="600519",
                name="贵州茅台",
                isin="CNE0000018R8",
                asset_type="stock",
                exchange="SHSE",
                currency="CNY",
            ),
            Asset(
                symbol="AAPL",
                name="Apple Inc.",
                isin="US0378331005",
                asset_type="stock",
                exchange="NASDAQ",
                currency="USD",
            ),
            Asset(
                symbol="MSFT",
                name="Microsoft Corporation",
                isin="US5949181045",
                asset_type="stock",
                exchange="NASDAQ",
                currency="USD",
            ),
            Asset(
                symbol="GOOG",
                name="Alphabet Inc.",
                isin="US02079K1079",
                asset_type="stock",
                exchange="NASDAQ",
                currency="USD",
            ),
        ]

        db.add_all(test_assets)
        db.commit()

        # Add test daily stock data
        today = date.today()
        test_data = []

        # Add daily stock data for test assets
        for asset in test_assets:
            for i in range(30):
                trade_date = today - timedelta(days=i)
                test_data.append(
                    DailyStockData(
                        asset_id=asset.asset_id,
                        trade_date=trade_date,
                        open=100.0 + i,
                        high=105.0 + i,
                        low=95.0 + i,
                        close=102.0 + i,
                        volume=1000000 + i * 10000,
                        adjusted_close=102.0 + i,
                        turnover=(100.0 + i) * (1000000 + i * 10000),
                        amplitude=5.0,
                        pct_change=1.0 + i * 0.1,
                        change=1.0 + i * 0.1,
                        turnover_rate=0.5 + i * 0.01,
                    )
                )

        db.add_all(test_data)
        db.commit()
    finally:
        db.close()

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
    # if hasattr(mcp_interpreter, 'set_db'):  # MCP功能已归档
    #     mcp_interpreter.set_db(db)

    yield db

    # Clean up
    db.close()


@pytest.fixture
def mock_akshare_adapter():
    """
    Create a mock AKShare adapter for testing.
    """
    from unittest.mock import MagicMock

    mock_akshare_adapter = MagicMock(spec=AKShareAdapter)

    return mock_akshare_adapter
