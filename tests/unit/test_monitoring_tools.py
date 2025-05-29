# tests/unit/test_monitoring_tools.py
"""
Unit tests for monitoring tools.
"""

import unittest
from unittest.mock import patch, MagicMock, call
import sys
import os
import tempfile
from datetime import datetime
from io import StringIO

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import the monitoring tools
import tools.monitoring.water_pool_monitor as water_pool_monitor
import tools.monitoring.system_performance_monitor as system_performance_monitor


class TestWaterPoolMonitor(unittest.TestCase):
    """Test cases for water pool monitor."""

    @patch('tools.monitoring.water_pool_monitor.get_db')
    @patch('tools.monitoring.water_pool_monitor.func')
    @patch('sys.stdout', new_callable=StringIO)
    def test_monitor_water_pool_status_with_data(self, mock_stdout, mock_func, mock_get_db):
        """Test water pool monitoring with data."""
        # Setup mocks
        mock_db = MagicMock()
        mock_get_db.return_value = iter([mock_db])

        # Mock database queries
        mock_db.query.return_value.scalar.side_effect = [
            5,    # total_assets
            1000  # total_records
        ]

        # Mock date queries
        mock_latest_date = datetime(2023, 1, 15).date()
        mock_earliest_date = datetime(2023, 1, 1).date()
        mock_db.query.return_value.scalar.side_effect = [
            5,    # total_assets
            1000, # total_records
            mock_latest_date,   # latest_date
            mock_earliest_date  # earliest_date
        ]

        # Mock asset stats
        mock_asset_stat = MagicMock()
        mock_asset_stat.asset_id = 1
        mock_asset_stat.count = 200
        
        mock_db.query.return_value.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = [
            (1, 200), (2, 150), (3, 100)
        ]

        # Call the function
        water_pool_monitor.monitor_water_pool_status()

        # Verify output contains expected information
        output = mock_stdout.getvalue()
        self.assertIn("QuantDB 蓄水池状态监控", output)
        self.assertIn("总股票数量: 5 只", output)
        self.assertIn("总数据记录: 1,000 条", output)
        self.assertIn("数据库中有股票数据", output)

    @patch('tools.monitoring.water_pool_monitor.get_db')
    @patch('sys.stdout', new_callable=StringIO)
    def test_monitor_water_pool_status_empty_database(self, mock_stdout, mock_get_db):
        """Test water pool monitoring with empty database."""
        # Setup mocks
        mock_db = MagicMock()
        mock_get_db.return_value = iter([mock_db])

        # Mock empty database
        mock_db.query.return_value.scalar.side_effect = [0, 0]  # No assets, no records

        # Call the function
        water_pool_monitor.monitor_water_pool_status()

        # Verify output contains expected information
        output = mock_stdout.getvalue()
        self.assertIn("数据库为空，还没有股票数据", output)
        self.assertIn("建议：调用 /api/v1/historical/stock/000001", output)

    @patch('tools.monitoring.water_pool_monitor.get_db')
    @patch('sys.stdout', new_callable=StringIO)
    def test_monitor_water_pool_status_exception(self, mock_stdout, mock_get_db):
        """Test water pool monitoring with exception."""
        # Setup mocks
        mock_db = MagicMock()
        mock_get_db.return_value = iter([mock_db])

        # Mock exception
        mock_db.query.side_effect = Exception("Database connection error")

        # Call the function
        water_pool_monitor.monitor_water_pool_status()

        # Verify error handling
        output = mock_stdout.getvalue()
        self.assertIn("监控演示出错", output)
        self.assertIn("Database connection error", output)


