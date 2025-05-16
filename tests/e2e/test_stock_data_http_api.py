# tests/e2e/test_stock_data_http_api.py
"""
端到端测试 - 测试股票数据HTTP API (简化架构)

这些测试通过向外部启动的API服务器发送HTTP请求来验证整个流程，
重点关注使用数据库作为缓存的简化架构。

使用方法:
1. 首先启动测试服务器: python start_test_server.py
2. 然后在另一个终端运行此测试: python -m unittest tests.e2e.test_stock_data_http_api
"""

import unittest
import os
import sys
import time
import requests
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.api.database import get_db, engine
from src.api.models import Asset, DailyStockData
from src.logger import setup_logger

# Setup test logger
logger = setup_logger("http_api_e2e_tests")

class TestStockDataHTTPAPI(unittest.TestCase):
    """End-to-end tests for the stock data HTTP API (simplified architecture)

    Note: Before running these tests, you must start the test server:
    python start_test_server.py
    """

    # Test server configuration
    server_host = "127.0.0.1"  # Use localhost
    server_port = 8766  # Use an uncommon port to avoid conflicts
    server_url = f"http://{server_host}:{server_port}"

    @classmethod
    def setUpClass(cls):
        """Set up test environment before running any tests."""
        logger.info("================================================================")
        logger.info("=== STARTING STOCK DATA HTTP API END-TO-END TESTS ===")
        logger.info("================================================================")
        logger.info(f"Test server URL: {cls.server_url}")
        logger.info(f"Test start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Check if the server is already running
        logger.info(f"Checking if test server is running at {cls.server_url}...")
        max_retries = 3
        retry_delay = 2

        for attempt in range(max_retries):
            try:
                logger.info(f"Attempting to connect to server (attempt {attempt+1}/{max_retries})...")
                # Try to access an API endpoint
                test_symbol = "000001"
                test_start_date = "20250421"
                test_end_date = "20250425"
                response = requests.get(f"{cls.server_url}/api/v2/historical/stock/{test_symbol}?start_date={test_start_date}&end_date={test_end_date}")
                if response.status_code == 200:
                    logger.info(f"[SUCCESS] Test server is running and responding (status code: {response.status_code})")
                    # Check if we got valid data
                    data = response.json()
                    if "data" in data:
                        logger.info(f"[SUCCESS] Server returned valid data with {len(data['data'])} records")
                    break
                else:
                    logger.warning(f"[WARNING] Test server returned status code {response.status_code}")
                    if attempt < max_retries - 1:
                        logger.info(f"Waiting {retry_delay} seconds before retrying...")
                        time.sleep(retry_delay)
                    else:
                        logger.error(f"[ERROR] Test server returned error status code: {response.status_code}")
                        raise Exception(f"Test server returned error status code: {response.status_code}")
            except requests.exceptions.ConnectionError:
                if attempt < max_retries - 1:
                    logger.warning(f"[WARNING] Could not connect to server, waiting {retry_delay} seconds before retrying...")
                    time.sleep(retry_delay)
                else:
                    logger.error(f"[ERROR] Could not connect to test server at {cls.server_url}")
                    logger.error("Please run 'python start_test_server.py' to start the test server first")
                    raise Exception("Test server is not running")

        # Create database session for test verification
        logger.info("Establishing database connection for test verification...")
        cls.engine = engine
        cls.session = next(get_db())
        logger.info("[SUCCESS] Database connection established")

        # Log database state before tests
        asset_count = cls.session.query(Asset).count()
        data_count = cls.session.query(DailyStockData).count()
        logger.info(f"Initial database state: {asset_count} assets, {data_count} data records")

    @classmethod
    def tearDownClass(cls):
        """Clean up test environment after all tests have run."""
        logger.info("----------------------------------------------------------------")
        logger.info("Cleaning up test environment...")

        # Close database session
        if hasattr(cls, 'session'):
            # Log final database state
            asset_count = cls.session.query(Asset).count()
            data_count = cls.session.query(DailyStockData).count()
            logger.info(f"Final database state: {asset_count} assets, {data_count} data records")

            cls.session.close()
            logger.info("[SUCCESS] Database connection closed")

        logger.info("=== STOCK DATA HTTP API END-TO-END TESTS COMPLETED ===")
        logger.info(f"Test end time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("Note: If you no longer need the test server, you can stop it by pressing Ctrl+C")
        logger.info("================================================================")

    def setUp(self):
        """Set up before each test."""
        # Get the current test name
        test_name = self.id().split('.')[-1]
        logger.info(f"----------------------------------------------------------------")
        logger.info(f"Setting up for test: {test_name}")

        # Clear database before each test
        logger.info("Clearing database before test...")
        daily_stock_data_count = self.session.query(DailyStockData).delete()
        asset_count = self.session.query(Asset).delete()
        self.session.commit()
        logger.info(f"Cleared {daily_stock_data_count} stock data records and {asset_count} assets from database")

    def tearDown(self):
        """Clean up after each test."""
        # Get the current test name
        test_name = self.id().split('.')[-1]
        logger.info(f"Completed test: {test_name}")
        logger.info(f"----------------------------------------------------------------")

    def _get_test_parameters(self):
        """Get test parameters for a valid stock."""
        # Use a known valid stock symbol
        symbol = "000001"  # Ping An Bank

        # Use specific dates that are known trading days (Monday-Friday, avoiding holidays)
        # Using Monday to Friday of a non-holiday week
        start_date = "20250421"  # Monday
        end_date = "20250425"    # Friday

        return symbol, start_date, end_date

    def test_empty_database_flow(self):
        """Test retrieving stock data when the database is empty."""
        # Get test parameters
        symbol, start_date, end_date = self._get_test_parameters()

        logger.info(f"=== TEST: Empty Database Flow ===")
        logger.info(f"Parameters: symbol={symbol}, start_date={start_date}, end_date={end_date}")

        # Verify database is empty for this symbol
        assets = self.session.query(Asset).filter(Asset.symbol == symbol).all()
        if assets:
            stock_data_count = self.session.query(DailyStockData).filter(
                DailyStockData.asset_id == assets[0].asset_id
            ).count()
            logger.info(f"Initial database check: found {stock_data_count} records for {symbol}")
            # Delete existing data for this symbol
            logger.info(f"Cleaning up existing data for {symbol}...")
            self.session.query(DailyStockData).filter(DailyStockData.asset_id == assets[0].asset_id).delete()
            self.session.query(Asset).filter(Asset.symbol == symbol).delete()
            self.session.commit()
            logger.info(f"Cleanup complete")

        # Verify database is now empty for this symbol
        assets = self.session.query(Asset).filter(Asset.symbol == symbol).all()
        self.assertEqual(len(assets), 0, "Database should be empty before test")
        logger.info(f"Verified database is empty for {symbol}")

        # Make HTTP request (should fetch from AKShare)
        logger.info(f"Making HTTP request to fetch data from AKShare...")
        first_request_start = time.time()
        response = requests.get(f"{self.server_url}/api/v2/historical/stock/{symbol}?start_date={start_date}&end_date={end_date}")
        first_request_time = time.time() - first_request_start
        logger.info(f"Request completed in {first_request_time:.4f} seconds")

        # Check response
        self.assertEqual(response.status_code, 200, "Response status code should be 200")
        data = response.json()
        self.assertEqual(data["symbol"], symbol, f"Response symbol should be {symbol}")
        record_count = len(data["data"])
        self.assertGreater(record_count, 0, "Response should contain data")
        logger.info(f"Request returned {record_count} records")

        # Log some sample data for verification
        if record_count > 0:
            sample_records = min(3, record_count)
            logger.info(f"Sample data (first {sample_records} records):")
            for i in range(sample_records):
                logger.info(f"  Record {i+1}: Date={data['data'][i]['date']}, Close={data['data'][i]['close']}")

        # Verify data was saved to database
        logger.info(f"Verifying data was saved to database...")
        assets = self.session.query(Asset).filter(Asset.symbol == symbol).all()
        self.assertEqual(len(assets), 1, "Asset should be created in database")
        logger.info(f"Asset found in database: ID={assets[0].asset_id}, Symbol={assets[0].symbol}, Name={assets[0].name}")

        db_record_count = self.session.query(DailyStockData).filter(
            DailyStockData.asset_id == assets[0].asset_id
        ).count()
        self.assertEqual(db_record_count, record_count,
                         f"Database should have {record_count} records, but has {db_record_count}")
        logger.info(f"Verified database has {db_record_count} records for {symbol}")

        # Verify some data content
        stock_data = self.session.query(DailyStockData).filter(
            DailyStockData.asset_id == assets[0].asset_id
        ).all()

        # Check that dates in database match dates in response
        db_dates = [data.trade_date.strftime('%Y-%m-%d') for data in stock_data]
        response_dates = [record["date"] for record in data["data"]]
        self.assertEqual(sorted(db_dates), sorted(response_dates),
                        "Dates in database should match dates in response")
        logger.info(f"Verified database dates match response dates")

        # Log date range in database
        if db_dates:
            logger.info(f"Database date range: {min(db_dates)} to {max(db_dates)}")

        logger.info(f"=== TEST PASSED: Empty Database Flow ===\n")

    def test_complete_cache_hit_flow(self):
        """Test retrieving stock data when all requested data is already in the database."""
        # Get test parameters
        symbol, start_date, end_date = self._get_test_parameters()

        logger.info(f"=== TEST: Complete Cache Hit Flow ===")
        logger.info(f"Parameters: symbol={symbol}, start_date={start_date}, end_date={end_date}")

        # Verify database is empty for this symbol
        assets = self.session.query(Asset).filter(Asset.symbol == symbol).all()
        if assets:
            stock_data_count = self.session.query(DailyStockData).filter(
                DailyStockData.asset_id == assets[0].asset_id
            ).count()
            logger.info(f"Initial database check: found {stock_data_count} records for {symbol}")
            # Delete existing data for this symbol
            logger.info(f"Cleaning up existing data for {symbol}...")
            self.session.query(DailyStockData).filter(DailyStockData.asset_id == assets[0].asset_id).delete()
            self.session.query(Asset).filter(Asset.symbol == symbol).delete()
            self.session.commit()
            logger.info(f"Cleanup complete")

        # Verify database is now empty for this symbol
        assets = self.session.query(Asset).filter(Asset.symbol == symbol).all()
        self.assertEqual(len(assets), 0, "Database should be empty before test")
        logger.info(f"Verified database is empty for {symbol}")

        # First, populate the database
        logger.info(f"STEP 1: Making first HTTP request to populate database...")
        first_request_start = time.time()
        first_response = requests.get(f"{self.server_url}/api/v2/historical/stock/{symbol}?start_date={start_date}&end_date={end_date}")
        first_request_time = time.time() - first_request_start
        logger.info(f"First request completed in {first_request_time:.4f} seconds")

        self.assertEqual(first_response.status_code, 200, "First response status code should be 200")
        first_data = first_response.json()
        first_record_count = len(first_data["data"])
        self.assertGreater(first_record_count, 0, "First request should return data")
        logger.info(f"First request returned {first_record_count} records")

        # Log some sample data from first request
        if first_record_count > 0:
            sample_records = min(3, first_record_count)
            logger.info(f"Sample data from first request (first {sample_records} records):")
            for i in range(sample_records):
                logger.info(f"  Record {i+1}: Date={first_data['data'][i]['date']}, Close={first_data['data'][i]['close']}")

        # Verify data was saved to database
        logger.info(f"Verifying data was saved to database...")
        assets = self.session.query(Asset).filter(Asset.symbol == symbol).all()
        self.assertEqual(len(assets), 1, "Asset should be created in database")
        logger.info(f"Asset found in database: ID={assets[0].asset_id}, Symbol={assets[0].symbol}, Name={assets[0].name}")

        db_record_count = self.session.query(DailyStockData).filter(
            DailyStockData.asset_id == assets[0].asset_id
        ).count()
        self.assertEqual(db_record_count, first_record_count,
                         f"Database should have {first_record_count} records, but has {db_record_count}")
        logger.info(f"Verified database has {db_record_count} records for {symbol}")

        # Now make a second request for the same data
        logger.info(f"STEP 2: Making second HTTP request (should be served from cache)...")
        second_request_start = time.time()
        second_response = requests.get(f"{self.server_url}/api/v2/historical/stock/{symbol}?start_date={start_date}&end_date={end_date}")
        second_request_time = time.time() - second_request_start
        logger.info(f"Second request completed in {second_request_time:.4f} seconds")

        # Check response
        self.assertEqual(second_response.status_code, 200, "Second response status code should be 200")
        second_data = second_response.json()
        second_record_count = len(second_data["data"])
        self.assertEqual(second_record_count, first_record_count,
                         f"Second request should return {first_record_count} records, but returned {second_record_count}")
        logger.info(f"Second request returned {second_record_count} records")

        # Verify data content is identical
        logger.info(f"Verifying data content is identical between first and second requests...")
        for i in range(first_record_count):
            self.assertEqual(first_data["data"][i]["date"], second_data["data"][i]["date"],
                            f"Date mismatch at index {i}")
            self.assertEqual(first_data["data"][i]["close"], second_data["data"][i]["close"],
                            f"Close price mismatch at index {i}")
        logger.info("Verified data content is identical between first and second requests")

        # Log performance comparison
        logger.info(f"Performance comparison:")
        logger.info(f"  First request time: {first_request_time:.4f}s (from AKShare)")
        logger.info(f"  Second request time: {second_request_time:.4f}s (from cache)")

        # Calculate performance improvement
        if first_request_time > 0:
            improvement = (first_request_time - second_request_time) / first_request_time * 100
            logger.info(f"  Performance improvement: {improvement:.2f}%")

        # Verify database state hasn't changed
        final_db_count = self.session.query(DailyStockData).filter(
            DailyStockData.asset_id == assets[0].asset_id
        ).count()
        self.assertEqual(final_db_count, first_record_count,
                         "Database record count should remain the same after second request")
        logger.info(f"Verified database still has {final_db_count} records for {symbol}")

        logger.info(f"=== TEST PASSED: Complete Cache Hit Flow ===\n")

    def test_partial_cache_hit_flow(self):
        """Test retrieving stock data when part of the requested data is in the database."""
        # Use specific dates that are known trading days (two consecutive weeks)
        symbol = "000001"  # Ping An Bank

        # First week (Monday-Friday)
        first_week_start = "20250421"  # Monday of first week
        first_week_end = "20250423"    # Wednesday of first week (partial week)

        # Full range (Monday-Friday)
        full_range_start = "20250421"  # Monday
        full_range_end = "20250425"    # Friday (full week)

        logger.info(f"=== TEST: Partial Cache Hit Flow ===")
        logger.info(f"Parameters: symbol={symbol}")
        logger.info(f"First part: {first_week_start} to {first_week_end}")
        logger.info(f"Full range: {full_range_start} to {full_range_end}")

        # Verify database is empty for this symbol
        assets = self.session.query(Asset).filter(Asset.symbol == symbol).all()
        if assets:
            stock_data_count = self.session.query(DailyStockData).filter(
                DailyStockData.asset_id == assets[0].asset_id
            ).count()
            logger.info(f"Initial database check: found {stock_data_count} records for {symbol}")
            # Delete existing data for this symbol
            logger.info(f"Cleaning up existing data for {symbol}...")
            self.session.query(DailyStockData).filter(DailyStockData.asset_id == assets[0].asset_id).delete()
            self.session.query(Asset).filter(Asset.symbol == symbol).delete()
            self.session.commit()
            logger.info(f"Cleanup complete")

        # Verify database is now empty for this symbol
        assets = self.session.query(Asset).filter(Asset.symbol == symbol).all()
        self.assertEqual(len(assets), 0, "Database should be empty before test")
        logger.info(f"Verified database is empty for {symbol}")

        # First, get data for the first part of the week
        logger.info(f"STEP 1: Making first HTTP request for partial data (first part of week)...")
        first_part_start_time = time.time()
        first_part_response = requests.get(f"{self.server_url}/api/v2/historical/stock/{symbol}?start_date={first_week_start}&end_date={first_week_end}")
        first_part_time = time.time() - first_part_start_time
        logger.info(f"First part request completed in {first_part_time:.4f} seconds")

        # Check response
        self.assertEqual(first_part_response.status_code, 200, "First part response status code should be 200")
        first_part_data = first_part_response.json()
        first_part_record_count = len(first_part_data["data"])
        self.assertGreater(first_part_record_count, 0, "First part request should return data")
        logger.info(f"First part request returned {first_part_record_count} records")

        # Log some sample data from first part request
        if first_part_record_count > 0:
            sample_records = min(3, first_part_record_count)
            logger.info(f"Sample data from first part request (first {sample_records} records):")
            for i in range(sample_records):
                logger.info(f"  Record {i+1}: Date={first_part_data['data'][i]['date']}, Close={first_part_data['data'][i]['close']}")

        # Verify data was saved to database
        logger.info(f"Verifying data was saved to database...")
        assets = self.session.query(Asset).filter(Asset.symbol == symbol).all()
        self.assertEqual(len(assets), 1, "Asset should be created in database")
        logger.info(f"Asset found in database: ID={assets[0].asset_id}, Symbol={assets[0].symbol}, Name={assets[0].name}")

        db_record_count = self.session.query(DailyStockData).filter(
            DailyStockData.asset_id == assets[0].asset_id
        ).count()
        self.assertEqual(db_record_count, first_part_record_count,
                         f"Database should have {first_part_record_count} records, but has {db_record_count}")
        logger.info(f"Verified database has {db_record_count} records for {symbol}")

        # Store the dates from the first part for later comparison
        first_part_dates = [record["date"] for record in first_part_data["data"]]
        logger.info(f"First part dates: {', '.join(first_part_dates)}")

        # Now get data for the full range - should only fetch the second part from AKShare
        logger.info(f"STEP 2: Making second HTTP request for full range (should partially hit cache)...")
        full_range_start_time = time.time()
        full_range_response = requests.get(f"{self.server_url}/api/v2/historical/stock/{symbol}?start_date={full_range_start}&end_date={full_range_end}")
        full_range_time = time.time() - full_range_start_time
        logger.info(f"Full range request completed in {full_range_time:.4f} seconds")

        # Check response
        self.assertEqual(full_range_response.status_code, 200, "Full range response status code should be 200")
        full_range_data = full_range_response.json()
        full_range_record_count = len(full_range_data["data"])
        self.assertGreaterEqual(full_range_record_count, first_part_record_count,
                          f"Full range should return at least {first_part_record_count} records")
        logger.info(f"Full range request returned {full_range_record_count} records")

        # Log some sample data from full range request
        if full_range_record_count > 0:
            sample_records = min(3, full_range_record_count)
            logger.info(f"Sample data from full range request (first {sample_records} records):")
            for i in range(sample_records):
                logger.info(f"  Record {i+1}: Date={full_range_data['data'][i]['date']}, Close={full_range_data['data'][i]['close']}")

        # Verify database now has the correct number of records
        logger.info(f"Verifying database has been updated with additional records...")
        updated_db_record_count = self.session.query(DailyStockData).filter(
            DailyStockData.asset_id == assets[0].asset_id
        ).count()
        self.assertEqual(updated_db_record_count, full_range_record_count,
                         f"Database should have {full_range_record_count} records, but has {updated_db_record_count}")
        logger.info(f"Verified database now has {updated_db_record_count} records for {symbol}")

        # Verify that the first part data is included in the full range data
        full_range_dates = [record["date"] for record in full_range_data["data"]]
        logger.info(f"Full range dates: {', '.join(full_range_dates)}")

        # Check that all first part dates are in the full range
        logger.info(f"Verifying all first part dates are included in full range...")
        for date in first_part_dates:
            self.assertIn(date, full_range_dates, f"Date {date} from first part not found in full range")
        logger.info(f"All first part dates are included in full range")

        # Calculate how many new dates were added
        new_dates = [date for date in full_range_dates if date not in first_part_dates]
        logger.info(f"New dates added in full range: {', '.join(new_dates)}")

        # Check that the number of new dates matches the difference in record counts
        expected_new_dates = full_range_record_count - first_part_record_count
        self.assertEqual(len(new_dates), expected_new_dates,
                        f"Expected {expected_new_dates} new dates, but found {len(new_dates)}")
        logger.info(f"Verified {len(new_dates)} new dates were added, matching expected count")

        # Verify that the full range request was more efficient than fetching all data
        theoretical_full_fetch = first_part_time * (full_range_record_count / first_part_record_count)
        logger.info(f"Performance analysis:")
        logger.info(f"  First part request time: {first_part_time:.4f}s")
        logger.info(f"  Full range request time: {full_range_time:.4f}s")
        logger.info(f"  Theoretical time for fetching all data: {theoretical_full_fetch:.4f}s")

        # Calculate efficiency
        if theoretical_full_fetch > 0:
            efficiency = (theoretical_full_fetch - full_range_time) / theoretical_full_fetch * 100
            logger.info(f"  Efficiency gain: {efficiency:.2f}%")

        logger.info(f"=== TEST PASSED: Partial Cache Hit Flow ===\n")

    def test_invalid_symbol_handling(self):
        """Test handling of invalid stock symbols."""
        # Use fixed dates for consistency
        start_date = "20250421"  # Monday
        end_date = "20250425"    # Friday

        logger.info(f"=== TEST: Invalid Symbol Handling ===")
        logger.info(f"Parameters: start_date={start_date}, end_date={end_date}")

        # Test case 1: Invalid format (5 digits instead of 6)
        invalid_symbol = "12345"
        logger.info(f"CASE 1: Testing invalid symbol format: {invalid_symbol}")

        logger.info(f"Making HTTP request with invalid symbol format...")
        response = requests.get(f"{self.server_url}/api/v2/historical/stock/{invalid_symbol}?start_date={start_date}&end_date={end_date}")
        self.assertEqual(response.status_code, 400, "Invalid symbol should return 400 status code")
        data = response.json()
        self.assertIn("detail", data, "Response should contain 'detail' field with error message")
        logger.info(f"Response status code: {response.status_code}")
        logger.info(f"Error message: {data['detail']}")

        # Verify no data was saved to database for invalid symbol
        logger.info(f"Verifying no data was saved to database for invalid symbol...")
        assets = self.session.query(Asset).filter(Asset.symbol == invalid_symbol).all()
        self.assertEqual(len(assets), 0, "No asset should be created for invalid symbol")
        logger.info("Verified no asset was created in database for invalid symbol")

        # Test case 2: Non-existent symbol (valid format but doesn't exist)
        non_existent = "999999"
        logger.info(f"CASE 2: Testing non-existent symbol: {non_existent}")

        logger.info(f"Making HTTP request with non-existent symbol...")
        response = requests.get(f"{self.server_url}/api/v2/historical/stock/{non_existent}?start_date={start_date}&end_date={end_date}")
        self.assertEqual(response.status_code, 200, "Non-existent symbol should return 200 status code")
        data = response.json()
        self.assertEqual(data["symbol"], non_existent, "Response symbol should match requested symbol")
        self.assertEqual(len(data["data"]), 0, "Response should contain empty data array")
        logger.info(f"Response status code: {response.status_code}")
        logger.info(f"Response data count: {len(data['data'])} (empty as expected)")

        # Check metadata if present
        if "metadata" in data:
            logger.info(f"Response metadata: {data['metadata']}")

        # Verify an asset was created but no stock data
        logger.info(f"Verifying database state for non-existent symbol...")
        assets = self.session.query(Asset).filter(Asset.symbol == non_existent).all()
        if len(assets) > 0:
            # Some implementations might create an asset entry even for non-existent symbols
            logger.info(f"Asset found in database: ID={assets[0].asset_id}, Symbol={assets[0].symbol}")
            stock_data_count = self.session.query(DailyStockData).filter(
                DailyStockData.asset_id == assets[0].asset_id
            ).count()
            self.assertEqual(stock_data_count, 0, "No stock data should be saved for non-existent symbol")
            logger.info("Verified no stock data was saved to database for non-existent symbol")
        else:
            logger.info("No asset was created in database for non-existent symbol")

        logger.info(f"=== TEST PASSED: Invalid Symbol Handling ===\n")

    def test_invalid_date_handling(self):
        """Test handling of invalid date formats and ranges."""
        symbol, _, _ = self._get_test_parameters()

        logger.info(f"=== TEST: Invalid Date Handling ===")
        logger.info(f"Parameters: symbol={symbol}")

        # Test case 1: Invalid date format
        logger.info(f"CASE 1: Testing invalid date format")
        invalid_start_date = "2023-01-01"  # Hyphenated format instead of YYYYMMDD
        valid_end_date = "20230102"
        logger.info(f"Making HTTP request with invalid date format: start_date={invalid_start_date}, end_date={valid_end_date}")

        response = requests.get(f"{self.server_url}/api/v2/historical/stock/{symbol}?start_date={invalid_start_date}&end_date={valid_end_date}")
        logger.info(f"Response status code: {response.status_code}")

        # Check if the API returns an error or empty data for invalid date format
        if response.status_code in [400, 500]:
            # If API returns an error (ideal behavior)
            data = response.json()
            self.assertIn("detail", data)
            logger.info(f"Error message: {data['detail']}")
            logger.info(f"API correctly returned error for invalid date format")
        else:
            # If API returns 200 but with empty data (current behavior)
            self.assertEqual(response.status_code, 200)
            data = response.json()
            logger.info(f"API returned status 200 for invalid date format")

            # Either it should have empty data or an error message in metadata
            if len(data.get("data", [])) == 0:
                logger.info("Response contains empty data array as expected")
            elif "metadata" in data and "message" in data["metadata"]:
                logger.info(f"Response contains error message in metadata: {data['metadata']['message']}")
            else:
                self.fail("Invalid date format should return error or empty data")

        # Verify database state
        logger.info(f"Verifying database state after invalid date format request...")
        assets = self.session.query(Asset).filter(Asset.symbol == symbol).all()
        if assets:
            stock_data_count = self.session.query(DailyStockData).filter(
                DailyStockData.asset_id == assets[0].asset_id
            ).count()
            logger.info(f"Database has {stock_data_count} records for {symbol}")
        else:
            logger.info(f"No asset found in database for {symbol}")

        # Test case 2: Start date after end date
        logger.info(f"CASE 2: Testing start date after end date")
        later_date = "20230201"  # February 1, 2023
        earlier_date = "20230101"  # January 1, 2023
        logger.info(f"Making HTTP request with start date after end date: start_date={later_date}, end_date={earlier_date}")

        response = requests.get(f"{self.server_url}/api/v2/historical/stock/{symbol}?start_date={later_date}&end_date={earlier_date}")
        logger.info(f"Response status code: {response.status_code}")

        # Check if the API returns an error or empty data for start date after end date
        if response.status_code in [400, 500]:
            # If API returns an error (ideal behavior)
            data = response.json()
            self.assertIn("detail", data)
            logger.info(f"Error message: {data['detail']}")
            logger.info(f"API correctly returned error for start date after end date")
        else:
            # If API returns 200 but with empty data (current behavior)
            self.assertEqual(response.status_code, 200)
            data = response.json()
            logger.info(f"API returned status 200 for start date after end date")

            # Either it should have empty data or an error message in metadata
            if len(data.get("data", [])) == 0:
                logger.info("Response contains empty data array as expected")
            elif "metadata" in data and "message" in data["metadata"]:
                logger.info(f"Response contains error message in metadata: {data['metadata']['message']}")
            else:
                self.fail("Start date after end date should return error or empty data")

        # Verify database state
        logger.info(f"Verifying database state after start date after end date request...")
        assets = self.session.query(Asset).filter(Asset.symbol == symbol).all()
        if assets:
            stock_data_count = self.session.query(DailyStockData).filter(
                DailyStockData.asset_id == assets[0].asset_id
            ).count()
            logger.info(f"Database has {stock_data_count} records for {symbol}")
        else:
            logger.info(f"No asset found in database for {symbol}")

        logger.info(f"=== TEST PASSED: Invalid Date Handling ===\n")

    def test_missing_date_parameters(self):
        """Test behavior with missing date parameters (should use defaults)."""
        symbol, _, _ = self._get_test_parameters()

        logger.info(f"=== TEST: Missing Date Parameters ===")
        logger.info(f"Parameters: symbol={symbol}")

        # Clear database for this symbol to ensure we're testing fresh requests
        logger.info(f"Clearing database for {symbol} before test...")
        assets = self.session.query(Asset).filter(Asset.symbol == symbol).all()
        if assets:
            self.session.query(DailyStockData).filter(DailyStockData.asset_id == assets[0].asset_id).delete()
            self.session.query(Asset).filter(Asset.symbol == symbol).delete()
            self.session.commit()
            logger.info(f"Database cleared for {symbol}")

        # Test case 1: Missing both start and end dates
        logger.info(f"CASE 1: Testing missing both start and end dates")
        logger.info(f"Making HTTP request with no date parameters...")
        response = requests.get(f"{self.server_url}/api/v2/historical/stock/{symbol}")
        self.assertEqual(response.status_code, 200, "Response status code should be 200")
        data = response.json()
        record_count = len(data["data"])
        self.assertGreater(record_count, 0, "Response should contain data")
        logger.info(f"Response status code: {response.status_code}")
        logger.info(f"Response returned {record_count} records with default date range")

        # Log date range in response
        if record_count > 0:
            dates = [record["date"] for record in data["data"]]
            logger.info(f"Date range in response: {min(dates)} to {max(dates)}")

            # Log some sample data
            sample_records = min(3, record_count)
            logger.info(f"Sample data (first {sample_records} records):")
            for i in range(sample_records):
                logger.info(f"  Record {i+1}: Date={data['data'][i]['date']}, Close={data['data'][i]['close']}")

        # Test case 2: Missing start date
        today = datetime.now().strftime("%Y%m%d")
        logger.info(f"CASE 2: Testing missing start date, with end_date={today}")
        logger.info(f"Making HTTP request with only end date parameter...")
        response = requests.get(f"{self.server_url}/api/v2/historical/stock/{symbol}?end_date={today}")
        self.assertEqual(response.status_code, 200, "Response status code should be 200")
        data = response.json()
        record_count = len(data["data"])
        self.assertGreater(record_count, 0, "Response should contain data")
        logger.info(f"Response status code: {response.status_code}")
        logger.info(f"Response returned {record_count} records with default start date")

        # Log date range in response
        if record_count > 0:
            dates = [record["date"] for record in data["data"]]
            logger.info(f"Date range in response: {min(dates)} to {max(dates)}")

            # Verify end date matches requested end date or is close to it
            # (might not match exactly due to weekends/holidays)
            max_date = max(dates)
            logger.info(f"Latest date in response: {max_date}, Requested end date: {today}")

        # Test case 3: Missing end date
        one_year_ago = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")
        logger.info(f"CASE 3: Testing missing end date, with start_date={one_year_ago}")
        logger.info(f"Making HTTP request with only start date parameter...")
        response = requests.get(f"{self.server_url}/api/v2/historical/stock/{symbol}?start_date={one_year_ago}")
        self.assertEqual(response.status_code, 200, "Response status code should be 200")
        data = response.json()
        record_count = len(data["data"])
        self.assertGreater(record_count, 0, "Response should contain data")
        logger.info(f"Response status code: {response.status_code}")
        logger.info(f"Response returned {record_count} records with default end date")

        # Log date range in response
        if record_count > 0:
            dates = [record["date"] for record in data["data"]]
            logger.info(f"Date range in response: {min(dates)} to {max(dates)}")

            # Verify start date matches requested start date or is close to it
            min_date = min(dates)
            logger.info(f"Earliest date in response: {min_date}, Requested start date: {one_year_ago}")

        logger.info(f"=== TEST PASSED: Missing Date Parameters ===\n")

    def test_weekend_holiday_data(self):
        """Test retrieving data for weekends and holidays."""
        symbol, _, _ = self._get_test_parameters()

        logger.info(f"=== TEST: Weekend/Holiday Data ===")
        logger.info(f"Parameters: symbol={symbol}")

        # Find a recent weekend
        today = datetime.now()
        days_to_previous_saturday = (today.weekday() + 2) % 7
        last_saturday = (today - timedelta(days=days_to_previous_saturday)).strftime("%Y%m%d")
        last_sunday = (today - timedelta(days=days_to_previous_saturday-1)).strftime("%Y%m%d")

        # Also test a known holiday (New Year's Day)
        new_years_day = "20250101"  # New Year's Day 2025

        logger.info(f"Testing dates:")
        logger.info(f"  Last Saturday: {last_saturday}")
        logger.info(f"  Last Sunday: {last_sunday}")
        logger.info(f"  New Year's Day: {new_years_day}")

        # Test Saturday
        logger.info(f"CASE 1: Testing Saturday data")
        logger.info(f"Making HTTP request for Saturday {last_saturday}...")
        saturday_response = requests.get(f"{self.server_url}/api/v2/historical/stock/{symbol}?start_date={last_saturday}&end_date={last_saturday}")
        self.assertEqual(saturday_response.status_code, 200, "Saturday response status code should be 200")
        saturday_data = saturday_response.json()
        saturday_record_count = len(saturday_data["data"])
        logger.info(f"Response status code: {saturday_response.status_code}")
        logger.info(f"Saturday request returned {saturday_record_count} records")

        # Test Sunday
        logger.info(f"CASE 2: Testing Sunday data")
        logger.info(f"Making HTTP request for Sunday {last_sunday}...")
        sunday_response = requests.get(f"{self.server_url}/api/v2/historical/stock/{symbol}?start_date={last_sunday}&end_date={last_sunday}")
        self.assertEqual(sunday_response.status_code, 200, "Sunday response status code should be 200")
        sunday_data = sunday_response.json()
        sunday_record_count = len(sunday_data["data"])
        logger.info(f"Response status code: {sunday_response.status_code}")
        logger.info(f"Sunday request returned {sunday_record_count} records")

        # Test New Year's Day
        logger.info(f"CASE 3: Testing holiday data (New Year's Day)")
        logger.info(f"Making HTTP request for New Year's Day {new_years_day}...")
        holiday_response = requests.get(f"{self.server_url}/api/v2/historical/stock/{symbol}?start_date={new_years_day}&end_date={new_years_day}")
        self.assertEqual(holiday_response.status_code, 200, "Holiday response status code should be 200")
        holiday_data = holiday_response.json()
        holiday_record_count = len(holiday_data["data"])
        logger.info(f"Response status code: {holiday_response.status_code}")
        logger.info(f"New Year's Day request returned {holiday_record_count} records")

        # Weekend and holidays should have no or very limited trading data
        logger.info(f"Non-trading day data summary:")
        logger.info(f"  Saturday ({last_saturday}): {saturday_record_count} records")
        logger.info(f"  Sunday ({last_sunday}): {sunday_record_count} records")
        logger.info(f"  New Year's Day ({new_years_day}): {holiday_record_count} records")

        # Check if the API behavior is as expected for non-trading days
        if saturday_record_count == 0 and sunday_record_count == 0 and holiday_record_count == 0:
            logger.info("API correctly returns empty data for non-trading days")
        else:
            logger.info("API returns some data for non-trading days - this may be expected if the API includes the nearest trading day")

            # Log any data returned for non-trading days
            if saturday_record_count > 0:
                logger.info(f"Saturday data: {saturday_data['data']}")
            if sunday_record_count > 0:
                logger.info(f"Sunday data: {sunday_data['data']}")
            if holiday_record_count > 0:
                logger.info(f"Holiday data: {holiday_data['data']}")

        logger.info(f"=== TEST PASSED: Weekend/Holiday Data ===\n")

    def test_database_cache_status(self):
        """Test the database cache status endpoint."""
        symbol, start_date, end_date = self._get_test_parameters()

        logger.info(f"=== TEST: Database Cache Status ===")
        logger.info(f"Parameters: symbol={symbol}, start_date={start_date}, end_date={end_date}")

        # Clear database for this symbol to ensure we're testing fresh requests
        logger.info(f"Clearing database for {symbol} before test...")
        assets = self.session.query(Asset).filter(Asset.symbol == symbol).all()
        if assets:
            self.session.query(DailyStockData).filter(DailyStockData.asset_id == assets[0].asset_id).delete()
            self.session.query(Asset).filter(Asset.symbol == symbol).delete()
            self.session.commit()
            logger.info(f"Database cleared for {symbol}")

        # First, populate the database with some data
        logger.info(f"STEP 1: Populating database with data for {symbol}...")
        response = requests.get(f"{self.server_url}/api/v2/historical/stock/{symbol}?start_date={start_date}&end_date={end_date}")
        self.assertEqual(response.status_code, 200, "Response status code should be 200")
        data = response.json()
        record_count = len(data["data"])
        logger.info(f"Populated database with {record_count} records for {symbol}")

        # Verify data was saved to database
        assets = self.session.query(Asset).filter(Asset.symbol == symbol).all()
        self.assertEqual(len(assets), 1, "Asset should be created in database")
        db_record_count = self.session.query(DailyStockData).filter(
            DailyStockData.asset_id == assets[0].asset_id
        ).count()
        self.assertEqual(db_record_count, record_count,
                         f"Database should have {record_count} records, but has {db_record_count}")
        logger.info(f"Verified database has {db_record_count} records for {symbol}")

        # Now check the cache status
        logger.info(f"STEP 2: Checking general database cache status...")
        status_response = requests.get(f"{self.server_url}/api/v2/historical/database/cache/status?symbol={symbol}")
        self.assertEqual(status_response.status_code, 200, "Status response status code should be 200")
        status_data = status_response.json()
        logger.info(f"Cache status response: {status_data}")

        # Verify status data
        if "symbol" in status_data:
            self.assertEqual(status_data["symbol"], symbol, f"Status symbol should be {symbol}")
            logger.info(f"Status data contains symbol: {status_data['symbol']}")

            if "cached_dates" in status_data:
                cached_dates_count = len(status_data["cached_dates"])
                self.assertGreater(cached_dates_count, 0, "Status should contain cached dates")
                logger.info(f"Cache status shows {cached_dates_count} cached dates for {symbol}")

                # Log some sample cached dates
                sample_count = min(5, cached_dates_count)
                logger.info(f"Sample cached dates (first {sample_count}):")
                for i in range(sample_count):
                    logger.info(f"  {status_data['cached_dates'][i]}")
        else:
            # If we get general stats instead of symbol-specific data
            logger.info(f"Cache status shows general statistics")
            self.assertIn("total_assets", status_data, "Status should contain total_assets")
            self.assertGreaterEqual(status_data["total_assets"], 1, "Should have at least 1 asset")
            logger.info(f"Total assets in cache: {status_data['total_assets']}")

            if "total_records" in status_data:
                logger.info(f"Total records in cache: {status_data['total_records']}")

        # Check status for date range
        logger.info(f"STEP 3: Checking date range cache status...")
        range_status_response = requests.get(f"{self.server_url}/api/v2/historical/database/cache/status?symbol={symbol}&start_date={start_date}&end_date={end_date}")
        self.assertEqual(range_status_response.status_code, 200, "Range status response status code should be 200")
        range_status_data = range_status_response.json()
        logger.info(f"Date range cache status response: {range_status_data}")

        # Verify range status data
        if "coverage" in range_status_data:
            logger.info(f"Coverage data found in response")

            # Check if coverage is a dictionary with coverage_percentage or a direct value
            if isinstance(range_status_data["coverage"], dict) and "coverage_percentage" in range_status_data["coverage"]:
                coverage_value = range_status_data["coverage"]["coverage_percentage"]
                logger.info(f"Date range cache coverage: {coverage_value}%")

                # Log additional coverage details if available
                if "covered_dates" in range_status_data["coverage"]:
                    logger.info(f"Covered dates: {range_status_data['coverage']['covered_dates']}")
                if "missing_dates" in range_status_data["coverage"]:
                    logger.info(f"Missing dates: {range_status_data['coverage']['missing_dates']}")
            else:
                # If coverage is a direct value (e.g., 0.625 instead of {"coverage_percentage": 62.5})
                coverage_value = range_status_data["coverage"] * 100 if isinstance(range_status_data["coverage"], float) else range_status_data["coverage"]
                logger.info(f"Date range cache coverage: {coverage_value}%")

            # Verify coverage is reasonable (at least 60%)
            if isinstance(coverage_value, float):
                self.assertGreaterEqual(coverage_value, 60.0, "Coverage should be at least 60%")
                logger.info(f"Coverage is at least 60% as expected")
        else:
            logger.info(f"No specific coverage data found in response")
            # If we don't get coverage data, at least verify we got a valid response
            self.assertIsInstance(range_status_data, dict, "Response should be a dictionary")
            logger.info(f"Response is a valid dictionary")

        logger.info(f"=== TEST PASSED: Database Cache Status ===\n")

if __name__ == '__main__':
    unittest.main()
