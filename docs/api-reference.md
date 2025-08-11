# API Reference (Public Interface)

The following functions are exported by qdb (see qdb/__init__.py). Parameters and return types follow the implementation.

## Core
- init(cache_dir: Optional[str] = None)
  - Initialize QuantDB and set cache directory (optional). First call is lazy-inited automatically.

- get_stock_data(symbol: str, start_date: Optional[str] = None, end_date: Optional[str] = None, days: Optional[int] = None, adjust: str = "") -> DataFrame
  - Get historical OHLCV for a stock. Either use `days` or `start_date`/`end_date`.
  - Example: `qdb.get_stock_data("000001", days=30)`; `qdb.get_stock_data("600000", start_date="20240101", end_date="20240201")`

- get_multiple_stocks(symbols: List[str], days: int = 30, **kwargs) -> Dict[str, DataFrame]
  - Batch fetch for multiple symbols; forwards kwargs to `get_stock_data`.

- get_asset_info(symbol: str) -> Dict[str, Any]
  - Basic asset info (symbol, name, market, status).

## Realtime
- get_realtime_data(symbol: str, force_refresh: bool = False) -> Dict[str, Any]
  - Realtime quote for a single symbol. May return fallback/mock data if source unavailable.

- get_realtime_data_batch(symbols: List[str], force_refresh: bool = False) -> Dict[str, Dict[str, Any]]
  - Realtime quotes for multiple symbols.

## Index
- get_index_data(symbol: str, start_date: Optional[str] = None, end_date: Optional[str] = None, period: str = "daily", force_refresh: bool = False) -> DataFrame
  - Historical index data for specified period ('daily'|'weekly'|'monthly').
  - **Hong Kong Support**: HSI, HSCEI, HSTECH with aliases (^HSI, HK.HSI, HANG SENG, etc.)
- get_index_realtime(symbol: str, force_refresh: bool = False) -> Dict[str, Any]
  - Realtime index quote.
  - **Hong Kong Support**: Real-time quotes for HSI, HSCEI, HSTECH
- get_index_list(category: Optional[str] = None, force_refresh: bool = False) -> List[Dict[str, Any]]
  - Daily-cached index list by category.
  - **Categories**: "沪深重要指数", "上证系列指数", "深证系列指数", "中证系列指数", "香港指数"

## Stock List
- get_stock_list(market: Optional[str] = None, force_refresh: bool = False) -> List[Dict[str, Any]]
  - Daily-cached list of stocks; first run may take minutes to warm up.

## Financials
- get_financial_summary(symbol: str, force_refresh: bool = False) -> Dict[str, Any]
  - Latest quarters summary (net_profit, total_revenue, roe, etc.).

- get_financial_indicators(symbol: str, force_refresh: bool = False) -> Dict[str, Any]
  - Sample columns and a few rows for indicators; may be empty for some symbols.

## Cache
- cache_stats() -> Dict[str, Any]
  - Cache directory, size (MB), and current status.
- clear_cache(symbol: Optional[str] = None) -> None
  - Clear all cache. Note: per-symbol clearing is not implemented in simplified mode.

## AKShare Compatibility
- stock_zh_a_hist(symbol: str, start_date: Optional[str] = None, end_date: Optional[str] = None, **kwargs) -> DataFrame
  - Compatibility alias of `get_stock_data`.

## Configuration
- set_cache_dir(cache_dir: str) -> None
- set_log_level(level: str) -> None

## Exceptions
- QDBError
- CacheError
- DataError
- NetworkError

## 📚 More Details

For detailed parameter descriptions, return value formats, and comprehensive examples, see:
- [API Reference - Detailed Documentation](api-reference-detailed.md)

Note: Full auto-generated docs using mkdocstrings will be available in a future update.

