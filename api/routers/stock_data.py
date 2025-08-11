"""
Stock data API routes for QuantDB API service.

This module provides API endpoints for retrieving historical stock data,
using the core business layer.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from datetime import date, datetime
import pandas as pd

# Import core modules
from core.database.connection import get_db
from core.models.asset import Asset
from core.services.stock_data_service import StockDataService
from core.services.database_cache import DatabaseCache
from core.services.asset_info_service import AssetInfoService
from core.cache.akshare_adapter import AKShareAdapter
from core.utils.logger import logger

# Import API schemas
from ..schemas import HistoricalDataResponse, HistoricalDataPoint


# Create dependencies for services
def get_akshare_adapter(db: Session = Depends(get_db)):
    """Get AKShare adapter instance."""
    return AKShareAdapter(db)


def get_stock_data_service(
    db: Session = Depends(get_db), akshare_adapter: AKShareAdapter = Depends(get_akshare_adapter)
):
    """Get stock data service instance."""
    return StockDataService(db, akshare_adapter)


def get_asset_info_service(db: Session = Depends(get_db)):
    """Get asset info service instance."""
    return AssetInfoService(db)


def get_database_cache(db: Session = Depends(get_db)):
    """Get database cache instance."""
    return DatabaseCache(db)


# Create router
router = APIRouter(
    prefix="/stock-data",
    tags=["Stock Data"],
    responses={404: {"description": "Not found"}},
)


@router.get("/{symbol}", response_model=HistoricalDataResponse)
async def get_historical_stock_data(
    symbol: str,
    request: Request,
    start_date: Optional[str] = Query(None, description="Start date in format YYYYMMDD"),
    end_date: Optional[str] = Query(None, description="End date in format YYYYMMDD"),
    adjust: Optional[str] = Query(
        "",
        description="Price adjustment: '' for no adjustment, 'qfq' for forward adjustment, 'hfq' for backward adjustment",
    ),
    db: Session = Depends(get_db),
    stock_data_service: StockDataService = Depends(get_stock_data_service),
    asset_info_service: AssetInfoService = Depends(get_asset_info_service),
):
    """
    Get historical stock data for a specific symbol

    - **symbol**: Stock symbol (6-digit for A-shares, 5-digit for Hong Kong stocks)
    - **start_date**: Optional start date in format YYYYMMDD
    - **end_date**: Optional end date in format YYYYMMDD
    - **adjust**: Price adjustment method ('' for no adjustment, 'qfq' for forward adjustment, 'hfq' for backward adjustment)
    """
    try:
        # Validate symbol format - support both A-shares and Hong Kong stocks
        if not symbol.isdigit() or (len(symbol) != 6 and len(symbol) != 5):
            raise HTTPException(
                status_code=400,
                detail="Symbol must be 6 digits for A-shares or 5 digits for Hong Kong stocks",
            )

        # Get or create asset with enhanced information
        asset, asset_metadata = asset_info_service.get_or_create_asset(symbol)

        # Set default dates if not provided
        if end_date is None:
            end_date = datetime.now().strftime("%Y%m%d")

        # Fetch data using the stock data service
        logger.info(
            f"Fetching historical data for {symbol} from {start_date} to {end_date} with adjust={adjust}"
        )
        try:
            df = stock_data_service.get_stock_data(
                symbol=symbol, start_date=start_date, end_date=end_date, adjust=adjust
            )

            if df.empty:
                logger.warning(
                    f"No historical data found for {symbol} from {start_date} to {end_date}"
                )

                return {
                    "symbol": symbol,
                    "name": asset.name if asset else f"Stock {symbol}",
                    "start_date": start_date,
                    "end_date": end_date,
                    "adjust": adjust,
                    "data": [],
                    "metadata": {
                        "count": 0,
                        "status": "no_data",
                        "message": "No data found for the specified parameters",
                        "suggestions": [
                            "Try extending the date range to 30 days or more",
                            "Verify the stock code is correct and still trading",
                            "Check if the selected dates include trading days",
                            "Try querying active stocks like 600000, 000001, or 600519",
                        ],
                    },
                }

            # Convert DataFrame to response format
            data_points = []
            for _, row in df.iterrows():
                data_point = HistoricalDataPoint(
                    date=row.get("date", None),
                    open=row.get("open", None),
                    high=row.get("high", None),
                    low=row.get("low", None),
                    close=row.get("close", None),
                    volume=row.get("volume", None),
                    turnover=row.get("turnover", None),
                    amplitude=row.get("amplitude", None),
                    pct_change=row.get("pct_change", None),
                    change=row.get("change", None),
                    turnover_rate=row.get("turnover_rate", None),
                )
                data_points.append(data_point)

            # Get cache info
            cache_info = _get_cache_info(symbol, start_date, end_date, df, stock_data_service)

            # Create response
            response = {
                "symbol": symbol,
                "name": asset.name if asset else f"Stock {symbol}",
                "start_date": start_date,
                "end_date": end_date,
                "adjust": adjust,
                "data": data_points,
                "metadata": {
                    "count": len(data_points),
                    "status": "success",
                    "message": f"Successfully retrieved {len(data_points)} data points",
                    "cache_info": cache_info,
                },
            }

            return response

        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {e}")
            raise HTTPException(status_code=500, detail=f"Error fetching data: {str(e)}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_historical_stock_data: {e}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@router.get("/cache/status")
async def get_database_cache_status(
    symbol: Optional[str] = Query(None, description="Stock symbol"),
    start_date: Optional[str] = Query(None, description="Start date in format YYYYMMDD"),
    end_date: Optional[str] = Query(None, description="End date in format YYYYMMDD"),
    database_cache: DatabaseCache = Depends(get_database_cache),
):
    """
    Get database cache status

    - **symbol**: Optional stock symbol to check coverage for
    - **start_date**: Optional start date for coverage check
    - **end_date**: Optional end date for coverage check
    """
    try:
        # If symbol and date range provided, get coverage information
        if symbol and start_date and end_date:
            coverage_info = database_cache.get_date_range_coverage(symbol, start_date, end_date)
            return {
                "symbol": symbol,
                "start_date": start_date,
                "end_date": end_date,
                "coverage": coverage_info,
            }

        # Otherwise, get general cache statistics
        stats = database_cache.get_stats()
        return stats

    except Exception as e:
        logger.error(f"Error getting database cache status: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting cache status: {str(e)}")


def _get_cache_info(symbol: str, start_date: str, end_date: str, df, stock_data_service) -> dict:
    """Get real cache status information"""
    try:
        from core.services.trading_calendar import get_trading_calendar

        # Get trading calendar
        trading_calendar = get_trading_calendar()
        trading_days = trading_calendar.get_trading_days(start_date, end_date)
        total_trading_days = len(trading_days)

        # Check existing data in database
        db_cache = stock_data_service.db_cache
        existing_data = db_cache.get(symbol, trading_days)
        cached_days = len(existing_data)

        # Calculate cache hit ratio
        cache_hit_ratio = cached_days / total_trading_days if total_trading_days > 0 else 0.0

        # Determine if AKShare was called
        akshare_called = cached_days < total_trading_days

        # Determine if it's a cache hit
        cache_hit = cached_days == total_trading_days and total_trading_days > 0

        logger.info(
            f"Cache info for {symbol}: hit={cache_hit}, ratio={cache_hit_ratio:.2f}, "
            f"cached_days={cached_days}, total_days={total_trading_days}, akshare_called={akshare_called}"
        )

        return {
            "cache_hit": cache_hit,
            "akshare_called": akshare_called,
            "cache_hit_ratio": cache_hit_ratio,
            "cached_days": cached_days,
            "total_trading_days": total_trading_days,
            "response_time_ms": 0,  # This will be set in middleware
        }

    except Exception as e:
        logger.error(f"Error getting cache info: {e}")
        # Return default values
        return {
            "cache_hit": False,
            "akshare_called": True,
            "cache_hit_ratio": 0.0,
            "cached_days": 0,
            "total_trading_days": 0,
            "response_time_ms": 0,
        }
