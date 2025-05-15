"""
Tests for historical stock data API endpoints
"""
import pytest
from unittest.mock import patch, MagicMock
import pandas as pd

# Import from conftest.py
from tests.conftest import client, test_db
from src.cache.akshare_adapter import AKShareAdapter

# Sample test data
SAMPLE_STOCK_DATA = pd.DataFrame({
    'date': ['2023-01-01', '2023-01-02', '2023-01-03'],
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

@pytest.fixture
def mock_akshare_adapter():
    """Mock AKShareAdapter for testing"""
    # First patch the is_fresh method to always return False to avoid cache hits
    with patch('src.cache.freshness_tracker.FreshnessTracker.is_fresh', return_value=False):
        # Then patch the get_stock_data method
        with patch.object(AKShareAdapter, 'get_stock_data') as mock_get_stock_data:
            mock_get_stock_data.return_value = SAMPLE_STOCK_DATA
            yield mock_get_stock_data

def test_get_historical_stock_data(mock_akshare_adapter, test_db):
    """Test getting historical stock data"""
    response = client.get("/api/v1/historical/stock/000001")

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

    # Check that the mock was called with the right parameters
    mock_akshare_adapter.assert_called_once()
    call_args = mock_akshare_adapter.call_args[1]
    assert call_args["symbol"] == "000001"
    assert call_args["start_date"] == "20230101"
    assert call_args["end_date"] == "20230103"

def test_get_historical_stock_data_with_adjust(mock_akshare_adapter, test_db):
    """Test getting historical stock data with price adjustment"""
    response = client.get("/api/v1/historical/stock/000001?adjust=qfq")

    assert response.status_code == 200

    # Check that the mock was called with the right parameters
    mock_akshare_adapter.assert_called_once()
    call_args = mock_akshare_adapter.call_args[1]
    assert call_args["symbol"] == "000001"
    assert call_args["adjust"] == "qfq"

def test_get_historical_stock_data_invalid_symbol(test_db):
    """Test getting historical stock data with invalid symbol"""
    response = client.get("/api/v1/historical/stock/ABC")

    assert response.status_code == 400
    data = response.json()
    assert "Symbol must be a 6-digit number" in data["detail"]

def test_get_historical_stock_data_empty_result(test_db):
    """Test getting historical stock data with empty result"""
    # Patch both the freshness tracker and the get_stock_data method
    with patch('src.cache.freshness_tracker.FreshnessTracker.is_fresh', return_value=False):
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
    # Patch both the freshness tracker and the get_stock_data method
    with patch('src.cache.freshness_tracker.FreshnessTracker.is_fresh', return_value=False):
        with patch('src.cache.akshare_adapter.AKShareAdapter.get_stock_data', side_effect=Exception("Test error")):
            response = client.get("/api/v1/historical/stock/000001")

            assert response.status_code == 500
            data = response.json()
            assert "Error fetching data" in data["detail"]
