"""
Index data API routes for QuantDB API service.

This module provides API endpoints for retrieving index data
with intelligent caching strategies.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.cache.akshare_adapter import AKShareAdapter

# Import core modules
from core.database.connection import get_db
from core.services.index_data_service import IndexDataService
from core.utils.logger import logger

# Create router
router = APIRouter(prefix="/api/v1/index", tags=["index"])


# Request/Response models
class IndexDataResponse(BaseModel):
    """Response model for index historical data."""

    symbol: str
    name: str
    start_date: str
    end_date: str
    period: str
    data: List[Dict[str, Any]]
    metadata: Dict[str, Any]


class RealtimeIndexDataResponse(BaseModel):
    """Response model for single realtime index data."""

    symbol: str
    name: str
    price: float
    open: Optional[float]
    high: Optional[float]
    low: Optional[float]
    prev_close: Optional[float]
    change: Optional[float]
    pct_change: Optional[float]
    amplitude: Optional[float]
    volume: Optional[float]
    turnover: Optional[float]
    timestamp: str
    cache_hit: bool
    is_trading_hours: bool
    metadata: Dict[str, Any]


class IndexListResponse(BaseModel):
    """Response model for index list."""

    data: List[Dict[str, Any]]
    metadata: Dict[str, Any]


# Dependencies
def get_akshare_adapter(db: Session = Depends(get_db)):
    """Get AKShare adapter instance."""
    return AKShareAdapter(db)


def get_index_data_service(
    db: Session = Depends(get_db), akshare_adapter: AKShareAdapter = Depends(get_akshare_adapter)
):
    """Get index data service instance."""
    return IndexDataService(db, akshare_adapter)


# API Endpoints
@router.get("/historical/{symbol}", response_model=IndexDataResponse)
async def get_historical_index_data(
    symbol: str,
    start_date: Optional[str] = Query(None, description="Start date in format YYYYMMDD"),
    end_date: Optional[str] = Query(None, description="End date in format YYYYMMDD"),
    period: str = Query("daily", description="Data frequency: daily, weekly, monthly"),
    force_refresh: bool = Query(False, description="Force refresh data from source"),
    index_service: IndexDataService = Depends(get_index_data_service),
):
    """
    Get historical data for a specific index symbol.

    Args:
        symbol: Index symbol (e.g., '000001', '399001')
        start_date: Start date in YYYYMMDD format
        end_date: End date in YYYYMMDD format
        period: Data frequency (daily, weekly, monthly)
        force_refresh: If True, bypass cache and fetch fresh data

    Returns:
        Historical index data with metadata
    """
    try:
        logger.info(f"API request for historical index data: {symbol}")

        # Validate symbol format
        if not symbol or len(symbol.strip()) == 0:
            raise HTTPException(status_code=400, detail="Symbol cannot be empty")

        # Validate period
        valid_periods = ["daily", "weekly", "monthly"]
        if period not in valid_periods:
            raise HTTPException(
                status_code=400, detail=f"Invalid period. Must be one of: {valid_periods}"
            )

        # Get historical data
        df = index_service.get_index_data(
            symbol=symbol.strip(),
            start_date=start_date,
            end_date=end_date,
            period=period,
            force_refresh=force_refresh,
        )

        if df.empty:
            raise HTTPException(status_code=404, detail=f"No data found for index {symbol}")

        # Convert DataFrame to list of dictionaries
        data_points = df.to_dict("records")

        # Get index name from first row if available
        index_name = (
            df.iloc[0].get("name", f"Index {symbol}") if "name" in df.columns else f"Index {symbol}"
        )

        # Create response
        response = {
            "symbol": symbol,
            "name": index_name,
            "start_date": start_date or "auto",
            "end_date": end_date or "auto",
            "period": period,
            "data": data_points,
            "metadata": {
                "count": len(data_points),
                "status": "success",
                "message": f"Successfully retrieved {len(data_points)} data points",
                "force_refresh": force_refresh,
                "response_time_ms": 0,  # Will be set by middleware
            },
        }

        logger.info(f"Successfully returned historical index data for {symbol}")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting historical index data for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/realtime/{symbol}", response_model=RealtimeIndexDataResponse)
async def get_realtime_index_data(
    symbol: str,
    force_refresh: bool = Query(False, description="Force refresh data from source"),
    index_service: IndexDataService = Depends(get_index_data_service),
):
    """
    Get realtime data for a specific index symbol.

    Args:
        symbol: Index symbol (e.g., '000001', '399001')
        force_refresh: If True, bypass cache and fetch fresh data

    Returns:
        Realtime index data with metadata
    """
    try:
        logger.info(f"API request for realtime index data: {symbol}")

        # Validate symbol format
        if not symbol or len(symbol.strip()) == 0:
            raise HTTPException(status_code=400, detail="Symbol cannot be empty")

        # Get realtime data
        data = index_service.get_realtime_index_data(symbol.strip(), force_refresh)

        # Check for errors
        if "error" in data:
            raise HTTPException(status_code=404, detail=data["error"])

        # Create response
        response = {
            "symbol": data.get("symbol", symbol),
            "name": data.get("name", f"Index {symbol}"),
            "price": data.get("price", 0.0),
            "open": data.get("open"),
            "high": data.get("high"),
            "low": data.get("low"),
            "prev_close": data.get("prev_close"),
            "change": data.get("change"),
            "pct_change": data.get("pct_change"),
            "amplitude": data.get("amplitude"),
            "volume": data.get("volume"),
            "turnover": data.get("turnover"),
            "timestamp": data.get("timestamp", ""),
            "cache_hit": data.get("cache_hit", False),
            "is_trading_hours": data.get("is_trading_hours", False),
            "metadata": {
                "status": "success",
                "message": f"Successfully retrieved realtime data for {symbol}",
                "force_refresh": force_refresh,
                "response_time_ms": 0,  # Will be set by middleware
            },
        }

        logger.info(f"Successfully returned realtime index data for {symbol}")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting realtime index data for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/list", response_model=IndexListResponse)
async def get_index_list(
    category: Optional[str] = Query(None, description="Index category filter"),
    force_refresh: bool = Query(False, description="Force refresh data from source"),
    index_service: IndexDataService = Depends(get_index_data_service),
):
    """
    Get list of available indexes with optional category filtering.

    Args:
        category: Index category filter (e.g., '沪深重要指数', '上证系列指数')
        force_refresh: If True, bypass cache and fetch fresh data

    Returns:
        List of indexes with metadata
    """
    try:
        logger.info(f"API request for index list, category: {category or 'all'}")

        # Get index list
        index_list = index_service.get_index_list(category, force_refresh)

        # Create response
        response = {
            "data": index_list,
            "metadata": {
                "count": len(index_list),
                "status": "success",
                "message": f"Successfully retrieved {len(index_list)} indexes",
                "category": category or "all",
                "force_refresh": force_refresh,
                "response_time_ms": 0,  # Will be set by middleware
            },
        }

        logger.info(f"Successfully returned index list with {len(index_list)} entries")
        return response

    except Exception as e:
        logger.error(f"Error getting index list: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/categories")
async def get_index_categories():
    """
    Get available index categories.

    Returns:
        List of available index categories
    """
    try:
        categories = [
            {
                "code": "沪深重要指数",
                "name": "Major Shanghai-Shenzhen Indexes",
                "description": "Major market indexes including Shanghai Composite, Shenzhen Component, etc.",
            },
            {
                "code": "上证系列指数",
                "name": "Shanghai Stock Exchange Indexes",
                "description": "Shanghai Stock Exchange index series",
            },
            {
                "code": "深证系列指数",
                "name": "Shenzhen Stock Exchange Indexes",
                "description": "Shenzhen Stock Exchange index series",
            },
            {
                "code": "中证系列指数",
                "name": "CSI Index Series",
                "description": "China Securities Index series",
            },
            {
                "code": "香港指数",
                "name": "Hong Kong Stock Indexes",
                "description": "Hang Seng family indexes including HSI, HSCEI, HSTECH",
            },
        ]

        return {
            "data": categories,
            "metadata": {
                "count": len(categories),
                "status": "success",
                "message": "Successfully retrieved index categories",
            },
        }

    except Exception as e:
        logger.error(f"Error getting index categories: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
