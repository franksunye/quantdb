"""
Simplified cache API endpoints.

This module provides simplified cache management endpoints
for the QuantDB API using the database as the primary cache.
"""

from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from core.database import get_db
from core.models import Asset, DailyStockData
from core.utils.logger import get_logger

# Setup logger
logger = get_logger(__name__)

# Create router
router = APIRouter(
    tags=["cache"],
    responses={404: {"description": "Not found"}},
)


@router.get("/stats")
async def get_cache_stats(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Get cache statistics from the database.

    Returns:
        Dictionary with cache statistics.
    """
    try:
        # Count assets and prices in database
        asset_count = db.query(Asset).count()
        price_count = db.query(DailyStockData).count()

        # Get latest price date
        latest_price = db.query(DailyStockData).order_by(DailyStockData.trade_date.desc()).first()
        latest_date = latest_price.trade_date if latest_price else None

        stats = {
            "cache_type": "database",
            "total_assets": asset_count,
            "total_prices": price_count,
            "latest_data_date": latest_date,
            "timestamp": datetime.now().isoformat()
        }

        logger.info(f"Cache stats retrieved: {stats}")
        return stats

    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get cache statistics")


@router.delete("/clear")
async def clear_cache(db: Session = Depends(get_db)) -> Dict[str, str]:
    """
    Clear all cached data (prices only, keep assets).

    Returns:
        Success message.
    """
    try:
        # Delete all price data but keep assets
        deleted_count = db.query(DailyStockData).delete()
        db.commit()

        logger.info(f"Cleared {deleted_count} price records from cache")

        return {
            "message": f"Successfully cleared {deleted_count} price records from cache",
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to clear cache")


@router.delete("/clear/{symbol}")
async def clear_symbol_cache(symbol: str, db: Session = Depends(get_db)) -> Dict[str, str]:
    """
    Clear cached data for a specific symbol.

    Args:
        symbol: Stock symbol to clear

    Returns:
        Success message.
    """
    try:
        # Find the asset
        asset = db.query(Asset).filter(Asset.symbol == symbol).first()
        if not asset:
            raise HTTPException(status_code=404, detail=f"Symbol {symbol} not found")

        # Delete price data for this asset
        deleted_count = db.query(DailyStockData).filter(DailyStockData.asset_id == asset.asset_id).delete()
        db.commit()

        logger.info(f"Cleared {deleted_count} price records for symbol {symbol}")

        return {
            "message": f"Successfully cleared {deleted_count} price records for symbol {symbol}",
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing cache for symbol {symbol}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to clear cache for symbol {symbol}")


@router.get("/symbols")
async def get_cached_symbols(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """
    Get list of symbols that have cached data.

    Returns:
        List of symbols with cache information.
    """
    try:
        # Query assets that have price data
        assets_with_prices = db.query(Asset).join(DailyStockData).distinct().all()

        symbols = []
        for asset in assets_with_prices:
            # Get price count and date range for this asset
            price_count = db.query(DailyStockData).filter(DailyStockData.asset_id == asset.asset_id).count()

            earliest_price = db.query(DailyStockData).filter(DailyStockData.asset_id == asset.asset_id).order_by(DailyStockData.trade_date.asc()).first()
            latest_price = db.query(DailyStockData).filter(DailyStockData.asset_id == asset.asset_id).order_by(DailyStockData.trade_date.desc()).first()

            symbols.append({
                "symbol": asset.symbol,
                "name": asset.name,
                "price_count": price_count,
                "earliest_date": earliest_price.trade_date if earliest_price else None,
                "latest_date": latest_price.trade_date if latest_price else None
            })

        logger.info(f"Retrieved cache info for {len(symbols)} symbols")
        return symbols

    except Exception as e:
        logger.error(f"Error getting cached symbols: {e}")
        raise HTTPException(status_code=500, detail="Failed to get cached symbols")


@router.get("/health")
async def cache_health_check(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Check cache health status.

    Returns:
        Cache health information.
    """
    try:
        # Simple health check - try to query the database
        asset_count = db.query(Asset).count()

        return {
            "status": "healthy",
            "cache_type": "database",
            "asset_count": asset_count,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Cache health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
