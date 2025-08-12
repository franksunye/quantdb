"""
Core Service Manager

This module provides a unified service management system that handles
initialization and dependency injection for all core services.

This ensures that all products (qdb, API, cloud) use the same service
initialization logic, achieving 90%+ code reuse as specified in the architecture.
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from ..cache.akshare_adapter import AKShareAdapter
from ..database.connection import Base, engine, get_db
from ..utils.logger import logger
from .stock_data_service import StockDataService
from .asset_info_service import AssetInfoService
from .realtime_data_service import RealtimeDataService
from .index_data_service import IndexDataService
from .financial_data_service import FinancialDataService
from .database_cache import DatabaseCache


class ServiceManager:
    """
    Unified service manager for all QuantDB core services.

    This class centralizes service initialization and dependency injection,
    ensuring consistent service setup across all products (qdb, API, cloud).

    Architecture principle: All complex business logic stays in core/,
    while application layers (qdb, api, cloud) only make simple calls.
    """

    def __init__(
        self, cache_dir: Optional[str] = None, database_url: Optional[str] = None
    ):
        """
        Initialize the service manager.

        Args:
            cache_dir: Cache directory path for local storage
            database_url: Database URL override (optional)
        """
        self.cache_dir = cache_dir or os.path.expanduser("~/.quantdb_cache")
        self._ensure_cache_dir()

        # Set database URL if provided
        if database_url:
            os.environ["DATABASE_URL"] = database_url
        elif not os.getenv("DATABASE_URL"):
            # Default to local SQLite in cache directory
            db_path = os.path.join(self.cache_dir, "quantdb.db")
            os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"

        # Service instances (lazy initialized)
        self._db_session: Optional[Session] = None
        self._akshare_adapter: Optional[AKShareAdapter] = None
        self._services: Dict[str, Any] = {}
        self._initialized = False

        logger.info(f"ServiceManager initialized with cache_dir: {self.cache_dir}")

    def _ensure_cache_dir(self):
        """Ensure cache directory exists."""
        Path(self.cache_dir).mkdir(parents=True, exist_ok=True)

    def _initialize_core_components(self):
        """Initialize core database and adapter components."""
        if self._initialized:
            return

        try:
            # Create database tables
            Base.metadata.create_all(bind=engine)

            # Initialize database session
            self._db_session = next(get_db())

            # Initialize AKShare adapter
            self._akshare_adapter = AKShareAdapter(self._db_session)

            self._initialized = True
            logger.info("Core components initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize core components: {e}")
            raise

    def get_stock_data_service(self) -> StockDataService:
        """Get stock data service instance."""
        if "stock_data" not in self._services:
            self._initialize_core_components()
            self._services["stock_data"] = StockDataService(
                self._db_session, self._akshare_adapter
            )
            logger.debug("StockDataService initialized")
        return self._services["stock_data"]

    def get_asset_info_service(self) -> AssetInfoService:
        """Get asset info service instance."""
        if "asset_info" not in self._services:
            self._initialize_core_components()
            self._services["asset_info"] = AssetInfoService(self._db_session)
            logger.debug("AssetInfoService initialized")
        return self._services["asset_info"]

    def get_realtime_data_service(self) -> RealtimeDataService:
        """Get realtime data service instance."""
        if "realtime_data" not in self._services:
            self._initialize_core_components()
            self._services["realtime_data"] = RealtimeDataService(
                self._db_session, self._akshare_adapter
            )
            logger.debug("RealtimeDataService initialized")
        return self._services["realtime_data"]

    def get_index_data_service(self) -> IndexDataService:
        """Get index data service instance."""
        if "index_data" not in self._services:
            self._initialize_core_components()
            self._services["index_data"] = IndexDataService(
                self._db_session, self._akshare_adapter
            )
            logger.debug("IndexDataService initialized")
        return self._services["index_data"]

    def get_financial_data_service(self) -> FinancialDataService:
        """Get financial data service instance."""
        if "financial_data" not in self._services:
            self._initialize_core_components()
            self._services["financial_data"] = FinancialDataService(
                self._db_session, self._akshare_adapter
            )
            logger.debug("FinancialDataService initialized")
        return self._services["financial_data"]

    def get_database_cache(self) -> DatabaseCache:
        """Get database cache service instance."""
        if "database_cache" not in self._services:
            self._initialize_core_components()
            self._services["database_cache"] = DatabaseCache(self._db_session)
            logger.debug("DatabaseCache initialized")
        return self._services["database_cache"]

    def get_all_services(self) -> Dict[str, Any]:
        """
        Get all services in a single call.

        Returns:
            Dictionary containing all initialized services
        """
        return {
            "stock_data": self.get_stock_data_service(),
            "asset_info": self.get_asset_info_service(),
            "realtime_data": self.get_realtime_data_service(),
            "index_data": self.get_index_data_service(),
            "financial_data": self.get_financial_data_service(),
            "database_cache": self.get_database_cache(),
        }

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        cache_service = self.get_database_cache()
        return cache_service.get_cache_stats()

    def clear_cache(self, symbol: Optional[str] = None):
        """Clear cache data."""
        cache_service = self.get_database_cache()
        if symbol:
            cache_service.clear_symbol_cache(symbol)
        else:
            cache_service.clear_all_cache()

    def close(self):
        """Close all connections and cleanup resources."""
        if self._db_session:
            self._db_session.close()
            self._db_session = None

        self._services.clear()
        self._initialized = False
        logger.info("ServiceManager closed")


# Global service manager instance for singleton pattern
_global_service_manager: Optional[ServiceManager] = None


def get_service_manager(
    cache_dir: Optional[str] = None, database_url: Optional[str] = None
) -> ServiceManager:
    """
    Get the global service manager instance.

    This function implements a singleton pattern to ensure all parts of the
    application use the same service manager instance.

    Args:
        cache_dir: Cache directory path (only used on first call)
        database_url: Database URL override (only used on first call)

    Returns:
        ServiceManager instance
    """
    global _global_service_manager

    if _global_service_manager is None:
        _global_service_manager = ServiceManager(cache_dir, database_url)
        logger.info("Global ServiceManager created")

    return _global_service_manager


def reset_service_manager():
    """Reset the global service manager (mainly for testing)."""
    global _global_service_manager

    if _global_service_manager:
        _global_service_manager.close()
        _global_service_manager = None
        logger.info("Global ServiceManager reset")
