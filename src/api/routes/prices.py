"""
Price data API routes with simplified architecture
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import date, datetime, timedelta
import time
import pandas as pd

from src.api.database import get_db
from src.api.models import Price, Asset
from src.api.schemas import Price as PriceSchema
from src.logger import setup_logger
from src.cache.akshare_adapter import AKShareAdapter

# Setup regular logger
logger = setup_logger(__name__)

# Create cache components
akshare_adapter = AKShareAdapter()

# Create router
router = APIRouter(
    tags=["prices"],
    responses={404: {"description": "Not found"}},
)


@router.get("/stock/{symbol}", response_model=List[PriceSchema])
async def get_stock_prices(
    symbol: str,
    start_date: Optional[str] = Query(None, description="Start date in format YYYYMMDD"),
    end_date: Optional[str] = Query(None, description="End date in format YYYYMMDD"),
    limit: Optional[int] = Query(100, description="Maximum number of records to return"),
    adjust: Optional[str] = Query("", description="Price adjustment: '' for no adjustment, 'qfq' for forward adjustment, 'hfq' for backward adjustment"),
    period: Optional[str] = Query("daily", description="Data period: daily, weekly, monthly"),
    db: Session = Depends(get_db)
):
    """
    Get stock price data for a specific symbol
    
    - **symbol**: Stock symbol (6-digit code)
    - **start_date**: Optional start date in format YYYYMMDD
    - **end_date**: Optional end date in format YYYYMMDD
    - **limit**: Maximum number of records to return (default: 100)
    - **adjust**: Price adjustment method
    - **period**: Data period (daily, weekly, monthly)
    """
    try:
        logger.info(f"Processing request for price data: symbol={symbol}, start_date={start_date}, end_date={end_date}, limit={limit}")
        
        # Look up asset by symbol
        asset_query_start = time.time()
        asset = db.query(Asset).filter(Asset.symbol == symbol).first()
        asset_query_time = time.time() - asset_query_start
        
        if asset:
            logger.info(f"Found asset in database: id={asset.asset_id}, symbol={asset.symbol}, name={asset.name}")
        else:
            logger.info(f"Asset with symbol {symbol} not found in database")
        
        # Handle date parameters
        if end_date is None:
            end_date = datetime.now().strftime('%Y%m%d')
            logger.info(f"No end_date provided, using today: {end_date}")
        
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=limit)).strftime('%Y%m%d')
            logger.info(f"No start_date provided, using {start_date} (end_date - {limit} days)")
        
        # Convert dates to strings for AKShare
        start_date_str = str(start_date)
        end_date_str = str(end_date)
        
        logger.info(f"Using date strings for AKShare: start_date={start_date_str}, end_date={end_date_str}")
        
        # Try to get data from database first if asset exists
        if asset:
            logger.info("Querying prices from database")
            db_query_start = time.time()
            
            prices = db.query(Price).filter(
                Price.asset_id == asset.asset_id,
                Price.trade_date >= start_date_str,
                Price.trade_date <= end_date_str
            ).order_by(Price.trade_date.desc()).limit(limit).all()
            
            db_query_time = time.time() - db_query_start
            
            if prices:
                logger.info(f"DATABASE HIT: Found {len(prices)} price records in database for {symbol}")
                return prices
            else:
                logger.info(f"Database miss: No price records found in database for {symbol} in date range")
        else:
            logger.info(f"Asset {symbol} not found in database, will create after fetching data")
        
        # Fetch data from AKShare
        logger.info(f"Fetching price data for {symbol} from AKShare")
        akshare_start = time.time()
        
        try:
            logger.info(f"Calling AKShare adapter with: symbol={symbol}, start_date={start_date_str}, end_date={end_date_str}")
            
            df = akshare_adapter.get_stock_hist(
                symbol=symbol,
                start_date=start_date_str,
                end_date=end_date_str,
                adjust=adjust,
                period=period
            )
            
            akshare_time = time.time() - akshare_start
            
            if df.empty:
                logger.warning(f"AKShare returned empty DataFrame for {symbol}")
                return []
            
            logger.info(f"Successfully fetched {len(df)} records from AKShare for {symbol}")
            
            # If asset doesn't exist, create it
            if asset is None:
                logger.info("Creating new asset record")
                asset_create_start = time.time()
                
                try:
                    asset = Asset(
                        symbol=symbol,
                        name=f"Stock {symbol}",  # Default name
                        asset_type="stock",
                        exchange="CN",
                        currency="CNY"
                    )
                    db.add(asset)
                    db.commit()
                    db.refresh(asset)
                    
                    asset_create_time = time.time() - asset_create_start
                    logger.info(f"Created new asset record for {symbol} with ID {asset.asset_id}")
                    
                except Exception as e:
                    logger.error(f"Database error when creating asset for {symbol}: {e}")
                    db.rollback()
                    # Create a temporary asset object for response
                    asset = Asset(
                        asset_id=0,
                        symbol=symbol,
                        name=f"Stock {symbol}",
                        asset_type="stock",
                        exchange="CN",
                        currency="CNY"
                    )
            
            # Convert DataFrame to database objects
            logger.info("Converting data and preparing for database storage")
            conversion_start = time.time()
            
            db_prices = []
            response_prices = []
            
            for _, row in df.iterrows():
                # Create database object
                db_price = Price(
                    asset_id=asset.asset_id,
                    trade_date=row['date'],
                    open_price=float(row['open']),
                    high_price=float(row['high']),
                    low_price=float(row['low']),
                    close_price=float(row['close']),
                    volume=int(row['volume']),
                    turnover=float(row.get('turnover', 0)),
                    amplitude=float(row.get('amplitude', 0)),
                    pct_change=float(row.get('pct_change', 0)),
                    change=float(row.get('change', 0)),
                    turnover_rate=float(row.get('turnover_rate', 0))
                )
                db_prices.append(db_price)
                
                # Create response object
                response_price = PriceSchema(
                    asset_id=asset.asset_id,
                    trade_date=row['date'],
                    open_price=float(row['open']),
                    high_price=float(row['high']),
                    low_price=float(row['low']),
                    close_price=float(row['close']),
                    volume=int(row['volume']),
                    turnover=float(row.get('turnover', 0)),
                    amplitude=float(row.get('amplitude', 0)),
                    pct_change=float(row.get('pct_change', 0)),
                    change=float(row.get('change', 0)),
                    turnover_rate=float(row.get('turnover_rate', 0))
                )
                response_prices.append(response_price)
            
            conversion_time = time.time() - conversion_start
            logger.info(f"Converted {len(df)} records to database objects")
            
            # Try to save to database if asset has valid ID
            if asset.asset_id and asset.asset_id > 0:
                try:
                    logger.info("Storing data in database")
                    db_insert_start = time.time()
                    
                    db.add_all(db_prices)
                    db.commit()
                    
                    db_insert_time = time.time() - db_insert_start
                    logger.info(f"Saved {len(db_prices)} price records to database for {symbol}")
                    
                    # Query the inserted prices to get the actual database objects
                    logger.info("Querying inserted prices")
                    db_query_start = time.time()
                    
                    inserted_prices = db.query(Price).filter(
                        Price.asset_id == asset.asset_id,
                        Price.trade_date >= start_date_str,
                        Price.trade_date <= end_date_str
                    ).order_by(Price.trade_date.desc()).limit(limit).all()
                    
                    db_query_time = time.time() - db_query_start
                    logger.info(f"Retrieved {len(inserted_prices)} inserted price records from database")
                    
                    logger.info(f"AKSHARE + DATABASE: Returning {len(inserted_prices)} price records from AKShare via database")
                    return inserted_prices
                    
                except Exception as e:
                    logger.error(f"Database error when saving prices for {symbol}: {e}")
                    db.rollback()
                    # Fall back to returning AKShare data directly
                    logger.info(f"AKSHARE DIRECT: Returning {len(response_prices)} price records directly from AKShare")
                    return response_prices
            else:
                logger.warning(f"No price data to save for {symbol}")
                return []
                
        except Exception as e:
            logger.error(f"Error fetching data from AKShare for {symbol}: {e}")
            
            # If we have an asset but no prices, return empty list
            if asset:
                logger.info("Asset exists but no prices found, returning empty list")
                return []
            
            # If no asset and failed to fetch data, raise 404
            logger.error("Asset not found and failed to fetch data, raising 404")
            raise HTTPException(status_code=404, detail=f"Stock symbol {symbol} not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Database error when getting prices for symbol {symbol}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
