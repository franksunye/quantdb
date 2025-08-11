"""
Asset management API endpoints.

This module provides API endpoints for managing asset information,
including bulk import and refresh operations for Hong Kong stocks.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from core.database import get_db
from core.services.asset_info_service import AssetInfoService
from core.utils.logger import get_logger

# Setup logger
logger = get_logger(__name__)

# Create router
router = APIRouter(
    prefix="/assets",
    tags=["asset-management"],
    responses={404: {"description": "Not found"}},
)


@router.post("/hk-stocks/bulk-import")
async def bulk_import_hk_stocks(
    force_update: bool = Query(False, description="Force update existing stocks"),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Bulk import Hong Kong stocks to Assets table.

    This endpoint fetches all HK stocks from AKShare and saves them to the database.
    It's designed to be called once to populate the database with HK stock information.

    Args:
        force_update: Whether to update existing stocks
        db: Database session

    Returns:
        Import result statistics
    """
    try:
        logger.info(f"Starting bulk import of HK stocks (force_update={force_update})")

        asset_service = AssetInfoService(db)
        result = asset_service.bulk_import_hk_stocks(force_update=force_update)

        if result.get("success"):
            logger.info(f"Bulk import completed successfully: {result}")
            return {
                "success": True,
                "message": "HK stocks imported successfully",
                "data": result,
                "timestamp": datetime.now().isoformat(),
            }
        else:
            logger.error(f"Bulk import failed: {result}")
            raise HTTPException(
                status_code=500,
                detail=f"Bulk import failed: {result.get('error', 'Unknown error')}",
            )

    except Exception as e:
        logger.error(f"Error in bulk import endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/hk-stocks/{symbol}/refresh")
async def refresh_hk_stock(
    symbol: str, db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Force refresh a specific Hong Kong stock.

    This endpoint fetches the latest information for a specific HK stock
    from AKShare and updates the database record.

    Args:
        symbol: HK stock symbol (e.g., "00700")
        db: Database session

    Returns:
        Refresh result
    """
    try:
        logger.info(f"Refreshing HK stock: {symbol}")

        # Validate symbol format
        if not symbol.isdigit() or len(symbol) != 5:
            raise HTTPException(
                status_code=400,
                detail="Invalid HK stock symbol format. Expected 5-digit number.",
            )

        asset_service = AssetInfoService(db)
        success = asset_service.refresh_hk_stock(symbol)

        if success:
            logger.info(f"Successfully refreshed HK stock: {symbol}")
            return {
                "success": True,
                "message": f"HK stock {symbol} refreshed successfully",
                "symbol": symbol,
                "timestamp": datetime.now().isoformat(),
            }
        else:
            logger.warning(f"Failed to refresh HK stock: {symbol}")
            raise HTTPException(
                status_code=404,
                detail=f"Failed to refresh HK stock {symbol}. Stock may not exist in AKShare data.",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error refreshing HK stock {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/hk-stocks/stats")
async def get_hk_stocks_stats(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Get statistics about Hong Kong stocks in the database.

    Args:
        db: Database session

    Returns:
        HK stocks statistics
    """
    try:
        from core.models.asset import Asset

        # Count HK stocks in database
        hk_stocks_count = db.query(Asset).filter(Asset.exchange == "HKEX").count()

        # Get latest update time
        latest_hk_stock = (
            db.query(Asset)
            .filter(Asset.exchange == "HKEX")
            .order_by(Asset.last_updated.desc())
            .first()
        )

        latest_update = latest_hk_stock.last_updated if latest_hk_stock else None

        # Count by data source
        from sqlalchemy import func

        source_stats = (
            db.query(Asset.data_source, func.count(Asset.asset_id).label("count"))
            .filter(Asset.exchange == "HKEX")
            .group_by(Asset.data_source)
            .all()
        )

        source_breakdown = {source: count for source, count in source_stats}

        stats = {
            "total_hk_stocks": hk_stocks_count,
            "latest_update": latest_update.isoformat() if latest_update else None,
            "source_breakdown": source_breakdown,
            "timestamp": datetime.now().isoformat(),
        }

        logger.info(f"HK stocks stats: {stats}")
        return stats

    except Exception as e:
        logger.error(f"Error getting HK stocks stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/hk-stocks")
async def clear_hk_stocks(
    confirm: bool = Query(False, description="Confirm deletion of all HK stocks"),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Clear all Hong Kong stocks from the database.

    This is a destructive operation that removes all HK stock records.
    Use with caution and only for maintenance purposes.

    Args:
        confirm: Must be True to proceed with deletion
        db: Database session

    Returns:
        Deletion result
    """
    try:
        if not confirm:
            raise HTTPException(
                status_code=400, detail="Must set confirm=true to proceed with deletion"
            )

        from core.models.asset import Asset

        # Count before deletion
        count_before = db.query(Asset).filter(Asset.exchange == "HKEX").count()

        # Delete all HK stocks
        deleted_count = db.query(Asset).filter(Asset.exchange == "HKEX").delete()
        db.commit()

        logger.warning(f"Deleted {deleted_count} HK stocks from database")

        return {
            "success": True,
            "message": f"Successfully deleted {deleted_count} HK stocks",
            "deleted_count": deleted_count,
            "count_before": count_before,
            "timestamp": datetime.now().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing HK stocks: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
