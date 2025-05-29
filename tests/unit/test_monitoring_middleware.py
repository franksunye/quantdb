# tests/unit/test_monitoring_middleware.py
"""
Unit tests for the MonitoringMiddleware classes and decorators.
"""

import unittest
from unittest.mock import MagicMock, patch, AsyncMock
import asyncio
import sys
import os
from fastapi import Request

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.services.monitoring_middleware import RequestMonitor, monitor_stock_request


class TestRequestMonitor(unittest.TestCase):
    """Test cases for RequestMonitor."""

    def setUp(self):
        """Set up test fixtures."""
        self.db_mock = MagicMock()

    @patch('src.services.monitoring_middleware.MonitoringService')
    def test_log_stock_request_success(self, mock_monitoring_service_class):
        """Test successful stock request logging."""
        # Setup mocks
        mock_monitoring_service = MagicMock()
        mock_monitoring_service_class.return_value = mock_monitoring_service
        monitor = RequestMonitor(self.db_mock)

        # Create mock request
        mock_request = MagicMock()
        # Create a proper mock headers object that behaves like a dict
        headers_data = {
            "user-agent": "test-browser/1.0",
            "x-forwarded-for": "192.168.1.100, 10.0.0.1",
            "x-real-ip": "192.168.1.100"
        }
        mock_request.headers.get = lambda key, default="": headers_data.get(key, default)
        mock_request.client.host = "127.0.0.1"

        # Call the method
        monitor.log_stock_request(
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
            request=mock_request
        )

        # Verify MonitoringService was created and called
        mock_monitoring_service_class.assert_called_once_with(self.db_mock)

        # Verify MonitoringService was called
        mock_monitoring_service.log_request.assert_called_once_with(
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
            user_agent="test-browser/1.0",
            ip_address="192.168.1.100"
        )

    @patch('src.services.monitoring_middleware.MonitoringService')
    def test_log_stock_request_no_request(self, mock_monitoring_service_class):
        """Test stock request logging without request object."""
        # Setup mocks
        mock_monitoring_service = MagicMock()
        mock_monitoring_service_class.return_value = mock_monitoring_service
        monitor = RequestMonitor(self.db_mock)

        # Call the method without request
        monitor.log_stock_request(
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
            request=None
        )

        # Verify MonitoringService was called with empty user info
        mock_monitoring_service.log_request.assert_called_once_with(
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
            user_agent="",
            ip_address=""
        )

    @patch('src.services.monitoring_middleware.MonitoringService')
    def test_log_stock_request_ip_extraction(self, mock_monitoring_service_class):
        """Test IP address extraction from different headers."""
        # Setup mocks
        mock_monitoring_service = MagicMock()
        mock_monitoring_service_class.return_value = mock_monitoring_service
        monitor = RequestMonitor(self.db_mock)

        # Test x-forwarded-for header
        mock_request = MagicMock()
        headers_data = {"x-forwarded-for": "192.168.1.100, 10.0.0.1"}
        mock_request.headers.get = lambda key, default="": headers_data.get(key, default)
        mock_request.client.host = "127.0.0.1"

        monitor.log_stock_request(
            symbol="600000", start_date="20230101", end_date="20230102",
            endpoint="/test", response_time_ms=100, status_code=200,
            record_count=1, cache_hit=False, akshare_called=True,
            request=mock_request
        )

        # Verify IP was extracted from x-forwarded-for
        call_args = mock_monitoring_service.log_request.call_args[1]
        self.assertEqual(call_args["ip_address"], "192.168.1.100")

        # Test x-real-ip header
        headers_data = {"x-real-ip": "192.168.1.200"}
        mock_request.headers.get = lambda key, default="": headers_data.get(key, default)
        mock_monitoring_service.log_request.reset_mock()

        monitor.log_stock_request(
            symbol="600000", start_date="20230101", end_date="20230102",
            endpoint="/test", response_time_ms=100, status_code=200,
            record_count=1, cache_hit=False, akshare_called=True,
            request=mock_request
        )

        # Verify IP was extracted from x-real-ip
        call_args = mock_monitoring_service.log_request.call_args[1]
        self.assertEqual(call_args["ip_address"], "192.168.1.200")

        # Test fallback to client.host
        headers_data = {}  # Empty headers
        mock_request.headers.get = lambda key, default="": headers_data.get(key, default)
        mock_monitoring_service.log_request.reset_mock()

        monitor.log_stock_request(
            symbol="600000", start_date="20230101", end_date="20230102",
            endpoint="/test", response_time_ms=100, status_code=200,
            record_count=1, cache_hit=False, akshare_called=True,
            request=mock_request
        )

        # Verify IP was extracted from client.host
        call_args = mock_monitoring_service.log_request.call_args[1]
        self.assertEqual(call_args["ip_address"], "127.0.0.1")

    @patch('src.services.monitoring_middleware.MonitoringService')
    @patch('src.services.monitoring_middleware.logger')
    def test_log_stock_request_exception(self, mock_logger, mock_monitoring_service_class):
        """Test exception handling in stock request logging."""
        # Setup mocks
        mock_monitoring_service = MagicMock()
        mock_monitoring_service.log_request.side_effect = Exception("Database error")
        mock_monitoring_service_class.return_value = mock_monitoring_service
        monitor = RequestMonitor(self.db_mock)

        # Call the method
        monitor.log_stock_request(
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
            request=None
        )

        # Verify error was logged
        mock_logger.error.assert_called_once_with("Failed to log request: Database error")


