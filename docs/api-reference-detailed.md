# API Reference - Detailed Documentation

This page provides detailed parameter descriptions, return value formats, and code examples for all QuantDB functions.

## Core Functions

### init(cache_dir: Optional[str] = None)

Initialize QuantDB with optional cache directory specification.

**Parameters:**
- `cache_dir` (str, optional): Path to cache directory. Defaults to `~/.qdb_cache`

**Returns:** None

**Example:**
```python
import qdb

# Use default cache directory
qdb.init()

# Use custom cache directory
qdb.init(cache_dir="./my_cache")
```

### get_stock_data(symbol: str, start_date: Optional[str] = None, end_date: Optional[str] = None, days: Optional[int] = None, adjust: str = "") -> DataFrame

Get historical stock data with flexible date specification.

**Parameters:**
- `symbol` (str): Stock symbol (e.g., "000001", "600000")
- `start_date` (str, optional): Start date in "YYYYMMDD" format
- `end_date` (str, optional): End date in "YYYYMMDD" format  
- `days` (int, optional): Get recent N days of data (mutually exclusive with start_date/end_date)
- `adjust` (str): Adjustment type - "" (none), "qfq" (forward), "hfq" (backward)

**Returns:** pandas.DataFrame with columns:
- `股票代码` or `symbol`: Stock symbol
- `open`, `close`, `high`, `low`: OHLC prices
- `volume`, `amount`: Volume and turnover
- Additional columns may vary by data source

**Examples:**
```python
# Get recent 30 days
df = qdb.get_stock_data("000001", days=30)

# Get specific date range
df = qdb.get_stock_data("600000", start_date="20240101", end_date="20240201")

# Get forward-adjusted data
df = qdb.get_stock_data("000001", days=30, adjust="qfq")
```

### get_multiple_stocks(symbols: List[str], days: int = 30, **kwargs) -> Dict[str, DataFrame]

Batch fetch historical data for multiple stocks.

**Parameters:**
- `symbols` (List[str]): List of stock symbols
- `days` (int): Number of recent days to fetch (default: 30)
- `**kwargs`: Additional parameters passed to `get_stock_data`

**Returns:** Dict[str, DataFrame] - Dictionary mapping symbols to their DataFrames

**Example:**
```python
symbols = ["000001", "000002", "600000"]
data = qdb.get_multiple_stocks(symbols, days=30)
print(f"Fetched data for {len(data)} stocks")
```

### get_asset_info(symbol: str) -> Dict[str, Any]

Get basic asset information for a stock symbol.

**Parameters:**
- `symbol` (str): Stock symbol

**Returns:** Dict with keys:
- `symbol` (str): Stock symbol
- `name` (str): Stock name
- `market` (str): Market classification
- `status` (str): Trading status

**Example:**
```python
info = qdb.get_asset_info("000001")
print(f"Stock: {info['name']} ({info['symbol']})")
```

## Realtime Functions

### get_realtime_data(symbol: str, force_refresh: bool = False) -> Dict[str, Any]

Get realtime quote for a single stock.

**Parameters:**
- `symbol` (str): Stock symbol
- `force_refresh` (bool): If True, bypass cache and fetch fresh data

**Returns:** Dict with keys:
- `symbol` (str): Stock symbol
- `error` (str, optional): Error message if data unavailable
- `cache_hit` (bool): Whether data came from cache
- `timestamp` (str): Data timestamp
- Additional fields may include price, volume data when available

**Example:**
```python
tick = qdb.get_realtime_data("000001")
if 'error' not in tick:
    print(f"Realtime data for {tick['symbol']}")
```

### get_realtime_data_batch(symbols: List[str], force_refresh: bool = False) -> Dict[str, Dict[str, Any]]

Get realtime quotes for multiple stocks.

**Parameters:**
- `symbols` (List[str]): List of stock symbols
- `force_refresh` (bool): If True, bypass cache and fetch fresh data

**Returns:** Dict[str, Dict[str, Any]] - Dictionary mapping symbols to their realtime data

**Example:**
```python
symbols = ["000001", "000002"]
batch_data = qdb.get_realtime_data_batch(symbols)
for symbol, data in batch_data.items():
    print(f"{symbol}: {data}")
```

## Stock List Functions

### get_stock_list(market: Optional[str] = None, force_refresh: bool = False) -> List[Dict[str, Any]]

Get list of available stocks with market filtering.

**Parameters:**
- `market` (str, optional): Market filter ('SHSE', 'SZSE', 'HKEX', or None for all)
- `force_refresh` (bool): If True, bypass cache and fetch fresh data

**Returns:** List[Dict[str, Any]] - List of stock information dictionaries

Each dictionary contains:
- `symbol` (str): Stock symbol
- `name` (str): Stock name
- `market` (str): Market classification
- `price` (float): Current price
- `pct_change` (float): Percentage change
- Additional fields may vary

**Example:**
```python
# Get all stocks (cached daily)
all_stocks = qdb.get_stock_list()
print(f"Total stocks: {len(all_stocks)}")

# Get stocks from specific market
shse_stocks = qdb.get_stock_list(market="SHSE")
```

## Index Functions

