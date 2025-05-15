"""
Data import service for QuantDB

This service provides functionality for importing financial data from various sources
and integrates with the Reservoir Cache mechanism for efficient data management.
"""
import os
import pandas as pd
from datetime import datetime, date
from typing import List, Dict, Any, Optional, Union
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from src.api.models import Asset, Price, DailyStockData
from src.cache.cache_engine import CacheEngine
from src.cache.freshness_tracker import FreshnessTracker
from src.cache.akshare_adapter import AKShareAdapter
from src.logger import setup_logger

# Setup logger
logger = setup_logger(__name__)

class DataImportService:
    """
    Service for importing financial data from various sources

    This service integrates with the Reservoir Cache mechanism to efficiently
    manage data imports and ensure data freshness.
    """

    def __init__(self, db: Session,
                cache_engine: Optional[CacheEngine] = None,
                freshness_tracker: Optional[FreshnessTracker] = None,
                akshare_adapter: Optional[AKShareAdapter] = None):
        """
        Initialize the data import service

        Args:
            db: SQLAlchemy database session
            cache_engine: Cache engine instance (optional)
            freshness_tracker: Freshness tracker instance (optional)
            akshare_adapter: AKShare adapter instance (optional)
        """
        self.db = db
        self.cache_engine = cache_engine or CacheEngine()
        self.freshness_tracker = freshness_tracker or FreshnessTracker()
        self.akshare_adapter = akshare_adapter or AKShareAdapter(
            cache_engine=self.cache_engine,
            freshness_tracker=self.freshness_tracker
        )
        logger.info("Data import service initialized with Reservoir Cache integration")

    def import_asset(self,
                    symbol: str,
                    name: str,
                    isin: str,
                    asset_type: str,
                    exchange: str,
                    currency: str) -> Asset:
        """
        Import an asset into the database

        Args:
            symbol: Asset symbol
            name: Asset name
            isin: International Securities Identification Number
            asset_type: Type of asset (e.g., "stock", "index")
            exchange: Exchange where the asset is traded
            currency: Currency of the asset

        Returns:
            The created or updated Asset object
        """
        try:
            # Check if asset already exists
            asset = self.db.query(Asset).filter(Asset.symbol == symbol).first()

            if asset:
                # Update existing asset
                asset.name = name
                asset.isin = isin
                asset.asset_type = asset_type
                asset.exchange = exchange
                asset.currency = currency
                logger.info(f"Updated asset: {symbol}")
            else:
                # Create new asset
                asset = Asset(
                    symbol=symbol,
                    name=name,
                    isin=isin,
                    asset_type=asset_type,
                    exchange=exchange,
                    currency=currency
                )
                self.db.add(asset)
                logger.info(f"Created new asset: {symbol}")

            self.db.commit()
            return asset

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error when importing asset {symbol}: {e}")
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Unexpected error when importing asset {symbol}: {e}")
            raise

    def import_price_data(self,
                         asset_id: int,
                         price_data: List[Dict[str, Any]]) -> List[Price]:
        """
        Import price data for an asset

        Args:
            asset_id: ID of the asset
            price_data: List of price data dictionaries with keys:
                        date, open, high, low, close, volume, adjusted_close

        Returns:
            List of created or updated Price objects
        """
        try:
            # Check if asset exists
            asset = self.db.query(Asset).filter(Asset.asset_id == asset_id).first()
            if not asset:
                logger.error(f"Asset with ID {asset_id} not found")
                raise ValueError(f"Asset with ID {asset_id} not found")

            imported_prices = []

            for data in price_data:
                # Convert date string to date object if needed
                price_date = data['date']
                if isinstance(price_date, str):
                    price_date = datetime.strptime(price_date, "%Y-%m-%d").date()

                # Check if price data already exists for this date
                price = self.db.query(Price).filter(
                    Price.asset_id == asset_id,
                    Price.date == price_date
                ).first()

                if price:
                    # Update existing price data
                    price.open = data.get('open')
                    price.high = data.get('high')
                    price.low = data.get('low')
                    price.close = data.get('close')
                    price.volume = data.get('volume')
                    price.adjusted_close = data.get('adjusted_close')
                    logger.debug(f"Updated price data for {asset.symbol} on {price_date}")
                else:
                    # Create new price data
                    price = Price(
                        asset_id=asset_id,
                        date=price_date,
                        open=data.get('open'),
                        high=data.get('high'),
                        low=data.get('low'),
                        close=data.get('close'),
                        volume=data.get('volume'),
                        adjusted_close=data.get('adjusted_close')
                    )
                    self.db.add(price)
                    logger.debug(f"Created new price data for {asset.symbol} on {price_date}")

                imported_prices.append(price)

            self.db.commit()
            logger.info(f"Imported {len(imported_prices)} price records for asset {asset.symbol}")
            return imported_prices

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error when importing price data for asset {asset_id}: {e}")
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Unexpected error when importing price data for asset {asset_id}: {e}")
            raise

    def import_from_csv(self,
                       file_path: str,
                       asset_id: Optional[int] = None,
                       symbol: Optional[str] = None) -> Dict[str, Any]:
        """
        Import price data from a CSV file

        Args:
            file_path: Path to the CSV file
            asset_id: ID of the asset (optional if symbol is provided)
            symbol: Symbol of the asset (optional if asset_id is provided)

        Returns:
            Dictionary with import statistics
        """
        try:
            if not os.path.exists(file_path):
                logger.error(f"File not found: {file_path}")
                raise FileNotFoundError(f"File not found: {file_path}")

            # Get asset ID if symbol is provided
            if asset_id is None and symbol is not None:
                asset = self.db.query(Asset).filter(Asset.symbol == symbol).first()
                if not asset:
                    logger.error(f"Asset with symbol {symbol} not found")
                    raise ValueError(f"Asset with symbol {symbol} not found")
                asset_id = asset.asset_id

            if asset_id is None:
                logger.error("Either asset_id or symbol must be provided")
                raise ValueError("Either asset_id or symbol must be provided")

            # Read CSV file
            df = pd.read_csv(file_path)

            # Convert DataFrame to list of dictionaries
            price_data = df.to_dict('records')

            # Import price data
            imported_prices = self.import_price_data(asset_id, price_data)

            # Generate cache key for this data
            cache_key = self.cache_engine.generate_key("price_data", asset_id, len(imported_prices))

            # Store in cache
            self.cache_engine.set(cache_key, imported_prices, ttl=86400)  # Cache for 24 hours

            # Mark as fresh
            self.freshness_tracker.mark_updated(cache_key, ttl=86400)

            logger.info(f"Imported price data cached with key: {cache_key}")

            return {
                "asset_id": asset_id,
                "file_path": file_path,
                "records_imported": len(imported_prices),
                "cache_key": cache_key
            }

        except Exception as e:
            logger.error(f"Error importing from CSV {file_path}: {e}")
            raise

    def import_from_akshare(self,
                          symbol: str,
                          start_date: Optional[str] = None,
                          end_date: Optional[str] = None,
                          use_mock_data: bool = False) -> Dict[str, Any]:
        """
        Import stock data directly from AKShare using the Reservoir Cache mechanism

        Args:
            symbol: Stock symbol
            start_date: Start date in format YYYYMMDD (optional)
            end_date: End date in format YYYYMMDD (optional)
            use_mock_data: Whether to use mock data if real data is unavailable (optional)

        Returns:
            Dictionary with import statistics
        """
        try:
            # Validate inputs
            if not symbol:
                logger.error("Symbol cannot be empty")
                raise ValueError("Symbol cannot be empty")

            # Check if asset exists
            asset = self.db.query(Asset).filter(Asset.symbol == symbol).first()
            if not asset:
                logger.warning(f"Asset with symbol {symbol} not found. Creating new asset.")
                # Create a new asset
                asset = Asset(
                    symbol=symbol,
                    name=f"Stock {symbol}",  # Placeholder name
                    isin=f"STK{symbol}",     # Placeholder ISIN
                    asset_type="stock",
                    exchange="CN",           # Placeholder exchange
                    currency="CNY"           # Placeholder currency
                )
                self.db.add(asset)
                self.db.commit()
                logger.info(f"Created new asset for symbol {symbol} with ID {asset.asset_id}")

            # Generate cache key for this request
            cache_key = self.cache_engine.generate_key(
                "import_stock_data", symbol, start_date, end_date
            )

            # Check if we have fresh data in cache
            if self.freshness_tracker.is_fresh(cache_key, "relaxed"):
                cached_result = self.cache_engine.get(cache_key)
                if cached_result:
                    logger.info(f"Using cached import result for {symbol}")
                    return cached_result

            # Get stock data from AKShare adapter (will use cache if available)
            logger.info(f"Fetching stock data for {symbol} from {start_date} to {end_date}")
            stock_data = self.akshare_adapter.get_stock_data(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                use_mock_data=use_mock_data
            )

            if stock_data.empty:
                logger.warning(f"No data returned from AKShare for symbol {symbol}")
                result = {
                    "asset_id": asset.asset_id,
                    "symbol": symbol,
                    "records_imported": 0,
                    "message": "No data returned from AKShare",
                    "success": False
                }
                # Cache the negative result to avoid repeated failed requests
                self.cache_engine.set(cache_key, result, ttl=3600)  # Cache for 1 hour
                return result

            # Convert DataFrame to list of dictionaries for database import
            price_data = []
            for _, row in stock_data.iterrows():
                try:
                    price_data.append({
                        'date': row['date'],
                        'open': row['open'],
                        'high': row['high'],
                        'low': row['low'],
                        'close': row['close'],
                        'volume': row['volume'],
                        'adjusted_close': row.get('adjusted_close', row['close'])
                    })
                except KeyError as e:
                    logger.warning(f"Missing key in row data: {e}. Skipping row.")
                    continue

            if not price_data:
                logger.warning(f"No valid price data found for {symbol}")
                result = {
                    "asset_id": asset.asset_id,
                    "symbol": symbol,
                    "records_imported": 0,
                    "message": "No valid price data found",
                    "success": False
                }
                self.cache_engine.set(cache_key, result, ttl=3600)
                return result

            # Import price data to database
            try:
                imported_prices = self.import_price_data(asset.asset_id, price_data)
                logger.info(f"Imported {len(imported_prices)} records for {symbol} from AKShare")

                # Store the result in cache
                result = {
                    "asset_id": asset.asset_id,
                    "symbol": symbol,
                    "records_imported": len(imported_prices),
                    "start_date": start_date,
                    "end_date": end_date,
                    "success": True
                }
                self.cache_engine.set(cache_key, result, ttl=86400)  # Cache for 24 hours
                self.freshness_tracker.mark_updated(cache_key, ttl=86400)

                return result

            except SQLAlchemyError as e:
                self.db.rollback()
                logger.error(f"Database error when importing price data: {e}")
                raise ValueError(f"Database error: {e}")

        except Exception as e:
            logger.error(f"Error importing from AKShare for symbol {symbol}: {e}")
            # Return error information rather than raising exception
            return {
                "symbol": symbol,
                "records_imported": 0,
                "message": f"Error: {str(e)}",
                "success": False
            }

    def import_index_data(self,
                        index_symbol: str,
                        start_date: Optional[str] = None,
                        end_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Import index data directly from AKShare using the Reservoir Cache mechanism

        Args:
            index_symbol: Index symbol
            start_date: Start date in format YYYYMMDD (optional)
            end_date: End date in format YYYYMMDD (optional)

        Returns:
            Dictionary with import statistics
        """
        try:
            # Check if asset exists
            asset = self.db.query(Asset).filter(Asset.symbol == index_symbol).first()
            if not asset:
                # Create a new asset for this index
                asset = self.import_asset(
                    symbol=index_symbol,
                    name=f"Index {index_symbol}",  # Placeholder name
                    isin=f"IDX{index_symbol}",     # Placeholder ISIN
                    asset_type="index",
                    exchange="CN",                 # Placeholder exchange
                    currency="CNY"                 # Placeholder currency
                )
                logger.info(f"Created new asset for index {index_symbol}")

            # Get index data from AKShare adapter (will use cache if available)
            index_data = self.akshare_adapter.get_index_data(
                symbol=index_symbol,
                start_date=start_date,
                end_date=end_date
            )

            if index_data.empty:
                logger.warning(f"No data returned from AKShare for index {index_symbol}")
                return {
                    "asset_id": asset.asset_id,
                    "symbol": index_symbol,
                    "records_imported": 0,
                    "message": "No data returned from AKShare"
                }

            # Convert DataFrame to list of dictionaries for database import
            price_data = []
            for _, row in index_data.iterrows():
                price_data.append({
                    'date': row['date'],
                    'open': row['open'],
                    'high': row['high'],
                    'low': row['low'],
                    'close': row['close'],
                    'volume': row['volume'],
                    'adjusted_close': row.get('adjusted_close', row['close'])
                })

            # Import price data to database
            imported_prices = self.import_price_data(asset.asset_id, price_data)

            logger.info(f"Imported {len(imported_prices)} records for index {index_symbol} from AKShare")

            return {
                "asset_id": asset.asset_id,
                "symbol": index_symbol,
                "records_imported": len(imported_prices),
                "start_date": start_date,
                "end_date": end_date
            }

        except Exception as e:
            logger.error(f"Error importing from AKShare for index {index_symbol}: {e}")
            raise

    def import_index_constituents(self, index_symbol: str) -> Dict[str, Any]:
        """
        Import index constituents from AKShare using the Reservoir Cache mechanism

        Args:
            index_symbol: Index symbol

        Returns:
            Dictionary with import statistics
        """
        try:
            # Get index constituents from AKShare adapter (will use cache if available)
            constituents = self.akshare_adapter.get_index_constituents(index_symbol)

            if constituents.empty:
                logger.warning(f"No constituents returned from AKShare for index {index_symbol}")
                return {
                    "index_symbol": index_symbol,
                    "constituents_imported": 0,
                    "message": "No constituents returned from AKShare"
                }

            # Import each constituent as an asset if it doesn't exist
            imported_count = 0
            for _, row in constituents.iterrows():
                symbol = row.get('symbol')
                name = row.get('name')

                if not symbol or not name:
                    continue

                # Check if asset already exists
                asset = self.db.query(Asset).filter(Asset.symbol == symbol).first()

                if not asset:
                    # Create a new asset for this constituent
                    asset = self.import_asset(
                        symbol=symbol,
                        name=name,
                        isin=f"STK{symbol}",  # Placeholder ISIN
                        asset_type="stock",
                        exchange="CN",         # Placeholder exchange
                        currency="CNY"         # Placeholder currency
                    )
                    imported_count += 1

            logger.info(f"Imported {imported_count} new constituents for index {index_symbol}")

            return {
                "index_symbol": index_symbol,
                "constituents_imported": imported_count,
                "total_constituents": len(constituents)
            }

        except Exception as e:
            logger.error(f"Error importing constituents for index {index_symbol}: {e}")
            raise
