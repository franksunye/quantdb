"""
Tests for the MCP API
"""
import sys
from pathlib import Path
from datetime import date, timedelta

# Add the parent directory to the path so we can import from src
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.api.main import app, mcp_interpreter
from src.api.database import get_db, Base
from src.config import API_PREFIX
from src.api.models import Asset, Price
from src.mcp.schemas import MCPRequest

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
        )
    ]

    db.add_all(test_assets)
    db.commit()

    # Add test prices
    today = date.today()
    test_prices = []

    # Add prices for AAPL
    aapl = db.query(Asset).filter(Asset.symbol == "AAPL").first()
    for i in range(30):
        price_date = today - timedelta(days=i)
        test_prices.append(
            Price(
                asset_id=aapl.asset_id,
                date=price_date,
                open=150.0 + i,
                high=155.0 + i,
                low=148.0 + i,
                close=152.0 + i,
                volume=1000000 + i * 10000,
                adjusted_close=152.0 + i
            )
        )

    # Add prices for MSFT
    msft = db.query(Asset).filter(Asset.symbol == "MSFT").first()
    for i in range(30):
        price_date = today - timedelta(days=i)
        test_prices.append(
            Price(
                asset_id=msft.asset_id,
                date=price_date,
                open=250.0 + i,
                high=255.0 + i,
                low=248.0 + i,
                close=252.0 + i,
                volume=2000000 + i * 10000,
                adjusted_close=252.0 + i
            )
        )

    db.add_all(test_prices)
    db.commit()

    # Set the database for the MCP interpreter
    mcp_interpreter.set_db(db)

    yield db

    # Clean up
    db.close()
    Base.metadata.drop_all(bind=engine)

def test_mcp_get_price(test_db):
    """Test MCP get_price intent"""
    request = MCPRequest(
        query="Show me the price of AAPL",
        context={},
        session_id="test_session"
    )

    response = client.post(f"{API_PREFIX}/mcp/query", json=request.model_dump())
    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "get_price"
    assert "prices" in data["data"]
    assert len(data["data"]["prices"]) > 0
    assert data["data"]["asset"]["symbol"] == "AAPL"

def test_mcp_get_asset_info(test_db):
    """Test MCP get_asset_info intent"""
    request = MCPRequest(
        query="Show me information about Microsoft",
        context={},
        session_id="test_session"
    )

    response = client.post(f"{API_PREFIX}/mcp/query", json=request.model_dump())
    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "get_asset_info"
    assert "asset" in data["data"]
    assert data["data"]["asset"]["symbol"] == "MSFT"

def test_mcp_list_assets(test_db):
    """Test MCP list_assets intent"""
    request = MCPRequest(
        query="List all available stocks",
        context={},
        session_id="test_session"
    )

    response = client.post(f"{API_PREFIX}/mcp/query", json=request.model_dump())
    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "list_assets"
    assert "assets" in data["data"]
    assert len(data["data"]["assets"]) == 2

def test_mcp_unknown_intent(test_db):
    """Test MCP with unknown intent"""
    request = MCPRequest(
        query="What is the meaning of life?",
        context={},
        session_id="test_session"
    )

    response = client.post(f"{API_PREFIX}/mcp/query", json=request.model_dump())
    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "unknown"
    assert "message" in data["data"]
