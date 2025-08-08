# API Reference (Public Interface)

The following functions are exported by qdb (see qdb/__init__.py). Parameters and return types follow the implementation.

## Core
- init(cache_dir: Optional[str] = None)
- get_stock_data(symbol: str, start_date: Optional[str] = None, end_date: Optional[str] = None, **kwargs) -> DataFrame
- get_multiple_stocks(stocks: List[str], days: int = 30, **kwargs) -> Dict[str, DataFrame]
- get_asset_info(symbol: str) -> Dict[str, Any]

## Realtime
- get_realtime_data(symbol: str, force_refresh: bool = False) -> Dict[str, Any]
- get_realtime_data_batch(symbols: List[str], force_refresh: bool = False) -> List[Dict[str, Any]]

## Stock List
- get_stock_list(market: Optional[str] = None, force_refresh: bool = False) -> List[Dict[str, Any]]

## Financials
- get_financial_summary(symbol: str) -> Dict[str, Any]
- get_financial_indicators(symbol: str) -> Dict[str, Any]

## Cache
- cache_stats() -> Dict[str, Any]
- clear_cache(symbol: Optional[str] = None) -> None

## AKShare Compatibility
- stock_zh_a_hist(symbol: str, start_date: Optional[str] = None, end_date: Optional[str] = None, **kwargs) -> DataFrame

## Configuration
- set_cache_dir(cache_dir: str) -> None
- set_log_level(level: str) -> None

## Exceptions
- QDBError
- CacheError
- DataError
- NetworkError

Note: We plan to adopt mkdocstrings to auto-generate detailed API docs.

