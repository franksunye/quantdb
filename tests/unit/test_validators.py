"""
Validators unit tests for QuantDB.

This module tests the validation utilities including:
- Stock symbol validation
- Date format validation
- Data range validation
- Input sanitization
"""

import unittest
from datetime import date, datetime, timedelta
from decimal import Decimal

from core.utils.validators import (
    validate_stock_symbol,
    validate_date_format,
    validate_date_range,
    normalize_symbol,
    detect_market_type,
    validate_adjust_parameter,
    validate_period_parameter
)


class TestStockSymbolValidation(unittest.TestCase):
    """Test stock symbol validation functions."""
    
    def test_validate_stock_symbol_valid_symbols(self):
        """Test validation of valid stock symbols."""
        valid_symbols = [
            "000001",  # Shenzhen A-share
            "000002",
            "002001",  # SME board
            "300001",  # ChiNext
            "600000",  # Shanghai A-share
            "601001",
            "688001",  # STAR Market
            "SH000001",  # With exchange prefix
            "SZ000001",
            "sh600000",  # Lowercase prefix
            "sz000001"
        ]
        
        for symbol in valid_symbols:
            with self.subTest(symbol=symbol):
                self.assertTrue(validate_stock_symbol(symbol))
    
    def test_validate_stock_symbol_invalid_symbols(self):
        """Test validation of invalid stock symbols."""
        invalid_symbols = [
            "",           # Empty string
            "0001",       # Too short (4 digits)
            "0000001",    # Too long (7 digits)
            "AAAA01",     # Letters in number part
            "12345A",     # Letter at end
            "BJ000001",   # Invalid exchange
            "HK0001",     # Hong Kong format (not supported)
            "US.AAPL",    # US format
            None,         # None value
            123456,       # Integer instead of string
        ]

        for symbol in invalid_symbols:
            with self.subTest(symbol=symbol):
                self.assertFalse(validate_stock_symbol(symbol))
    
    def test_normalize_symbol(self):
        """Test symbol normalization."""
        test_cases = [
            ("SH600000", "600000"),
            ("SZ000001", "000001"),
            ("sh600000", "600000"),
            ("sz000001", "000001"),
            ("  600000  ", "600000"),
            ("600000.SH", "600000"),
            ("000001.SZ", "000001"),
            ("600000", "600000"),  # Already clean
        ]

        for input_symbol, expected in test_cases:
            with self.subTest(input_symbol=input_symbol):
                result = normalize_symbol(input_symbol)
                self.assertEqual(result, expected)

    def test_normalize_symbol_invalid_input(self):
        """Test symbol normalization with invalid input."""
        invalid_inputs = [None, "", "   "]

        for invalid_input in invalid_inputs:
            with self.subTest(input=invalid_input):
                result = normalize_symbol(invalid_input)
                self.assertEqual(result, "")


class TestDateValidation(unittest.TestCase):
    """Test date validation functions."""
    
    def test_validate_date_format_valid_dates(self):
        """Test validation of valid date formats."""
        valid_dates = [
            "20240115",
            "20231231",
            "20200229",  # Leap year
            "19900101",
        ]

        for date_str in valid_dates:
            with self.subTest(date_str=date_str):
                self.assertTrue(validate_date_format(date_str))
    
    def test_validate_date_format_invalid_dates(self):
        """Test validation of invalid date formats."""
        invalid_dates = [
            "",
            "20241301",    # Invalid month
            "20240132",    # Invalid day
            "20230229",    # Not a leap year
            "240115",      # Wrong year format
            "2024/01/15",  # Wrong separator
            "15012024",    # Wrong order
            "2024115",     # Missing zero padding
            "not-a-date",
            None,
            20240115,      # Integer
        ]

        for date_str in invalid_dates:
            with self.subTest(date_str=date_str):
                self.assertFalse(validate_date_format(date_str))
    
    def test_validate_date_range_valid_ranges(self):
        """Test validation of valid date ranges."""
        today = date.today()
        yesterday = today - timedelta(days=1)
        last_week = today - timedelta(days=7)

        valid_ranges = [
            (yesterday.strftime("%Y%m%d"), today.strftime("%Y%m%d")),
            (last_week.strftime("%Y%m%d"), yesterday.strftime("%Y%m%d")),
            ("20240101", "20240131"),
            ("20230101", "20231231"),
        ]

        for start_date, end_date in valid_ranges:
            with self.subTest(start=start_date, end=end_date):
                is_valid, error_msg = validate_date_range(start_date, end_date)
                self.assertTrue(is_valid, f"Error: {error_msg}")
    
    def test_validate_date_range_invalid_ranges(self):
        """Test validation of invalid date ranges."""
        today = date.today()
        yesterday = today - timedelta(days=1)
        tomorrow = today + timedelta(days=1)

        invalid_ranges = [
            (today.strftime("%Y%m%d"), yesterday.strftime("%Y%m%d")),  # End before start
            (tomorrow.strftime("%Y%m%d"), today.strftime("%Y%m%d")),   # Future start date
            ("20240131", "20240101"),               # End before start
            ("invalid-date", "20240131"),           # Invalid start
            ("20240101", "invalid-date"),           # Invalid end
            ("", "20240131"),                       # Empty start
            ("20240101", ""),                       # Empty end
        ]

        for start_date, end_date in invalid_ranges:
            with self.subTest(start=start_date, end=end_date):
                is_valid, error_msg = validate_date_range(start_date, end_date)
                self.assertFalse(is_valid, f"Should be invalid but got: {error_msg}")


