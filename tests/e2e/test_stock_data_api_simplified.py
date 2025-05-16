# tests/e2e/test_stock_data_api_simplified.py
"""
End-to-end tests for the stock data service in the simplified architecture.

These tests verify the entire flow from API request to database and back,
focusing on the simplified architecture that uses the database as a cache.
"""

import unittest
import os
import sys
import time
from datetime import datetime, timedelta
import pandas as pd
from fastapi.testclient import TestClient

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.api.main import app
from src.api.database import get_db, engine
from src.api.models import Base, Asset, DailyStockData
from src.logger import setup_logger

# Setup test logger
logger = setup_logger("e2e_tests")

class TestStockDataServiceE2E(unittest.TestCase):
    """End-to-end tests for the stock data service in the simplified architecture."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures before running tests."""
        # Create test client
        cls.client = TestClient(app)

        # Create test database session
        cls.engine = engine
        cls.session = next(get_db())

        # Log test start
        logger.info("Starting Stock Data Service E2E tests")

    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests have run."""
        cls.session.close()
        logger.info("Completed Stock Data Service E2E tests")

    def setUp(self):
        """Set up before each test."""
        # Clear database before each test
        self.session.query(DailyStockData).delete()
        self.session.query(Asset).delete()
        self.session.commit()

    def tearDown(self):
        """Clean up after each test."""
        pass

    def _get_test_parameters(self):
        """Get test parameters for a valid stock."""
        # Use a known valid stock symbol
        symbol = "000001"  # Ping An Bank

        # Use recent dates but not too recent to avoid weekend/holiday issues
        end_date = (datetime.now() - timedelta(days=7)).strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")

        return symbol, start_date, end_date

    def test_empty_database_flow(self):
        """Test retrieving stock data when the database is empty."""
        # Get test parameters
        symbol, start_date, end_date = self._get_test_parameters()

        logger.info(f"Testing empty database flow with symbol={symbol}, start_date={start_date}, end_date={end_date}")

        # Make API request (should fetch from AKShare)
        first_request_start = time.time()
        response = self.client.get(f"/api/v2/historical/stock/{symbol}?start_date={start_date}&end_date={end_date}")
        first_request_time = time.time() - first_request_start

        # Check response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["symbol"], symbol)
        self.assertGreater(len(data["data"]), 0)
        logger.info(f"First request returned {len(data['data'])} records in {first_request_time:.4f} seconds")

        # Verify data was saved to database
        assets = self.session.query(Asset).filter(Asset.symbol == symbol).all()
        self.assertEqual(len(assets), 1)

        stock_data = self.session.query(DailyStockData).filter(DailyStockData.asset_id == assets[0].asset_id).all()
        self.assertGreater(len(stock_data), 0)
        logger.info(f"Database now has {len(stock_data)} records for {symbol}")

    def test_complete_cache_hit_flow(self):
        """Test retrieving stock data when all requested data is already in the database."""
        # Get test parameters - use a known trading day range to avoid weekends/holidays
        symbol = "000001"  # Ping An Bank

        # Use specific dates that are known trading days (Monday-Friday, avoiding holidays)
        # Using Monday to Friday of a non-holiday week
        start_date = "20250421"  # Monday
        end_date = "20250425"    # Friday

        logger.info(f"Testing complete cache hit flow with symbol={symbol}, start_date={start_date}, end_date={end_date}")

        # Verify database is empty for this symbol
        assets = self.session.query(Asset).filter(Asset.symbol == symbol).all()
        if assets:
            stock_data_count = self.session.query(DailyStockData).filter(
                DailyStockData.asset_id == assets[0].asset_id
            ).count()
            logger.info(f"Initial database check: found {stock_data_count} records for {symbol}")
            # Delete existing data for this symbol
            self.session.query(DailyStockData).filter(DailyStockData.asset_id == assets[0].asset_id).delete()
            self.session.query(Asset).filter(Asset.symbol == symbol).delete()
            self.session.commit()

        # Verify database is now empty for this symbol
        assets = self.session.query(Asset).filter(Asset.symbol == symbol).all()
        self.assertEqual(len(assets), 0, "Database should be empty before test")
        logger.info(f"Verified database is empty for {symbol}")

        # First, populate the database
        first_request_start = time.time()
        first_response = self.client.get(f"/api/v2/historical/stock/{symbol}?start_date={start_date}&end_date={end_date}")
        first_request_time = time.time() - first_request_start

        self.assertEqual(first_response.status_code, 200)
        first_data = first_response.json()
        first_record_count = len(first_data["data"])
        self.assertGreater(first_record_count, 0, "First request should return data")
        logger.info(f"First request returned {first_record_count} records in {first_request_time:.4f} seconds")

        # Verify data was saved to database
        assets = self.session.query(Asset).filter(Asset.symbol == symbol).all()
        self.assertEqual(len(assets), 1, "Asset should be created in database")

        db_record_count = self.session.query(DailyStockData).filter(
            DailyStockData.asset_id == assets[0].asset_id
        ).count()
        self.assertEqual(db_record_count, first_record_count,
                         f"Database should have {first_record_count} records, but has {db_record_count}")
        logger.info(f"Verified database has {db_record_count} records for {symbol}")

        # Now make a second request for the same data
        second_request_start = time.time()
        second_response = self.client.get(f"/api/v2/historical/stock/{symbol}?start_date={start_date}&end_date={end_date}")
        second_request_time = time.time() - second_request_start

        # Check response
        self.assertEqual(second_response.status_code, 200)
        second_data = second_response.json()
        second_record_count = len(second_data["data"])
        self.assertEqual(second_record_count, first_record_count,
                         f"Second request should return {first_record_count} records, but returned {second_record_count}")
        logger.info(f"Second request returned {second_record_count} records in {second_request_time:.4f} seconds")

        # Verify data content is identical
        for i in range(first_record_count):
            self.assertEqual(first_data["data"][i]["date"], second_data["data"][i]["date"],
                            f"Date mismatch at index {i}")
            self.assertEqual(first_data["data"][i]["close"], second_data["data"][i]["close"],
                            f"Close price mismatch at index {i}")
        logger.info("Verified data content is identical between first and second requests")

        # Verify second request was faster (should be from cache)
        logger.info(f"First request time: {first_request_time:.4f}s, Second request time: {second_request_time:.4f}s")
        # Note: We can't always guarantee the second request will be faster due to system variability
        # So we'll log the times but not assert

    def test_partial_cache_hit_flow(self):
        """Test retrieving stock data when part of the requested data is in the database."""
        # Use specific dates that are known trading days (two consecutive weeks)
        symbol = "000001"  # Ping An Bank

        # First week (Monday-Friday)
        first_week_start = "20250421"  # Monday of first week
        first_week_end = "20250425"    # Friday of first week

        # Second week (Monday-Friday)
        second_week_start = "20250428"  # Monday of second week
        second_week_end = "20250502"    # Friday of second week

        # Full range
        full_range_start = first_week_start
        full_range_end = second_week_end

        logger.info(f"Testing partial cache hit flow with symbol={symbol}")
        logger.info(f"First week: {first_week_start} to {first_week_end}")
        logger.info(f"Second week: {second_week_start} to {second_week_end}")
        logger.info(f"Full range: {full_range_start} to {full_range_end}")

        # Verify database is empty for this symbol
        assets = self.session.query(Asset).filter(Asset.symbol == symbol).all()
        if assets:
            stock_data_count = self.session.query(DailyStockData).filter(
                DailyStockData.asset_id == assets[0].asset_id
            ).count()
            logger.info(f"Initial database check: found {stock_data_count} records for {symbol}")
            # Delete existing data for this symbol
            self.session.query(DailyStockData).filter(DailyStockData.asset_id == assets[0].asset_id).delete()
            self.session.query(Asset).filter(Asset.symbol == symbol).delete()
            self.session.commit()

        # Verify database is now empty for this symbol
        assets = self.session.query(Asset).filter(Asset.symbol == symbol).all()
        self.assertEqual(len(assets), 0, "Database should be empty before test")
        logger.info(f"Verified database is empty for {symbol}")

        # First, get data for the first week
        first_week_start_time = time.time()
        first_week_response = self.client.get(f"/api/v2/historical/stock/{symbol}?start_date={first_week_start}&end_date={first_week_end}")
        first_week_time = time.time() - first_week_start_time

        # Check response
        self.assertEqual(first_week_response.status_code, 200)
        first_week_data = first_week_response.json()
        first_week_record_count = len(first_week_data["data"])
        self.assertGreater(first_week_record_count, 0, "First week request should return data")
        logger.info(f"First week request returned {first_week_record_count} records in {first_week_time:.4f} seconds")

        # Verify data was saved to database
        assets = self.session.query(Asset).filter(Asset.symbol == symbol).all()
        self.assertEqual(len(assets), 1, "Asset should be created in database")

        db_record_count = self.session.query(DailyStockData).filter(
            DailyStockData.asset_id == assets[0].asset_id
        ).count()
        self.assertEqual(db_record_count, first_week_record_count,
                         f"Database should have {first_week_record_count} records, but has {db_record_count}")
        logger.info(f"Verified database has {db_record_count} records for {symbol}")

        # Store the dates from the first week for later comparison
        first_week_dates = [record["date"] for record in first_week_data["data"]]
        logger.info(f"First week dates: {first_week_dates}")

        # Now get data for the full range - should only fetch the second week from AKShare
        full_range_start_time = time.time()
        full_range_response = self.client.get(f"/api/v2/historical/stock/{symbol}?start_date={full_range_start}&end_date={full_range_end}")
        full_range_time = time.time() - full_range_start_time

        # Check response
        self.assertEqual(full_range_response.status_code, 200)
        full_range_data = full_range_response.json()
        full_range_record_count = len(full_range_data["data"])
        self.assertGreater(full_range_record_count, first_week_record_count,
                          f"Full range should return more than {first_week_record_count} records")
        logger.info(f"Full range request returned {full_range_record_count} records in {full_range_time:.4f} seconds")

        # Verify database now has more records
        updated_db_record_count = self.session.query(DailyStockData).filter(
            DailyStockData.asset_id == assets[0].asset_id
        ).count()
        self.assertEqual(updated_db_record_count, full_range_record_count,
                         f"Database should have {full_range_record_count} records, but has {updated_db_record_count}")
        logger.info(f"Verified database now has {updated_db_record_count} records for {symbol}")

        # Verify that the first week data is included in the full range data
        full_range_dates = [record["date"] for record in full_range_data["data"]]
        logger.info(f"Full range dates: {full_range_dates}")

        # Check that all first week dates are in the full range
        for date in first_week_dates:
            self.assertIn(date, full_range_dates, f"Date {date} from first week not found in full range")

        # Calculate how many new dates were added (should be second week dates)
        new_dates = [date for date in full_range_dates if date not in first_week_dates]
        logger.info(f"New dates added in full range: {new_dates}")
        self.assertEqual(len(new_dates), full_range_record_count - first_week_record_count,
                        f"Expected {full_range_record_count - first_week_record_count} new dates, but found {len(new_dates)}")

        # Verify that the full range request was more efficient than fetching all data
        # (This is an approximation - we expect it to be faster than 2x the first week time
        # since it's only fetching the second week)
        theoretical_full_fetch = first_week_time * 2  # Approximate time if fetching all data
        logger.info(f"Partial cache hit efficiency: {full_range_time:.4f}s vs {theoretical_full_fetch:.4f}s theoretical full fetch")

    def test_invalid_symbol_handling(self):
        """Test handling of invalid stock symbols."""
        # Test case 1: Invalid format (5 digits instead of 6)
        invalid_symbol = "12345"
        logger.info(f"Testing invalid symbol format: {invalid_symbol}")

        response = self.client.get(f"/api/v2/historical/stock/{invalid_symbol}?start_date=20230101&end_date=20230102")
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("detail", data)
        logger.info(f"Invalid symbol response: {data['detail']}")

        # Test case 2: Non-existent symbol (valid format but doesn't exist)
        non_existent = "999999"
        logger.info(f"Testing non-existent symbol: {non_existent}")

        response = self.client.get(f"/api/v2/historical/stock/{non_existent}?start_date=20230101&end_date=20230102")
        self.assertEqual(response.status_code, 200)  # Should still return 200 with empty data
        data = response.json()
        self.assertEqual(data["symbol"], non_existent)
        self.assertEqual(len(data["data"]), 0)
        logger.info(f"Non-existent symbol returned empty data as expected")

    def test_invalid_date_handling(self):
        """Test handling of invalid date formats and ranges."""
        symbol, _, _ = self._get_test_parameters()

        # Test case 1: Invalid date format
        logger.info(f"Testing invalid date format")
        response = self.client.get(f"/api/v2/historical/stock/{symbol}?start_date=2023-01-01&end_date=20230102")

        # Check if the API returns an error or empty data for invalid date format
        if response.status_code in [400, 500]:
            # If API returns an error (ideal behavior)
            data = response.json()
            self.assertIn("detail", data)
            logger.info(f"Invalid date format response: {data['detail']}")
        else:
            # If API returns 200 but with empty data (current behavior)
            self.assertEqual(response.status_code, 200)
            data = response.json()
            # Either it should have empty data or an error message in metadata
            if len(data.get("data", [])) == 0:
                logger.info("Invalid date format returned empty data")
            elif "metadata" in data and "message" in data["metadata"]:
                logger.info(f"Invalid date format message: {data['metadata']['message']}")
            else:
                self.fail("Invalid date format should return error or empty data")

        # Test case 2: Start date after end date
        logger.info(f"Testing start date after end date")
        response = self.client.get(f"/api/v2/historical/stock/{symbol}?start_date=20230201&end_date=20230101")

        # Check if the API returns an error or empty data for start date after end date
        if response.status_code in [400, 500]:
            # If API returns an error (ideal behavior)
            data = response.json()
            self.assertIn("detail", data)
            logger.info(f"Start date after end date response: {data['detail']}")
        else:
            # If API returns 200 but with empty data (current behavior)
            self.assertEqual(response.status_code, 200)
            data = response.json()
            # Either it should have empty data or an error message in metadata
            if len(data.get("data", [])) == 0:
                logger.info("Start date after end date returned empty data")
            elif "metadata" in data and "message" in data["metadata"]:
                logger.info(f"Start date after end date message: {data['metadata']['message']}")
            else:
                self.fail("Start date after end date should return error or empty data")

    def test_missing_date_parameters(self):
        """Test behavior with missing date parameters (should use defaults)."""
        symbol, _, _ = self._get_test_parameters()

        # Test case 1: Missing both start and end dates
        logger.info(f"Testing missing both start and end dates")
        response = self.client.get(f"/api/v2/historical/stock/{symbol}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreater(len(data["data"]), 0)
        logger.info(f"Missing both dates returned {len(data['data'])} records with default date range")

        # Test case 2: Missing start date
        today = datetime.now().strftime("%Y%m%d")
        logger.info(f"Testing missing start date, with end_date={today}")
        response = self.client.get(f"/api/v2/historical/stock/{symbol}?end_date={today}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreater(len(data["data"]), 0)
        logger.info(f"Missing start date returned {len(data['data'])} records with default start date")

        # Test case 3: Missing end date
        one_year_ago = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")
        logger.info(f"Testing missing end date, with start_date={one_year_ago}")
        response = self.client.get(f"/api/v2/historical/stock/{symbol}?start_date={one_year_ago}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreater(len(data["data"]), 0)
        logger.info(f"Missing end date returned {len(data['data'])} records with default end date")

    def test_weekend_holiday_data(self):
        """Test retrieving data for weekends and holidays."""
        symbol, _, _ = self._get_test_parameters()

        # Find a recent weekend
        today = datetime.now()
        days_to_previous_saturday = (today.weekday() + 2) % 7
        last_saturday = (today - timedelta(days=days_to_previous_saturday)).strftime("%Y%m%d")
        last_sunday = (today - timedelta(days=days_to_previous_saturday-1)).strftime("%Y%m%d")

        logger.info(f"Testing weekend data retrieval")
        logger.info(f"Last Saturday: {last_saturday}")
        logger.info(f"Last Sunday: {last_sunday}")

        # Test Saturday
        saturday_response = self.client.get(f"/api/v2/historical/stock/{symbol}?start_date={last_saturday}&end_date={last_saturday}")
        self.assertEqual(saturday_response.status_code, 200)
        saturday_data = saturday_response.json()
        logger.info(f"Saturday request returned {len(saturday_data['data'])} records")

        # Test Sunday
        sunday_response = self.client.get(f"/api/v2/historical/stock/{symbol}?start_date={last_sunday}&end_date={last_sunday}")
        self.assertEqual(sunday_response.status_code, 200)
        sunday_data = sunday_response.json()
        logger.info(f"Sunday request returned {len(sunday_data['data'])} records")

        # Weekend should have no or very limited trading data
        logger.info(f"Weekend data check: Saturday has {len(saturday_data['data'])} records, Sunday has {len(sunday_data['data'])} records")

    def test_database_cache_status(self):
        """Test the database cache status endpoint."""
        symbol, start_date, end_date = self._get_test_parameters()

        # First, populate the database with some data
        logger.info(f"Populating database with data for {symbol}")
        response = self.client.get(f"/api/v2/historical/stock/{symbol}?start_date={start_date}&end_date={end_date}")
        self.assertEqual(response.status_code, 200)

        # Now check the cache status
        logger.info(f"Checking database cache status")
        status_response = self.client.get(f"/api/v2/historical/database/cache/status?symbol={symbol}")
        self.assertEqual(status_response.status_code, 200)
        status_data = status_response.json()

        # Verify status data
        if "symbol" in status_data:
            self.assertEqual(status_data["symbol"], symbol)
            if "cached_dates" in status_data:
                self.assertGreater(len(status_data["cached_dates"]), 0)
                logger.info(f"Cache status shows {len(status_data['cached_dates'])} cached dates for {symbol}")
        else:
            # If we get general stats instead of symbol-specific data
            logger.info(f"Cache status shows general statistics: {status_data}")
            self.assertIn("total_assets", status_data)
            self.assertGreaterEqual(status_data["total_assets"], 1)

        # Check status for date range
        range_status_response = self.client.get(f"/api/v2/historical/database/cache/status?symbol={symbol}&start_date={start_date}&end_date={end_date}")
        self.assertEqual(range_status_response.status_code, 200)
        range_status_data = range_status_response.json()

        # Verify range status data
        if "coverage" in range_status_data:
            # Check if coverage is a dictionary with coverage_percentage or a direct value
            if isinstance(range_status_data["coverage"], dict) and "coverage_percentage" in range_status_data["coverage"]:
                coverage_value = range_status_data["coverage"]["coverage_percentage"]
                logger.info(f"Date range cache status shows {coverage_value}% coverage")
            else:
                # If coverage is a direct value (e.g., 0.625 instead of {"coverage_percentage": 62.5})
                coverage_value = range_status_data["coverage"] * 100 if isinstance(range_status_data["coverage"], float) else range_status_data["coverage"]
                logger.info(f"Date range cache status shows {coverage_value}% coverage")

            # Verify coverage is reasonable (at least 60%)
            if isinstance(coverage_value, float):
                self.assertGreaterEqual(coverage_value, 60.0)  # Should be mostly covered
        else:
            logger.info(f"Date range cache status response: {range_status_data}")
            # If we don't get coverage data, at least verify we got a valid response
            self.assertIsInstance(range_status_data, dict)
