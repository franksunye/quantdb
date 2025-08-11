"""
Historical stock data API routes
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import date, datetime
import pandas as pd

from core.database import get_db
from core.models import Asset
from api.schemas import HistoricalDataResponse, HistoricalDataPoint
from core.cache.akshare_adapter import AKShareAdapter
from core.utils.logger import get_logger

# Setup logger
logger = get_logger(__name__)

# Create router
router = APIRouter(
    tags=["historical"],
    responses={404: {"description": "Not found"}},
)

# Create cache components
akshare_adapter = AKShareAdapter()


# Simple cache implementations for this old file
class SimpleCacheEngine:
    def __init__(self):
        self._cache = {}

    def get(self, key):
        return self._cache.get(key)

    def set(self, key, value, ttl=None):
        self._cache[key] = value


class SimpleFreshnessTracker:
    def __init__(self):
        self._freshness = {}

    def is_fresh(self, key, policy="relaxed"):
        # For this old file, always return False to force fresh data
        return False

    def mark_updated(self, key, ttl=None):
        self._freshness[key] = True


# Initialize cache components
cache_engine = SimpleCacheEngine()
freshness_tracker = SimpleFreshnessTracker()


@router.get("/stock/{symbol}", response_model=HistoricalDataResponse)
async def get_historical_stock_data(
    symbol: str,
    start_date: Optional[str] = Query(None, description="Start date in format YYYYMMDD"),
    end_date: Optional[str] = Query(None, description="End date in format YYYYMMDD"),
    adjust: Optional[str] = Query(
        "",
        description="Price adjustment: '' for no adjustment, 'qfq' for forward adjustment, 'hfq' for backward adjustment",
    ),
    db: Session = Depends(get_db),
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

        # Generate cache key
        cache_key = f"historical_stock_{symbol}_{start_date}_{end_date}_{adjust}"

        # Check if data is in cache and fresh
        if freshness_tracker.is_fresh(cache_key, "relaxed"):
            cached_data = cache_engine.get(cache_key)
            if cached_data is not None:
                logger.info(f"Returning cached historical data for {symbol}")
                return cached_data

        # Fetch data from AKShare
        logger.info(
            f"Fetching historical data for {symbol} from {start_date} to {end_date} with adjust={adjust}"
        )
        try:
            df = akshare_adapter.get_stock_data(
                symbol=symbol, start_date=start_date, end_date=end_date, adjust=adjust
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
                        "message": "No data found for the specified parameters",
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
                },
            }

            # Cache the response
            cache_engine.set(cache_key, response, ttl=86400)  # Cache for 24 hours
            freshness_tracker.mark_updated(cache_key, ttl=86400)

            return response

        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {e}")
            raise HTTPException(status_code=500, detail=f"Error fetching data: {str(e)}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_historical_stock_data: {e}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
