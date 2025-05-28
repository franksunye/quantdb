"""
Data import service for QuantDB

This service provides functionality for importing financial data from various sources
and integrates with the Reservoir Cache mechanism for efficient data management.
"""
import os
import time
import pandas as pd
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional, Union, Callable
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from src.api.models import Asset, DailyStockData, ImportTask
from src.api.schemas import ImportTaskStatusEnum
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
                akshare_adapter: Optional[AKShareAdapter] = None):
        """
        Initialize the data import service

        Args:
            db: SQLAlchemy database session
            akshare_adapter: AKShare adapter instance (optional)
        """
        self.db = db
        self.akshare_adapter = akshare_adapter or AKShareAdapter()
        logger.info("Data import service initialized with simplified architecture")

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
                         price_data: List[Dict[str, Any]]) -> List[DailyStockData]:
        """
        Import price data for an asset

        Args:
            asset_id: ID of the asset
            price_data: List of price data dictionaries with keys:
                        date, open, high, low, close, volume, adjusted_close

        Returns:
            List of created or updated DailyStockData objects
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
                daily_data = self.db.query(DailyStockData).filter(
                    DailyStockData.asset_id == asset_id,
                    DailyStockData.trade_date == price_date
                ).first()

                if daily_data:
                    # Update existing price data
                    daily_data.open = data.get('open')
                    daily_data.high = data.get('high')
                    daily_data.low = data.get('low')
                    daily_data.close = data.get('close')
                    daily_data.volume = data.get('volume')
                    daily_data.adjusted_close = data.get('adjusted_close')
                    # Update technical indicators if available
                    daily_data.turnover = data.get('turnover', 0)
                    daily_data.amplitude = data.get('amplitude', 0)
                    daily_data.pct_change = data.get('pct_change', 0)
                    daily_data.change = data.get('change', 0)
                    daily_data.turnover_rate = data.get('turnover_rate', 0)
                    logger.debug(f"Updated daily stock data for {asset.symbol} on {price_date}")
                else:
                    # Create new price data
                    daily_data = DailyStockData(
                        asset_id=asset_id,
                        trade_date=price_date,
                        open=data.get('open'),
                        high=data.get('high'),
                        low=data.get('low'),
                        close=data.get('close'),
                        volume=data.get('volume'),
                        adjusted_close=data.get('adjusted_close'),
                        turnover=data.get('turnover', 0),
                        amplitude=data.get('amplitude', 0),
                        pct_change=data.get('pct_change', 0),
                        change=data.get('change', 0),
                        turnover_rate=data.get('turnover_rate', 0)
                    )
                    self.db.add(daily_data)
                    logger.debug(f"Created new daily stock data for {asset.symbol} on {price_date}")

                imported_prices.append(daily_data)

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

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type((SQLAlchemyError, ConnectionError, TimeoutError)),
        reraise=True
    )
    def _fetch_stock_data(self, symbol: str, start_date: Optional[str] = None,
                         end_date: Optional[str] = None, use_mock_data: bool = False) -> pd.DataFrame:
        """
        Fetch stock data from AKShare with retry mechanism.

        Args:
            symbol: Stock symbol
            start_date: Start date in format YYYYMMDD (optional)
            end_date: End date in format YYYYMMDD (optional)
            use_mock_data: Whether to use mock data if real data is unavailable (optional)

        Returns:
            DataFrame with stock data

        Raises:
            Exception: If all retries fail
        """
        try:
            logger.info(f"Fetching stock data for {symbol} from {start_date} to {end_date}")
            stock_data = self.akshare_adapter.get_stock_data(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                use_mock_data=use_mock_data
            )

            if stock_data.empty:
                logger.warning(f"No data returned from AKShare for symbol {symbol}")
            else:
                logger.info(f"Successfully fetched {len(stock_data)} rows for {symbol}")

            return stock_data

        except Exception as e:
            logger.error(f"Error fetching stock data for {symbol}: {e}")
            # Re-raise to trigger retry
            raise

    def create_import_task(self, task_type: str, parameters: Dict[str, Any]) -> ImportTask:
        """
        Create a new import task in the database.

        Args:
            task_type: Type of import task (e.g., "stock", "index")
            parameters: Dictionary of task parameters

        Returns:
            Created ImportTask object
        """
        try:
            # Create new task
            task = ImportTask(
                task_type=task_type,
                parameters=parameters,
                status=ImportTaskStatusEnum.PENDING,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )

            self.db.add(task)
            self.db.commit()

            logger.info(f"Created new import task: {task.task_id} of type {task_type}")
            return task

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error creating import task: {e}")
            raise

    def update_task_status(self, task_id: int, status: ImportTaskStatusEnum,
                          result: Optional[Dict[str, Any]] = None) -> ImportTask:
        """
        Update the status of an import task.

        Args:
            task_id: ID of the task to update
            status: New status
            result: Optional result data

        Returns:
            Updated ImportTask object
        """
        try:
            task = self.db.query(ImportTask).filter(ImportTask.task_id == task_id).first()

            if not task:
                logger.error(f"Task with ID {task_id} not found")
                raise ValueError(f"Task with ID {task_id} not found")

            task.status = status
            task.updated_at = datetime.now()

            if result:
                task.result = result

            self.db.commit()

            logger.info(f"Updated task {task_id} status to {status}")
            return task

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error updating task status: {e}")
            raise

    def import_from_akshare(self,
                          symbol: str,
                          start_date: Optional[str] = None,
                          end_date: Optional[str] = None,
                          use_mock_data: bool = False,
                          create_task: bool = False) -> Dict[str, Any]:
        """
        Import stock data directly from AKShare using the Reservoir Cache mechanism

        Args:
            symbol: Stock symbol
            start_date: Start date in format YYYYMMDD (optional)
            end_date: End date in format YYYYMMDD (optional)
            use_mock_data: Whether to use mock data if real data is unavailable (optional)
            create_task: Whether to create a task record for this import (optional)

        Returns:
            Dictionary with import statistics
        """
        # Create task if requested
        task = None
        if create_task:
            task_params = {
                "symbol": symbol,
                "start_date": start_date,
                "end_date": end_date,
                "use_mock_data": use_mock_data
            }
            task = self.create_import_task("stock_import", task_params)

        try:
            # Validate inputs
            if not symbol:
                logger.error("Symbol cannot be empty")
                error_result = {
                    "symbol": symbol,
                    "records_imported": 0,
                    "message": "Symbol cannot be empty",
                    "success": False
                }

                if task:
                    self.update_task_status(task.task_id, ImportTaskStatusEnum.FAILED, error_result)

                return error_result

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

            # Update task status if exists
            if task:
                self.update_task_status(task.task_id, ImportTaskStatusEnum.PROCESSING)

            # Generate cache key for this request
            cache_key = self.cache_engine.generate_key(
                "import_stock_data", symbol, start_date, end_date
            )

            # Check if we have fresh data in cache
            if self.freshness_tracker.is_fresh(cache_key, "relaxed"):
                cached_result = self.cache_engine.get(cache_key)
                if cached_result:
                    logger.info(f"Using cached import result for {symbol}")

                    if task:
                        self.update_task_status(task.task_id,
                                              ImportTaskStatusEnum.COMPLETED if cached_result.get("success", False)
                                              else ImportTaskStatusEnum.FAILED,
                                              cached_result)

                    return cached_result

            # Get stock data from AKShare adapter with retry mechanism
            try:
                stock_data = self._fetch_stock_data(
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date,
                    use_mock_data=use_mock_data
                )
            except Exception as e:
                logger.error(f"All retries failed for fetching data for {symbol}: {e}")
                error_result = {
                    "asset_id": asset.asset_id if asset else None,
                    "symbol": symbol,
                    "records_imported": 0,
                    "message": f"Failed to fetch data after retries: {str(e)}",
                    "success": False
                }

                # Cache the negative result to avoid repeated failed requests
                self.cache_engine.set(cache_key, error_result, ttl=3600)  # Cache for 1 hour

                if task:
                    self.update_task_status(task.task_id, ImportTaskStatusEnum.FAILED, error_result)

                return error_result

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

                if task:
                    self.update_task_status(task.task_id, ImportTaskStatusEnum.FAILED, result)

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

                if task:
                    self.update_task_status(task.task_id, ImportTaskStatusEnum.FAILED, result)

                return result

            # Import price data to database with retry
            max_retries = 3
            retry_count = 0

            while retry_count < max_retries:
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

                    if task:
                        self.update_task_status(task.task_id, ImportTaskStatusEnum.COMPLETED, result)

                    return result

                except SQLAlchemyError as e:
                    self.db.rollback()
                    retry_count += 1
                    logger.warning(f"Database error when importing price data (attempt {retry_count}/{max_retries}): {e}")

                    if retry_count >= max_retries:
                        logger.error(f"All database retries failed for {symbol}")
                        error_result = {
                            "asset_id": asset.asset_id,
                            "symbol": symbol,
                            "records_imported": 0,
                            "message": f"Database error after {max_retries} retries: {str(e)}",
                            "success": False
                        }

                        if task:
                            self.update_task_status(task.task_id, ImportTaskStatusEnum.FAILED, error_result)

                        return error_result

                    # Wait before retrying
                    time.sleep(2 ** retry_count)  # Exponential backoff

        except Exception as e:
            logger.error(f"Error importing from AKShare for symbol {symbol}: {e}")
            # Return error information rather than raising exception
            error_result = {
                "symbol": symbol,
                "records_imported": 0,
                "message": f"Error: {str(e)}",
                "success": False
            }

            if task:
                self.update_task_status(task.task_id, ImportTaskStatusEnum.FAILED, error_result)

            return error_result

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
