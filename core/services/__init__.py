"""
Core Business Services

This module contains all business service classes that implement
the core functionality of QuantDB.
"""

from .asset_info_service import AssetInfoService
from .database_cache import DatabaseCache
# monitoring_middleware is optional (requires fastapi)
from .monitoring_service import MonitoringService
from .query_service import QueryService
from .service_manager import ServiceManager, get_service_manager, reset_service_manager
from .stock_data_service import StockDataService
from .trading_calendar import (
    Market,
    TradingCalendar,
    get_trading_calendar,
    get_trading_days,
    is_trading_day,
    # New multi-market functions
    is_hk_trading_day,
    get_hk_trading_days,
    is_china_a_trading_day,
    get_china_a_trading_days,
)

__all__ = [
    "StockDataService",
    "AssetInfoService",
    "QueryService",
    "DatabaseCache",
    "TradingCalendar",
    "get_trading_calendar",
    "is_trading_day",
    "get_trading_days",
    "MonitoringService",
    "ServiceManager",
    "get_service_manager",
    "reset_service_manager",
]
