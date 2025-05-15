"""
Tests for the assets API
"""
import pytest
from src.config import API_PREFIX

# Import from conftest.py
from tests.conftest import client, test_db

def test_get_assets(test_db):
    """Test getting a list of assets"""
    response = client.get(f"{API_PREFIX}/assets/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5
    # Check that the expected symbols are in the response
    symbols = [asset["symbol"] for asset in data]
    assert "000001" in symbols
    assert "600519" in symbols
    assert "AAPL" in symbols
    assert "MSFT" in symbols
    assert "GOOG" in symbols

def test_get_asset_by_id(test_db):
    """Test getting a specific asset by ID"""
    # Get the first asset
    response = client.get(f"{API_PREFIX}/assets/1")
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "000001"
    assert data["name"] == "平安银行"

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
    assert len(data) == 5  # All test assets are stocks
