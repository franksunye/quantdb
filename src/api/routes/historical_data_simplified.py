# src/api/routes/historical_data_simplified.py
"""
Historical stock data API routes with simplified cache architecture.

This module provides API endpoints for retrieving historical stock data,
using the simplified cache architecture with database as persistent cache.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import date, datetime
import pandas as pd

from src.api.database import get_db
from src.api.models import Asset
from src.api.schemas import HistoricalDataResponse, HistoricalDataPoint
from src.cache.akshare_adapter_simplified import AKShareAdapter
from src.services.stock_data_service import StockDataService
from src.services.database_cache import DatabaseCache
from src.logger import setup_logger

# Create dependencies for services
def get_akshare_adapter(db: Session = Depends(get_db)):
    """Get AKShare adapter instance."""
    return AKShareAdapter(db)

def get_stock_data_service(
    db: Session = Depends(get_db),
    akshare_adapter: AKShareAdapter = Depends(get_akshare_adapter)
):
    """Get stock data service instance."""
    return StockDataService(db, akshare_adapter)

# Setup logger
logger = setup_logger(__name__)

# Create router
router = APIRouter(
    tags=["historical"],
    responses={404: {"description": "Not found"}},
)

@router.get("/stock/{symbol}", response_model=HistoricalDataResponse)
async def get_historical_stock_data(
    symbol: str,
    start_date: Optional[str] = Query(None, description="Start date in format YYYYMMDD"),
    end_date: Optional[str] = Query(None, description="End date in format YYYYMMDD"),
    adjust: Optional[str] = Query("", description="Price adjustment: '' for no adjustment, 'qfq' for forward adjustment, 'hfq' for backward adjustment"),
    db: Session = Depends(get_db),
    stock_data_service: StockDataService = Depends(get_stock_data_service)
):
    """
    Get historical stock data for a specific symbol

    - **symbol**: Stock symbol (6-digit code)
    - **start_date**: Optional start date in format YYYYMMDD
    - **end_date**: Optional end date in format YYYYMMDD
    - **adjust**: Price adjustment method ('' for no adjustment, 'qfq' for forward adjustment, 'hfq' for backward adjustment)
    """
    try:
        # Validate symbol format
        if not symbol.isdigit() or len(symbol) != 6:
            raise HTTPException(status_code=400, detail="Symbol must be a 6-digit number")

        # Check if asset exists in database
        asset = db.query(Asset).filter(Asset.symbol == symbol).first()

        # Set default dates if not provided
        if end_date is None:
            end_date = datetime.now().strftime("%Y%m%d")

        # Fetch data using the stock data service
        logger.info(f"Fetching historical data for {symbol} from {start_date} to {end_date} with adjust={adjust}")
        try:
            df = stock_data_service.get_stock_data(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                adjust=adjust
            )

            if df.empty:
                logger.warning(f"No historical data found for {symbol}")
                return {
                    "symbol": symbol,
                    "name": asset.name if asset else f"Stock {symbol}",
                    "start_date": start_date,
                    "end_date": end_date,
                    "adjust": adjust,
                    "data": [],
                    "metadata": {
                        "count": 0,
                        "status": "success",
                        "message": "No data found for the specified parameters"
                    }
                }

            # Convert DataFrame to response format
            data_points = []
            for _, row in df.iterrows():
                data_point = HistoricalDataPoint(
                    date=row.get('date', None),
                    open=row.get('open', None),
                    high=row.get('high', None),
                    low=row.get('low', None),
                    close=row.get('close', None),
                    volume=row.get('volume', None),
                    turnover=row.get('turnover', None),
                    amplitude=row.get('amplitude', None),
                    pct_change=row.get('pct_change', None),
                    change=row.get('change', None),
                    turnover_rate=row.get('turnover_rate', None)
                )
                data_points.append(data_point)

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
                    "message": f"Successfully retrieved {len(data_points)} data points"
                }
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

def get_database_cache(db: Session = Depends(get_db)):
    """Get database cache instance."""
    return DatabaseCache(db)

@router.get("/database/cache/status")
async def get_database_cache_status(
    symbol: Optional[str] = Query(None, description="Stock symbol"),
    start_date: Optional[str] = Query(None, description="Start date in format YYYYMMDD"),
    end_date: Optional[str] = Query(None, description="End date in format YYYYMMDD"),
    database_cache: DatabaseCache = Depends(get_database_cache)
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
                "coverage": coverage_info
            }

        # Otherwise, get general cache statistics
        stats = database_cache.get_stats()
        return stats

    except Exception as e:
        logger.error(f"Error getting database cache status: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting cache status: {str(e)}")
