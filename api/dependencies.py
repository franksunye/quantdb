"""
API Dependencies

Dependency injection for API services using ServiceManager.
"""

from fastapi import Depends

from core.services import ServiceManager, get_service_manager


def get_service_manager_instance() -> ServiceManager:
    """Get ServiceManager instance for API."""
    return get_service_manager()


def get_stock_data_service(
    service_manager: ServiceManager = Depends(get_service_manager_instance),
):
    """Get stock data service instance via ServiceManager."""
    return service_manager.get_stock_data_service()


def get_asset_info_service(
    service_manager: ServiceManager = Depends(get_service_manager_instance),
):
    """Get asset info service instance via ServiceManager."""
    return service_manager.get_asset_info_service()


def get_database_cache(db: Session = Depends(get_db)) -> DatabaseCache:
    """Get database cache instance."""
    return DatabaseCache(db)
