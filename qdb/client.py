"""
QDB Lightweight Client - True Frontend Layer

This module provides a lightweight wrapper around core services,
following the architecture principle: "核心功能都在core里面，qdb只是前端的一个调用"

Key principles:
- NO complex business logic in qdb
- NO service initialization logic in qdb  
- NO parameter processing logic in qdb
- ONLY simple delegation to core services
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from .exceptions import QDBError

# Lazy import of core services to avoid heavy dependencies
def _get_service_manager():
    """Lazy import of service manager to avoid loading heavy dependencies at import time."""
    try:
        from core.services import get_service_manager
        return get_service_manager()
    except ImportError as e:
        raise QDBError(f"Failed to import core services: {e}. Please install required dependencies.")


class LightweightQDBClient:
    """
    Lightweight QDB client that delegates ALL functionality to core services.
    
    This client contains ZERO business logic - it's purely a thin wrapper
    that calls the core ServiceManager. All complex logic is in core/.
    """
    
    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialize lightweight client.

        Args:
            cache_dir: Cache directory path (passed to ServiceManager)
        """
        # Store cache_dir for lazy initialization
        self._cache_dir = cache_dir
        self._service_manager = None

    def _get_service_manager(self):
        """Get service manager with lazy initialization."""
        if self._service_manager is None:
            service_manager_factory = _get_service_manager()
            if self._cache_dir:
                # Reset and create with specific cache_dir
                from core.services import reset_service_manager, get_service_manager
                reset_service_manager()
                self._service_manager = get_service_manager(cache_dir=self._cache_dir)
            else:
                self._service_manager = service_manager_factory
        return self._service_manager

    def get_stock_data(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        days: Optional[int] = None,
        adjust: str = "",
    ):
        """
        Get stock data - delegates to core service.
        
        NO business logic here - just pass through to core.
        """
        try:
            stock_service = self._get_service_manager().get_stock_data_service()

            # Let core service handle ALL parameter processing and business logic
            if days is not None:
                return stock_service.get_stock_data_by_days(symbol, days, adjust)
            else:
                return stock_service.get_stock_data(symbol, start_date, end_date, adjust)

        except Exception as e:
            raise QDBError(f"Failed to get stock data: {str(e)}")
    
    def get_multiple_stocks(
        self, symbols: List[str], days: int = 30, **kwargs
    ):
        """
        Get multiple stocks data - delegates to core service.
        """
        try:
            stock_service = self._get_service_manager().get_stock_data_service()
            return stock_service.get_multiple_stocks(symbols, days, **kwargs)
        except Exception as e:
            raise QDBError(f"Failed to get multiple stocks data: {str(e)}")

    def get_asset_info(self, symbol: str) -> Dict[str, Any]:
        """
        Get asset info - delegates to core service.
        """
        try:
            asset_service = self._get_service_manager().get_asset_info_service()
            return asset_service.get_asset_info(symbol)
        except Exception as e:
            raise QDBError(f"Failed to get asset info: {str(e)}")

    def get_realtime_data(self, symbol: str) -> Dict[str, Any]:
        """
        Get realtime data - delegates to core service.
        """
        try:
            realtime_service = self._get_service_manager().get_realtime_data_service()
            return realtime_service.get_realtime_data(symbol)
        except Exception as e:
            raise QDBError(f"Failed to get realtime data: {str(e)}")
    
    def get_realtime_data_batch(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Get batch realtime data - delegates to core service.
        """
        try:
            realtime_service = self._get_service_manager().get_realtime_data_service()
            return realtime_service.get_realtime_data_batch(symbols)
        except Exception as e:
            raise QDBError(f"Failed to get batch realtime data: {str(e)}")

    def get_stock_list(self, market: str = "all"):
        """
        Get stock list - delegates to core service.
        """
        try:
            # Use stock service for stock list functionality
            stock_service = self._get_service_manager().get_stock_data_service()
            return stock_service.get_stock_list(market)
        except Exception as e:
            raise QDBError(f"Failed to get stock list: {str(e)}")

    def get_index_data(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        days: Optional[int] = None,
    ):
        """
        Get index data - delegates to core service.
        """
        try:
            index_service = self._get_service_manager().get_index_data_service()
            if days is not None:
                return index_service.get_index_data_by_days(symbol, days)
            else:
                return index_service.get_index_data(symbol, start_date, end_date)
        except Exception as e:
            raise QDBError(f"Failed to get index data: {str(e)}")

    def get_index_realtime(self, symbol: str) -> Dict[str, Any]:
        """
        Get realtime index data - delegates to core service.
        """
        try:
            index_service = self._get_service_manager().get_index_data_service()
            return index_service.get_realtime_index_data(symbol)
        except Exception as e:
            raise QDBError(f"Failed to get realtime index data: {str(e)}")

    def get_index_list(self):
        """
        Get index list - delegates to core service.
        """
        try:
            index_service = self._get_service_manager().get_index_data_service()
            return index_service.get_index_list()
        except Exception as e:
            raise QDBError(f"Failed to get index list: {str(e)}")

    def get_financial_summary(self, symbol: str) -> Dict[str, Any]:
        """
        Get financial summary - delegates to core service.
        """
        try:
            financial_service = self._get_service_manager().get_financial_data_service()
            return financial_service.get_financial_summary(symbol)
        except Exception as e:
            raise QDBError(f"Failed to get financial summary: {str(e)}")

    def get_financial_indicators(self, symbol: str) -> Dict[str, Any]:
        """
        Get financial indicators - delegates to core service.
        """
        try:
            financial_service = self._get_service_manager().get_financial_data_service()
            return financial_service.get_financial_indicators(symbol)
        except Exception as e:
            raise QDBError(f"Failed to get financial indicators: {str(e)}")

    def cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics - delegates to core service.
        """
        try:
            return self._get_service_manager().get_cache_stats()
        except Exception as e:
            raise QDBError(f"Failed to get cache stats: {str(e)}")

    def clear_cache(self, symbol: Optional[str] = None):
        """
        Clear cache - delegates to core service.
        """
        try:
            self._get_service_manager().clear_cache(symbol)
        except Exception as e:
            raise QDBError(f"Failed to clear cache: {str(e)}")
    
    # AKShare compatibility method
    def stock_zh_a_hist(
        self,
        symbol: str,
        period: str = "daily",
        start_date: str = "19700101",
        end_date: str = "20500101",
        adjust: str = "",
    ):
        """
        AKShare compatible interface - delegates to core service.
        """
        try:
            stock_service = self._get_service_manager().get_stock_data_service()
            return stock_service.stock_zh_a_hist(symbol, period, start_date, end_date, adjust)
        except Exception as e:
            raise QDBError(f"Failed to get stock data (AKShare compatible): {str(e)}")


# Global lightweight client instance
_global_lightweight_client: Optional[LightweightQDBClient] = None


def get_lightweight_client(cache_dir: Optional[str] = None) -> LightweightQDBClient:
    """Get the global lightweight client instance."""
    global _global_lightweight_client
    
    if _global_lightweight_client is None:
        _global_lightweight_client = LightweightQDBClient(cache_dir)
    
    return _global_lightweight_client


def reset_lightweight_client():
    """Reset the global lightweight client (mainly for testing)."""
    global _global_lightweight_client
    _global_lightweight_client = None
