"""
QDB Client - Simplified User Interface

Encapsulates core/ functionality, provides concise and easy-to-use API
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Optional, Union, Any
import pandas as pd
from datetime import datetime, timedelta

# Add project root directory to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from .exceptions import QDBError, CacheError, DataError, NetworkError

class QDBClient:
    """QDB client, manages local cache and data acquisition"""

    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialize QDB client

        Args:
            cache_dir: Cache directory path, defaults to ~/.qdb_cache
        """
        self.cache_dir = cache_dir or os.path.expanduser("~/.qdb_cache")
        self._ensure_cache_dir()
        self._db_session = None
        self._akshare_adapter = None
        self._stock_service = None
        self._asset_service = None
        self._initialized = False
        
    def _ensure_cache_dir(self):
        """Ensure cache directory exists"""
        Path(self.cache_dir).mkdir(parents=True, exist_ok=True)

    def _lazy_init(self):
        """Lazy initialization of core components"""
        if self._initialized:
            return

        try:
            # Set database path
            db_path = os.path.join(self.cache_dir, "qdb_cache.db")
            os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"

            # 导入核心组件（避免导入FastAPI相关模块）
            from core.database.connection import get_db, Base, engine
            from core.cache.akshare_adapter import AKShareAdapter

            # 创建数据库表
            Base.metadata.create_all(bind=engine)

            # 初始化组件
            self._db_session = next(get_db())
            self._akshare_adapter = AKShareAdapter()

            # 简化版服务（避免导入复杂的服务层）
            self._initialized = True

        except Exception as e:
            raise QDBError(f"初始化QDB客户端失败: {str(e)}")
    
    def get_stock_data(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        days: Optional[int] = None,
        adjust: str = ""
    ) -> pd.DataFrame:
        """
        获取股票历史数据

        Args:
            symbol: 股票代码，如 "000001", "600000"
            start_date: 开始日期，格式 "20240101"
            end_date: 结束日期，格式 "20240201"
            days: 获取最近N天数据（与start_date/end_date互斥）
            adjust: 复权类型，"" 不复权，"qfq" 前复权，"hfq" 后复权

        Returns:
            包含股票数据的DataFrame

        Examples:
            >>> df = qdb.get_stock_data("000001", days=30)
            >>> df = qdb.get_stock_data("600000", start_date="20240101", end_date="20240201")
        """
        self._lazy_init()

        try:
            # 处理days参数
            if days is not None:
                end_date = datetime.now().strftime("%Y%m%d")
                start_date = (datetime.now() - timedelta(days=days*2)).strftime("%Y%m%d")  # *2确保有足够交易日

            # 直接使用AKShare适配器获取数据（简化版）
            return self._akshare_adapter.get_stock_data(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                adjust=adjust
            )

        except Exception as e:
            raise DataError(f"获取股票数据失败 {symbol}: {str(e)}")
    
    def get_multiple_stocks(
        self, 
        symbols: List[str], 
        days: int = 30,
        **kwargs
    ) -> Dict[str, pd.DataFrame]:
        """
        批量获取多只股票数据
        
        Args:
            symbols: 股票代码列表
            days: 获取最近N天数据
            **kwargs: 其他参数传递给get_stock_data
            
        Returns:
            字典，键为股票代码，值为对应的DataFrame
        """
        result = {}
        for symbol in symbols:
            try:
                result[symbol] = self.get_stock_data(symbol, days=days, **kwargs)
            except Exception as e:
                print(f"⚠️ 获取 {symbol} 数据失败: {e}")
                result[symbol] = pd.DataFrame()  # 返回空DataFrame
        return result
    
    def get_asset_info(self, symbol: str) -> Dict[str, Any]:
        """
        获取资产基本信息

        Args:
            symbol: 股票代码

        Returns:
            包含资产信息的字典
        """
        self._lazy_init()

        try:
            # 简化版：直接返回基本信息
            return {
                "symbol": symbol,
                "name": f"股票{symbol}",
                "market": "A股" if symbol.startswith(('0', '3', '6')) else "未知",
                "status": "正常"
            }
        except Exception as e:
            raise DataError(f"获取资产信息失败 {symbol}: {str(e)}")
    
    def cache_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            包含缓存统计的字典
        """
        try:
            # 计算缓存目录大小
            cache_size = 0
            if Path(self.cache_dir).exists():
                cache_size = sum(
                    f.stat().st_size for f in Path(self.cache_dir).rglob('*') if f.is_file()
                ) / (1024 * 1024)  # MB

            return {
                "cache_dir": self.cache_dir,
                "cache_size_mb": round(cache_size, 2),
                "initialized": self._initialized,
                "status": "Running" if self._initialized else "Not initialized"
            }

        except Exception as e:
            raise CacheError(f"获取缓存统计失败: {str(e)}")
    
    def clear_cache(self, symbol: Optional[str] = None):
        """
        清除缓存

        Args:
            symbol: 指定股票代码，None表示清除所有缓存
        """
        try:
            if symbol:
                print(f"⚠️ 清除特定股票缓存功能暂未实现: {symbol}")
            else:
                # 清除缓存目录
                if Path(self.cache_dir).exists():
                    import shutil
                    shutil.rmtree(self.cache_dir)
                    Path(self.cache_dir).mkdir(parents=True, exist_ok=True)
                    print("✅ Cache cleared")
                    self._initialized = False
                else:
                    print("⚠️ 缓存目录不存在")

        except Exception as e:
            raise CacheError(f"清除缓存失败: {str(e)}")

    def get_financial_summary(self, symbol: str, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Get financial summary data for a stock symbol

        Args:
            symbol: Stock symbol (e.g., '000001', '600000')
            force_refresh: If True, bypass cache and fetch fresh data

        Returns:
            Dictionary containing financial summary data
        """
        self._lazy_init()

        try:
            print(f"📊 Getting financial summary for {symbol}...")

            # Use AKShare adapter to get financial summary
            df = self._akshare_adapter.get_financial_summary(symbol)

            if df.empty:
                print(f"⚠️ No financial summary data available for {symbol}")
                return {
                    'symbol': symbol,
                    'error': 'No financial summary data available',
                    'timestamp': datetime.now().isoformat()
                }

            # Process the data into a simplified format
            quarters = []
            date_columns = [col for col in df.columns if col not in ['选项', '指标']]

            # Get latest 4 quarters
            for date_col in date_columns[:4]:
                quarter_data = {'period': date_col}

                for _, row in df.iterrows():
                    indicator = row['指标']
                    value = row.get(date_col)

                    if value is not None and not pd.isna(value):
                        # Map key indicators
                        if indicator == '归母净利润':
                            quarter_data['net_profit'] = float(value)
                        elif indicator == '营业总收入':
                            quarter_data['total_revenue'] = float(value)
                        elif indicator == '营业成本':
                            quarter_data['operating_cost'] = float(value)
                        elif indicator == '净资产收益率':
                            quarter_data['roe'] = float(value)
                        elif indicator == '总资产收益率':
                            quarter_data['roa'] = float(value)

                quarters.append(quarter_data)

            result = {
                'symbol': symbol,
                'data_type': 'financial_summary',
                'quarters': quarters,
                'count': len(quarters),
                'timestamp': datetime.now().isoformat()
            }

            print(f"✅ Retrieved financial summary for {symbol} ({len(quarters)} quarters)")
            return result

        except Exception as e:
            print(f"⚠️ Error getting financial summary for {symbol}: {e}")
            return {
                'symbol': symbol,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def get_financial_indicators(self, symbol: str, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Get financial indicators data for a stock symbol

        Args:
            symbol: Stock symbol (e.g., '000001', '600000')
            force_refresh: If True, bypass cache and fetch fresh data

        Returns:
            Dictionary containing financial indicators data
        """
        self._lazy_init()

        try:
            print(f"📈 Getting financial indicators for {symbol}...")

            # Use AKShare adapter to get financial indicators
            df = self._akshare_adapter.get_financial_indicators(symbol)

            if df.empty:
                print(f"⚠️ No financial indicators data available for {symbol}")
                return {
                    'symbol': symbol,
                    'error': 'No financial indicators data available',
                    'timestamp': datetime.now().isoformat()
                }

            # Process the indicators data
            result = {
                'symbol': symbol,
                'data_type': 'financial_indicators',
                'data_shape': f"{df.shape[0]}x{df.shape[1]}",
                'columns': list(df.columns)[:10],  # First 10 columns as sample
                'sample_data': df.head(3).to_dict('records') if len(df) > 0 else [],
                'timestamp': datetime.now().isoformat()
            }

            print(f"✅ Retrieved financial indicators for {symbol} (shape: {df.shape})")
            return result

        except Exception as e:
            print(f"⚠️ Error getting financial indicators for {symbol}: {e}")
            return {
                'symbol': symbol,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

# 全局客户端实例
_global_client: Optional[QDBClient] = None

def _get_client():
    """获取全局客户端实例"""
    global _global_client
    if _global_client is None:
        # 直接使用简化版，避免依赖问题
        _global_client = SimpleQDBClient()
    return _global_client

# 导入简化客户端作为后备
from .simple_client import SimpleQDBClient

# 公开API函数
def init(cache_dir: Optional[str] = None):
    """
    初始化QDB

    Args:
        cache_dir: 缓存目录路径
    """
    global _global_client
    # 直接使用简化版客户端，避免依赖问题
    print("🚀 Using QDB simplified mode (standalone version)")
    _global_client = SimpleQDBClient(cache_dir)
    print(f"✅ QDB initialized, cache directory: {_global_client.cache_dir}")

def get_stock_data(symbol: str, **kwargs) -> pd.DataFrame:
    """获取股票数据"""
    return _get_client().get_stock_data(symbol, **kwargs)

def get_multiple_stocks(symbols: List[str], **kwargs) -> Dict[str, pd.DataFrame]:
    """批量获取股票数据"""
    return _get_client().get_multiple_stocks(symbols, **kwargs)

def get_asset_info(symbol: str) -> Dict[str, Any]:
    """获取资产信息"""
    return _get_client().get_asset_info(symbol)

def cache_stats() -> Dict[str, Any]:
    """获取缓存统计"""
    return _get_client().cache_stats()

def clear_cache(symbol: Optional[str] = None):
    """清除缓存"""
    return _get_client().clear_cache(symbol)

# AKShare兼容接口
def stock_zh_a_hist(symbol: str, **kwargs) -> pd.DataFrame:
    """
    兼容AKShare的股票历史数据接口
    
    Args:
        symbol: 股票代码
        **kwargs: 其他参数
        
    Returns:
        股票历史数据DataFrame
    """
    return get_stock_data(symbol, **kwargs)

# 配置函数
def set_cache_dir(cache_dir: str):
    """设置缓存目录"""
    global _global_client
    _global_client = QDBClient(cache_dir)
    print(f"✅ Cache directory set to: {cache_dir}")

def set_log_level(level: str):
    """设置日志级别"""
    os.environ["LOG_LEVEL"] = level.upper()
    print(f"✅ Log level set to: {level.upper()}")

def get_realtime_data(symbol: str, force_refresh: bool = False) -> Dict[str, Any]:
    """
    Get realtime stock data

    Args:
        symbol: Stock symbol
        force_refresh: If True, bypass cache and fetch fresh data

    Returns:
        Dictionary with realtime stock data
    """
    return _get_client().get_realtime_data(symbol, force_refresh)

def get_realtime_data_batch(symbols: List[str], force_refresh: bool = False) -> Dict[str, Dict[str, Any]]:
    """
    Get realtime data for multiple stocks

    Args:
        symbols: List of stock symbols
        force_refresh: If True, bypass cache and fetch fresh data

    Returns:
        Dictionary with symbol as key and realtime data as value
    """
    return _get_client().get_realtime_data_batch(symbols, force_refresh)

def get_stock_list(market: Optional[str] = None, force_refresh: bool = False) -> List[Dict[str, Any]]:
    """
    Get stock list with market filtering and daily caching

    Args:
        market: Market filter ('SHSE', 'SZSE', 'HKEX', or None for all markets)
        force_refresh: If True, bypass cache and fetch fresh data

    Returns:
        List of dictionaries containing stock information
    """
    return _get_client().get_stock_list(market, force_refresh)

def get_index_data(
    symbol: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    period: str = "daily",
    force_refresh: bool = False
) -> pd.DataFrame:
    """
    Get historical index data

    Args:
        symbol: Index symbol (e.g., '000001', '399001')
        start_date: Start date in YYYYMMDD format
        end_date: End date in YYYYMMDD format
        period: Data frequency ('daily', 'weekly', 'monthly')
        force_refresh: If True, bypass cache and fetch fresh data

    Returns:
        DataFrame with historical index data
    """
    return _get_client().get_index_data(symbol, start_date, end_date, period, force_refresh)

def get_index_realtime(symbol: str, force_refresh: bool = False) -> Dict[str, Any]:
    """
    Get realtime index data

    Args:
        symbol: Index symbol (e.g., '000001', '399001')
        force_refresh: If True, bypass cache and fetch fresh data

    Returns:
        Dictionary with realtime index data
    """
    return _get_client().get_index_realtime(symbol, force_refresh)

def get_index_list(category: Optional[str] = None, force_refresh: bool = False) -> List[Dict[str, Any]]:
    """
    Get index list with category filtering and daily caching

    Args:
        category: Index category filter (e.g., '沪深重要指数', '上证系列指数')
        force_refresh: If True, bypass cache and fetch fresh data

    Returns:
        List of dictionaries containing index information
    """
    return _get_client().get_index_list(category, force_refresh)

def get_financial_summary(symbol: str, force_refresh: bool = False) -> Dict[str, Any]:
    """
    Get financial summary data for a stock symbol

    Args:
        symbol: Stock symbol (e.g., '000001', '600000')
        force_refresh: If True, bypass cache and fetch fresh data

    Returns:
        Dictionary containing financial summary data
    """
    return _get_client().get_financial_summary(symbol, force_refresh)

def get_financial_indicators(symbol: str, force_refresh: bool = False) -> Dict[str, Any]:
    """
    Get financial indicators data for a stock symbol

    Args:
        symbol: Stock symbol (e.g., '000001', '600000')
        force_refresh: If True, bypass cache and fetch fresh data

    Returns:
        Dictionary containing financial indicators data
    """
    return _get_client().get_financial_indicators(symbol, force_refresh)
