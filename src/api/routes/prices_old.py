"""
Price API routes
"""
from typing import List, Optional
from datetime import date, timedelta, datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import pandas as pd
import time
import uuid

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
    adjust: str = Query("", description="Price adjustment method: '' (no adjustment), 'qfq' (forward), 'hfq' (backward)"),
    period: str = Query("daily", description="Data frequency: 'daily', 'weekly', 'monthly'"),
    debug: bool = Query(False, description="Enable debug mode for detailed logging"),
    request: Request = None,
    db: Session = Depends(get_db)
):
    """
    Get price history for a specific asset by symbol

    If data is not found in the database, it will be fetched from AKShare and stored in the database.
    """
    # Create a trace ID from the request or generate a new one
    trace_id = str(uuid.uuid4())

    # Set debug mode if requested
    if debug:
        trace_logger.debug_mode = True

    # Start trace with context information
    trace_logger.start_trace(trace_id, {
        'symbol': symbol,
        'start_date': start_date.isoformat() if start_date else None,
        'end_date': end_date.isoformat() if end_date else None,
        'limit': limit,
        'adjust': adjust,
        'period': period,
        'debug_mode': debug
    })

    try:
        trace_logger.info(f"Processing request for price data: symbol={symbol}, start_date={start_date}, end_date={end_date}, limit={limit}, adjust={adjust}, period={period}")
        trace_logger.step("Request received")

        # Get asset by symbol
        trace_logger.transition("API", "Database", "Querying asset by symbol")
        asset_query_start = time.time()
        asset = db.query(Asset).filter(Asset.symbol == symbol).first()
        asset_query_time = time.time() - asset_query_start

        if asset:
            trace_logger.info(f"Found asset in database: id={asset.asset_id}, symbol={asset.symbol}, name={asset.name}")
            trace_logger.data("asset_query_time", f"{asset_query_time:.4f}s")
        else:
            trace_logger.info(f"Asset with symbol {symbol} not found in database")
            trace_logger.data("asset_query_time", f"{asset_query_time:.4f}s")

        trace_logger.step("Asset lookup completed")

        # Set default dates if not provided
        if end_date is None:
            end_date = date.today()
            trace_logger.info(f"No end_date provided, using today: {end_date}")
        else:
            trace_logger.info(f"Using provided end_date: {end_date} (type: {type(end_date).__name__})")

        if start_date is None:
            start_date = end_date - timedelta(days=limit)
            trace_logger.info(f"No start_date provided, using {start_date} (end_date - {limit} days)")
        else:
            trace_logger.info(f"Using provided start_date: {start_date} (type: {type(start_date).__name__})")

        # Convert dates to string format for cache key and AKShare
        start_date_str = start_date.strftime("%Y%m%d") if start_date else None
        end_date_str = end_date.strftime("%Y%m%d") if end_date else None

        # Log the exact date strings that will be used
        trace_logger.info(f"Using date strings for AKShare: start_date={start_date_str}, end_date={end_date_str}")

        # Generate cache key - simplified for better performance
        cache_key = f"prices_symbol_{symbol}_{start_date_str}_{end_date_str}_{adjust}_{period}"
        trace_logger.info(f"Generated cache key: {cache_key}")
        trace_logger.step("Parameters processed")

        # Add a flag to track data source for performance analysis
        data_source = None

        # Check if data is in cache and fresh
        trace_logger.transition("API", "Cache", "Checking cache for data")
        cache_check_start = time.time()
        is_fresh = freshness_tracker.is_fresh(cache_key, "relaxed")

        if is_fresh:
            trace_logger.info(f"Cache entry is fresh for key: {cache_key}")
            cached_data = cache_engine.get(cache_key)
            cache_check_time = time.time() - cache_check_start
            trace_logger.data("cache_check_time", f"{cache_check_time:.4f}s")

            if cached_data is not None:
                # Mark data source as cache for performance tracking
                data_source = "cache"

                # Add detailed performance metrics for cache retrieval
                trace_logger.data("data_source", data_source)

                # Add more detailed logging about cache performance
                trace_logger.info(f"CACHE HIT: Returning {len(cached_data) if cached_data else 0} cached price records for {symbol}")
                trace_logger.info(f"Cache retrieval time: {cache_check_time:.4f}s")
                trace_logger.step("Cache hit - returning cached data")

                # Add a header to the response to indicate data source
                # This will be visible in the API response for debugging
                for price in cached_data:
                    if hasattr(price, '_sa_instance_state'):
                        # This is an SQLAlchemy model instance
                        # We can't add attributes directly, but we can log it
                        pass

                trace_logger.end_trace()
                return cached_data
            else:
                trace_logger.info(f"Cache entry is fresh but data is None")
        else:
            trace_logger.info(f"Cache miss: No fresh data found for key {cache_key}")
            cache_check_time = time.time() - cache_check_start
            trace_logger.data("cache_check_time", f"{cache_check_time:.4f}s")

        trace_logger.step("Cache check completed")

        # If asset exists, try to get data from database
        if asset is not None:
            trace_logger.transition("API", "Database", "Querying prices from database")
            db_query_start = time.time()

            # Query prices from database
            prices = db.query(Price).filter(
                Price.asset_id == asset.asset_id,
                Price.date >= start_date,
                Price.date <= end_date
            ).order_by(Price.date.desc()).limit(limit).all()

            db_query_time = time.time() - db_query_start
            trace_logger.data("db_query_time", f"{db_query_time:.4f}s")

            # If we have data in the database, return it
            if prices:
                # Mark data source as database for performance tracking
                data_source = "database"
                trace_logger.data("data_source", data_source)

                trace_logger.info(f"DATABASE HIT: Found {len(prices)} price records in database for {symbol}")
                trace_logger.info(f"Database query time: {db_query_time:.4f}s")
                trace_logger.step("Database hit - returning database data")

                # Cache the results with optimized settings
                trace_logger.transition("Database", "Cache", "Storing database results in cache")
                cache_start = time.time()

                # Use a longer TTL for database results to improve cache hit rate
                cache_ttl = 86400 * 7  # Cache for 7 days
                cache_engine.set(cache_key, prices, ttl=cache_ttl)
                freshness_tracker.mark_updated(cache_key, ttl=cache_ttl)

                cache_time = time.time() - cache_start
                trace_logger.data("cache_store_time", f"{cache_time:.4f}s")
                trace_logger.info(f"Stored {len(prices)} records in cache with TTL={cache_ttl}s")

                trace_logger.step("Data cached")
                trace_logger.end_trace()
                return prices
            else:
                trace_logger.info(f"Database miss: No price records found in database for {symbol} in date range")
        else:
            trace_logger.info(f"Asset {symbol} not found in database, will create after fetching data")

        # If we get here, we need to fetch data from AKShare
        trace_logger.transition("API", "AKShare", "Fetching data from external API")
        trace_logger.info(f"Fetching price data for {symbol} from AKShare with parameters: start_date={start_date_str}, end_date={end_date_str}")
        trace_logger.step("Starting AKShare data fetch")

        try:
            # Fetch data from AKShare
            akshare_start = time.time()

            # AKShare adapter expects dates in YYYYMMDD format
            # We've already converted the dates above, but let's log the exact parameters
            trace_logger.info(f"Calling AKShare adapter with: symbol={symbol}, start_date={start_date_str}, end_date={end_date_str}, adjust={adjust}, period={period}")

            # Log the exact call for debugging
            trace_logger.debug(f"DEBUG: Calling AKShare adapter with: symbol={symbol}, start_date={start_date_str}, end_date={end_date_str}, adjust={adjust}, period={period}")

            df = akshare_adapter.get_stock_data(
                symbol=symbol,
                start_date=start_date_str,
                end_date=end_date_str,
                adjust=adjust,
                period=period
            )
            akshare_time = time.time() - akshare_start
            trace_logger.data("akshare_fetch_time", f"{akshare_time:.4f}s")

            if df.empty:
                trace_logger.warning(f"AKShare returned empty DataFrame for {symbol}")
                trace_logger.warning(f"This could be due to invalid symbol, date range, or AKShare API issues")
                trace_logger.warning(f"Check AKShare logs for more details")
                trace_logger.step("AKShare returned empty data")
                trace_logger.end_trace()
                return []

            trace_logger.info(f"Successfully fetched {len(df)} records from AKShare for {symbol}")
            trace_logger.data("akshare_data_sample", df.head(2).to_dict() if not df.empty else "Empty DataFrame")
            trace_logger.step("AKShare data fetch completed")

            # If asset doesn't exist, create it
            if asset is None:
                trace_logger.transition("AKShare", "Database", "Creating new asset record")
                asset_create_start = time.time()

                try:
                    asset = Asset(
                        symbol=symbol,
                        name=f"Stock {symbol}",  # Default name, can be updated later
                        asset_type="stock",
                        exchange="CN",  # Default exchange for Chinese stocks
                        currency="CNY",  # Default currency for Chinese stocks
                        isin=symbol  # Using symbol as ISIN for simplicity
                    )
                    db.add(asset)
                    db.commit()
                    db.refresh(asset)

                    asset_create_time = time.time() - asset_create_start
                    trace_logger.data("asset_create_time", f"{asset_create_time:.4f}s")
                    trace_logger.info(f"Created new asset record for {symbol} with ID {asset.asset_id}")
                    trace_logger.step("Asset created in database")
                except SQLAlchemyError as e:
                    # If asset creation fails, log the error and create a temporary asset object
                    trace_logger.error(f"Database error when creating asset for {symbol}: {e}")
                    trace_logger.step("Database error - creating temporary asset object")

                    # Create a temporary asset object with a dummy ID
                    # This won't be saved to the database but allows the rest of the code to work
                    asset = Asset(
                        asset_id=999999,  # Temporary ID
                        symbol=symbol,
                        name=f"Stock {symbol}",
                        asset_type="stock",
                        exchange="CN",
                        currency="CNY",
                        isin=symbol
                    )

                    # Roll back the transaction
                    db.rollback()

            # Convert DataFrame to Price objects and store in database
            trace_logger.transition("AKShare", "Database", "Converting data and preparing for database storage")
            conversion_start = time.time()

            price_objects = []
            db_prices = []

            for _, row in df.iterrows():
                # Convert date to date object, handling both string and Timestamp
                if isinstance(row['date'], str):
                    date_obj = datetime.strptime(row['date'], '%Y-%m-%d').date()
                elif isinstance(row['date'], pd.Timestamp):
                    date_obj = row['date'].date()
                else:
                    # If it's already a date object or something else, try to convert it
                    date_obj = pd.to_datetime(row['date']).date()

                # Create Price object
                price = Price(
                    asset_id=asset.asset_id,
                    date=date_obj,
                    open=float(row['open']) if pd.notna(row['open']) else None,
                    high=float(row['high']) if pd.notna(row['high']) else None,
                    low=float(row['low']) if pd.notna(row['low']) else None,
                    close=float(row['close']) if pd.notna(row['close']) else None,
                    volume=int(row['volume']) if pd.notna(row['volume']) else None,
                    adjusted_close=None  # Match the model field name
                )

                # Add to list for bulk insert
                db_prices.append(price)

                # Also create a dict for the response
                price_dict = {
                    "price_id": None,  # Will be set after database insert
                    "asset_id": asset.asset_id,
                    "date": date_obj,
                    "open": float(row['open']) if pd.notna(row['open']) else None,
                    "high": float(row['high']) if pd.notna(row['high']) else None,
                    "low": float(row['low']) if pd.notna(row['low']) else None,
                    "close": float(row['close']) if pd.notna(row['close']) else None,
                    "volume": int(row['volume']) if pd.notna(row['volume']) else None,
                    "adjusted_close": None  # Match the model field name
                }
                price_objects.append(price_dict)

            conversion_time = time.time() - conversion_start
            trace_logger.data("data_conversion_time", f"{conversion_time:.4f}s")
            trace_logger.info(f"Converted {len(df)} records to database objects")
            trace_logger.step("Data conversion completed")

            # Bulk insert into database
            if db_prices:
                trace_logger.transition("AKShare", "Database", "Storing data in database")
                db_insert_start = time.time()

                try:
                    db.bulk_save_objects(db_prices)
                    db.commit()

                    db_insert_time = time.time() - db_insert_start
                    trace_logger.data("db_insert_time", f"{db_insert_time:.4f}s")
                    trace_logger.info(f"Saved {len(db_prices)} price records to database for {symbol}")
                    trace_logger.step("Database storage completed")

                    # Query the inserted prices to get their IDs
                    trace_logger.transition("Database", "Database", "Querying inserted prices")
                    db_query_start = time.time()

                    inserted_prices = db.query(Price).filter(
                        Price.asset_id == asset.asset_id,
                        Price.date >= start_date,
                        Price.date <= end_date
                    ).order_by(Price.date.desc()).limit(limit).all()

                    db_query_time = time.time() - db_query_start
                    trace_logger.data("db_query_time", f"{db_query_time:.4f}s")
                    trace_logger.info(f"Retrieved {len(inserted_prices)} inserted price records from database")
                    trace_logger.step("Database query completed")

                    # Cache the results
                    trace_logger.transition("Database", "Cache", "Storing results in cache")
                    cache_start = time.time()

                    cache_engine.set(cache_key, inserted_prices, ttl=86400)  # Cache for 24 hours
                    freshness_tracker.mark_updated(cache_key, ttl=86400)

                    cache_time = time.time() - cache_start
                    trace_logger.data("cache_store_time", f"{cache_time:.4f}s")
                    trace_logger.info(f"Stored {len(inserted_prices)} records in cache with TTL=86400s")
                    trace_logger.step("Data cached")

                    # Mark data source as akshare for performance tracking
                    data_source = "akshare_then_database"
                    trace_logger.data("data_source", data_source)

                    trace_logger.info(f"AKSHARE + DATABASE: Returning {len(inserted_prices)} price records from AKShare via database")
                    trace_logger.info(f"Total processing time: {time.time() - akshare_start:.4f}s")
                    trace_logger.end_trace()
                    return inserted_prices
                except SQLAlchemyError as e:
                    # If database operation fails, log the error but continue with returning the data from AKShare
                    trace_logger.error(f"Database error when saving prices for {symbol}: {e}")
                    trace_logger.step("Database error - falling back to AKShare data")

                    # Create price objects from the AKShare data for the response
                    response_prices = []
                    for price_dict in price_objects:
                        price = Price(
                            price_id=None,  # No ID since not saved to database
                            asset_id=asset.asset_id,
                            date=price_dict['date'],
                            open=price_dict['open'],
                            high=price_dict['high'],
                            low=price_dict['low'],
                            close=price_dict['close'],
                            volume=price_dict['volume'],
                            adjusted_close=None
                        )
                        response_prices.append(price)

                    # Cache the results even if database save failed
                    trace_logger.transition("AKShare", "Cache", "Storing AKShare results in cache")
                    cache_start = time.time()

                    cache_engine.set(cache_key, response_prices, ttl=86400)  # Cache for 24 hours
                    freshness_tracker.mark_updated(cache_key, ttl=86400)

                    cache_time = time.time() - cache_start
                    trace_logger.data("cache_store_time", f"{cache_time:.4f}s")
                    trace_logger.info(f"Stored {len(response_prices)} records in cache with TTL=86400s")
                    trace_logger.step("AKShare data cached")

                    # Mark data source as akshare_direct for performance tracking
                    data_source = "akshare_direct"
                    trace_logger.data("data_source", data_source)

                    trace_logger.info(f"AKSHARE DIRECT: Returning {len(response_prices)} price records directly from AKShare")
                    trace_logger.info(f"Total processing time: {time.time() - akshare_start:.4f}s")
                    trace_logger.end_trace()
                    return response_prices
            else:
                trace_logger.warning(f"No price data to save for {symbol}")
                trace_logger.step("No data to save")
                trace_logger.end_trace()
                return []

        except Exception as e:
            trace_logger.error(f"Error fetching data from AKShare for {symbol}: {e}")
            trace_logger.step("AKShare fetch error")

            # If we have an asset but no prices, return empty list
            if asset:
                trace_logger.info("Asset exists but no prices found, returning empty list")
                trace_logger.end_trace()
                return []

            # Otherwise, raise 404
            trace_logger.error("Asset not found and failed to fetch data, raising 404")
            trace_logger.end_trace()
            raise HTTPException(status_code=404, detail="Asset not found and failed to fetch data")

    except HTTPException:
        trace_logger.end_trace()
        raise
    except SQLAlchemyError as e:
        trace_logger.error(f"Database error when getting prices for symbol {symbol}: {e}")
        trace_logger.step("Database error")
        trace_logger.end_trace()
        raise HTTPException(status_code=500, detail="Database error")
    except Exception as e:
        trace_logger.error(f"Unexpected error when getting prices for symbol {symbol}: {e}")
        trace_logger.step("Unexpected error")
        trace_logger.end_trace()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
