"""
Test file specifically designed to boost QDB client.py coverage
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from qdb.client import (
    LightweightQDBClient,
    _get_service_manager,
    get_lightweight_client,
    reset_lightweight_client,
)
from qdb.exceptions import QDBError


class TestLightweightQDBClientCoverage(unittest.TestCase):
    """Test class to boost LightweightQDBClient coverage"""

    def setUp(self):
        """Set up test environment"""
        reset_lightweight_client()

    def tearDown(self):
        """Clean up after tests"""
        reset_lightweight_client()

    def test_client_initialization_with_cache_dir(self):
        """Test client initialization with cache_dir"""
        client = LightweightQDBClient(cache_dir="/tmp/test_cache")
        self.assertEqual(client._cache_dir, "/tmp/test_cache")
        self.assertIsNone(client._service_manager)

    def test_client_initialization_without_cache_dir(self):
        """Test client initialization without cache_dir"""
        client = LightweightQDBClient()
        self.assertIsNone(client._cache_dir)
        self.assertIsNone(client._service_manager)

    @patch("qdb.client._get_service_manager")
    def test_get_service_manager_lazy_init_without_cache_dir(
        self, mock_get_service_manager
    ):
        """Test lazy initialization of service manager without cache_dir"""
        mock_service_manager = Mock()
        mock_get_service_manager.return_value = mock_service_manager

        client = LightweightQDBClient()
        result = client._get_service_manager()

        self.assertEqual(result, mock_service_manager)
        self.assertEqual(client._service_manager, mock_service_manager)
        mock_get_service_manager.assert_called_once()

    @patch("core.services.get_service_manager")
    @patch("core.services.reset_service_manager")
    @patch("qdb.client._get_service_manager")
    def test_get_service_manager_lazy_init_with_cache_dir(
        self, mock_get_service_manager, mock_reset, mock_core_get
    ):
        """Test lazy initialization of service manager with cache_dir"""
        mock_service_manager = Mock()
        mock_core_get.return_value = mock_service_manager
        mock_get_service_manager.return_value = Mock()

        client = LightweightQDBClient(cache_dir="/tmp/test")
        result = client._get_service_manager()

        mock_reset.assert_called_once()
        mock_core_get.assert_called_once_with(cache_dir="/tmp/test")
        self.assertEqual(result, mock_service_manager)

    def test_get_service_manager_cached(self):
        """Test that service manager is cached after first call"""
        client = LightweightQDBClient()
        mock_service_manager = Mock()
        client._service_manager = mock_service_manager

        result = client._get_service_manager()
        self.assertEqual(result, mock_service_manager)

    @patch.object(LightweightQDBClient, "_get_service_manager")
    def test_get_stock_data_with_days(self, mock_get_service_manager):
        """Test get_stock_data with days parameter"""
        mock_service_manager = Mock()
        mock_stock_service = Mock()
        mock_stock_service.get_stock_data_by_days.return_value = {"test": "data"}
        mock_service_manager.get_stock_data_service.return_value = mock_stock_service
        mock_get_service_manager.return_value = mock_service_manager

        client = LightweightQDBClient()
        result = client.get_stock_data("000001", days=30)

        mock_stock_service.get_stock_data_by_days.assert_called_once_with(
            "000001", 30, ""
        )
        self.assertEqual(result, {"test": "data"})

    @patch.object(LightweightQDBClient, "_get_service_manager")
    def test_get_stock_data_with_date_range(self, mock_get_service_manager):
        """Test get_stock_data with date range"""
        mock_service_manager = Mock()
        mock_stock_service = Mock()
        mock_stock_service.get_stock_data.return_value = {"test": "data"}
        mock_service_manager.get_stock_data_service.return_value = mock_stock_service
        mock_get_service_manager.return_value = mock_service_manager

        client = LightweightQDBClient()
        result = client.get_stock_data(
            "000001", start_date="20240101", end_date="20240201"
        )

        mock_stock_service.get_stock_data.assert_called_once_with(
            "000001", "20240101", "20240201", ""
        )
        self.assertEqual(result, {"test": "data"})

    @patch.object(LightweightQDBClient, "_get_service_manager")
    def test_get_stock_data_exception_handling(self, mock_get_service_manager):
        """Test get_stock_data exception handling"""
        mock_get_service_manager.side_effect = Exception("Service error")

        client = LightweightQDBClient()

        with self.assertRaises(QDBError) as context:
            client.get_stock_data("000001", days=30)

        self.assertIn("Failed to get stock data", str(context.exception))

    @patch.object(LightweightQDBClient, "_get_service_manager")
    def test_get_multiple_stocks(self, mock_get_service_manager):
        """Test get_multiple_stocks method"""
        mock_service_manager = Mock()
        mock_stock_service = Mock()
        mock_stock_service.get_multiple_stocks.return_value = {
            "000001": {"test": "data"}
        }
        mock_service_manager.get_stock_data_service.return_value = mock_stock_service
        mock_get_service_manager.return_value = mock_service_manager

        client = LightweightQDBClient()
        result = client.get_multiple_stocks(["000001", "000002"], days=30, adjust="qfq")

        mock_stock_service.get_multiple_stocks.assert_called_once_with(
            ["000001", "000002"], 30, adjust="qfq"
        )
        self.assertEqual(result, {"000001": {"test": "data"}})

    @patch.object(LightweightQDBClient, "_get_service_manager")
    def test_get_multiple_stocks_exception_handling(self, mock_get_service_manager):
        """Test get_multiple_stocks exception handling"""
        mock_get_service_manager.side_effect = Exception("Service error")

        client = LightweightQDBClient()

        with self.assertRaises(QDBError) as context:
            client.get_multiple_stocks(["000001"], days=30)

        self.assertIn("Failed to get multiple stocks data", str(context.exception))

    @patch.object(LightweightQDBClient, "_get_service_manager")
    def test_get_asset_info(self, mock_get_service_manager):
        """Test get_asset_info method"""
        mock_service_manager = Mock()
        mock_asset_service = Mock()
        mock_asset_service.get_asset_info.return_value = {"name": "Test Company"}
        mock_service_manager.get_asset_info_service.return_value = mock_asset_service
        mock_get_service_manager.return_value = mock_service_manager

        client = LightweightQDBClient()
        result = client.get_asset_info("000001")

        mock_asset_service.get_asset_info.assert_called_once_with("000001")
        self.assertEqual(result, {"name": "Test Company"})

    @patch.object(LightweightQDBClient, "_get_service_manager")
    def test_get_asset_info_exception_handling(self, mock_get_service_manager):
        """Test get_asset_info exception handling"""
        mock_get_service_manager.side_effect = Exception("Service error")

        client = LightweightQDBClient()

        with self.assertRaises(QDBError) as context:
            client.get_asset_info("000001")

        self.assertIn("Failed to get asset info", str(context.exception))

    @patch.object(LightweightQDBClient, "_get_service_manager")
    def test_get_realtime_data(self, mock_get_service_manager):
        """Test get_realtime_data method"""
        mock_service_manager = Mock()
        mock_realtime_service = Mock()
        mock_realtime_service.get_realtime_data.return_value = {"current_price": 10.5}
        mock_service_manager.get_realtime_data_service.return_value = (
            mock_realtime_service
        )
        mock_get_service_manager.return_value = mock_service_manager

        client = LightweightQDBClient()
        result = client.get_realtime_data("000001")

        mock_realtime_service.get_realtime_data.assert_called_once_with("000001")
        self.assertEqual(result, {"current_price": 10.5})

    @patch.object(LightweightQDBClient, "_get_service_manager")
    def test_get_realtime_data_exception_handling(self, mock_get_service_manager):
        """Test get_realtime_data exception handling"""
        mock_get_service_manager.side_effect = Exception("Service error")

        client = LightweightQDBClient()

        with self.assertRaises(QDBError) as context:
            client.get_realtime_data("000001")

        self.assertIn("Failed to get realtime data", str(context.exception))

    @patch.object(LightweightQDBClient, "_get_service_manager")
    def test_get_realtime_data_batch(self, mock_get_service_manager):
        """Test get_realtime_data_batch method"""
        mock_service_manager = Mock()
        mock_realtime_service = Mock()
        mock_realtime_service.get_realtime_data_batch.return_value = {
            "000001": {"current_price": 10.5}
        }
        mock_service_manager.get_realtime_data_service.return_value = (
            mock_realtime_service
        )
        mock_get_service_manager.return_value = mock_service_manager

        client = LightweightQDBClient()
        result = client.get_realtime_data_batch(["000001", "000002"])

        mock_realtime_service.get_realtime_data_batch.assert_called_once_with(
            ["000001", "000002"]
        )
        self.assertEqual(result, {"000001": {"current_price": 10.5}})

    @patch.object(LightweightQDBClient, "_get_service_manager")
    def test_get_realtime_data_batch_exception_handling(self, mock_get_service_manager):
        """Test get_realtime_data_batch exception handling"""
        mock_get_service_manager.side_effect = Exception("Service error")

        client = LightweightQDBClient()

        with self.assertRaises(QDBError) as context:
            client.get_realtime_data_batch(["000001"])

        self.assertIn("Failed to get batch realtime data", str(context.exception))

    @patch.object(LightweightQDBClient, "_get_service_manager")
    def test_get_stock_list(self, mock_get_service_manager):
        """Test get_stock_list method"""
        mock_service_manager = Mock()
        mock_stock_service = Mock()
        mock_stock_service.get_stock_list.return_value = [
            {"symbol": "000001", "name": "Test"}
        ]
        mock_service_manager.get_stock_data_service.return_value = mock_stock_service
        mock_get_service_manager.return_value = mock_service_manager

        client = LightweightQDBClient()
        result = client.get_stock_list("A")

        mock_stock_service.get_stock_list.assert_called_once_with("A")
        self.assertEqual(result, [{"symbol": "000001", "name": "Test"}])

    @patch.object(LightweightQDBClient, "_get_service_manager")
    def test_get_stock_list_exception_handling(self, mock_get_service_manager):
        """Test get_stock_list exception handling"""
        mock_get_service_manager.side_effect = Exception("Service error")

        client = LightweightQDBClient()

        with self.assertRaises(QDBError) as context:
            client.get_stock_list("A")

        self.assertIn("Failed to get stock list", str(context.exception))

    @patch.object(LightweightQDBClient, "_get_service_manager")
    def test_cache_stats(self, mock_get_service_manager):
        """Test cache_stats method"""
        mock_service_manager = Mock()
        mock_service_manager.get_cache_stats.return_value = {"hit_rate": 85.5}
        mock_get_service_manager.return_value = mock_service_manager

        client = LightweightQDBClient()
        result = client.cache_stats()

        mock_service_manager.get_cache_stats.assert_called_once()
        self.assertEqual(result, {"hit_rate": 85.5})

    @patch.object(LightweightQDBClient, "_get_service_manager")
    def test_cache_stats_exception_handling(self, mock_get_service_manager):
        """Test cache_stats exception handling"""
        mock_get_service_manager.side_effect = Exception("Service error")

        client = LightweightQDBClient()

        with self.assertRaises(QDBError) as context:
            client.cache_stats()

        self.assertIn("Failed to get cache stats", str(context.exception))

    @patch.object(LightweightQDBClient, "_get_service_manager")
    def test_clear_cache(self, mock_get_service_manager):
        """Test clear_cache method"""
        mock_service_manager = Mock()
        mock_get_service_manager.return_value = mock_service_manager

        client = LightweightQDBClient()
        client.clear_cache("000001")

        mock_service_manager.clear_cache.assert_called_once_with("000001")

    @patch.object(LightweightQDBClient, "_get_service_manager")
    def test_clear_cache_exception_handling(self, mock_get_service_manager):
        """Test clear_cache exception handling"""
        mock_get_service_manager.side_effect = Exception("Service error")

        client = LightweightQDBClient()

        with self.assertRaises(QDBError) as context:
            client.clear_cache("000001")

        self.assertIn("Failed to clear cache", str(context.exception))

    @patch.object(LightweightQDBClient, "_get_service_manager")
    def test_stock_zh_a_hist(self, mock_get_service_manager):
        """Test stock_zh_a_hist method"""
        mock_service_manager = Mock()
        mock_stock_service = Mock()
        mock_stock_service.stock_zh_a_hist.return_value = {"test": "hist_data"}
        mock_service_manager.get_stock_data_service.return_value = mock_stock_service
        mock_get_service_manager.return_value = mock_service_manager

        client = LightweightQDBClient()
        result = client.stock_zh_a_hist(
            "000001", "daily", "20240101", "20240201", "qfq"
        )

        mock_stock_service.stock_zh_a_hist.assert_called_once_with(
            "000001", "daily", "20240101", "20240201", "qfq"
        )
        self.assertEqual(result, {"test": "hist_data"})

    @patch.object(LightweightQDBClient, "_get_service_manager")
    def test_stock_zh_a_hist_exception_handling(self, mock_get_service_manager):
        """Test stock_zh_a_hist exception handling"""
        mock_get_service_manager.side_effect = Exception("Service error")

        client = LightweightQDBClient()

        with self.assertRaises(QDBError) as context:
            client.stock_zh_a_hist("000001")

        self.assertIn("Failed to get stock data", str(context.exception))


class TestGlobalClientFunctions(unittest.TestCase):
    """Test global client management functions"""

    def setUp(self):
        """Set up test environment"""
        reset_lightweight_client()

    def tearDown(self):
        """Clean up after tests"""
        reset_lightweight_client()

    def test_get_lightweight_client_first_call(self):
        """Test get_lightweight_client creates new instance on first call"""
        client = get_lightweight_client()
        self.assertIsInstance(client, LightweightQDBClient)

    def test_get_lightweight_client_cached(self):
        """Test get_lightweight_client returns cached instance"""
        client1 = get_lightweight_client()
        client2 = get_lightweight_client()
        self.assertIs(client1, client2)

    def test_get_lightweight_client_with_cache_dir(self):
        """Test get_lightweight_client with cache_dir"""
        client = get_lightweight_client(cache_dir="/tmp/test")
        self.assertEqual(client._cache_dir, "/tmp/test")

    def test_reset_lightweight_client(self):
        """Test reset_lightweight_client clears global instance"""
        client1 = get_lightweight_client()
        reset_lightweight_client()
        client2 = get_lightweight_client()
        self.assertIsNot(client1, client2)


class TestServiceManagerFunction(unittest.TestCase):
    """Test _get_service_manager function"""

    @patch("core.services.get_service_manager")
    def test_get_service_manager_success(self, mock_get_service_manager):
        """Test successful service manager import"""
        mock_service_manager = Mock()
        mock_get_service_manager.return_value = mock_service_manager

        result = _get_service_manager()
        self.assertEqual(result, mock_service_manager)

    @patch("core.services.get_service_manager")
    def test_get_service_manager_import_error(self, mock_get_service_manager):
        """Test ImportError handling in _get_service_manager"""
        mock_get_service_manager.side_effect = ImportError("Module not found")

        with self.assertRaises(QDBError) as context:
            _get_service_manager()

        self.assertIn("Failed to import core services", str(context.exception))


if __name__ == "__main__":
    unittest.main()