class TestMarketDetection(unittest.TestCase):
    """Test market detection functions."""

    def test_detect_market_type_a_stocks(self):
        """Test detection of A-share stocks."""
        a_stock_symbols = [
            "000001",  # Shenzhen A-share
            "600000",  # Shanghai A-share
            "300001",  # ChiNext
            "SH600000",  # With prefix
            "SZ000001"   # With prefix
        ]

        for symbol in a_stock_symbols:
            with self.subTest(symbol=symbol):
                market_type = detect_market_type(symbol)
                self.assertEqual(market_type, 'A_STOCK')

    def test_detect_market_type_hk_stocks(self):
        """Test detection of Hong Kong stocks."""
        hk_stock_symbols = [
            "00700",  # Tencent
            "02171",  # Xiaomi
            "01810"   # Xiaomi-W
        ]

        for symbol in hk_stock_symbols:
            with self.subTest(symbol=symbol):
                market_type = detect_market_type(symbol)
                self.assertEqual(market_type, 'HK_STOCK')

    def test_detect_market_type_unknown(self):
        """Test detection of unknown market types."""
        unknown_symbols = [
            "AAPL",     # US stock
            "INVALID",  # Invalid format
            "",         # Empty
            "1234",     # Too short (4 digits)
            "1234567"   # Too long (7 digits)
        ]

        for symbol in unknown_symbols:
            with self.subTest(symbol=symbol):
                market_type = detect_market_type(symbol)
                self.assertEqual(market_type, 'UNKNOWN')


class TestParameterValidation(unittest.TestCase):
    """Test parameter validation functions."""

    def test_validate_adjust_parameter_valid(self):
        """Test validation of valid adjust parameters."""
        valid_adjusts = ["", "qfq", "hfq"]

        for adjust in valid_adjusts:
            with self.subTest(adjust=adjust):
                self.assertTrue(validate_adjust_parameter(adjust))

    def test_validate_adjust_parameter_invalid(self):
        """Test validation of invalid adjust parameters."""
        invalid_adjusts = ["invalid", "QFQ", "HFQ", None, 123]

        for adjust in invalid_adjusts:
            with self.subTest(adjust=adjust):
                self.assertFalse(validate_adjust_parameter(adjust))

    def test_validate_period_parameter_valid(self):
        """Test validation of valid period parameters."""
        valid_periods = ["daily", "weekly", "monthly"]

        for period in valid_periods:
            with self.subTest(period=period):
                self.assertTrue(validate_period_parameter(period))

    def test_validate_period_parameter_invalid(self):
        """Test validation of invalid period parameters."""
        invalid_periods = ["yearly", "DAILY", "WEEKLY", None, 123]

        for period in invalid_periods:
            with self.subTest(period=period):
                self.assertFalse(validate_period_parameter(period))





if __name__ == "__main__":
    unittest.main()
