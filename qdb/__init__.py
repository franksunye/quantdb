"""
QDB - Intelligent Caching Stock Database

Installation and Import:
    pip install quantdb  # Package name: quantdb
    import qdb           # Import name: qdb (concise and easy to use)

One-line code to enjoy AKShare caching acceleration:
    import qdb
    df = qdb.get_stock_data("000001", days=30)

Features:
- 🚀 90%+ Performance Boost: Local SQLite cache avoids repeated network requests
- 🧠 Smart Incremental Updates: Only fetch missing data, maximize cache efficiency
- ⚡ Millisecond Response: Cache hit response time < 10ms
- 📅 Trading Calendar Integration: Smart data acquisition based on real trading calendar
- 🔧 Zero Configuration Startup: Automatically initialize local cache database
- 🔄 Full Compatibility: Maintains same API interface as AKShare

Note: Package name (quantdb) and import name (qdb) are different, which is a common practice
in Python ecosystem, similar to scikit-learn → sklearn, beautifulsoup4 → bs4
"""

# Import from client that properly delegates to core services
from .client import get_lightweight_client

# Create module-level functions that delegate to the lightweight client
def init(cache_dir: str = None):
    """Initialize QDB with core services."""
    global _client
    _client = get_lightweight_client(cache_dir)
    print(f"🚀 QDB initialized with lightweight architecture")
    print(f"✅ All business logic handled by core services")

def get_stock_data(symbol: str, start_date: str = None, end_date: str = None,
                   days: int = None, adjust: str = ""):
    """Get stock data - delegates to core service."""
    return _get_client().get_stock_data(symbol, start_date, end_date, days, adjust)

def get_multiple_stocks(symbols: list, days: int = 30, **kwargs):
    """Get multiple stocks data - delegates to core service."""
    return _get_client().get_multiple_stocks(symbols, days, **kwargs)

def get_asset_info(symbol: str):
    """Get asset info - delegates to core service."""
    return _get_client().get_asset_info(symbol)

def get_realtime_data(symbol: str):
    """Get realtime data - delegates to core service."""
    return _get_client().get_realtime_data(symbol)

def get_realtime_data_batch(symbols: list):
    """Get batch realtime data - delegates to core service."""
    return _get_client().get_realtime_data_batch(symbols)

def get_stock_list(market: str = "all"):
    """Get stock list - delegates to core service."""
    return _get_client().get_stock_list(market)

def get_index_data(symbol: str, start_date: str = None, end_date: str = None, days: int = None):
    """Get index data - delegates to core service."""
    return _get_client().get_index_data(symbol, start_date, end_date, days)

def get_index_realtime(symbol: str):
    """Get realtime index data - delegates to core service."""
    return _get_client().get_index_realtime(symbol)

def get_index_list():
    """Get index list - delegates to core service."""
    return _get_client().get_index_list()

def get_financial_summary(symbol: str):
    """Get financial summary - delegates to core service."""
    return _get_client().get_financial_summary(symbol)

def get_financial_indicators(symbol: str):
    """Get financial indicators - delegates to core service."""
    return _get_client().get_financial_indicators(symbol)

def cache_stats():
    """Get cache statistics - delegates to core service."""
    return _get_client().cache_stats()

def clear_cache(symbol: str = None):
    """Clear cache - delegates to core service."""
    return _get_client().clear_cache(symbol)

def stock_zh_a_hist(symbol: str, period: str = "daily", start_date: str = "19700101",
                    end_date: str = "20500101", adjust: str = ""):
    """AKShare compatible interface - delegates to core service."""
    return _get_client().stock_zh_a_hist(symbol, period, start_date, end_date, adjust)

def set_cache_dir(cache_dir: str):
    """Set cache directory - reinitialize client."""
    global _client
    _client = get_lightweight_client(cache_dir)
    print(f"✅ Cache directory set to: {cache_dir}")

def set_log_level(level: str):
    """Set log level."""
    import os
    os.environ["LOG_LEVEL"] = level.upper()
    print(f"✅ Log level set to: {level.upper()}")

# Global client instance
_client = None

def _get_client():
    """Get or create the global client instance."""
    global _client
    if _client is None:
        _client = get_lightweight_client()
    return _client
from .exceptions import CacheError, DataError, NetworkError, QDBError

# Version information
__version__ = "2.2.8"
__author__ = "Ye Sun"
__email__ = "franksunye@hotmail.com"
__description__ = "Intelligent caching wrapper for AKShare, providing high-performance stock data access"

# Public API
__all__ = [
    # Core functionality
    "init",
    "get_stock_data",
    "get_multiple_stocks",
    "get_asset_info",
    # Realtime data functionality
    "get_realtime_data",
    "get_realtime_data_batch",
    # Stock list functionality
    "get_stock_list",
    # Index data functionality
    "get_index_data",
    "get_index_realtime",
    "get_index_list",
    # Financial data functionality
    "get_financial_summary",
    "get_financial_indicators",
    # Cache management
    "cache_stats",
    "clear_cache",
    # AKShare compatibility
    "stock_zh_a_hist",
    # Configuration
    "set_cache_dir",
    "set_log_level",
    # Exceptions
    "QDBError",
    "CacheError",
    "DataError",
    "NetworkError",
    # Meta information
    "__version__",
]


# Auto-initialization prompt
def _show_welcome():
    """Display welcome information"""
    print("🚀 QuantDB - Intelligent Caching Stock Database")
    print("📦 Install: pip install quantdb")
    print("📖 Usage: qdb.get_stock_data('000001', days=30)")
    print("📊 Stats: qdb.cache_stats()")
    print("🔧 Config: qdb.set_cache_dir('./my_cache')")
    print("💡 Tip: Package name quantdb, import name qdb (like sklearn)")


# Optional welcome message (only displayed in interactive environment)
import sys

if hasattr(sys, "ps1"):  # Check if in interactive environment
    try:
        _show_welcome()
    except:
        pass  # Silent failure, does not affect import
