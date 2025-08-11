"""
Realtime stock data API routes for QuantDB API service.

This module provides API endpoints for retrieving realtime stock data
with intelligent caching strategies.
"""

from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

# Import core modules
from core.database.connection import get_db
from core.cache.akshare_adapter import AKShareAdapter
from core.services.realtime_data_service import RealtimeDataService
from core.utils.logger import logger

# Create router
router = APIRouter(prefix="/api/v1/realtime", tags=["realtime"])


# Request/Response models
class BatchRealtimeRequest(BaseModel):
    """Request model for batch realtime data."""

    symbols: List[str]
    force_refresh: bool = False


class RealtimeDataResponse(BaseModel):
    """Response model for single realtime data."""

    symbol: str
    name: str
    price: float
    open: float
    high: float
    low: float
    prev_close: float
    change: float
    pct_change: float
    volume: float
    turnover: float
    timestamp: str
    cache_hit: bool
    is_trading_hours: bool
    metadata: Dict[str, Any]


class BatchRealtimeResponse(BaseModel):
    """Response model for batch realtime data."""

    data: Dict[str, Dict[str, Any]]
    metadata: Dict[str, Any]


# Dependencies
def get_akshare_adapter(db: Session = Depends(get_db)):
    """Get AKShare adapter instance."""
    return AKShareAdapter(db)


def get_realtime_service(
    db: Session = Depends(get_db), akshare_adapter: AKShareAdapter = Depends(get_akshare_adapter)
):
    """Get realtime data service instance."""
    return RealtimeDataService(db, akshare_adapter)


# API Endpoints
@router.get("/stock/{symbol}", response_model=RealtimeDataResponse)
async def get_realtime_stock_data(
    symbol: str,
    force_refresh: bool = Query(False, description="Force refresh data from source"),
    realtime_service: RealtimeDataService = Depends(get_realtime_service),
):
    """
    Get realtime data for a specific stock symbol.

    Args:
        symbol: Stock symbol (e.g., '000001', '600000')
        force_refresh: If True, bypass cache and fetch fresh data

    Returns:
        Realtime stock data with metadata
    """
    try:
        logger.info(f"API request for realtime data: {symbol}")

        # Validate symbol format
        if not symbol or len(symbol.strip()) == 0:
            raise HTTPException(status_code=400, detail="Symbol cannot be empty")

        # Get realtime data
        data = realtime_service.get_realtime_data(symbol.strip(), force_refresh)

        # Check for errors
        if "error" in data:
            raise HTTPException(status_code=404, detail=data["error"])

        # Create response
        response = {
            "symbol": data["symbol"],
            "name": data.get("name", f"Stock {data['symbol']}"),
            "price": data.get("price", 0),
            "open": data.get("open", 0),
            "high": data.get("high", 0),
            "low": data.get("low", 0),
            "prev_close": data.get("prev_close", 0),
            "change": data.get("change", 0),
            "pct_change": data.get("pct_change", 0),
            "volume": data.get("volume", 0),
            "turnover": data.get("turnover", 0),
            "timestamp": data.get("timestamp", ""),
            "cache_hit": data.get("cache_hit", False),
            "is_trading_hours": data.get("is_trading_hours", False),
            "metadata": {
                "status": "success",
                "message": f"Successfully retrieved realtime data for {symbol}",
                "cache_hit": data.get("cache_hit", False),
                "force_refresh": force_refresh,
                "response_time_ms": 0,  # Will be set by middleware
            },
        }

        logger.info(f"Successfully returned realtime data for {symbol}")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting realtime data for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/batch", response_model=BatchRealtimeResponse)
async def get_batch_realtime_data(
    request: BatchRealtimeRequest,
    realtime_service: RealtimeDataService = Depends(get_realtime_service),
):
    """
    Get realtime data for multiple stocks in a single request.

    Args:
        request: Batch request with list of symbols

    Returns:
        Dictionary with realtime data for each symbol
    """
    try:
        symbols = request.symbols
        force_refresh = request.force_refresh

        logger.info(f"API batch request for {len(symbols)} symbols")

        # Validate input
        if not symbols or len(symbols) == 0:
            raise HTTPException(status_code=400, detail="Symbols list cannot be empty")

        if len(symbols) > 100:  # Limit batch size
            raise HTTPException(status_code=400, detail="Maximum 100 symbols per batch request")

        # Clean and validate symbols
        clean_symbols = []
        for symbol in symbols:
            if symbol and len(symbol.strip()) > 0:
                clean_symbols.append(symbol.strip())

        if not clean_symbols:
            raise HTTPException(status_code=400, detail="No valid symbols provided")

        # Get batch realtime data
        batch_data = realtime_service.get_realtime_data_batch(clean_symbols, force_refresh)

        # Count successful vs failed requests
        successful_count = sum(1 for data in batch_data.values() if "error" not in data)
        failed_count = len(batch_data) - successful_count

        # Create response
        response = {
            "data": batch_data,
            "metadata": {
                "status": "success",
                "message": f"Batch request completed: {successful_count} successful, {failed_count} failed",
                "total_requested": len(clean_symbols),
                "successful_count": successful_count,
                "failed_count": failed_count,
                "force_refresh": force_refresh,
                "response_time_ms": 0,  # Will be set by middleware
            },
        }

        logger.info(
            f"Successfully returned batch realtime data: {successful_count}/{len(clean_symbols)} successful"
        )
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting batch realtime data: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/cache/stats")
async def get_realtime_cache_stats(
    realtime_service: RealtimeDataService = Depends(get_realtime_service),
):
    """
    Get realtime data cache statistics.

    Returns:
        Cache statistics including hit ratio and record counts
    """
    try:
        logger.info("API request for realtime cache stats")

        stats = realtime_service.get_cache_stats()

        response = {
            "cache_stats": stats,
            "metadata": {
                "status": "success",
                "message": "Cache statistics retrieved successfully",
                "timestamp": "datetime.now().isoformat()",
            },
        }

        return response

    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete("/cache/cleanup")
async def cleanup_realtime_cache(
    realtime_service: RealtimeDataService = Depends(get_realtime_service),
):
    """
    Clean up expired realtime cache entries.

    Returns:
        Number of records deleted
    """
    try:
        logger.info("API request for cache cleanup")

        deleted_count = realtime_service.cleanup_expired_cache()

        response = {
            "deleted_count": deleted_count,
            "metadata": {
                "status": "success",
                "message": f"Successfully deleted {deleted_count} expired cache entries",
                "timestamp": "datetime.now().isoformat()",
            },
        }

        return response

    except Exception as e:
        logger.error(f"Error cleaning up cache: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
