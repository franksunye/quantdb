---
title: AI Agent Developer Guide - QuantDB
description: Comprehensive guide for AI agents and automated tools on how to understand and use QuantDB effectively, including docstring standards and best practices.
keywords: ai agent development, api documentation, google style docstrings, function signatures, error handling
---

# AI Agent Developer Guide

This comprehensive guide provides documentation standards and best practices for helping AI agents better understand and use the QuantDB package.

## Overview

QuantDB is designed with AI agents in mind, providing structured documentation and schemas that enable automated tools to:

- Generate accurate code examples
- Validate function calls and parameters  
- Provide intelligent error handling
- Understand package structure and conventions

## AI Agent-Friendly Docstring Standards

### 1. Google Style Docstring Format

QuantDB follows Google-style docstrings with enhanced type information for AI consumption:

```python
def get_stock_data(
    symbol: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    days: Optional[int] = None,
    adjust: str = ""
) -> pd.DataFrame:
    """Get historical stock data with intelligent caching.
    
    Retrieves historical stock price data for Chinese A-shares with automatic
    caching to improve performance. Data is fetched from AKShare and cached
    locally using SQLite.
    
    Args:
        symbol (str): Stock symbol in 6-digit format. Supports:
            - Shanghai Stock Exchange: 600000-699999
            - Shenzhen Stock Exchange: 000000-399999
            - Examples: "000001", "600000", "300001"
        start_date (str, optional): Start date in YYYYMMDD format.
            Must be a valid trading date. Example: "20240101"
        end_date (str, optional): End date in YYYYMMDD format.
            Must be >= start_date. Example: "20240201"
        days (int, optional): Number of recent trading days to fetch.
            Range: 1-1000. Mutually exclusive with start_date/end_date.
        adjust (str, optional): Price adjustment type. Options:
            - "": No adjustment (default)
            - "qfq": Forward adjustment
            - "hfq": Backward adjustment
    
    Returns:
        pd.DataFrame: Historical stock data with columns:
            - date (datetime): Trading date
            - open (float): Opening price
            - high (float): Highest price
            - low (float): Lowest price
            - close (float): Closing price
            - volume (int): Trading volume
            - amount (float): Trading amount
    
    Raises:
        ValueError: If symbol format is invalid or date parameters are invalid.
        NetworkError: If unable to fetch data from AKShare after retries.
        CacheError: If local cache operations fail.
        DataError: If returned data is empty or malformed.
    
    Examples:
        Get last 30 days of data:
        >>> df = qdb.get_stock_data("000001", days=30)
        >>> print(f"Retrieved {len(df)} trading days")
        
        Get data for specific date range:
        >>> df = qdb.get_stock_data(
        ...     "600000", 
        ...     start_date="20240101", 
        ...     end_date="20240201"
        ... )
        
        Get forward-adjusted data:
        >>> df = qdb.get_stock_data("000001", days=100, adjust="qfq")
    
    Note:
        - Data is automatically cached for improved performance
        - Only trading days are included in the results
        - Cache is updated automatically for recent data
        - Historical data (>1 day old) is cached permanently
    """
```

### 2. Detailed Return Value Structure

For complex return types, provide comprehensive structure documentation:

```python
def get_realtime_data(symbol: str, force_refresh: bool = False) -> Dict[str, Any]:
    """Get real-time stock quote data.
    
    Args:
        symbol (str): Stock symbol in 6-digit format (e.g., "000001", "600000")
        force_refresh (bool, optional): If True, bypass cache and fetch fresh data.
            Defaults to False.
    
    Returns:
        Dict[str, Any]: Real-time stock data containing:
            - symbol (str): Stock symbol
            - name (str): Stock name in Chinese
            - current_price (float): Current trading price
            - change (float): Price change from previous close
            - change_percent (float): Percentage change
            - volume (int): Current day trading volume
            - amount (float): Current day trading amount
            - high (float): Day's highest price
            - low (float): Day's lowest price
            - open (float): Opening price
            - previous_close (float): Previous trading day's closing price
            - timestamp (str): Data timestamp in ISO format
    
    Raises:
        ValueError: If symbol format is invalid.
        NetworkError: If unable to fetch real-time data.
        DataError: If returned data is incomplete.
    
    Examples:
        >>> data = qdb.get_realtime_data("000001")
        >>> print(f"{data['name']}: {data['current_price']}")
        
        >>> # Force refresh from source
        >>> fresh_data = qdb.get_realtime_data("600000", force_refresh=True)
    """
```