class TestMonitorStockRequestDecorator(unittest.TestCase):
    """Test cases for monitor_stock_request decorator."""

    def setUp(self):
        """Set up test fixtures."""
        self.db_getter_mock = MagicMock()
        self.db_session_mock = MagicMock()
        self.db_getter_mock.return_value = iter([self.db_session_mock])

    @patch('src.services.monitoring_middleware.RequestMonitor')
    @patch('src.services.monitoring_middleware.time')
    def test_decorator_success(self, mock_time, mock_request_monitor_class):
        """Test successful decorator execution."""
        # Setup mocks
        mock_time.time.side_effect = [1000.0, 1000.15]  # 150ms execution time
        mock_monitor = MagicMock()
        mock_request_monitor_class.return_value = mock_monitor

        # Create test function
        @monitor_stock_request(self.db_getter_mock)
        async def test_function(symbol, start_date, end_date, request=None):
            return {
                "data": [{"date": "20230101", "price": 100}],
                "metadata": {
                    "cache_info": {
                        "cache_hit": True,
                        "akshare_called": False,
                        "cache_hit_ratio": 1.0
                    }
                }
            }

        # Run the decorated function
        result = asyncio.run(test_function(
            symbol="600000",
            start_date="20230101",
            end_date="20230102",
            request=MagicMock()
        ))

        # Verify result
        self.assertIn("data", result)
        self.assertEqual(len(result["data"]), 1)

        # Verify monitoring was called
        mock_request_monitor_class.assert_called_once_with(self.db_session_mock)
        mock_monitor.log_stock_request.assert_called_once()

        # Verify monitoring parameters
        call_args = mock_monitor.log_stock_request.call_args[1]
        self.assertEqual(call_args["symbol"], "600000")
        self.assertEqual(call_args["start_date"], "20230101")
        self.assertEqual(call_args["end_date"], "20230102")
        self.assertEqual(call_args["endpoint"], "/api/v1/historical/stock/600000")
        self.assertAlmostEqual(call_args["response_time_ms"], 150.0, places=0)
        self.assertEqual(call_args["status_code"], 200)
        self.assertEqual(call_args["record_count"], 1)
        self.assertTrue(call_args["cache_hit"])
        self.assertFalse(call_args["akshare_called"])
        self.assertEqual(call_args["cache_hit_ratio"], 1.0)

    @patch('src.services.monitoring_middleware.RequestMonitor')
    @patch('src.services.monitoring_middleware.time')
    def test_decorator_no_metadata(self, mock_time, mock_request_monitor_class):
        """Test decorator with response that has no metadata."""
        # Setup mocks
        mock_time.time.side_effect = [1000.0, 1000.1]  # 100ms execution time
        mock_monitor = MagicMock()
        mock_request_monitor_class.return_value = mock_monitor

        # Create test function
        @monitor_stock_request(self.db_getter_mock)
        async def test_function(symbol, start_date, end_date, request=None):
            return {
                "data": [{"date": "20230101"}, {"date": "20230102"}]
            }

        # Run the decorated function
        result = asyncio.run(test_function(
            symbol="000001",
            start_date="20230101",
            end_date="20230102"
        ))

        # Verify monitoring was called with defaults
        call_args = mock_monitor.log_stock_request.call_args[1]
        self.assertEqual(call_args["record_count"], 2)
        self.assertFalse(call_args["cache_hit"])
        self.assertFalse(call_args["akshare_called"])
        self.assertEqual(call_args["cache_hit_ratio"], 0.0)

    @patch('src.services.monitoring_middleware.RequestMonitor')
    @patch('src.services.monitoring_middleware.time')
    def test_decorator_exception(self, mock_time, mock_request_monitor_class):
        """Test decorator when function raises exception."""
        # Setup mocks
        mock_time.time.side_effect = [1000.0, 1000.05]  # 50ms execution time
        mock_monitor = MagicMock()
        mock_request_monitor_class.return_value = mock_monitor

        # Create test function that raises exception
        @monitor_stock_request(self.db_getter_mock)
        async def test_function(symbol, start_date, end_date, request=None):
            raise ValueError("Test error")

        # Run the decorated function and expect exception
        with self.assertRaises(ValueError):
            asyncio.run(test_function(
                symbol="600000",
                start_date="20230101",
                end_date="20230102"
            ))

        # Verify error monitoring was called
        call_args = mock_monitor.log_stock_request.call_args[1]
        self.assertEqual(call_args["status_code"], 500)
        self.assertEqual(call_args["record_count"], 0)
        self.assertFalse(call_args["cache_hit"])
        self.assertFalse(call_args["akshare_called"])


if __name__ == '__main__':
    unittest.main()
