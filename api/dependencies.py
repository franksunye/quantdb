"""
API Dependencies

Dependency injection for API services.
"""

from fastapi import Depends
from sqlalchemy.orm import Session

from core.cache import AKShareAdapter
from core.database import get_db
from core.services import AssetInfoService, DatabaseCache, StockDataService


def get_akshare_adapter() -> AKShareAdapter:
    """Get AKShare adapter instance."""
    return AKShareAdapter()


def get_stock_data_service(
    db: Session = Depends(get_db),
    adapter: AKShareAdapter = Depends(get_akshare_adapter),
) -> StockDataService:
    """Get stock data service instance."""
    return StockDataService(db, adapter)


def get_asset_info_service(db: Session = Depends(get_db)) -> AssetInfoService:
    """Get asset info service instance."""
    return AssetInfoService(db)


def get_database_cache(db: Session = Depends(get_db)) -> DatabaseCache:
    """Get database cache instance."""
    return DatabaseCache(db)
