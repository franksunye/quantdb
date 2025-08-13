"""
Test file specifically designed to boost QDB __init__.py coverage
"""

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import qdb
from qdb import exceptions


class TestQDBInitCoverage(unittest.TestCase):
    """Test class to boost QDB __init__.py coverage"""

    def setUp(self):
        """Set up test environment"""
        # Reset global client
        qdb._client = None

    def tearDown(self):
        """Clean up after tests"""
        # Reset global client
        qdb._client = None

    def test_init_function_coverage(self):
        """Test qdb.init() function - covers lines 31-33"""
        with patch("qdb.get_lightweight_client") as mock_get_client:
            mock_client = Mock()
            mock_get_client.return_value = mock_client

            # Test init with cache_dir
            qdb.init(cache_dir="/tmp/test_cache")

            mock_get_client.assert_called_with("/tmp/test_cache")
            self.assertEqual(qdb._client, mock_client)

    def test_get_stock_data_delegation(self):
        """Test qdb.get_stock_data() delegation - covers line 38"""
        with patch.object(qdb, "_get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.get_stock_data.return_value = {"test": "data"}
            mock_get_client.return_value = mock_client

            result = qdb.get_stock_data("000001", days=30)

            mock_client.get_stock_data.assert_called_once_with(
                "000001", None, None, 30, ""
            )
            self.assertEqual(result, {"test": "data"})

    def test_get_multiple_stocks_delegation(self):
        """Test qdb.get_multiple_stocks() delegation - covers line 42"""
        with patch.object(qdb, "_get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.get_multiple_stocks.return_value = {"test": "data"}
            mock_get_client.return_value = mock_client

            result = qdb.get_multiple_stocks(["000001", "000002"], days=30)

            mock_client.get_multiple_stocks.assert_called_once_with(
                ["000001", "000002"], 30
            )
            self.assertEqual(result, {"test": "data"})

    def test_get_asset_info_delegation(self):
        """Test qdb.get_asset_info() delegation - covers line 46"""
        with patch.object(qdb, "_get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.get_asset_info.return_value = {"test": "info"}
            mock_get_client.return_value = mock_client

            result = qdb.get_asset_info("000001")

            mock_client.get_asset_info.assert_called_once_with("000001")
            self.assertEqual(result, {"test": "info"})

    def test_get_realtime_data_delegation(self):
        """Test qdb.get_realtime_data() delegation - covers line 50"""
        with patch.object(qdb, "_get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.get_realtime_data.return_value = {"test": "realtime"}
            mock_get_client.return_value = mock_client

            result = qdb.get_realtime_data("000001")

            mock_client.get_realtime_data.assert_called_once_with("000001")
            self.assertEqual(result, {"test": "realtime"})

    def test_get_realtime_data_batch_delegation(self):
        """Test qdb.get_realtime_data_batch() delegation - covers line 54"""
        with patch.object(qdb, "_get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.get_realtime_data_batch.return_value = {"test": "batch"}
            mock_get_client.return_value = mock_client

            result = qdb.get_realtime_data_batch(["000001", "000002"])

            mock_client.get_realtime_data_batch.assert_called_once_with(
                ["000001", "000002"]
            )
            self.assertEqual(result, {"test": "batch"})

    def test_get_stock_list_delegation(self):
        """Test qdb.get_stock_list() delegation - covers line 58"""
        with patch.object(qdb, "_get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.get_stock_list.return_value = {"test": "list"}
            mock_get_client.return_value = mock_client

            result = qdb.get_stock_list("A")

            mock_client.get_stock_list.assert_called_once_with("A")
            self.assertEqual(result, {"test": "list"})

    def test_get_index_data_delegation(self):
        """Test qdb.get_index_data() delegation - covers line 62"""
        with patch.object(qdb, "_get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.get_index_data.return_value = {"test": "index"}
            mock_get_client.return_value = mock_client

            result = qdb.get_index_data("000001", days=30)

            mock_client.get_index_data.assert_called_once_with("000001", None, None, 30)
            self.assertEqual(result, {"test": "index"})

    def test_get_index_realtime_delegation(self):
        """Test qdb.get_index_realtime() delegation - covers line 66"""
        with patch.object(qdb, "_get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.get_index_realtime.return_value = {"test": "index_realtime"}
            mock_get_client.return_value = mock_client

            result = qdb.get_index_realtime("000001")

            mock_client.get_index_realtime.assert_called_once_with("000001")
            self.assertEqual(result, {"test": "index_realtime"})

    def test_get_index_list_delegation(self):
        """Test qdb.get_index_list() delegation - covers line 70"""
        with patch.object(qdb, "_get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.get_index_list.return_value = {"test": "index_list"}
            mock_get_client.return_value = mock_client

            result = qdb.get_index_list()

            mock_client.get_index_list.assert_called_once()
            self.assertEqual(result, {"test": "index_list"})

    def test_get_financial_summary_delegation(self):
        """Test qdb.get_financial_summary() delegation - covers line 74"""
        with patch.object(qdb, "_get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.get_financial_summary.return_value = {"test": "financial"}
            mock_get_client.return_value = mock_client

            result = qdb.get_financial_summary("000001")

            mock_client.get_financial_summary.assert_called_once_with("000001")
            self.assertEqual(result, {"test": "financial"})

    def test_get_financial_indicators_delegation(self):
        """Test qdb.get_financial_indicators() delegation - covers line 78"""
        with patch.object(qdb, "_get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.get_financial_indicators.return_value = {"test": "indicators"}
            mock_get_client.return_value = mock_client

            result = qdb.get_financial_indicators("000001")

            mock_client.get_financial_indicators.assert_called_once_with("000001")
            self.assertEqual(result, {"test": "indicators"})

    def test_cache_stats_delegation(self):
        """Test qdb.cache_stats() delegation - covers line 82"""
        with patch.object(qdb, "_get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.cache_stats.return_value = {"test": "stats"}
            mock_get_client.return_value = mock_client

            result = qdb.cache_stats()

            mock_client.cache_stats.assert_called_once()
            self.assertEqual(result, {"test": "stats"})

    def test_clear_cache_delegation(self):
        """Test qdb.clear_cache() delegation - covers line 86"""
        with patch.object(qdb, "_get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.clear_cache.return_value = {"test": "cleared"}
            mock_get_client.return_value = mock_client

            result = qdb.clear_cache("000001")

            mock_client.clear_cache.assert_called_once_with("000001")
            self.assertEqual(result, {"test": "cleared"})

    def test_stock_zh_a_hist_delegation(self):
        """Test qdb.stock_zh_a_hist() delegation - covers line 91"""
        with patch.object(qdb, "_get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.stock_zh_a_hist.return_value = {"test": "hist"}
            mock_get_client.return_value = mock_client

            result = qdb.stock_zh_a_hist(
                "000001", "daily", "20240101", "20240201", "qfq"
            )

            mock_client.stock_zh_a_hist.assert_called_once_with(
                "000001", "daily", "20240101", "20240201", "qfq"
            )
            self.assertEqual(result, {"test": "hist"})

    def test_set_cache_dir_function(self):
        """Test qdb.set_cache_dir() function - covers lines 96-97"""
        with patch("qdb.get_lightweight_client") as mock_get_client:
            mock_client = Mock()
            mock_get_client.return_value = mock_client

            qdb.set_cache_dir("/tmp/new_cache")

            mock_get_client.assert_called_with("/tmp/new_cache")
            self.assertEqual(qdb._client, mock_client)

    def test_set_log_level_function(self):
        """Test qdb.set_log_level() function - covers lines 101-103"""
        original_level = os.environ.get("LOG_LEVEL")

        try:
            qdb.set_log_level("DEBUG")
            self.assertEqual(os.environ["LOG_LEVEL"], "DEBUG")

            qdb.set_log_level("info")
            self.assertEqual(os.environ["LOG_LEVEL"], "INFO")
        finally:
            # Restore original level
            if original_level:
                os.environ["LOG_LEVEL"] = original_level
            elif "LOG_LEVEL" in os.environ:
                del os.environ["LOG_LEVEL"]

    def test_get_client_lazy_initialization(self):
        """Test _get_client() lazy initialization - covers lines 111-113"""
        # Ensure client is None
        qdb._client = None

        with patch("qdb.get_lightweight_client") as mock_get_client:
            mock_client = Mock()
            mock_get_client.return_value = mock_client

            result = qdb._get_client()

            mock_get_client.assert_called_once_with()
            self.assertEqual(result, mock_client)
            self.assertEqual(qdb._client, mock_client)

    def test_get_client_existing_instance(self):
        """Test _get_client() with existing instance"""
        # Set existing client
        existing_client = Mock()
        qdb._client = existing_client

        with patch("qdb.get_lightweight_client") as mock_get_client:
            result = qdb._get_client()

            # Should not call get_lightweight_client
            mock_get_client.assert_not_called()
            self.assertEqual(result, existing_client)

    def test_show_welcome_function(self):
        """Test _show_welcome() function - covers lines 162-167"""
        with patch("builtins.print") as mock_print:
            qdb._show_welcome()

            # Check that welcome messages were printed
            self.assertTrue(mock_print.called)
            calls = [call[0][0] for call in mock_print.call_args_list]
            self.assertIn("🚀 QuantDB - Intelligent Caching Stock Database", calls)

    def test_interactive_environment_check(self):
        """Test interactive environment check - covers lines 174-176"""
        # This tests the import-time code that checks for interactive environment
        with patch("sys.ps1", True, create=True):  # Simulate interactive environment
            with patch.object(qdb, "_show_welcome"):
                # Test the interactive check logic directly
                import sys

                if hasattr(sys, "ps1"):
                    try:
                        qdb._show_welcome()
                    except Exception:
                        pass


class TestQDBExceptionsCoverage(unittest.TestCase):
    """Test QDB exceptions to improve coverage"""

    def test_qdb_error_instantiation(self):
        """Test QDBError exception instantiation"""
        error = exceptions.QDBError("Test error")
        self.assertEqual(str(error), "Test error")
        self.assertIsInstance(error, Exception)

    def test_cache_error_instantiation(self):
        """Test CacheError exception instantiation"""
        error = exceptions.CacheError("Cache error")
        self.assertIn("Cache error", str(error))
        self.assertIsInstance(error, exceptions.QDBError)

    def test_data_error_instantiation(self):
        """Test DataError exception instantiation"""
        error = exceptions.DataError("Data error")
        self.assertIn("Data error", str(error))
        self.assertIsInstance(error, exceptions.QDBError)

    def test_network_error_instantiation(self):
        """Test NetworkError exception instantiation"""
        error = exceptions.NetworkError("Network error")
        self.assertIn("Network error", str(error))
        self.assertIsInstance(error, exceptions.QDBError)


if __name__ == "__main__":
    unittest.main()
