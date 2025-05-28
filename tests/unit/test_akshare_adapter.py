# tests/unit/test_akshare_adapter.py
"""
Unit tests for the AKShare adapter.
"""

import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
import pandas as pd
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.cache.akshare_adapter import AKShareAdapter

class TestAKShareAdapter(unittest.TestCase):
    """Test cases for AKShareAdapter."""

    def setUp(self):
        """Set up test fixtures."""
        self.db_mock = MagicMock()
        self.adapter = AKShareAdapter(self.db_mock)

    def test_validate_symbol(self):
        """Test symbol validation."""
        # Valid symbols
        self.assertTrue(self.adapter._validate_symbol("600000"))
        self.assertTrue(self.adapter._validate_symbol("000001"))
        self.assertTrue(self.adapter._validate_symbol("sh600000"))
        self.assertTrue(self.adapter._validate_symbol("sz000001"))
        self.assertTrue(self.adapter._validate_symbol("600000.SH"))
        self.assertTrue(self.adapter._validate_symbol("000001.SZ"))

        # Invalid symbols
        self.assertFalse(self.adapter._validate_symbol("60000"))  # Too short
        self.assertFalse(self.adapter._validate_symbol("6000000"))  # Too long
        self.assertFalse(self.adapter._validate_symbol("60000A"))  # Contains letter
        self.assertFalse(self.adapter._validate_symbol(""))  # Empty

    def test_validate_and_format_date(self):
        """Test date validation and formatting."""
        # Valid date
        self.assertEqual(self.adapter._validate_and_format_date("20230101"), "20230101")

        # None date (should return current date)
        result = self.adapter._validate_and_format_date(None)
        self.assertTrue(isinstance(result, str))
        self.assertEqual(len(result), 8)

        # Invalid format
        with self.assertRaises(ValueError):
            self.adapter._validate_and_format_date("2023-01-01")

        # Invalid date
        with self.assertRaises(ValueError):
            self.adapter._validate_and_format_date("20230231")  # February 31 doesn't exist

    def test_is_future_date(self):
        """Test future date detection."""
        # Past date
        self.assertFalse(self.adapter._is_future_date("20200101"))

        # Current date
        today = datetime.now().strftime("%Y%m%d")
        self.assertFalse(self.adapter._is_future_date(today))

        # Future date
        future = (datetime.now() + timedelta(days=10)).strftime("%Y%m%d")
        self.assertTrue(self.adapter._is_future_date(future))

    def test_compare_dates(self):
        """Test date comparison."""
        # First date earlier
        self.assertEqual(self.adapter._compare_dates("20230101", "20230102"), -1)

        # Dates equal
        self.assertEqual(self.adapter._compare_dates("20230101", "20230101"), 0)

        # First date later
        self.assertEqual(self.adapter._compare_dates("20230102", "20230101"), 1)

    def test_standardize_stock_data(self):
        """Test standardizing stock data."""
        # Test with English column names
        df = pd.DataFrame({
            'date': ['2023-01-01', '2023-01-02'],
            'open': [100.0, 101.0],
            'close': [101.0, 102.0]
        })
        result = self.adapter._standardize_stock_data(df)
        self.assertTrue(pd.api.types.is_datetime64_dtype(result['date']))

        # Test with Chinese column names
        df = pd.DataFrame({
            '日期': ['2023-01-01', '2023-01-02'],
            '开盘': [100.0, 101.0],
            '收盘': [101.0, 102.0]
        })
        result = self.adapter._standardize_stock_data(df)
        self.assertTrue('date' in result.columns)
        self.assertTrue('open' in result.columns)
        self.assertTrue('close' in result.columns)

    def test_validate_stock_data(self):
        """Test stock data validation."""
        # Valid data
        df = pd.DataFrame({
            'date': pd.to_datetime(['2023-01-01', '2023-01-02']),
            'open': [100.0, 101.0],
            'high': [105.0, 106.0],
            'low': [99.0, 100.0],
            'close': [101.0, 102.0],
            'volume': [1000, 1100]
        })
        self.assertTrue(self.adapter._validate_stock_data(df, "600000", "20230101", "20230102"))

        # Empty data
        self.assertFalse(self.adapter._validate_stock_data(pd.DataFrame(), "600000", "20230101", "20230102"))

        # Missing required column
        df = pd.DataFrame({
            'date': pd.to_datetime(['2023-01-01', '2023-01-02']),
            'open': [100.0, 101.0],
            'close': [101.0, 102.0]
        })
        self.assertFalse(self.adapter._validate_stock_data(df, "600000", "20230101", "20230102"))

        # Date range mismatch
        df = pd.DataFrame({
            'date': pd.to_datetime(['2023-01-01', '2023-01-02']),
            'open': [100.0, 101.0],
            'high': [105.0, 106.0],
            'low': [99.0, 100.0],
            'close': [101.0, 102.0],
            'volume': [1000, 1100]
        })
        self.assertFalse(self.adapter._validate_stock_data(df, "600000", "20230101", "20230110"))

    def test_generate_mock_stock_data(self):
        """Test generating mock stock data."""
        # Generate mock data
        result = self.adapter._generate_mock_stock_data("600000", "20230101", "20230105", "", "daily")

        # Check result
        self.assertEqual(len(result), 5)  # 5 days
        self.assertTrue('date' in result.columns)
        self.assertTrue('open' in result.columns)
        self.assertTrue('close' in result.columns)

        # Test with weekly period
        result = self.adapter._generate_mock_stock_data("600000", "20230101", "20230131", "", "weekly")
        self.assertTrue(len(result) <= 5)  # About 4-5 weeks in a month

        # Test with monthly period
        result = self.adapter._generate_mock_stock_data("600000", "20230101", "20231231", "", "monthly")
        self.assertEqual(len(result), 12)  # 12 months in a year

    @patch('src.cache.akshare_adapter.AKShareAdapter._safe_call')
    @patch('src.cache.akshare_adapter.logger')
    def test_get_stock_data_success(self, logger_mock, safe_call_mock):
        """Test getting stock data successfully."""
        # Setup mock
        mock_df = pd.DataFrame({
            'date': pd.to_datetime(['2023-01-01', '2023-01-02']),
            'open': [100.0, 101.0],
            'high': [105.0, 106.0],
            'low': [99.0, 100.0],
            'close': [101.0, 102.0],
            'volume': [1000, 1100]
        })
        safe_call_mock.return_value = mock_df

        # Call method
        result = self.adapter.get_stock_data("600000", "20230101", "20230102")

        # Check result
        self.assertEqual(len(result), 2)

        # Verify mocks
        safe_call_mock.assert_called_once()
        logger_mock.info.assert_called()

    @patch('src.cache.akshare_adapter.AKShareAdapter._safe_call')
    @patch('src.cache.akshare_adapter.logger')
    def test_get_stock_data_empty(self, logger_mock, safe_call_mock):
        """Test getting stock data with empty result."""
        # Setup mock
        safe_call_mock.return_value = pd.DataFrame()

        # Call method
        result = self.adapter.get_stock_data("600000", "20230101", "20230102")

        # Check result
        self.assertTrue(result.empty)

        # Verify mocks
        safe_call_mock.assert_called_once()
        logger_mock.warning.assert_called()

    @patch('src.cache.akshare_adapter.AKShareAdapter._safe_call')
    @patch('src.cache.akshare_adapter.logger')
    def test_get_stock_data_exception(self, logger_mock, safe_call_mock):
        """Test getting stock data with exception."""
        # Setup mock
        safe_call_mock.side_effect = Exception("Test exception")

        # Call method
        result = self.adapter.get_stock_data("600000", "20230101", "20230102")

        # Check result
        self.assertTrue(result.empty)

        # Verify mocks
        safe_call_mock.assert_called_once()
        logger_mock.error.assert_called()

    @patch('src.cache.akshare_adapter.AKShareAdapter._safe_call')
    @patch('src.cache.akshare_adapter.logger')
    def test_get_stock_data_with_mock_data(self, logger_mock, safe_call_mock):
        """Test getting stock data with mock data."""
        # Setup mock
        safe_call_mock.side_effect = Exception("Test exception")

        # Call method
        result = self.adapter.get_stock_data("600000", "20230101", "20230102", use_mock_data=True)

        # Check result
        self.assertFalse(result.empty)

        # Verify mocks
        safe_call_mock.assert_called_once()
        logger_mock.warning.assert_called()

    @patch('src.cache.akshare_adapter.logger')
    def test_get_stock_data_invalid_symbol(self, logger_mock):
        """Test getting stock data with invalid symbol."""
        # Call method with invalid symbol and no mock data
        with self.assertRaises(ValueError):
            self.adapter.get_stock_data("60000", "20230101", "20230102")

        # Call method with invalid symbol and mock data
        result = self.adapter.get_stock_data("60000", "20230101", "20230102", use_mock_data=True)
        self.assertFalse(result.empty)

        # Verify mocks
        logger_mock.error.assert_called()
        logger_mock.warning.assert_called()

    @patch('src.cache.akshare_adapter.logger')
    def test_get_stock_data_invalid_period(self, logger_mock):
        """Test getting stock data with invalid period."""
        # Call method with invalid period
        with self.assertRaises(ValueError):
            self.adapter.get_stock_data("600000", "20230101", "20230102", period="invalid")

        # Verify mocks
        logger_mock.error.assert_called()

    @patch('src.cache.akshare_adapter.logger')
    def test_get_stock_data_invalid_adjust(self, logger_mock):
        """Test getting stock data with invalid adjust."""
        # Call method with invalid adjust
        with self.assertRaises(ValueError):
            self.adapter.get_stock_data("600000", "20230101", "20230102", adjust="invalid")

        # Verify mocks
        logger_mock.error.assert_called()

    @patch('src.cache.akshare_adapter.logger')
    def test_get_stock_data_start_after_end(self, logger_mock):
        """Test getting stock data with start date after end date."""
        # Call method with start date after end date
        with self.assertRaises(ValueError):
            self.adapter.get_stock_data("600000", "20230102", "20230101")

        # Verify mocks
        logger_mock.error.assert_called()

if __name__ == '__main__':
    unittest.main()
