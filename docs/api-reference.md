# API 参考（公开接口）

下列函数来自 qdb 的公开 API（参考 qdb/__init__.py）。参数与返回类型以实际实现为准。

## 核心功能
- init(cache_dir: Optional[str] = None)
- get_stock_data(symbol: str, start_date: Optional[str] = None, end_date: Optional[str] = None, **kwargs) -> DataFrame
- get_multiple_stocks(stocks: List[str], days: int = 30, **kwargs) -> Dict[str, DataFrame]
- get_asset_info(symbol: str) -> Dict[str, Any]

## 实时数据
- get_realtime_data(symbol: str, force_refresh: bool = False) -> Dict[str, Any]
- get_realtime_data_batch(symbols: List[str], force_refresh: bool = False) -> List[Dict[str, Any]]

## 股票列表
- get_stock_list(market: Optional[str] = None, force_refresh: bool = False) -> List[Dict[str, Any]]

## 财务数据
- get_financial_summary(symbol: str) -> Dict[str, Any]
- get_financial_indicators(symbol: str) -> Dict[str, Any]

## 缓存管理
- cache_stats() -> Dict[str, Any]
- clear_cache(symbol: Optional[str] = None) -> None

## AKShare 兼容接口
- stock_zh_a_hist(symbol: str, start_date: Optional[str] = None, end_date: Optional[str] = None, **kwargs) -> DataFrame

## 配置
- set_cache_dir(cache_dir: str) -> None
- set_log_level(level: str) -> None

## 异常类型
- QDBError
- CacheError
- DataError
- NetworkError

提示：未来将接入 mkdocstrings 自动生成 API 文档。

