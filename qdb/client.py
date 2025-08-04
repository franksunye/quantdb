"""
QDB客户端 - 简化的用户接口

封装core/功能，提供简洁易用的API
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Optional, Union, Any
import pandas as pd
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from .exceptions import QDBError, CacheError, DataError, NetworkError

class QDBClient:
    """QDB客户端，管理本地缓存和数据获取"""
    
    def __init__(self, cache_dir: Optional[str] = None):
        """
        初始化QDB客户端
        
        Args:
            cache_dir: 缓存目录路径，默认为 ~/.qdb_cache
        """
        self.cache_dir = cache_dir or os.path.expanduser("~/.qdb_cache")
        self._ensure_cache_dir()
        self._db_session = None
        self._akshare_adapter = None
        self._stock_service = None
        self._asset_service = None
        self._initialized = False
        
    def _ensure_cache_dir(self):
        """确保缓存目录存在"""
        Path(self.cache_dir).mkdir(parents=True, exist_ok=True)
        
    def _lazy_init(self):
        """延迟初始化核心组件"""
        if self._initialized:
            return

        try:
            # 设置数据库路径
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
                "status": "运行中" if self._initialized else "未初始化"
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
                    print("✅ 已清除所有缓存")
                    self._initialized = False
                else:
                    print("⚠️ 缓存目录不存在")

        except Exception as e:
            raise CacheError(f"清除缓存失败: {str(e)}")

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
    print("🚀 使用QDB简化模式（独立版本）")
    _global_client = SimpleQDBClient(cache_dir)
    print(f"✅ QDB已初始化，缓存目录: {_global_client.cache_dir}")

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
    print(f"✅ 缓存目录已设置为: {cache_dir}")

def set_log_level(level: str):
    """设置日志级别"""
    os.environ["LOG_LEVEL"] = level.upper()
    print(f"✅ 日志级别已设置为: {level.upper()}")