### get_index_data(symbol: str, start_date: Optional[str] = None, end_date: Optional[str] = None, period: str = "daily", force_refresh: bool = False) -> DataFrame

Get historical index data.

**Parameters:**
- `symbol` (str): Index symbol (e.g., '000001', '399001')
- `start_date` (str, optional): Start date in "YYYYMMDD" format
- `end_date` (str, optional): End date in "YYYYMMDD" format
- `period` (str): Data frequency ('daily', 'weekly', 'monthly')
- `force_refresh` (bool): If True, bypass cache and fetch fresh data

**Returns:** pandas.DataFrame with index historical data

### get_index_realtime(symbol: str, force_refresh: bool = False) -> Dict[str, Any]

Get realtime index quote.

**Parameters:**
- `symbol` (str): Index symbol
- `force_refresh` (bool): If True, bypass cache and fetch fresh data

**Returns:** Dict with realtime index data

### get_index_list(category: Optional[str] = None, force_refresh: bool = False) -> List[Dict[str, Any]]

Get list of available indices.

**Parameters:**
- `category` (str, optional): Index category filter
- `force_refresh` (bool): If True, bypass cache and fetch fresh data

**Returns:** List of index information dictionaries

## Financial Functions

### get_financial_summary(symbol: str, force_refresh: bool = False) -> Dict[str, Any]

Get financial summary data for recent quarters.

**Parameters:**
- `symbol` (str): Stock symbol
- `force_refresh` (bool): If True, bypass cache and fetch fresh data

**Returns:** Dict with keys:
- `symbol` (str): Stock symbol
- `data_type` (str): "financial_summary"
- `quarters` (List[Dict]): List of quarterly data
- `count` (int): Number of quarters
- `timestamp` (str): Data timestamp

Each quarter dict may contain:
- `period` (str): Quarter period
- `net_profit` (float): Net profit
- `total_revenue` (float): Total revenue
- `roe` (float): Return on equity
- `roa` (float): Return on assets

**Example:**
```python
summary = qdb.get_financial_summary("000001")
if 'quarters' in summary:
    for quarter in summary['quarters']:
        print(f"Period: {quarter['period']}, ROE: {quarter.get('roe', 'N/A')}")
```

### get_financial_indicators(symbol: str, force_refresh: bool = False) -> Dict[str, Any]

Get financial indicators data.

**Parameters:**
- `symbol` (str): Stock symbol
- `force_refresh` (bool): If True, bypass cache and fetch fresh data

**Returns:** Dict with keys:
- `symbol` (str): Stock symbol
- `data_type` (str): "financial_indicators"
- `data_shape` (str): Shape of underlying data
- `columns` (List[str]): Sample column names
- `sample_data` (List[Dict]): Sample rows
- `timestamp` (str): Data timestamp

## Cache Management

### cache_stats() -> Dict[str, Any]

Get cache statistics and status information.

**Returns:** Dict with keys:
- `cache_dir` (str): Cache directory path
- `cache_size_mb` (float): Cache size in megabytes
- `initialized` (bool): Whether cache is initialized
- `status` (str): Cache status

**Example:**
```python
stats = qdb.cache_stats()
print(f"Cache size: {stats['cache_size_mb']:.2f} MB")
print(f"Status: {stats['status']}")
```

### clear_cache(symbol: Optional[str] = None) -> None

Clear cache data.

**Parameters:**
- `symbol` (str, optional): Specific symbol to clear (not implemented in simplified mode)

**Returns:** None

**Example:**
```python
# Clear all cache
qdb.clear_cache()

# Note: Per-symbol clearing not yet implemented in simplified mode
# qdb.clear_cache("000001")  # This will show a warning
```

## AKShare Compatibility

### stock_zh_a_hist(symbol: str, start_date: Optional[str] = None, end_date: Optional[str] = None, **kwargs) -> DataFrame

AKShare-compatible interface for historical stock data.

**Parameters:**
- `symbol` (str): Stock symbol
- `start_date` (str, optional): Start date in "YYYYMMDD" format
- `end_date` (str, optional): End date in "YYYYMMDD" format
- `**kwargs`: Additional parameters

**Returns:** pandas.DataFrame - Same as `get_stock_data`

**Example:**
```python
# Drop-in replacement for AKShare
df = qdb.stock_zh_a_hist("000001", start_date="20240101", end_date="20240201")
```

## Configuration

### set_cache_dir(cache_dir: str) -> None

Set cache directory path.

**Parameters:**
- `cache_dir` (str): Path to cache directory

**Returns:** None

### set_log_level(level: str) -> None

Set logging level.

**Parameters:**
- `level` (str): Log level ("DEBUG", "INFO", "WARNING", "ERROR")

**Returns:** None

## Exceptions

- **QDBError**: Base exception for QuantDB errors
- **CacheError**: Cache-related errors
- **DataError**: Data fetching/processing errors  
- **NetworkError**: Network-related errors

**Example:**
```python
from qdb import QDBError, DataError

try:
    df = qdb.get_stock_data("INVALID")
except DataError as e:
    print(f"Data error: {e}")
except QDBError as e:
    print(f"General QDB error: {e}")
```
