# tests/unit/test_stock_data_service.py
"""
Unit tests for the StockDataService class.
"""

import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
import pandas as pd
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.services.stock_data_service import StockDataService

class TestStockDataService(unittest.TestCase):
    """Test cases for StockDataService."""

    def setUp(self):
        """Set up test fixtures."""
        self.db_mock = MagicMock()
        self.akshare_adapter_mock = MagicMock()
        self.db_cache_mock = MagicMock()

        # Create service with mocked dependencies
        self.service = StockDataService(self.db_mock, self.akshare_adapter_mock)
        self.service.db_cache = self.db_cache_mock

    def test_standardize_stock_symbol(self):
        """Test standardizing stock symbols."""
        # Test with market prefix
        self.assertEqual(self.service._standardize_stock_symbol("sh600000"), "600000")
        self.assertEqual(self.service._standardize_stock_symbol("sz000001"), "000001")

        # Test with suffix
        self.assertEqual(self.service._standardize_stock_symbol("600000.SH"), "600000")
        self.assertEqual(self.service._standardize_stock_symbol("000001.SZ"), "000001")

        # Test with both
        self.assertEqual(self.service._standardize_stock_symbol("sh600000.SH"), "600000")

        # Test with clean symbol
        self.assertEqual(self.service._standardize_stock_symbol("600000"), "600000")

    def test_validate_and_format_date(self):
        """Test date validation and formatting."""
        # Test with valid date
        self.assertEqual(self.service._validate_and_format_date("20230101"), "20230101")

        # Test with None (should return a date string)
        result = self.service._validate_and_format_date(None)
        self.assertTrue(isinstance(result, str))
        self.assertEqual(len(result), 8)

        # Test with invalid format
        with self.assertRaises(ValueError):
            self.service._validate_and_format_date("2023-01-01")

    def test_get_trading_days(self):
        """Test getting trading days."""
        # Test with short range
        days = self.service._get_trading_days("20230101", "20230105")
        self.assertEqual(len(days), 5)
        self.assertEqual(days[0], "20230101")
        self.assertEqual(days[-1], "20230105")

        # Test with longer range
        days = self.service._get_trading_days("20230101", "20230131")
        self.assertEqual(len(days), 31)
        self.assertEqual(days[0], "20230101")
        self.assertEqual(days[-1], "20230131")

    def test_group_consecutive_dates(self):
        """Test grouping consecutive dates."""
        # Test with consecutive dates
        dates = ["20230101", "20230102", "20230103", "20230104", "20230105"]
        groups = self.service._group_consecutive_dates(dates)
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0], ("20230101", "20230105"))

        # Test with non-consecutive dates
        dates = ["20230101", "20230102", "20230103", "20230107", "20230108"]
        groups = self.service._group_consecutive_dates(dates)
        self.assertEqual(len(groups), 2)
        self.assertEqual(groups[0], ("20230101", "20230103"))
        self.assertEqual(groups[1], ("20230107", "20230108"))

        # Test with weekend gap (should be considered consecutive)
        dates = ["20230106", "20230107", "20230108", "20230109"]  # Fri, Sat, Sun, Mon
        groups = self.service._group_consecutive_dates(dates)
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0], ("20230106", "20230109"))

        # Test with empty list
        self.assertEqual(self.service._group_consecutive_dates([]), [])

    def test_dataframe_to_dict(self):
        """Test converting DataFrame to dictionary."""
        # Create test DataFrame
        df = pd.DataFrame({
            'date': [datetime(2023, 1, 1), datetime(2023, 1, 2)],
            'open': [100.0, 101.0],
            'close': [101.0, 102.0]
        })

        # Convert to dictionary
        result = self.service._dataframe_to_dict(df)

        # Check result
        self.assertEqual(len(result), 2)
        self.assertIn('20230101', result)
        self.assertIn('20230102', result)
        self.assertEqual(result['20230101']['open'], 100.0)
        self.assertEqual(result['20230102']['close'], 102.0)

    def test_dict_to_dataframe(self):
        """Test converting dictionary to DataFrame."""
        # Create test dictionary
        data_dict = {
            '20230101': {'date': datetime(2023, 1, 1), 'open': 100.0, 'close': 101.0},
            '20230102': {'date': datetime(2023, 1, 2), 'open': 101.0, 'close': 102.0}
        }

        # Convert to DataFrame
        result = self.service._dict_to_dataframe(data_dict)

        # Check result
        self.assertEqual(len(result), 2)
        self.assertEqual(result['open'].tolist(), [100.0, 101.0])
        self.assertEqual(result['close'].tolist(), [101.0, 102.0])

    def test_filter_dataframe_by_date_range(self):
        """Test filtering DataFrame by date range."""
        # Create test DataFrame
        df = pd.DataFrame({
            'date': pd.to_datetime(['2023-01-01', '2023-01-02', '2023-01-03', '2023-01-04', '2023-01-05']),
            'value': [1, 2, 3, 4, 5]
        })

        # Filter DataFrame
        result = self.service._filter_dataframe_by_date_range(df, '20230102', '20230104')

        # Check result
        self.assertEqual(len(result), 3)
        self.assertEqual(result['value'].tolist(), [2, 3, 4])

    @patch('src.services.stock_data_service.logger')
    def test_get_stock_data_all_in_cache(self, logger_mock):
        """Test getting stock data when all data is in cache."""
        # Setup mocks
        self.db_cache_mock.get.return_value = {
            '20230101': {'date': datetime(2023, 1, 1), 'open': 100.0, 'close': 101.0},
            '20230102': {'date': datetime(2023, 1, 2), 'open': 101.0, 'close': 102.0}
        }

        # Call method
        result = self.service.get_stock_data('600000', '20230101', '20230102')

        # Check result
        self.assertEqual(len(result), 2)
        self.assertEqual(result['open'].tolist(), [100.0, 101.0])
        self.assertEqual(result['close'].tolist(), [101.0, 102.0])

        # Verify mocks
        self.db_cache_mock.get.assert_called_once()
        self.akshare_adapter_mock.get_stock_data.assert_not_called()
        logger_mock.info.assert_any_call("All requested data for 600000 already exists in database")

    @patch('src.services.stock_data_service.logger')
    def test_get_stock_data_partial_cache(self, logger_mock):
        """Test getting stock data when some data is in cache."""
        # Setup mocks
        self.db_cache_mock.get.return_value = {
            '20230101': {'date': datetime(2023, 1, 1), 'open': 100.0, 'close': 101.0}
        }

        akshare_data = pd.DataFrame({
            'date': [datetime(2023, 1, 2)],
            'open': [101.0],
            'close': [102.0]
        })
        self.akshare_adapter_mock.get_stock_data.return_value = akshare_data

        # Call method
        result = self.service.get_stock_data('600000', '20230101', '20230102')

        # Check result
        self.assertEqual(len(result), 2)

        # Verify mocks
        self.db_cache_mock.get.assert_called_once()
        self.akshare_adapter_mock.get_stock_data.assert_called_once()
        self.db_cache_mock.save.assert_called_once()
        logger_mock.info.assert_any_call("Found 1 missing dates for 600000")

    @patch('src.services.stock_data_service.logger')
    def test_get_stock_data_empty_cache(self, logger_mock):
        """Test getting stock data when cache is empty."""
        # Setup mocks
        self.db_cache_mock.get.return_value = {}

        akshare_data = pd.DataFrame({
            'date': [datetime(2023, 1, 1), datetime(2023, 1, 2)],
            'open': [100.0, 101.0],
            'close': [101.0, 102.0]
        })
        self.akshare_adapter_mock.get_stock_data.return_value = akshare_data

        # Call method
        result = self.service.get_stock_data('600000', '20230101', '20230102')

        # Check result
        self.assertEqual(len(result), 2)

        # Verify mocks
        self.db_cache_mock.get.assert_called_once()
        self.akshare_adapter_mock.get_stock_data.assert_called_once()
        self.db_cache_mock.save.assert_called_once()
        logger_mock.info.assert_any_call("Found 2 missing dates for 600000")

    @patch('src.services.stock_data_service.logger')
    def test_get_stock_data_akshare_empty(self, logger_mock):
        """Test getting stock data when AKShare returns empty data."""
        # Setup mocks
        self.db_cache_mock.get.return_value = {}
        self.akshare_adapter_mock.get_stock_data.return_value = pd.DataFrame()

        # Call method
        result = self.service.get_stock_data('600000', '20230101', '20230102')

        # Check result
        self.assertTrue(result.empty)

        # Verify mocks
        self.db_cache_mock.get.assert_called_once()
        self.akshare_adapter_mock.get_stock_data.assert_called_once()
        self.db_cache_mock.save.assert_not_called()
        logger_mock.warning.assert_any_call("No data returned from AKShare for 600000 from 20230101 to 20230102")

if __name__ == '__main__':
    unittest.main()
