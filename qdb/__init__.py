"""
QDB - 智能缓存的股票数据库

一行代码享受AKShare缓存加速：
    import qdb
    df = qdb.get_stock_data("000001", days=30)

特性：
- 🚀 90%+性能提升：本地SQLite缓存避免重复网络请求
- 🧠 智能增量更新：只获取缺失的数据，最大化缓存效率
- ⚡ 毫秒级响应：缓存命中时响应时间 < 10ms
- 📅 交易日历集成：基于真实交易日历的智能数据获取
- 🔧 零配置启动：自动初始化本地缓存数据库
- 🔄 完全兼容：保持AKShare相同的API接口
"""

from .client import (
    # 核心功能
    init,
    get_stock_data,
    get_multiple_stocks,
    get_asset_info,
    
    # 缓存管理
    cache_stats,
    clear_cache,
    
    # AKShare兼容接口
    stock_zh_a_hist,
    
    # 配置管理
    set_cache_dir,
    set_log_level,
)

from .exceptions import (
    QDBError,
    CacheError,
    DataError,
    NetworkError
)

# 版本信息
__version__ = "2.2.1"
__author__ = "Ye Sun"
__email__ = "franksunye@hotmail.com"
__description__ = "智能缓存的AKShare包装器，提供高性能股票数据访问"

# 公开API
__all__ = [
    # 核心功能
    "init",
    "get_stock_data",
    "get_multiple_stocks", 
    "get_asset_info",
    
    # 缓存管理
    "cache_stats",
    "clear_cache",
    
    # AKShare兼容
    "stock_zh_a_hist",
    
    # 配置
    "set_cache_dir",
    "set_log_level",
    
    # 异常
    "QDBError",
    "CacheError", 
    "DataError",
    "NetworkError",
    
    # 元信息
    "__version__",
]

# 自动初始化提示
def _show_welcome():
    """显示欢迎信息"""
    print("🚀 QDB - 智能缓存的股票数据库")
    print("📖 使用指南: qdb.get_stock_data('000001', days=30)")
    print("📊 缓存统计: qdb.cache_stats()")
    print("🔧 配置缓存: qdb.set_cache_dir('./my_cache')")

# 可选的欢迎信息（仅在交互式环境中显示）
import sys
if hasattr(sys, 'ps1'):  # 检查是否在交互式环境
    try:
        _show_welcome()
    except:
        pass  # 静默失败，不影响导入
