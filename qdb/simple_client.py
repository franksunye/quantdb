"""
QDB Simple Client - Lightweight wrapper around core services

This module provides a simplified interface that delegates to the core services
while maintaining backward compatibility with the original simple client API.
"""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Union, Any

import pandas as pd

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from .exceptions import QDBError, DataError, NetworkError


class SimpleQDBClient:
    """Simplified QDB client that delegates to core services"""

    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialize simplified client

        Args:
            cache_dir: Cache directory path
        """
        self.cache_dir = cache_dir or os.path.expanduser("~/.qdb_cache")
        self._ensure_cache_dir()
        self._db_session = None
        self._stock_service = None
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
            db_path = os.path.join(self.cache_dir, "qdb_simple.db")
            os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"

            # Import core components
            from core.database.connection import get_db, Base, engine
            from core.cache.akshare_adapter import AKShareAdapter
            from core.services.stock_data_service import StockDataService

            # Create database tables
            Base.metadata.create_all(bind=engine)

            # Initialize components
            self._db_session = next(get_db())
            akshare_adapter = AKShareAdapter(self._db_session)
            self._stock_service = StockDataService(self._db_session, akshare_adapter)

            self._initialized = True
            print("🚀 Simple client initialized with core services")

        except Exception as e:
            # Fallback to legacy implementation if core services fail
            print(f"⚠️ Core services unavailable, using fallback: {e}")
            self._init_fallback()

    def _init_fallback(self):
        """Initialize fallback implementation"""
        # Legacy client has been removed, raise error if core services fail
        raise QDBError(
            "Core services initialization failed and legacy client is no longer available"
        )

    def get_stock_data(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        days: Optional[int] = None,
        adjust: str = "",
    ) -> pd.DataFrame:
        """
        Get stock historical data

        Args:
            symbol: Stock code (supports both A-shares and HK stocks)
            start_date: Start date, format "20240101"
            end_date: End date, format "20240201"
            days: Get recent N days data
            adjust: Adjustment type

        Returns:
            Stock data DataFrame
        """
        self._lazy_init()

        try:
            # Handle days parameter
            if days is not None:
                end_date = datetime.now().strftime("%Y%m%d")
                start_date = (datetime.now() - timedelta(days=days * 2)).strftime("%Y%m%d")

            # Use core service if available
            if hasattr(self, "_use_legacy") and self._use_legacy:
                return self._legacy_client.get_stock_data(
                    symbol, start_date, end_date, days, adjust
                )
            else:
                return self._stock_service.get_stock_data(symbol, start_date, end_date, adjust)

        except Exception as e:
            raise DataError(f"Failed to get stock data for {symbol}: {str(e)}")

    def get_multiple_stocks(
        self, symbols: List[str], days: int = 30, **kwargs
    ) -> Dict[str, pd.DataFrame]:
        """Get multiple stocks data in batch"""
        result = {}
        for symbol in symbols:
            try:
                result[symbol] = self.get_stock_data(symbol, days=days, **kwargs)
            except Exception as e:
                print(f"⚠️ Failed to get data for {symbol}: {e}")
                result[symbol] = pd.DataFrame()
        return result

    def cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        cache_size = 0
        if Path(self.cache_dir).exists():
            cache_size = sum(
                f.stat().st_size for f in Path(self.cache_dir).rglob("*") if f.is_file()
            ) / (
                1024 * 1024
            )  # MB

        return {
            "cache_dir": self.cache_dir,
            "cache_size_mb": round(cache_size, 2),
            "initialized": self._initialized,
            "status": "Running" if self._initialized else "Not initialized",
        }

    def clear_cache(self, symbol: Optional[str] = None):
        """Clear cache"""
        print(f"🗑️ Cache clear requested for {symbol or 'all symbols'}")
        print("💡 Cache clearing will be implemented in future versions")

    # Additional methods for compatibility
    def get_realtime_data(self, symbol: str) -> Dict[str, Any]:
        """Get realtime data (placeholder)"""
        return {"symbol": symbol, "error": "Realtime data not implemented in simple client"}

    def get_realtime_data_batch(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """Get batch realtime data (placeholder)"""
        return {symbol: self.get_realtime_data(symbol) for symbol in symbols}

    def get_stock_list(
        self, market: Optional[str] = None, force_refresh: bool = False
    ) -> List[Dict[str, Any]]:
        """Get stock list (placeholder)"""
        return []

    def get_index_data(self, symbol: str, **kwargs) -> pd.DataFrame:
        """Get index data (placeholder)"""
        return pd.DataFrame()

    def get_index_realtime(self, symbol: str) -> Dict[str, Any]:
        """Get index realtime data (placeholder)"""
        return {"symbol": symbol, "error": "Index data not implemented in simple client"}

    def get_index_list(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get index list (placeholder)"""
        return []

    def get_financial_summary(self, symbol: str) -> Dict[str, Any]:
        """Get financial summary (placeholder)"""
        return {"symbol": symbol, "error": "Financial data not implemented in simple client"}

    def get_financial_indicators(self, symbol: str) -> Dict[str, Any]:
        """Get financial indicators (placeholder)"""
        return {"symbol": symbol, "error": "Financial data not implemented in simple client"}

    def get_asset_info(self, symbol: str) -> Dict[str, Any]:
        """Get asset info (placeholder)"""
        return {
            "symbol": symbol,
            "name": f"Stock {symbol}",
            "market": "A-Share" if symbol.startswith(("0", "3", "6")) else "Unknown",
            "status": "Active",
        }

    def stock_zh_a_hist(self, symbol: str, **kwargs) -> pd.DataFrame:
        """AKShare compatible interface"""
        return self.get_stock_data(symbol, **kwargs)
