"""
Core Helper Utilities

This module contains helper functions and utilities for the QuantDB core layer.
"""
import os
import time
from datetime import datetime, timedelta, date
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

def format_currency(amount: float, currency: str = "CNY") -> str:
    """
    Format currency amount.
    
    Args:
        amount: Amount to format
        currency: Currency code
        
    Returns:
        Formatted currency string
    """
    if currency == "CNY":
        return f"¥{amount:,.2f}"
    elif currency == "HKD":
        return f"HK${amount:,.2f}"
    elif currency == "USD":
        return f"${amount:,.2f}"
    else:
        return f"{amount:,.2f} {currency}"

def format_percentage(value: float, decimals: int = 2) -> str:
    """
    Format percentage value.

    Args:
        value: Percentage value (e.g., 0.05 for 5%)
        decimals: Number of decimal places

    Returns:
        Formatted percentage string
    """
    return f"{value * 100:.{decimals}f}%"

def format_number(number: Union[int, float]) -> str:
    """
    Format number with thousands separators.

    Args:
        number: Number to format

    Returns:
        Formatted number string
    """
    return f"{number:,}"

def format_currency(amount: float, symbol: str = "¥") -> str:
    """
    Format currency amount.

    Args:
        amount: Amount to format
        symbol: Currency symbol

    Returns:
        Formatted currency string
    """
    if amount < 0:
        return f"-{symbol}{abs(amount):,.2f}"
    return f"{symbol}{amount:,.2f}"

def format_large_number(number: Union[int, float]) -> str:
    """
    Format large numbers with appropriate units.
    
    Args:
        number: Number to format
        
    Returns:
        Formatted number string
    """
    if abs(number) >= 1e12:
        return f"{number / 1e12:.2f}T"
    elif abs(number) >= 1e9:
        return f"{number / 1e9:.2f}B"
    elif abs(number) >= 1e6:
        return f"{number / 1e6:.2f}M"
    elif abs(number) >= 1e3:
        return f"{number / 1e3:.2f}K"
    else:
        return f"{number:.2f}"

def calculate_date_range(days: int, end_date: Optional[str] = None) -> tuple[str, str]:
    """
    Calculate date range.
    
    Args:
        days: Number of days to go back
        end_date: End date in YYYYMMDD format (default: today)
        
    Returns:
        Tuple of (start_date, end_date) in YYYYMMDD format
    """
    if end_date:
        end_dt = datetime.strptime(end_date, '%Y%m%d')
    else:
        end_dt = datetime.now()
    
    start_dt = end_dt - timedelta(days=days)
    
    return start_dt.strftime('%Y%m%d'), end_dt.strftime('%Y%m%d')

def get_trading_days_count(start_date: str, end_date: str) -> int:
    """
    Estimate trading days count between two dates.
    
    Args:
        start_date: Start date in YYYYMMDD format
        end_date: End date in YYYYMMDD format
        
    Returns:
        Estimated number of trading days
    """
    start_dt = datetime.strptime(start_date, '%Y%m%d')
    end_dt = datetime.strptime(end_date, '%Y%m%d')
    
    total_days = (end_dt - start_dt).days + 1
    
    # Rough estimate: 5/7 of days are trading days
    # This doesn't account for holidays but gives a reasonable estimate
    return int(total_days * 5 / 7)

def ensure_directory_exists(file_path: str) -> None:
    """
    Ensure directory exists for a file path.
    
    Args:
        file_path: File path
    """
    directory = os.path.dirname(file_path)
    if directory:
        Path(directory).mkdir(parents=True, exist_ok=True)

def get_file_size_mb(file_path: str) -> float:
    """
    Get file size in MB.
    
    Args:
        file_path: Path to file
        
    Returns:
        File size in MB
    """
    if not os.path.exists(file_path):
        return 0.0
    
    size_bytes = os.path.getsize(file_path)
    return size_bytes / (1024 * 1024)

def timing_decorator(func):
    """
    Decorator to measure function execution time.
    
    Args:
        func: Function to decorate
        
    Returns:
        Decorated function
    """
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        # Add timing info to result if it's a dict
        if isinstance(result, dict) and 'metadata' not in result:
            result['metadata'] = {}
        if isinstance(result, dict) and 'metadata' in result:
            result['metadata']['execution_time_ms'] = execution_time
        
        return result
    return wrapper

def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    Safely divide two numbers.
    
    Args:
        numerator: Numerator
        denominator: Denominator
        default: Default value if division by zero
        
    Returns:
        Division result or default value
    """
    if denominator == 0:
        return default
    return numerator / denominator

def clean_dict(data: Dict[str, Any], remove_none: bool = True, remove_empty: bool = False) -> Dict[str, Any]:
    """
    Clean dictionary by removing None or empty values.
    
    Args:
        data: Dictionary to clean
        remove_none: Remove None values
        remove_empty: Remove empty strings/lists/dicts
        
    Returns:
        Cleaned dictionary
    """
    cleaned = {}
    
    for key, value in data.items():
        if remove_none and value is None:
            continue
        
        if remove_empty and value in ("", [], {}):
            continue
        
        cleaned[key] = value
    
    return cleaned

def merge_dicts(*dicts: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge multiple dictionaries.

    Args:
        *dicts: Dictionaries to merge

    Returns:
        Merged dictionary
    """
    result = {}
    for d in dicts:
        if d:
            result.update(d)
    return result

def parse_date_string(date_str: Optional[str]) -> Optional[date]:
    """
    Parse date string to date object.

    Args:
        date_str: Date string in YYYYMMDD or YYYY-MM-DD format

    Returns:
        Date object or None if invalid
    """
    if not date_str:
        return None

    try:
        if len(date_str) == 8 and date_str.isdigit():
            # YYYYMMDD format
            return datetime.strptime(date_str, '%Y%m%d').date()
        elif len(date_str) == 10 and '-' in date_str:
            # YYYY-MM-DD format
            return datetime.strptime(date_str, '%Y-%m-%d').date()
        else:
            return None
    except ValueError:
        return None

def calculate_percentage_change(old_value: float, new_value: float) -> Optional[float]:
    """
    Calculate percentage change between two values.

    Args:
        old_value: Original value
        new_value: New value

    Returns:
        Percentage change or None if old_value is zero
    """
    if old_value == 0:
        return None

    return ((new_value - old_value) / old_value) * 100

def safe_float_conversion(value: Any) -> Optional[float]:
    """
    Safely convert value to float.

    Args:
        value: Value to convert

    Returns:
        Float value or None if conversion fails
    """
    if value is None or value == "":
        return None

    try:
        return float(value)
    except (ValueError, TypeError):
        return None

def safe_int_conversion(value: Any) -> Optional[int]:
    """
    Safely convert value to int.

    Args:
        value: Value to convert

    Returns:
        Int value or None if conversion fails
    """
    if value is None or value == "":
        return None

    try:
        return int(float(value))  # Handle string floats like "123.45"
    except (ValueError, TypeError):
        return None
