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

from .client import (
    # Core functionality
    init,
    get_stock_data,
    get_multiple_stocks,
    get_asset_info,

    # Cache management
    cache_stats,
    clear_cache,

    # AKShare compatible interface
    stock_zh_a_hist,

    # Configuration management
    set_cache_dir,
    set_log_level,
)

from .exceptions import (
    QDBError,
    CacheError,
    DataError,
    NetworkError
)

# Version information
__version__ = "2.2.4"
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
if hasattr(sys, 'ps1'):  # Check if in interactive environment
    try:
        _show_welcome()
    except:
        pass  # Silent failure, does not affect import
