"""
Tests for the assets API
"""
import sys
from pathlib import Path

# Add the parent directory to the path so we can import from src
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.api.main import app
from src.api.database import get_db, Base
from src.config import API_PREFIX
from src.api.models import Asset

# Create in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
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

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="function")
def test_db():
    # Drop all tables first to ensure clean state
    Base.metadata.drop_all(bind=engine)

    # Create the database tables
    Base.metadata.create_all(bind=engine)

    # Add test data
    db = TestingSessionLocal()

    # Add test assets
    test_assets = [
        Asset(
            symbol="AAPL",
            name="Apple Inc.",
            isin="US0378331005",
            asset_type="stock",
            exchange="NASDAQ",
            currency="USD"
        ),
        Asset(
            symbol="MSFT",
            name="Microsoft Corporation",
            isin="US5949181045",
            asset_type="stock",
            exchange="NASDAQ",
            currency="USD"
        ),
        Asset(
            symbol="GOOG",
            name="Alphabet Inc.",
            isin="US02079K1079",
            asset_type="stock",
            exchange="NASDAQ",
            currency="USD"
        )
    ]

    db.add_all(test_assets)
    db.commit()

    yield db

    # Clean up
    db.close()
    Base.metadata.drop_all(bind=engine)

def test_get_assets(test_db):
    """Test getting a list of assets"""
    response = client.get(f"{API_PREFIX}/assets/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert data[0]["symbol"] == "AAPL"
    assert data[1]["symbol"] == "MSFT"
    assert data[2]["symbol"] == "GOOG"

def test_get_asset_by_id(test_db):
    """Test getting a specific asset by ID"""
    # Get the first asset
    response = client.get(f"{API_PREFIX}/assets/1")
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "AAPL"
    assert data["name"] == "Apple Inc."

    # Test non-existent asset
    response = client.get(f"{API_PREFIX}/assets/999")
    assert response.status_code == 404

def test_get_asset_by_symbol(test_db):
    """Test getting a specific asset by symbol"""
    response = client.get(f"{API_PREFIX}/assets/symbol/MSFT")
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "MSFT"
    assert data["name"] == "Microsoft Corporation"

    # Test non-existent symbol
    response = client.get(f"{API_PREFIX}/assets/symbol/NONEXISTENT")
    assert response.status_code == 404

def test_filter_assets(test_db):
    """Test filtering assets"""
    # Filter by symbol
    response = client.get(f"{API_PREFIX}/assets/?symbol=OO")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["symbol"] == "GOOG"

    # Filter by name
    response = client.get(f"{API_PREFIX}/assets/?name=Apple")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["symbol"] == "AAPL"

    # Filter by exchange
    response = client.get(f"{API_PREFIX}/assets/?exchange=NASDAQ")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3

    # Filter by asset_type
    response = client.get(f"{API_PREFIX}/assets/?asset_type=stock")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
