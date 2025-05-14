"""
Price API routes
"""
from typing import List, Optional
from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from src.api.database import get_db
from src.api.models import Price, Asset
from src.api.schemas import Price as PriceSchema
from src.logger import setup_logger

# Setup logger
logger = setup_logger(__name__)

# Create router
router = APIRouter(
    prefix="/prices",
    tags=["prices"],
    responses={404: {"description": "Not found"}},
)

@router.get("/", response_model=List[PriceSchema])
async def get_prices(
    asset_id: Optional[int] = Query(None, description="Filter by asset ID"),
    symbol: Optional[str] = Query(None, description="Filter by asset symbol"),
    start_date: Optional[date] = Query(None, description="Start date for price data"),
    end_date: Optional[date] = Query(None, description="End date for price data"),
    skip: int = Query(0, ge=0, description="Number of prices to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of prices to return"),
    db: Session = Depends(get_db)
):
    """
    Get a list of prices with optional filtering
    """
    try:
        query = db.query(Price)
        
        # Apply filters if provided
        if asset_id:
            query = query.filter(Price.asset_id == asset_id)
        
        if symbol:
            # Join with Asset table to filter by symbol
            query = query.join(Asset).filter(Asset.symbol == symbol)
        
        if start_date:
            query = query.filter(Price.date >= start_date)
        
        if end_date:
            query = query.filter(Price.date <= end_date)
        
        # Order by date (newest first)
        query = query.order_by(Price.date.desc())
        
        # Apply pagination
        prices = query.offset(skip).limit(limit).all()
        
        return prices
    except SQLAlchemyError as e:
        logger.error(f"Database error when getting prices: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    except Exception as e:
        logger.error(f"Unexpected error when getting prices: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/asset/{asset_id}", response_model=List[PriceSchema])
async def get_prices_by_asset(
    asset_id: int,
    start_date: Optional[date] = Query(None, description="Start date for price data"),
    end_date: Optional[date] = Query(None, description="End date for price data"),
    period: str = Query("daily", description="Time period: daily, weekly, monthly"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of prices to return"),
    db: Session = Depends(get_db)
):
    """
    Get price history for a specific asset
    """
    try:
        # Check if asset exists
        asset = db.query(Asset).filter(Asset.asset_id == asset_id).first()
        if asset is None:
            raise HTTPException(status_code=404, detail="Asset not found")
        
        # Set default dates if not provided
        if end_date is None:
            end_date = date.today()
        
        if start_date is None:
            if period == "daily":
                start_date = end_date - timedelta(days=limit)
            elif period == "weekly":
                start_date = end_date - timedelta(weeks=limit)
            elif period == "monthly":
                # Approximate months as 30 days
                start_date = end_date - timedelta(days=30 * limit)
            else:
                start_date = end_date - timedelta(days=limit)
        
        # Query prices
        query = db.query(Price).filter(
            Price.asset_id == asset_id,
            Price.date >= start_date,
            Price.date <= end_date
        ).order_by(Price.date.desc())
        
        # Apply period aggregation (simplified version)
        # For a real implementation, you would use SQL window functions or ORM aggregation
        # This is a placeholder for the concept
        if period == "weekly" or period == "monthly":
            logger.info(f"Period aggregation for {period} is not fully implemented")
            # In a real implementation, you would aggregate the data here
        
        # Apply limit
        prices = query.limit(limit).all()
        
        return prices
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error when getting prices for asset {asset_id}: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    except Exception as e:
        logger.error(f"Unexpected error when getting prices for asset {asset_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/symbol/{symbol}", response_model=List[PriceSchema])
async def get_prices_by_symbol(
    symbol: str,
    start_date: Optional[date] = Query(None, description="Start date for price data"),
    end_date: Optional[date] = Query(None, description="End date for price data"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of prices to return"),
    db: Session = Depends(get_db)
):
    """
    Get price history for a specific asset by symbol
    """
    try:
        # Get asset by symbol
        asset = db.query(Asset).filter(Asset.symbol == symbol).first()
        if asset is None:
            raise HTTPException(status_code=404, detail="Asset not found")
        
        # Set default dates if not provided
        if end_date is None:
            end_date = date.today()
        
        if start_date is None:
            start_date = end_date - timedelta(days=limit)
        
        # Query prices
        prices = db.query(Price).filter(
            Price.asset_id == asset.asset_id,
            Price.date >= start_date,
            Price.date <= end_date
        ).order_by(Price.date.desc()).limit(limit).all()
        
        return prices
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error when getting prices for symbol {symbol}: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    except Exception as e:
        logger.error(f"Unexpected error when getting prices for symbol {symbol}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
