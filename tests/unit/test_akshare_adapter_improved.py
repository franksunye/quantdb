#!/usr/bin/env python
# tests/unit/test_akshare_adapter_improved.py
"""
Unit tests for the improved AKShare adapter.

This script tests the improved AKShare adapter's functionality,
including error handling, date validation, and mock data generation.
"""

import os
import sys
import unittest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.cache.akshare_adapter import AKShareAdapter
from src.logger import setup_logger

# Setup logger
logger = setup_logger(__name__)

class TestAKShareAdapterImproved(unittest.TestCase):
    """Unit tests for the improved AKShareAdapter class."""

    def setUp(self):
        """Set up test fixtures."""
        # Initialize cache engine and freshness tracker
        self.        self.
        # Initialize AKShare adapter with the cache engine and freshness tracker
        self.adapter = AKShareAdapter(
            cache_engine=self.cache_engine,
            freshness_tracker=self.freshness_tracker
        )

        # Clear the cache to ensure a fresh start
        self.cache_engine.clear()
        self.freshness_tracker.clear()

    def test_validate_and_format_date(self):
        """Test the _validate_and_format_date method."""
        # Test with various date formats
        test_cases = [
            # (input, expected_output)
            ("20230101", "20230101"),
            ("2023-01-01", "20230101"),
            ("2023/01/01", "20230101"),
            ("01/01/2023", "20230101"),
            ("2023.01.01", "20230101"),
            ("2023年01月01日", "20230101"),
            ("Jan 01, 2023", "20230101"),
            ("01 Jan 2023", "20230101"),
            ("January 01, 2023", "20230101"),
            ("01 January 2023", "20230101"),
            ("today", datetime.now().strftime('%Y%m%d')),
            ("yesterday", (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')),
            ("7 days ago", (datetime.now() - timedelta(days=7)).strftime('%Y%m%d')),
            ("2 weeks ago", (datetime.now() - timedelta(weeks=2)).strftime('%Y%m%d')),
            ("1 month ago", (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')),
            ("1 year ago", (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')),
            ("last week", (datetime.now() - timedelta(weeks=1)).strftime('%Y%m%d')),
            ("last month", (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')),
            ("last year", (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')),
            ("2023", "20230101"),  # Only year
            ("", datetime.now().strftime('%Y%m%d')),  # Empty string
            (None, datetime.now().strftime('%Y%m%d')),  # None
        ]

        for input_date, expected_output in test_cases:
            result = self.adapter._validate_and_format_date(input_date)
            self.assertEqual(result, expected_output, f"Failed for input: {input_date}")

    def test_validate_symbol(self):
        """Test the _validate_symbol method."""
        # Test with various symbol formats
        valid_symbols = [
            "000001",  # 6-digit number
            "600000",  # 6-digit number
            "300001",  # 6-digit number
            "sh000001",  # With market prefix
            "sz000001",  # With market prefix
            "SH000001",  # With market prefix (uppercase)
            "SZ000001",  # With market prefix (uppercase)
            "000001.SZ",  # With market suffix
            "600000.SH",  # With market suffix
        ]

        invalid_symbols = [
            "",  # Empty string
            "12345",  # 5-digit number
            "1234567",  # 7-digit number
            "ABCDEF",  # Not a number
            "sh12345",  # Invalid with prefix
            "sz12345",  # Invalid with prefix
        ]

        for symbol in valid_symbols:
            self.assertTrue(self.adapter._validate_symbol(symbol), f"Failed for valid symbol: {symbol}")

        for symbol in invalid_symbols:
            self.assertFalse(self.adapter._validate_symbol(symbol), f"Failed for invalid symbol: {symbol}")

    def test_generate_mock_stock_data(self):
        """Test the _generate_mock_stock_data method."""
        # Test with various parameters
        symbol = "000001"
        start_date = "20230101"
        end_date = "20230131"

        # Test with default parameters
        df = self.adapter._generate_mock_stock_data(symbol, start_date, end_date)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)

        # Check that the DataFrame has the expected columns
        expected_columns = ['date', 'open', 'high', 'low', 'close', 'volume', 'turnover', 'amplitude', 'pct_change', 'change']
        for col in expected_columns:
            self.assertIn(col, df.columns)

        # Check that the date range is correct
        self.assertEqual(df['date'].min(), "2023-01-02")  # First business day in January 2023
        self.assertEqual(df['date'].max(), "2023-01-31")

        # Test with different periods
        periods = ["daily", "weekly", "monthly"]
        for period in periods:
            df = self.adapter._generate_mock_stock_data(symbol, start_date, end_date, period=period)
            self.assertIsInstance(df, pd.DataFrame)
            self.assertFalse(df.empty)

            # For weekly data, there should be fewer rows
            if period == "weekly":
                self.assertLess(len(df), 31)

            # For monthly data, there should be only one row (January 2023)
            if period == "monthly":
                self.assertEqual(len(df), 1)

        # Test with different adjustments
        adjustments = ["", "qfq", "hfq"]
        for adjust in adjustments:
            df = self.adapter._generate_mock_stock_data(symbol, start_date, end_date, adjust=adjust)
            self.assertIsInstance(df, pd.DataFrame)
            self.assertFalse(df.empty)

    def test_convert_to_period(self):
        """Test the _convert_to_period method."""
        # Create a sample daily DataFrame
        dates = pd.date_range(start="2023-01-01", end="2023-01-31", freq='B')
        daily_data = pd.DataFrame({
            'date': dates,
            'open': np.random.uniform(10, 20, len(dates)),
            'high': np.random.uniform(20, 30, len(dates)),
            'low': np.random.uniform(5, 10, len(dates)),
            'close': np.random.uniform(15, 25, len(dates)),
            'volume': np.random.randint(1000000, 10000000, len(dates)),
            'turnover': np.random.uniform(10000000, 100000000, len(dates)),
            'amplitude': np.random.uniform(1, 10, len(dates)),
            'pct_change': np.random.uniform(-5, 5, len(dates)),
            'change': np.random.uniform(-1, 1, len(dates))
        })

        # Convert to weekly data
        weekly_data = self.adapter._convert_to_period(daily_data, "weekly")
        self.assertIsInstance(weekly_data, pd.DataFrame)
        self.assertFalse(weekly_data.empty)
        self.assertLess(len(weekly_data), len(daily_data))

        # Convert to monthly data
        monthly_data = self.adapter._convert_to_period(daily_data, "monthly")
        self.assertIsInstance(monthly_data, pd.DataFrame)
        self.assertFalse(monthly_data.empty)
        self.assertEqual(len(monthly_data), 1)  # Only January 2023

    def test_validate_stock_data(self):
        """Test the _validate_stock_data method."""
        # Create a valid DataFrame
        dates = pd.date_range(start="2023-01-01", end="2023-01-31", freq='B')
        num_days = len(dates)

        valid_df = pd.DataFrame({
            'date': dates,
            'open': np.random.uniform(10, 20, num_days),
            'high': np.random.uniform(20, 30, num_days),
            'low': np.random.uniform(5, 10, num_days),
            'close': np.random.uniform(15, 25, num_days),
            'volume': np.random.randint(1000000, 10000000, num_days)
        })

        # Test with valid data
        self.assertTrue(self.adapter._validate_stock_data(valid_df, "000001", "20230101", "20230131"))

        # Test with missing columns
        invalid_df1 = valid_df.drop(columns=['high'])
        self.assertFalse(self.adapter._validate_stock_data(invalid_df1, "000001", "20230101", "20230131"))

        # Test with non-numeric data
        invalid_df2 = valid_df.copy()
        invalid_df2['close'] = 'not_a_number'
        self.assertFalse(self.adapter._validate_stock_data(invalid_df2, "000001", "20230101", "20230131"))

        # Test with negative prices
        invalid_df3 = valid_df.copy()
        invalid_df3.loc[0, 'close'] = -10
        self.assertFalse(self.adapter._validate_stock_data(invalid_df3, "000001", "20230101", "20230131"))

        # Test with high < low
        invalid_df4 = valid_df.copy()
        invalid_df4.loc[0, 'high'] = 5
        invalid_df4.loc[0, 'low'] = 10
        self.assertFalse(self.adapter._validate_stock_data(invalid_df4, "000001", "20230101", "20230131"))

if __name__ == "__main__":
    unittest.main()
