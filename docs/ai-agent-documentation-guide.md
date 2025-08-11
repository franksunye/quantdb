# QDB AI Agent Documentation Guide

## 概述

本文档提供了让AI agent更好理解和使用QDB包的文档标准和最佳实践。

## AI Agent友好的Docstring标准

### 1. 使用Google Style Docstring格式

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

### 2. 返回值结构详细说明

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

### 3. 异常处理详细说明

所有函数都应该明确说明：
- 什么情况下抛出什么异常
- 异常的具体含义
- 如何处理这些异常

### 4. 参数验证规则

明确说明每个参数的：
- 数据类型
- 有效值范围
- 格式要求
- 默认值含义

## AI Agent Schema定义

为了让AI agent更好地理解API，建议创建JSON Schema定义：

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

## 实施建议

1. **优先级1**: 标准化所有公共API的docstring格式
2. **优先级2**: 添加详细的参数约束和返回值结构说明
3. **优先级3**: 创建JSON Schema文件供AI agent使用
4. **优先级4**: 添加更多实际使用示例

这样的改进将大大提升AI agent理解和使用你的包的能力。