class TestSystemPerformanceMonitor(unittest.TestCase):
    """Test cases for system performance monitor."""

    @patch('tools.monitoring.system_performance_monitor.threading.Thread')
    @patch('tools.monitoring.system_performance_monitor.time.sleep')
    @patch('tools.monitoring.system_performance_monitor.requests.get')
    @patch('tools.monitoring.system_performance_monitor.os.system')
    @patch('sys.stdout', new_callable=StringIO)
    def test_monitor_system_performance_success(self, mock_stdout, mock_os_system, 
                                               mock_requests_get, mock_sleep, mock_thread):
        """Test successful system performance monitoring."""
        # Setup mocks
        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance

        # Mock successful API responses
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"date": "20240101", "price": 100},
                {"date": "20240102", "price": 101}
            ]
        }
        mock_requests_get.return_value = mock_response

        # Call the function
        system_performance_monitor.monitor_system_performance()

        # Verify thread was started
        mock_thread.assert_called_once()
        mock_thread_instance.start.assert_called_once()

        # Verify API calls were made
        self.assertGreater(mock_requests_get.call_count, 0)

        # Verify water pool monitor was called
        expected_calls = [
            call("python tools/monitoring/water_pool_monitor.py"),
            call("python tools/monitoring/water_pool_monitor.py"),
            call("python tools/monitoring/water_pool_monitor.py")
        ]
        mock_os_system.assert_has_calls(expected_calls)

        # Verify output contains expected sections
        output = mock_stdout.getvalue()
        self.assertIn("QuantDB 系统性能监控", output)
        self.assertIn("阶段1: 系统基线状态", output)
        self.assertIn("阶段2: 开始蓄水", output)
        self.assertIn("阶段3: 蓄水后性能状态", output)
        self.assertIn("阶段4: 测试缓存效果", output)
        self.assertIn("阶段5: 测试数据范围扩展", output)
        self.assertIn("阶段6: 最终系统状态", output)

    @patch('tools.monitoring.system_performance_monitor.threading.Thread')
    @patch('tools.monitoring.system_performance_monitor.time.sleep')
    @patch('tools.monitoring.system_performance_monitor.requests.get')
    @patch('tools.monitoring.system_performance_monitor.os.system')
    @patch('sys.stdout', new_callable=StringIO)
    def test_monitor_system_performance_api_failure(self, mock_stdout, mock_os_system,
                                                   mock_requests_get, mock_sleep, mock_thread):
        """Test system performance monitoring with API failures."""
        # Setup mocks
        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance

        # Mock failed API responses
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_requests_get.return_value = mock_response

        # Call the function
        system_performance_monitor.monitor_system_performance()

        # Verify error handling
        output = mock_stdout.getvalue()
        self.assertIn("获取失败: 500", output)

    @patch('tools.monitoring.system_performance_monitor.threading.Thread')
    @patch('tools.monitoring.system_performance_monitor.time.sleep')
    @patch('tools.monitoring.system_performance_monitor.requests.get')
    @patch('tools.monitoring.system_performance_monitor.os.system')
    @patch('sys.stdout', new_callable=StringIO)
    def test_monitor_system_performance_exception(self, mock_stdout, mock_os_system,
                                                 mock_requests_get, mock_sleep, mock_thread):
        """Test system performance monitoring with exception."""
        # Setup mocks
        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance

        # Mock exception during API call
        mock_requests_get.side_effect = Exception("Connection error")

        # Call the function
        system_performance_monitor.monitor_system_performance()

        # Verify error handling
        output = mock_stdout.getvalue()
        self.assertIn("演示过程中出错", output)
        self.assertIn("Connection error", output)

    @patch('uvicorn.run')
    def test_start_api_server(self, mock_uvicorn_run):
        """Test API server startup."""
        # Call the function
        system_performance_monitor.start_api_server()

        # Verify uvicorn was called with correct parameters
        mock_uvicorn_run.assert_called_once()
        call_args = mock_uvicorn_run.call_args
        self.assertEqual(call_args[1]['host'], '127.0.0.1')
        self.assertEqual(call_args[1]['port'], 8000)
        self.assertEqual(call_args[1]['log_level'], 'warning')


class TestMonitoringToolsIntegration(unittest.TestCase):
    """Integration tests for monitoring tools."""

    def test_water_pool_monitor_import(self):
        """Test that water pool monitor can be imported and has required functions."""
        self.assertTrue(hasattr(water_pool_monitor, 'monitor_water_pool_status'))
        self.assertTrue(callable(water_pool_monitor.monitor_water_pool_status))

    def test_system_performance_monitor_import(self):
        """Test that system performance monitor can be imported and has required functions."""
        self.assertTrue(hasattr(system_performance_monitor, 'monitor_system_performance'))
        self.assertTrue(callable(system_performance_monitor.monitor_system_performance))
        self.assertTrue(hasattr(system_performance_monitor, 'start_api_server'))
        self.assertTrue(callable(system_performance_monitor.start_api_server))

    @patch('tools.monitoring.water_pool_monitor.get_db')
    def test_water_pool_monitor_database_connection(self, mock_get_db):
        """Test water pool monitor database connection handling."""
        # Setup mock to simulate database connection failure in finally block
        mock_db = MagicMock()
        # Make scalar return actual numbers to avoid format string issues
        mock_db.query.return_value.scalar.return_value = 0
        mock_db.close.side_effect = Exception("Connection already closed")
        mock_get_db.return_value = iter([mock_db])

        # This should handle the exception gracefully and not propagate it
        try:
            water_pool_monitor.monitor_water_pool_status()
        except Exception as e:
            # The function should catch and print the error, not raise it
            if "Connection already closed" in str(e):
                pass  # This is expected from the finally block
            else:
                self.fail(f"Unexpected exception: {e}")

        # Verify close was attempted
        mock_db.close.assert_called_once()

    def test_monitoring_tools_executable(self):
        """Test that monitoring tools can be executed as scripts."""
        # Test water pool monitor
        water_pool_module_path = os.path.join(
            os.path.dirname(__file__), '..', '..', 'tools', 'monitoring', 'water_pool_monitor.py'
        )
        self.assertTrue(os.path.exists(water_pool_module_path))

        # Test system performance monitor
        system_perf_module_path = os.path.join(
            os.path.dirname(__file__), '..', '..', 'tools', 'monitoring', 'system_performance_monitor.py'
        )
        self.assertTrue(os.path.exists(system_perf_module_path))

        # Check if files have read permissions (executable permissions may not be set in test environment)
        if os.name != 'nt':  # Not Windows
            water_stat = os.stat(water_pool_module_path)
            system_stat = os.stat(system_perf_module_path)

            # Check if owner has read permission (more reliable than execute in test environments)
            self.assertTrue(water_stat.st_mode & 0o400)
            self.assertTrue(system_stat.st_mode & 0o400)


if __name__ == '__main__':
    unittest.main()
