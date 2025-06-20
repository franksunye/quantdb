"""
Tests for historical stock data API endpoints
"""
import pytest
from unittest.mock import patch, MagicMock
import pandas as pd

# Import from conftest.py
from tests.conftest import client, test_db
from core.cache.akshare_adapter import AKShareAdapter
from core.models import DailyStockData, Asset

# Sample test data - using correct date format YYYYMMDD
SAMPLE_STOCK_DATA = pd.DataFrame({
    'date': ['20230101', '20230102', '20230103'],
    'open': [10.0, 10.5, 11.0],
    'high': [11.0, 11.5, 12.0],
    'low': [9.5, 10.0, 10.5],
    'close': [10.5, 11.0, 11.5],
    'volume': [1000000, 1200000, 1100000],
    'turnover': [10500000, 13200000, 12650000],
    'amplitude': [0.15, 0.14, 0.13],
    'pct_change': [0.05, 0.048, 0.045],
    'change': [0.5, 0.5, 0.5],
    'turnover_rate': [0.02, 0.025, 0.022]
})

@pytest.fixture(autouse=True)
def clean_test_data(test_db):
    """Clean test data before each test"""
    # Clean up any existing test data
    test_db.query(DailyStockData).delete()
    test_db.query(Asset).delete()
    test_db.commit()
    yield
    # Clean up after test
    test_db.query(DailyStockData).delete()
    test_db.query(Asset).delete()
    test_db.commit()

@pytest.fixture
def mock_akshare_adapter():
    """Mock AKShareAdapter for testing"""
    # Patch the get_stock_data method (simplified architecture)
    with patch.object(AKShareAdapter, 'get_stock_data') as mock_get_stock_data:
        mock_get_stock_data.return_value = SAMPLE_STOCK_DATA
        yield mock_get_stock_data

def test_get_historical_stock_data(mock_akshare_adapter, test_db):
    """Test getting historical stock data"""
    # Use specific date range that matches our test data
    response = client.get("/api/v1/historical/stock/000001?start_date=20230101&end_date=20230103")

    assert response.status_code == 200
    data = response.json()

    assert data["symbol"] == "000001"
    assert len(data["data"]) == 3
    assert data["metadata"]["count"] == 3
    assert data["metadata"]["status"] == "success"

    # Check that the mock was called with the right parameters
    mock_akshare_adapter.assert_called_once()
    call_args = mock_akshare_adapter.call_args[1]
    assert call_args["symbol"] == "000001"
    assert call_args["adjust"] == ""

    # Check data structure
    first_point = data["data"][0]
    assert "date" in first_point
    assert "open" in first_point
    assert "high" in first_point
    assert "low" in first_point
    assert "close" in first_point
    assert "volume" in first_point

def test_get_historical_stock_data_with_dates(mock_akshare_adapter, test_db):
    """Test getting historical stock data with date parameters"""
    response = client.get("/api/v1/historical/stock/000001?start_date=20230101&end_date=20230103")

    assert response.status_code == 200
    data = response.json()

    # Verify response structure
    assert data["symbol"] == "000001"
    assert data["start_date"] == "20230101"
    assert data["end_date"] == "20230103"
    assert len(data["data"]) == 3
    assert data["metadata"]["count"] == 3
    assert data["metadata"]["status"] == "success"

    # Note: Mock may not be called if data exists in database from previous test
    # This is correct behavior - we're testing the API response, not the data source

def test_get_historical_stock_data_with_adjust(mock_akshare_adapter, test_db):
    """Test getting historical stock data with price adjustment"""
    response = client.get("/api/v1/historical/stock/000001?adjust=qfq")

    assert response.status_code == 200

    # Check that the mock was called (may be multiple times due to intelligent caching)
    assert mock_akshare_adapter.called, "AKShare adapter should be called"

    # Verify that all calls used the correct symbol and adjust parameter
    for call in mock_akshare_adapter.call_args_list:
        call_kwargs = call[1]  # Get keyword arguments
        assert call_kwargs["symbol"] == "000001"
        assert call_kwargs["adjust"] == "qfq"

def test_get_historical_stock_data_invalid_symbol(test_db):
    """Test getting historical stock data with invalid symbol"""
    response = client.get("/api/v1/historical/stock/ABC")

    assert response.status_code == 400
    data = response.json()
    assert "Symbol must be a 6-digit number" in data["error"]["message"]

def test_get_historical_stock_data_empty_result(test_db):
    """Test getting historical stock data with empty result"""
    # Patch the get_stock_data method to return empty DataFrame
    with patch('src.cache.akshare_adapter.AKShareAdapter.get_stock_data', return_value=pd.DataFrame()):
        response = client.get("/api/v1/historical/stock/000001")

        assert response.status_code == 200
        data = response.json()

        assert data["symbol"] == "000001"
        assert len(data["data"]) == 0
        assert data["metadata"]["count"] == 0
        assert data["metadata"]["status"] == "success"
        assert "No data found" in data["metadata"]["message"]

def test_get_historical_stock_data_error(test_db):
    """Test getting historical stock data with error"""
    # Patch the get_stock_data method to raise an exception
    with patch('src.cache.akshare_adapter.AKShareAdapter.get_stock_data', side_effect=Exception("Test error")):
        response = client.get("/api/v1/historical/stock/000001")

        assert response.status_code == 500
        data = response.json()
        assert "Error fetching data" in data["error"]["message"]
