"""
Data import service for QuantDB
"""
import os
import pandas as pd
from datetime import datetime, date
from typing import List, Dict, Any, Optional, Union
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from src.api.models import Asset, Price, DailyStockData
from src.logger import setup_logger

# Setup logger
logger = setup_logger(__name__)

class DataImportService:
    """
    Service for importing financial data from various sources
    """
    
    def __init__(self, db: Session):
        """
        Initialize the data import service
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
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
            
            return {
                "asset_id": asset_id,
                "file_path": file_path,
                "records_imported": len(imported_prices)
            }
        
        except Exception as e:
            logger.error(f"Error importing from CSV {file_path}: {e}")
            raise
