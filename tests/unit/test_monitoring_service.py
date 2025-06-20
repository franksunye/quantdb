# tests/unit/test_monitoring_service.py
"""
Unit tests for the MonitoringService class.
"""

import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from core.services.monitoring_service import MonitoringService
from core.models import RequestLog, DataCoverage, SystemMetrics, DailyStockData, Asset


class TestMonitoringService(unittest.TestCase):
    """Test cases for MonitoringService."""

    def setUp(self):
        """Set up test fixtures."""
        self.db_mock = MagicMock()
        self.service = MonitoringService(self.db_mock)

    def test_log_request_success(self):
        """Test successful request logging."""
        # Call the method
        self.service.log_request(
            symbol="600000",
            start_date="20230101",
            end_date="20230102",
            endpoint="/api/v1/historical/stock/600000",
            response_time_ms=150.5,
            status_code=200,
            record_count=2,
            cache_hit=True,
            akshare_called=False,
            cache_hit_ratio=1.0,
            user_agent="test-agent",
            ip_address="127.0.0.1"
        )

        # Verify database operations
        self.db_mock.add.assert_called_once()
        self.db_mock.commit.assert_called()

        # Verify the RequestLog object was created correctly
        added_log = self.db_mock.add.call_args[0][0]
        self.assertIsInstance(added_log, RequestLog)
        self.assertEqual(added_log.symbol, "600000")
        self.assertEqual(added_log.start_date, "20230101")
        self.assertEqual(added_log.end_date, "20230102")
        self.assertEqual(added_log.endpoint, "/api/v1/historical/stock/600000")
        self.assertEqual(added_log.response_time_ms, 150.5)
        self.assertEqual(added_log.status_code, 200)
        self.assertEqual(added_log.record_count, 2)
        self.assertTrue(added_log.cache_hit)
        self.assertFalse(added_log.akshare_called)
        self.assertEqual(added_log.cache_hit_ratio, 1.0)
        self.assertEqual(added_log.user_agent, "test-agent")
        self.assertEqual(added_log.ip_address, "127.0.0.1")

    def test_log_request_with_defaults(self):
        """Test request logging with default values."""
        # Call the method with minimal parameters
        self.service.log_request(
            symbol="000001",
            start_date="20230101",
            end_date="20230102",
            endpoint="/api/v1/historical/stock/000001",
            response_time_ms=200.0,
            status_code=200,
            record_count=5,
            cache_hit=False,
            akshare_called=True
        )

        # Verify database operations
        self.db_mock.add.assert_called_once()
        self.db_mock.commit.assert_called()

        # Verify the RequestLog object was created with defaults
        added_log = self.db_mock.add.call_args[0][0]
        self.assertEqual(added_log.cache_hit_ratio, 0.0)
        self.assertEqual(added_log.user_agent, "")
        self.assertEqual(added_log.ip_address, "")

    @patch('core.services.monitoring_service.func')
    def test_update_data_coverage_new_symbol(self, mock_func):
        """Test updating data coverage for a new symbol."""
        # Setup mocks
        mock_stats = MagicMock()
        mock_stats.earliest = datetime(2023, 1, 1).date()
        mock_stats.latest = datetime(2023, 1, 5).date()
        mock_stats.total = 5

        # Mock the join query chain
        self.db_mock.query.return_value.join.return_value.filter.return_value.first.return_value = mock_stats

        # Mock the coverage query
        self.db_mock.query.return_value.filter.return_value.first.return_value = None

        # Call the method
        self.service._update_data_coverage("600000")

        # Verify database operations
        self.assertEqual(self.db_mock.add.call_count, 1)
        self.db_mock.commit.assert_called()

        # Verify the DataCoverage object was created
        added_coverage = self.db_mock.add.call_args[0][0]
        self.assertIsInstance(added_coverage, DataCoverage)
        self.assertEqual(added_coverage.symbol, "600000")
        self.assertEqual(added_coverage.access_count, 1)
        self.assertEqual(added_coverage.earliest_date, "20230101")
        self.assertEqual(added_coverage.latest_date, "20230105")
        self.assertEqual(added_coverage.total_records, 5)

    @patch('core.services.monitoring_service.func')
    def test_update_data_coverage_existing_symbol(self, mock_func):
        """Test updating data coverage for an existing symbol."""
        # Setup mocks
        mock_stats = MagicMock()
        mock_stats.earliest = datetime(2023, 1, 1).date()
        mock_stats.latest = datetime(2023, 1, 10).date()
        mock_stats.total = 10

        mock_existing_coverage = MagicMock()
        mock_existing_coverage.access_count = 5

        # Mock the join query chain for data stats
        self.db_mock.query.return_value.join.return_value.filter.return_value.first.return_value = mock_stats

        # Mock the coverage query to return existing coverage
        self.db_mock.query.return_value.filter.return_value.first.return_value = mock_existing_coverage

        # Call the method
        self.service._update_data_coverage("600000")

        # Verify database operations
        self.db_mock.add.assert_not_called()  # Should not add new record
        self.db_mock.commit.assert_called()

        # Verify the existing coverage was updated
        self.assertEqual(mock_existing_coverage.access_count, 6)
        self.assertEqual(mock_existing_coverage.earliest_date, "20230101")
        self.assertEqual(mock_existing_coverage.latest_date, "20230110")
        self.assertEqual(mock_existing_coverage.total_records, 10)

    @patch('core.services.monitoring_service.func')
    def test_update_data_coverage_no_data(self, mock_func):
        """Test updating data coverage when no data exists."""
        # Setup mocks - no data found
        mock_stats = MagicMock()
        mock_stats.total = 0

        # Mock the join query chain for data stats
        self.db_mock.query.return_value.join.return_value.filter.return_value.first.return_value = mock_stats

        # Call the method
        self.service._update_data_coverage("600000")

        # Verify no database operations were performed
        self.db_mock.add.assert_not_called()
        self.db_mock.commit.assert_not_called()

    @patch('core.services.monitoring_service.func')
    @patch('core.services.monitoring_service.datetime')
    def test_get_water_pool_status(self, mock_datetime, mock_func):
        """Test getting water pool status."""
        # Setup mocks
        mock_now = datetime(2023, 1, 15, 10, 30, 0)
        mock_datetime.now.return_value = mock_now
        mock_datetime.combine = datetime.combine
        mock_datetime.min = datetime.min

        # Mock database queries - create separate mocks for each query
        mock_query1 = MagicMock()
        mock_query1.scalar.return_value = 5  # total_symbols

        mock_query2 = MagicMock()
        mock_query2.scalar.return_value = 1000  # total_records

        mock_query3 = MagicMock()
        mock_query3.filter.return_value.scalar.return_value = 50  # today_requests

        mock_query4 = MagicMock()
        mock_query4.filter.return_value.scalar.return_value = 10  # today_akshare_calls

        mock_query5 = MagicMock()
        mock_query5.filter.return_value.scalar.return_value = 40  # today_cache_hits

        mock_query6 = MagicMock()
        mock_query6.filter.return_value.scalar.return_value = 125.5  # avg_response_time

        # Set up the query mock to return different objects for different calls
        self.db_mock.query.side_effect = [
            mock_query1, mock_query2, mock_query3, mock_query4, mock_query5, mock_query6, self.db_mock.query.return_value
        ]

        # Mock hot stocks query
        mock_hot_stock = MagicMock()
        mock_hot_stock.symbol = "600000"
        mock_hot_stock.requests = 15
        
        self.db_mock.query.return_value.filter.return_value.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = [
            mock_hot_stock
        ]

        # Call the method
        result = self.service.get_water_pool_status()

        # Verify result structure
        self.assertIn("timestamp", result)
        self.assertIn("water_pool", result)
        self.assertIn("today_performance", result)
        self.assertIn("hot_stocks", result)

        # Verify water pool data
        water_pool = result["water_pool"]
        self.assertEqual(water_pool["total_symbols"], 5)
        self.assertEqual(water_pool["total_records"], 1000)

        # Verify today performance data
        today_perf = result["today_performance"]
        self.assertEqual(today_perf["total_requests"], 50)
        self.assertEqual(today_perf["akshare_calls"], 10)
        self.assertEqual(today_perf["cache_hits"], 40)
        self.assertEqual(today_perf["cache_hit_rate"], "80.0%")
        self.assertEqual(today_perf["avg_response_time_ms"], "125.5")

        # Verify hot stocks
        hot_stocks = result["hot_stocks"]
        self.assertEqual(len(hot_stocks), 1)
        self.assertEqual(hot_stocks[0]["symbol"], "600000")
        self.assertEqual(hot_stocks[0]["requests"], 15)

    def test_get_detailed_coverage(self):
        """Test getting detailed coverage information."""
        # Setup mock coverage data
        mock_coverage1 = MagicMock()
        mock_coverage1.symbol = "600000"
        mock_coverage1.earliest_date = "20230101"
        mock_coverage1.latest_date = "20230110"
        mock_coverage1.total_records = 10
        mock_coverage1.access_count = 25
        mock_coverage1.first_requested = datetime(2023, 1, 1, 9, 0, 0)
        mock_coverage1.last_accessed = datetime(2023, 1, 15, 14, 30, 0)

        mock_coverage2 = MagicMock()
        mock_coverage2.symbol = "000001"
        mock_coverage2.earliest_date = "20230105"
        mock_coverage2.latest_date = "20230115"
        mock_coverage2.total_records = 11
        mock_coverage2.access_count = 15
        mock_coverage2.first_requested = datetime(2023, 1, 5, 10, 0, 0)
        mock_coverage2.last_accessed = datetime(2023, 1, 15, 16, 0, 0)

        self.db_mock.query.return_value.order_by.return_value.limit.return_value.all.return_value = [
            mock_coverage1, mock_coverage2
        ]

        # Call the method
        result = self.service.get_detailed_coverage()

        # Verify result
        self.assertEqual(len(result), 2)
        
        # Check first coverage
        coverage1 = result[0]
        self.assertEqual(coverage1["symbol"], "600000")
        self.assertEqual(coverage1["data_range"], "20230101 ~ 20230110")
        self.assertEqual(coverage1["span_days"], 10)
        self.assertEqual(coverage1["total_records"], 10)
        self.assertEqual(coverage1["access_count"], 25)
        self.assertEqual(coverage1["first_requested"], "2023-01-01 09:00")
        self.assertEqual(coverage1["last_accessed"], "2023-01-15 14:30")

        # Check second coverage
        coverage2 = result[1]
        self.assertEqual(coverage2["symbol"], "000001")
        self.assertEqual(coverage2["span_days"], 11)

    def test_get_detailed_coverage_empty(self):
        """Test getting detailed coverage when no data exists."""
        # Setup empty result
        self.db_mock.query.return_value.order_by.return_value.limit.return_value.all.return_value = []

        # Call the method
        result = self.service.get_detailed_coverage()

        # Verify empty result
        self.assertEqual(len(result), 0)
        self.assertIsInstance(result, list)

    def test_get_detailed_coverage_no_dates(self):
        """Test getting detailed coverage with missing date information."""
        # Setup mock coverage with no dates
        mock_coverage = MagicMock()
        mock_coverage.symbol = "600000"
        mock_coverage.earliest_date = None
        mock_coverage.latest_date = None
        mock_coverage.total_records = 0
        mock_coverage.access_count = 1
        mock_coverage.first_requested = None
        mock_coverage.last_accessed = None

        self.db_mock.query.return_value.order_by.return_value.limit.return_value.all.return_value = [
            mock_coverage
        ]

        # Call the method
        result = self.service.get_detailed_coverage()

        # Verify result
        self.assertEqual(len(result), 1)
        coverage = result[0]
        self.assertEqual(coverage["symbol"], "600000")
        self.assertEqual(coverage["span_days"], 0)
        self.assertEqual(coverage["first_requested"], "")
        self.assertEqual(coverage["last_accessed"], "")

    @patch('core.services.monitoring_service.datetime')
    @patch('core.services.monitoring_service.timedelta')
    @patch('core.services.monitoring_service.func')
    def test_get_performance_trends(self, mock_func, mock_timedelta, mock_datetime):
        """Test getting performance trends."""
        # Setup mocks
        mock_now = datetime(2023, 1, 15, 10, 30, 0)
        mock_datetime.now.return_value = mock_now
        mock_timedelta.return_value = timedelta(days=7)

        # Mock daily stats
        mock_stat1 = MagicMock()
        mock_stat1.date = datetime(2023, 1, 10).date()
        mock_stat1.total_requests = 100
        mock_stat1.akshare_calls = 20
        mock_stat1.avg_response_time = 150.0
        mock_stat1.active_symbols = 10

        mock_stat2 = MagicMock()
        mock_stat2.date = datetime(2023, 1, 11).date()
        mock_stat2.total_requests = 120
        mock_stat2.akshare_calls = 15
        mock_stat2.avg_response_time = 140.0
        mock_stat2.active_symbols = 12

        self.db_mock.query.return_value.filter.return_value.group_by.return_value.order_by.return_value.all.return_value = [
            mock_stat1, mock_stat2
        ]

        # Call the method
        result = self.service.get_performance_trends(days=7)

        # Verify result structure
        self.assertIn("period", result)
        self.assertIn("trends", result)
        self.assertEqual(result["period"], "最近 7 天")

        # Verify trends data
        trends = result["trends"]
        self.assertEqual(len(trends), 2)

        # Check first trend
        trend1 = trends[0]
        self.assertEqual(trend1["date"], "2023-01-10")
        self.assertEqual(trend1["total_requests"], 100)
        self.assertEqual(trend1["akshare_calls"], 20)
        self.assertEqual(trend1["cache_hit_rate"], "80.0%")
        self.assertEqual(trend1["avg_response_time_ms"], "150.0")
        self.assertEqual(trend1["active_symbols"], 10)
        self.assertEqual(trend1["efficiency"], "节省 80 次调用")

        # Check second trend
        trend2 = trends[1]
        self.assertEqual(trend2["date"], "2023-01-11")
        self.assertEqual(trend2["cache_hit_rate"], "87.5%")
        self.assertEqual(trend2["efficiency"], "节省 105 次调用")

    def test_get_performance_trends_empty(self):
        """Test getting performance trends with no data."""
        # Setup empty result
        self.db_mock.query.return_value.filter.return_value.group_by.return_value.order_by.return_value.all.return_value = []

        # Call the method
        result = self.service.get_performance_trends(days=7)

        # Verify result
        self.assertEqual(result["period"], "最近 7 天")
        self.assertEqual(len(result["trends"]), 0)

    def test_get_performance_trends_zero_requests(self):
        """Test getting performance trends with zero requests."""
        # Mock daily stats with zero requests
        mock_stat = MagicMock()
        mock_stat.date = datetime(2023, 1, 10).date()
        mock_stat.total_requests = 0
        mock_stat.akshare_calls = 0
        mock_stat.avg_response_time = 0.0
        mock_stat.active_symbols = 0

        self.db_mock.query.return_value.filter.return_value.group_by.return_value.order_by.return_value.all.return_value = [
            mock_stat
        ]

        # Call the method
        result = self.service.get_performance_trends(days=1)

        # Verify result
        trends = result["trends"]
        self.assertEqual(len(trends), 1)
        trend = trends[0]
        self.assertEqual(trend["cache_hit_rate"], "0.0%")
        self.assertEqual(trend["efficiency"], "节省 0 次调用")


if __name__ == '__main__':
    unittest.main()
