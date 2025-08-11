# tests/unit/test_helpers.py
"""
Unit tests for core/utils/helpers.py
"""

import os
import sys
import tempfile
import unittest
from datetime import date, datetime
from unittest.mock import mock_open, patch

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from core.utils.helpers import (
    calculate_date_range,
    calculate_percentage_change,
    clean_dict,
    ensure_directory_exists,
    format_currency,
    format_currency_by_code,
    format_large_number,
    format_number,
    format_percentage,
    get_file_size_mb,
    get_trading_days_count,
    merge_dicts,
    parse_date_string,
    safe_divide,
    safe_float_conversion,
    safe_int_conversion,
    timing_decorator,
)


class TestHelpers(unittest.TestCase):
    """Test cases for helper functions."""

    def test_format_currency_by_code(self):
        """Test format_currency_by_code with currency codes."""
        # Test CNY
        self.assertEqual(format_currency_by_code(1234.56, "CNY"), "¥1,234.56")
        self.assertEqual(format_currency_by_code(0, "CNY"), "¥0.00")
        self.assertEqual(format_currency_by_code(1000000, "CNY"), "¥1,000,000.00")

        # Test HKD
        self.assertEqual(format_currency_by_code(1234.56, "HKD"), "HK$1,234.56")

        # Test USD
        self.assertEqual(format_currency_by_code(1234.56, "USD"), "$1,234.56")

        # Test other currency
        self.assertEqual(format_currency_by_code(1234.56, "EUR"), "1,234.56 EUR")

        # Test default currency (CNY)
        self.assertEqual(format_currency_by_code(1234.56), "¥1,234.56")

    def test_format_currency_with_symbol(self):
        """Test format_currency with symbol parameter (the actual implementation)."""
        # Test positive amount with default symbol
        self.assertEqual(format_currency(1234.56), "¥1,234.56")
        self.assertEqual(format_currency(1000), "¥1,000.00")

        # Test positive amount with custom symbols
        self.assertEqual(format_currency(1234.56, "$"), "$1,234.56")
        self.assertEqual(format_currency(1000, "HK$"), "HK$1,000.00")
        self.assertEqual(format_currency(1234.56, "€"), "€1,234.56")

        # Test negative amount
        self.assertEqual(format_currency(-1234.56, "¥"), "-¥1,234.56")
        self.assertEqual(format_currency(-1000, "$"), "-$1,000.00")

        # Test zero
        self.assertEqual(format_currency(0, "¥"), "¥0.00")
        self.assertEqual(format_currency(0), "¥0.00")

    def test_format_percentage(self):
        """Test percentage formatting."""
        # Test basic formatting
        self.assertEqual(format_percentage(0.05), "5.00%")
        self.assertEqual(format_percentage(0.1234), "12.34%")
        self.assertEqual(format_percentage(1.0), "100.00%")
        
        # Test with different decimal places
        self.assertEqual(format_percentage(0.05, 0), "5%")
        self.assertEqual(format_percentage(0.05, 1), "5.0%")
        self.assertEqual(format_percentage(0.05, 3), "5.000%")
        
        # Test negative percentage
        self.assertEqual(format_percentage(-0.05), "-5.00%")
        
        # Test zero
        self.assertEqual(format_percentage(0), "0.00%")

    def test_format_number(self):
        """Test number formatting with thousands separators."""
        self.assertEqual(format_number(1234), "1,234")
        self.assertEqual(format_number(1234567), "1,234,567")
        self.assertEqual(format_number(1234.56), "1,234.56")
        self.assertEqual(format_number(0), "0")
        self.assertEqual(format_number(-1234), "-1,234")

    def test_format_large_number(self):
        """Test large number formatting with units."""
        # Test trillions
        self.assertEqual(format_large_number(1.5e12), "1.50T")
        self.assertEqual(format_large_number(-2.3e12), "-2.30T")
        
        # Test billions
        self.assertEqual(format_large_number(1.5e9), "1.50B")
        self.assertEqual(format_large_number(-2.3e9), "-2.30B")
        
        # Test millions
        self.assertEqual(format_large_number(1.5e6), "1.50M")
        self.assertEqual(format_large_number(-2.3e6), "-2.30M")
        
        # Test thousands
        self.assertEqual(format_large_number(1500), "1.50K")
        self.assertEqual(format_large_number(-2300), "-2.30K")
        
        # Test small numbers
        self.assertEqual(format_large_number(123), "123.00")
        self.assertEqual(format_large_number(0), "0.00")

    def test_calculate_date_range(self):
        """Test date range calculation."""
        # Test with end_date provided
        start, end = calculate_date_range(30, "20230201")
        self.assertEqual(end, "20230201")
        self.assertEqual(start, "20230102")  # 30 days before
        
        # Test with no end_date (should use current date)
        with patch('core.utils.helpers.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2023, 2, 1)
            mock_datetime.strptime = datetime.strptime
            start, end = calculate_date_range(30)
            self.assertEqual(end, "20230201")
            self.assertEqual(start, "20230102")

    def test_get_trading_days_count(self):
        """Test trading days count estimation."""
        # Test 7 days (should be 5 trading days)
        count = get_trading_days_count("20230101", "20230107")
        self.assertEqual(count, 5)
        
        # Test 14 days (should be 10 trading days)
        count = get_trading_days_count("20230101", "20230114")
        self.assertEqual(count, 10)
        
        # Test same day
        count = get_trading_days_count("20230101", "20230101")
        self.assertEqual(count, 0)  # int(1 * 5 / 7) = 0

    def test_ensure_directory_exists(self):
        """Test directory creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file_path = os.path.join(temp_dir, "subdir", "test.txt")
            
            # Directory should not exist initially
            self.assertFalse(os.path.exists(os.path.dirname(test_file_path)))
            
            # Call function
            ensure_directory_exists(test_file_path)
            
            # Directory should now exist
            self.assertTrue(os.path.exists(os.path.dirname(test_file_path)))

    def test_ensure_directory_exists_empty_path(self):
        """Test ensure_directory_exists with empty path."""
        # Should not raise an error
        ensure_directory_exists("")

    @patch('os.path.exists')
    @patch('os.path.getsize')
    def test_get_file_size_mb(self, mock_getsize, mock_exists):
        """Test file size calculation in MB."""
        # Test existing file
        mock_exists.return_value = True
        mock_getsize.return_value = 1024 * 1024 * 2.5  # 2.5 MB
        
        size = get_file_size_mb("test.txt")
        self.assertEqual(size, 2.5)
        
        # Test non-existing file
        mock_exists.return_value = False
        size = get_file_size_mb("nonexistent.txt")
        self.assertEqual(size, 0.0)

    def test_timing_decorator(self):
        """Test timing decorator."""
        @timing_decorator
        def test_function():
            return {"data": "test"}
        
        @timing_decorator
        def test_function_with_metadata():
            return {"data": "test", "metadata": {"existing": "value"}}
        
        # Test function without existing metadata
        result = test_function()
        self.assertIn("metadata", result)
        self.assertIn("execution_time_ms", result["metadata"])
        self.assertIsInstance(result["metadata"]["execution_time_ms"], float)
        
        # Test function with existing metadata
        result = test_function_with_metadata()
        self.assertIn("metadata", result)
        self.assertIn("execution_time_ms", result["metadata"])
        self.assertIn("existing", result["metadata"])
        self.assertEqual(result["metadata"]["existing"], "value")

    def test_timing_decorator_non_dict_result(self):
        """Test timing decorator with non-dict result."""
        @timing_decorator
        def test_function():
            return "string result"
        
        result = test_function()
        self.assertEqual(result, "string result")

    def test_safe_divide(self):
        """Test safe division."""
        # Test normal division
        self.assertEqual(safe_divide(10, 2), 5.0)
        self.assertEqual(safe_divide(7, 3), 7/3)
        
        # Test division by zero with default
        self.assertEqual(safe_divide(10, 0), 0.0)
        
        # Test division by zero with custom default
        self.assertEqual(safe_divide(10, 0, -1.0), -1.0)
        
        # Test negative numbers
        self.assertEqual(safe_divide(-10, 2), -5.0)
        self.assertEqual(safe_divide(10, -2), -5.0)

    def test_clean_dict(self):
        """Test dictionary cleaning."""
        test_dict = {
            "key1": "value1",
            "key2": None,
            "key3": "",
            "key4": [],
            "key5": {},
            "key6": "value6"
        }
        
        # Test removing None values only
        result = clean_dict(test_dict, remove_none=True, remove_empty=False)
        expected = {"key1": "value1", "key3": "", "key4": [], "key5": {}, "key6": "value6"}
        self.assertEqual(result, expected)
        
        # Test removing empty values only
        result = clean_dict(test_dict, remove_none=False, remove_empty=True)
        expected = {"key1": "value1", "key2": None, "key6": "value6"}
        self.assertEqual(result, expected)
        
        # Test removing both None and empty values
        result = clean_dict(test_dict, remove_none=True, remove_empty=True)
        expected = {"key1": "value1", "key6": "value6"}
        self.assertEqual(result, expected)

    def test_merge_dicts(self):
        """Test dictionary merging."""
        dict1 = {"a": 1, "b": 2}
        dict2 = {"c": 3, "d": 4}
        dict3 = {"b": 5, "e": 6}  # 'b' should be overwritten
        
        # Test merging multiple dicts
        result = merge_dicts(dict1, dict2, dict3)
        expected = {"a": 1, "b": 5, "c": 3, "d": 4, "e": 6}
        self.assertEqual(result, expected)
        
        # Test with None dict
        result = merge_dicts(dict1, None, dict2)
        expected = {"a": 1, "b": 2, "c": 3, "d": 4}
        self.assertEqual(result, expected)
        
        # Test with empty dict
        result = merge_dicts(dict1, {})
        self.assertEqual(result, dict1)

    def test_parse_date_string(self):
        """Test date string parsing."""
        # Test YYYYMMDD format
        result = parse_date_string("20230215")
        self.assertEqual(result, date(2023, 2, 15))
        
        # Test YYYY-MM-DD format
        result = parse_date_string("2023-02-15")
        self.assertEqual(result, date(2023, 2, 15))
        
        # Test None input
        result = parse_date_string(None)
        self.assertIsNone(result)
        
        # Test empty string
        result = parse_date_string("")
        self.assertIsNone(result)
        
        # Test invalid format
        result = parse_date_string("2023/02/15")
        self.assertIsNone(result)
        
        # Test invalid date
        result = parse_date_string("20230231")  # February 31 doesn't exist
        self.assertIsNone(result)

    def test_calculate_percentage_change(self):
        """Test percentage change calculation."""
        # Test normal calculation
        self.assertEqual(calculate_percentage_change(100, 110), 10.0)
        self.assertEqual(calculate_percentage_change(100, 90), -10.0)
        self.assertEqual(calculate_percentage_change(100, 100), 0.0)
        
        # Test with zero old value
        result = calculate_percentage_change(0, 100)
        self.assertIsNone(result)
        
        # Test with negative values
        self.assertEqual(calculate_percentage_change(-100, -110), 10.0)
        self.assertEqual(calculate_percentage_change(-100, -90), -10.0)

    def test_safe_float_conversion(self):
        """Test safe float conversion."""
        # Test valid conversions
        self.assertEqual(safe_float_conversion("123.45"), 123.45)
        self.assertEqual(safe_float_conversion(123), 123.0)
        self.assertEqual(safe_float_conversion("0"), 0.0)
        self.assertEqual(safe_float_conversion("-123.45"), -123.45)
        
        # Test None and empty string
        self.assertIsNone(safe_float_conversion(None))
        self.assertIsNone(safe_float_conversion(""))
        
        # Test invalid conversions
        self.assertIsNone(safe_float_conversion("abc"))
        self.assertIsNone(safe_float_conversion("123.45.67"))
        self.assertIsNone(safe_float_conversion({}))

    def test_safe_int_conversion(self):
        """Test safe int conversion."""
        # Test valid conversions
        self.assertEqual(safe_int_conversion("123"), 123)
        self.assertEqual(safe_int_conversion(123.45), 123)
        self.assertEqual(safe_int_conversion("123.45"), 123)
        self.assertEqual(safe_int_conversion("0"), 0)
        self.assertEqual(safe_int_conversion("-123"), -123)
        
        # Test None and empty string
        self.assertIsNone(safe_int_conversion(None))
        self.assertIsNone(safe_int_conversion(""))
        
        # Test invalid conversions
        self.assertIsNone(safe_int_conversion("abc"))
        self.assertIsNone(safe_int_conversion("123.45.67"))
        self.assertIsNone(safe_int_conversion({}))


if __name__ == '__main__':
    unittest.main()