## Exception Handling Standards

### 3. Comprehensive Exception Documentation

All functions clearly specify:

- **What exceptions are thrown** under what circumstances
- **The specific meaning** of each exception
- **How to handle** these exceptions appropriately

**Exception Types:**
- `ValueError`: Invalid input parameters
- `NetworkError`: Network connectivity issues
- `CacheError`: Local cache operation failures
- `DataError`: Data validation or format issues

### 4. Parameter Validation Rules

For each parameter, specify:

- **Data type** with Python type hints
- **Valid value range** with explicit constraints
- **Format requirements** with examples
- **Default value meaning** and behavior

## AI Agent Schema Integration

### JSON Schema Definition

QuantDB provides structured JSON schemas for AI agent consumption:

```json
{
  "functions": [
    {
      "name": "get_stock_data",
      "description": "Get historical stock data with intelligent caching",
      "parameters": {
        "type": "object",
        "properties": {
          "symbol": {
            "type": "string",
            "pattern": "^[0-9]{6}$",
            "description": "6-digit stock symbol (e.g., 000001, 600000)"
          },
          "start_date": {
            "type": "string",
            "pattern": "^[0-9]{8}$",
            "description": "Start date in YYYYMMDD format"
          },
          "end_date": {
            "type": "string", 
            "pattern": "^[0-9]{8}$",
            "description": "End date in YYYYMMDD format"
          },
          "days": {
            "type": "integer",
            "minimum": 1,
            "maximum": 1000,
            "description": "Number of recent trading days"
          },
          "adjust": {
            "type": "string",
            "enum": ["", "qfq", "hfq"],
            "description": "Price adjustment type"
          }
        },
        "required": ["symbol"]
      }
    }
  ]
}
```

## Best Practices for AI Code Generation

### 1. Error Handling Patterns

```python
# Recommended pattern for AI-generated code
try:
    data = qdb.get_stock_data("600000", days=30)
    if data.empty:
        print("No data available for the specified period")
    else:
        print(f"Retrieved {len(data)} trading days")
except ValueError as e:
    print(f"Invalid parameters: {e}")
except NetworkError as e:
    print(f"Network error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

### 2. Parameter Validation

```python
# AI agents should generate validation code
def validate_symbol(symbol: str) -> bool:
    """Validate stock symbol format."""
    return len(symbol) == 6 and symbol.isdigit()

# Usage in generated code
if not validate_symbol(symbol):
    raise ValueError(f"Invalid symbol format: {symbol}")
```

### 3. Caching Awareness

```python
# AI-generated code should leverage caching
# For recent data, cache is automatically managed
recent_data = qdb.get_stock_data("000001", days=5)

# For historical data, consider cache warming
historical_data = qdb.get_stock_data(
    "600000", 
    start_date="20230101", 
    end_date="20231231"
)
```

## Implementation Priorities

### Priority 1: Core Documentation
- Standardize docstring format for all public APIs
- Ensure type hints are comprehensive and accurate
- Document all exception conditions

### Priority 2: Enhanced Metadata
- Add detailed parameter constraints
- Provide complete return value structure descriptions
- Include performance characteristics

### Priority 3: AI Integration
- Create comprehensive JSON Schema files
- Provide structured function definitions
- Enable automated validation

### Priority 4: Examples and Patterns
- Add practical usage examples
- Document common patterns and anti-patterns
- Provide performance optimization guidelines

## Validation and Testing

AI agents should validate generated code against:

1. **Type constraints** defined in function signatures
2. **Parameter ranges** specified in documentation
3. **Return value structure** as documented
4. **Exception handling** patterns

## Continuous Improvement

QuantDB's AI agent support evolves based on:

- **Feedback from AI tool developers**
- **Analysis of generated code quality**
- **Performance metrics from automated tools**
- **Community contributions and suggestions**

---

For the complete API schema and additional resources, see the [API Schema](api-schema.md) page.
