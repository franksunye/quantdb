"""
Core Validation Utilities

This module contains validation functions and utilities for the QuantDB core layer.
"""
import re
from datetime import datetime
from typing import Optional, Tuple, Union

def validate_stock_symbol(symbol: str) -> bool:
    """
    Validate stock symbol format.
    
    Args:
        symbol: Stock symbol to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not symbol or not isinstance(symbol, str):
        return False
    
    # Remove whitespace
    symbol = symbol.strip()
    
    # Check for empty string after stripping
    if not symbol:
        return False
    
    # Remove market prefix if present (for A-shares)
    clean_symbol = symbol
    if clean_symbol.lower().startswith(("sh", "sz")):
        clean_symbol = clean_symbol[2:]
    
    # Remove suffix if present
    if "." in clean_symbol:
        clean_symbol = clean_symbol.split(".")[0]
    
    # Must be numeric
    if not clean_symbol.isdigit():
        return False
    
    # A-shares: 6-digit number (000001, 600000)
    if re.match(r'^\d{6}$', clean_symbol):
        return True
    
    # Hong Kong stocks: 5-digit number (02171, 00700)
    if re.match(r'^\d{5}$', clean_symbol):
        return True
    
    return False

def validate_date_format(date_str: str) -> bool:
    """
    Validate date string format (YYYYMMDD).
    
    Args:
        date_str: Date string to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not date_str or not isinstance(date_str, str):
        return False
    
    # Check format
    if not re.match(r'^\d{8}$', date_str):
        return False
    
    # Check if date is valid
    try:
        datetime.strptime(date_str, '%Y%m%d')
        return True
    except ValueError:
        return False

def validate_date_range(start_date: str, end_date: str) -> Tuple[bool, Optional[str]]:
    """
    Validate date range.
    
    Args:
        start_date: Start date in YYYYMMDD format
        end_date: End date in YYYYMMDD format
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Validate individual dates
    if not validate_date_format(start_date):
        return False, f"Invalid start date format: {start_date}"
    
    if not validate_date_format(end_date):
        return False, f"Invalid end date format: {end_date}"
    
    # Check date order
    start_dt = datetime.strptime(start_date, '%Y%m%d')
    end_dt = datetime.strptime(end_date, '%Y%m%d')
    
    if start_dt > end_dt:
        return False, f"Start date {start_date} cannot be after end date {end_date}"
    
    # Check if dates are too far in the future
    today = datetime.now()
    if start_dt > today:
        return False, f"Start date {start_date} cannot be in the future"
    
    return True, None

def detect_market_type(symbol: str) -> str:
    """
    Detect market type based on symbol format.
    
    Args:
        symbol: Stock symbol
        
    Returns:
        Market type: 'A_STOCK', 'HK_STOCK', or 'UNKNOWN'
    """
    if not validate_stock_symbol(symbol):
        return 'UNKNOWN'
    
    # Clean symbol
    clean_symbol = symbol.strip()
    if clean_symbol.lower().startswith(("sh", "sz")):
        clean_symbol = clean_symbol[2:]
    if "." in clean_symbol:
        clean_symbol = clean_symbol.split(".")[0]
    
    # Determine market by length
    if len(clean_symbol) == 6:
        return 'A_STOCK'
    elif len(clean_symbol) == 5:
        return 'HK_STOCK'
    else:
        return 'UNKNOWN'

def normalize_symbol(symbol: str) -> str:
    """
    Normalize stock symbol to standard format.
    
    Args:
        symbol: Stock symbol to normalize
        
    Returns:
        Normalized symbol
    """
    if not symbol:
        return ""
    
    # Remove whitespace
    symbol = symbol.strip()
    
    # Remove market prefix if present
    if symbol.lower().startswith(("sh", "sz")):
        symbol = symbol[2:]
    
    # Remove suffix if present
    if "." in symbol:
        symbol = symbol.split(".")[0]
    
    # Ensure it's uppercase (for consistency)
    return symbol.upper()

def validate_adjust_parameter(adjust: str) -> bool:
    """
    Validate price adjustment parameter.
    
    Args:
        adjust: Adjustment parameter
        
    Returns:
        True if valid, False otherwise
    """
    valid_adjusts = ["", "qfq", "hfq"]
    return adjust in valid_adjusts

def validate_period_parameter(period: str) -> bool:
    """
    Validate period parameter.
    
    Args:
        period: Period parameter
        
    Returns:
        True if valid, False otherwise
    """
    valid_periods = ["daily", "weekly", "monthly"]
    return period in valid_periods
