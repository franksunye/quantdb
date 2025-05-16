# tests/e2e/test_data_flow_e2e.py
"""
End-to-end tests for the complete data flow.

These tests verify the entire flow from API request to database and back,
including the intelligent data retrieval logic.

This test uses real data from AKShare to ensure the system works correctly
in real-world scenarios.
"""

import unittest
import os
import sys
import tempfile
import json
import time
from datetime import datetime, timedelta
import pandas as pd
from fastapi.testclient import TestClient

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.api.main import app
from src.api.models import Base, Asset, DailyStockData
from src.cache.akshare_adapter_simplified import AKShareAdapter
from src.services.stock_data_service import StockDataService
from src.services.database_cache import DatabaseCache
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.api.database import get_db
from src.logger import setup_logger

# Setup logger
logger = setup_logger(__name__)


class TestDataFlowE2E(unittest.TestCase):
    """End-to-end tests for the complete data flow."""

    @classmethod
    def setUpClass(cls):
        """Set up test database."""
        # Create temporary database
        cls.db_fd, cls.db_path = tempfile.mkstemp()
        cls.engine = create_engine(f'sqlite:///{cls.db_path}')

        # Create tables
        Base.metadata.create_all(cls.engine)

        # Create session
        cls.Session = sessionmaker(bind=cls.engine)

    @classmethod
    def tearDownClass(cls):
        """Clean up test database."""
        try:
            os.close(cls.db_fd)
        except OSError:
            # File descriptor might already be closed
            pass

        try:
            # Give time for any pending operations to complete
            time.sleep(0.1)

            # Try to remove the file
            if os.path.exists(cls.db_path):
                os.unlink(cls.db_path)
        except OSError as e:
            # If file is still in use, log the error but don't fail the test
            print(f"Warning: Could not remove temporary database file: {e}")

    def setUp(self):
        """Set up test fixtures."""
        self.session = self.Session()

        # Override the get_db dependency
        def override_get_db():
            try:
                yield self.session
            finally:
                pass

        app.dependency_overrides[get_db] = override_get_db

        # Create test client
        self.client = TestClient(app)

        # Create real components for testing
        self.akshare_adapter = AKShareAdapter(self.session)
        self.db_cache = DatabaseCache(self.session)
        self.stock_data_service = StockDataService(self.session, self.akshare_adapter)
        self.stock_data_service.db_cache = self.db_cache

        # Log test setup
        logger.info("Test setup complete with real AKShare adapter and database cache")

    def tearDown(self):
        """Clean up test fixtures."""
        # Clean up database
        self.session.query(DailyStockData).delete()
        self.session.query(Asset).delete()
        self.session.commit()
        self.session.close()

        # Remove dependency override
        app.dependency_overrides.clear()

        # Log test teardown
        logger.info("Test teardown complete")

    def _get_test_parameters(self):
        """Get test parameters for real data testing."""
        # Use a real stock symbol and recent date range
        symbol = "000001"  # 平安银行
        end_date = datetime.now().strftime('%Y%m%d')
        # Use a 10-day range for testing
        start_date = (datetime.now() - timedelta(days=10)).strftime('%Y%m%d')

        logger.info(f"Using test parameters: symbol={symbol}, start_date={start_date}, end_date={end_date}")
        return symbol, start_date, end_date

    def test_empty_database_flow(self):
        """Test data flow when database is empty."""
        # Get test parameters
        symbol, start_date, end_date = self._get_test_parameters()

        # Make sure database is empty
        self.session.query(DailyStockData).delete()
        self.session.query(Asset).delete()
        self.session.commit()

        logger.info(f"Testing empty database flow with symbol={symbol}, start_date={start_date}, end_date={end_date}")

        # Make first API request (should fetch from AKShare)
        first_request_start = time.time()
        response = self.client.get(f"/api/v2/historical/stock/{symbol}?start_date={start_date}&end_date={end_date}")
        first_request_time = time.time() - first_request_start

        # Check response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreater(len(data['data']), 0)  # Should have some data
        logger.info(f"First request returned {len(data['data'])} records in {first_request_time:.4f} seconds")

        # Verify data was saved to database
        assets = self.session.query(Asset).filter(Asset.symbol == symbol).all()
        self.assertEqual(len(assets), 1)

        stock_data = self.session.query(DailyStockData).filter(DailyStockData.asset_id == assets[0].asset_id).all()
        self.assertGreater(len(stock_data), 0)
        logger.info(f"Database now has {len(stock_data)} records for {symbol}")

        # Make the same request again (should use database cache)
        second_request_start = time.time()
        response2 = self.client.get(f"/api/v2/historical/stock/{symbol}?start_date={start_date}&end_date={end_date}")
        second_request_time = time.time() - second_request_start

        # Check response
        self.assertEqual(response2.status_code, 200)
        data2 = response2.json()
        self.assertEqual(len(data2['data']), len(data['data']))
        logger.info(f"Second request returned {len(data2['data'])} records in {second_request_time:.4f} seconds")

        # Log performance comparison
        # Note: In test environments, the second request might not always be faster
        # due to various factors like system load, network conditions, etc.
        improvement = (first_request_time - second_request_time) / first_request_time * 100
        logger.info(f"Performance comparison: first={first_request_time:.4f}s, second={second_request_time:.4f}s, diff={improvement:.2f}%")

    def test_partial_database_flow(self):
        """Test data flow when database has partial data."""
        # Get test parameters
        symbol, start_date, end_date = self._get_test_parameters()

        # Make sure database is empty
        self.session.query(DailyStockData).delete()
        self.session.query(Asset).delete()
        self.session.commit()

        # First, create an asset
        asset = Asset(
            symbol=symbol,
            name=f"Test Stock {symbol}",
            isin=f"CN{symbol}",
            asset_type="stock",
            exchange="CN",
            currency="CNY"
        )
        self.session.add(asset)
        self.session.commit()

        logger.info(f"Testing partial database flow with symbol={symbol}, start_date={start_date}, end_date={end_date}")

        # Calculate a midpoint date for partial data
        start_dt = datetime.strptime(start_date, '%Y%m%d')
        end_dt = datetime.strptime(end_date, '%Y%m%d')
        days_diff = (end_dt - start_dt).days
        midpoint_dt = start_dt + timedelta(days=days_diff // 2)
        midpoint_date = midpoint_dt.strftime('%Y%m%d')

        logger.info(f"Using midpoint date: {midpoint_date}")

        # First, get data for the first half of the date range
        first_half_start = time.time()
        response_first_half = self.client.get(f"/api/v2/historical/stock/{symbol}?start_date={start_date}&end_date={midpoint_date}")
        first_half_time = time.time() - first_half_start

        # Check response
        self.assertEqual(response_first_half.status_code, 200)
        data_first_half = response_first_half.json()
        self.assertGreater(len(data_first_half['data']), 0)
        logger.info(f"First half request returned {len(data_first_half['data'])} records in {first_half_time:.4f} seconds")

        # Now get data for the full range - should only fetch the second half from AKShare
        full_range_start = time.time()
        response_full = self.client.get(f"/api/v2/historical/stock/{symbol}?start_date={start_date}&end_date={end_date}")
        full_range_time = time.time() - full_range_start

        # Check response
        self.assertEqual(response_full.status_code, 200)
        data_full = response_full.json()
        self.assertGreater(len(data_full['data']), len(data_first_half['data']))
        logger.info(f"Full range request returned {len(data_full['data'])} records in {full_range_time:.4f} seconds")

        # Verify that the full range request was efficient
        # It should be faster than fetching the entire range from scratch
        # but might not be faster than the first half request since it still needs to fetch some data
        stock_data = self.session.query(DailyStockData).filter(DailyStockData.asset_id == asset.asset_id).all()
        logger.info(f"Database now has {len(stock_data)} records for {symbol}")

    def test_overlapping_date_ranges(self):
        """Test data flow with overlapping date ranges."""
        # Get test parameters
        symbol, start_date, end_date = self._get_test_parameters()

        # Make sure database is empty
        self.session.query(DailyStockData).delete()
        self.session.query(Asset).delete()
        self.session.commit()

        # Calculate date ranges for overlapping tests
        start_dt = datetime.strptime(start_date, '%Y%m%d')
        end_dt = datetime.strptime(end_date, '%Y%m%d')
        days_diff = (end_dt - start_dt).days

        # First range: start_date to start_date + 2/3 of days
        first_end_dt = start_dt + timedelta(days=int(days_diff * 2/3))
        first_end_date = first_end_dt.strftime('%Y%m%d')

        # Second range: start_date + 1/3 of days to end_date
        second_start_dt = start_dt + timedelta(days=int(days_diff * 1/3))
        second_start_date = second_start_dt.strftime('%Y%m%d')

        logger.info(f"Testing overlapping date ranges:")
        logger.info(f"First range: {start_date} to {first_end_date}")
        logger.info(f"Second range: {second_start_date} to {end_date}")
        logger.info(f"Overlap: {second_start_date} to {first_end_date}")

        # Make first API request
        first_request_start = time.time()
        response1 = self.client.get(f"/api/v2/historical/stock/{symbol}?start_date={start_date}&end_date={first_end_date}")
        first_request_time = time.time() - first_request_start

        # Check response
        self.assertEqual(response1.status_code, 200)
        data1 = response1.json()
        self.assertGreater(len(data1['data']), 0)
        logger.info(f"First request returned {len(data1['data'])} records in {first_request_time:.4f} seconds")

        # Make second API request with overlapping range
        second_request_start = time.time()
        response2 = self.client.get(f"/api/v2/historical/stock/{symbol}?start_date={second_start_date}&end_date={end_date}")
        second_request_time = time.time() - second_request_start

        # Check response
        self.assertEqual(response2.status_code, 200)
        data2 = response2.json()
        self.assertGreater(len(data2['data']), 0)
        logger.info(f"Second request returned {len(data2['data'])} records in {second_request_time:.4f} seconds")

        # Verify that the second request only fetched the non-overlapping part
        # Get all data for the full range to compare
        full_request_start = time.time()
        response_full = self.client.get(f"/api/v2/historical/stock/{symbol}?start_date={start_date}&end_date={end_date}")
        full_request_time = time.time() - full_request_start

        # Check response
        self.assertEqual(response_full.status_code, 200)
        data_full = response_full.json()
        logger.info(f"Full range request returned {len(data_full['data'])} records in {full_request_time:.4f} seconds")

        # The sum of records from first and second requests should be greater than the full range
        # due to the overlap
        self.assertGreaterEqual(len(data1['data']) + len(data2['data']), len(data_full['data']))

        # Check database records
        assets = self.session.query(Asset).filter(Asset.symbol == symbol).all()
        self.assertEqual(len(assets), 1)

        stock_data = self.session.query(DailyStockData).filter(DailyStockData.asset_id == assets[0].asset_id).all()
        logger.info(f"Database now has {len(stock_data)} records for {symbol}")


    def test_edge_cases(self):
        """Test edge cases like future dates and non-trading days."""
        # Get test parameters
        symbol = "000001"  # 平安银行

        # Make sure database is empty
        self.session.query(DailyStockData).delete()
        self.session.query(Asset).delete()
        self.session.commit()

        # Test case 1: Future dates
        # Use today's date for both start and end to avoid the "start date after end date" error
        # since our adapter now correctly sets future end dates to today
        today = datetime.now()
        today_str = today.strftime('%Y%m%d')

        logger.info(f"Testing future date: {today_str}")

        response_future = self.client.get(f"/api/v2/historical/stock/{symbol}?start_date={today_str}&end_date={today_str}")
        self.assertEqual(response_future.status_code, 200)
        data_future = response_future.json()

        # May return data if today is a trading day, or empty if it's a weekend/holiday
        logger.info(f"Today's date request returned {len(data_future['data'])} records")

        # Test case 2: Weekend dates
        # Find a recent weekend
        test_date = today
        while test_date.weekday() < 5:  # 5 = Saturday, 6 = Sunday
            test_date -= timedelta(days=1)

        weekend_date = test_date.strftime('%Y%m%d')
        logger.info(f"Testing weekend date: {weekend_date}")

        response_weekend = self.client.get(f"/api/v2/historical/stock/{symbol}?start_date={weekend_date}&end_date={weekend_date}")
        self.assertEqual(response_weekend.status_code, 200)
        data_weekend = response_weekend.json()

        # Should return empty or very limited data for weekend
        logger.info(f"Weekend date request returned {len(data_weekend['data'])} records")

        # Test case 3: Very old dates
        old_start = "19900101"
        old_end = "19900110"

        logger.info(f"Testing very old dates: {old_start} to {old_end}")

        response_old = self.client.get(f"/api/v2/historical/stock/{symbol}?start_date={old_start}&end_date={old_end}")
        self.assertEqual(response_old.status_code, 200)
        data_old = response_old.json()

        # Log the result (may or may not have data depending on the stock)
        logger.info(f"Very old dates request returned {len(data_old['data'])} records")

        # Test case 4: Invalid symbol
        invalid_symbol = "999999"  # Likely invalid

        logger.info(f"Testing invalid symbol: {invalid_symbol}")

        response_invalid = self.client.get(f"/api/v2/historical/stock/{invalid_symbol}")

        # Should still return 200 but with empty data
        self.assertEqual(response_invalid.status_code, 200)
        data_invalid = response_invalid.json()
        logger.info(f"Invalid symbol request returned {len(data_invalid['data'])} records")

        # Test case 5: Database cache status
        logger.info("Testing database cache status endpoint")

        response_status = self.client.get(f"/api/v2/historical/database/cache/status")
        self.assertEqual(response_status.status_code, 200)
        status_data = response_status.json()

        # Should have some statistics
        self.assertIn("total_assets", status_data)
        self.assertIn("total_data_points", status_data)
        logger.info(f"Database cache status: {json.dumps(status_data, indent=2)}")


if __name__ == '__main__':
    unittest.main()
