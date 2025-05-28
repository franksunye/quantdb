# src/services/database_cache.py
"""
Database cache interface for the QuantDB system.

This module provides a unified interface for using the database as a persistent cache,
optimized for stock historical data.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union

import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from src.api.models import Asset, DailyStockData
from src.logger import logger

class DatabaseCache:
    """
    Database cache interface that uses the main database as a persistent cache.

    This class provides methods for:
    1. Retrieving data from the database
    2. Saving data to the database
    3. Checking data existence
    4. Getting cache statistics
    """

    def __init__(self, db: Session):
        """
        Initialize the database cache.

        Args:
            db: Database session
        """
        self.db = db
        logger.info("Database cache initialized")

    def get(self, symbol: str, dates: List[str]) -> Dict[str, Dict]:
        """
        Get data from the database for specific dates.

        Args:
            symbol: Stock symbol
            dates: List of dates in format YYYYMMDD

        Returns:
            Dictionary with date as key and data as value
        """
        logger.info(f"Getting data from database for {symbol} with {len(dates)} dates")

        results = {}

        try:
            # Get asset ID
            asset = self._get_or_create_asset(symbol)
            if not asset:
                logger.warning(f"Asset not found for symbol {symbol}")
                return results

            # Convert dates to datetime objects
            date_objects = [datetime.strptime(date, "%Y%m%d").date() for date in dates]

            # Query database for all dates at once using IN clause
            query_results = self.db.query(DailyStockData).filter(
                DailyStockData.asset_id == asset.asset_id,
                DailyStockData.trade_date.in_(date_objects)
            ).all()

            logger.info(f"Found {len(query_results)} records in database for {symbol}")

            # Convert query results to dictionary
            for result in query_results:
                date_str = result.trade_date.strftime("%Y%m%d")
                results[date_str] = {
                    "date": result.trade_date,
                    "open": result.open,
                    "high": result.high,
                    "low": result.low,
                    "close": result.close,
                    "volume": result.volume,
                    "turnover": result.turnover,
                    "amplitude": result.amplitude,
                    "pct_change": result.pct_change,
                    "change": result.change,
                    "turnover_rate": result.turnover_rate
                }

            return results

        except Exception as e:
            logger.error(f"Error getting data from database: {e}")
            return results

    def save(self, symbol: str, data: Dict[str, Dict]) -> bool:
        """
        Save data to the database.

        Args:
            symbol: Stock symbol
            data: Dictionary with date as key and data as value

        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Saving {len(data)} records to database for {symbol}")

        try:
            # Get or create asset
            asset = self._get_or_create_asset(symbol)
            if not asset:
                logger.error(f"Failed to get or create asset for {symbol}")
                return False

            # Process each data point
            for date_str, item in data.items():
                # Convert date string to date object if it's not already
                if isinstance(item['date'], str):
                    date_obj = datetime.strptime(item['date'], "%Y%m%d").date()
                elif isinstance(item['date'], pd.Timestamp):
                    date_obj = item['date'].date()
                else:
                    date_obj = item['date']

                # Check if data already exists
                existing_data = self.db.query(DailyStockData).filter(
                    DailyStockData.asset_id == asset.asset_id,
                    DailyStockData.trade_date == date_obj
                ).first()

                if existing_data:
                    # Skip if data already exists
                    logger.debug(f"Data already exists for {symbol} on {date_str}, skipping")
                    continue

                # Create new data record
                stock_data = DailyStockData(
                    asset_id=asset.asset_id,
                    trade_date=date_obj,
                    open=item.get('open'),
                    high=item.get('high'),
                    low=item.get('low'),
                    close=item.get('close'),
                    volume=item.get('volume'),
                    turnover=item.get('turnover'),
                    amplitude=item.get('amplitude'),
                    pct_change=item.get('pct_change'),
                    change=item.get('change'),
                    turnover_rate=item.get('turnover_rate')
                )

                self.db.add(stock_data)

            # Commit changes
            self.db.commit()
            logger.info(f"Successfully saved data to database for {symbol}")
            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error saving data to database: {e}")
            return False

    def get_date_range_coverage(self, symbol: str, start_date: str, end_date: str) -> Dict[str, Any]:
        """
        Get coverage information for a date range.

        Args:
            symbol: Stock symbol
            start_date: Start date in format YYYYMMDD
            end_date: End date in format YYYYMMDD

        Returns:
            Dictionary with coverage information
        """
        logger.info(f"Getting date range coverage for {symbol} from {start_date} to {end_date}")

        try:
            # Get asset ID
            asset = self._get_or_create_asset(symbol)
            if not asset:
                # Convert dates to datetime objects to calculate total_dates
                start_date_obj = datetime.strptime(start_date, "%Y%m%d").date()
                end_date_obj = datetime.strptime(end_date, "%Y%m%d").date()
                delta = end_date_obj - start_date_obj
                total_dates = delta.days + 1

                return {"coverage": 0, "total_dates": total_dates, "covered_dates": 0}

            # Convert dates to datetime objects
            start_date_obj = datetime.strptime(start_date, "%Y%m%d").date()
            end_date_obj = datetime.strptime(end_date, "%Y%m%d").date()

            # Count total days in range
            delta = end_date_obj - start_date_obj
            total_dates = delta.days + 1

            # Count covered days
            covered_dates = self.db.query(DailyStockData).filter(
                DailyStockData.asset_id == asset.asset_id,
                DailyStockData.trade_date >= start_date_obj,
                DailyStockData.trade_date <= end_date_obj
            ).count()

            # Calculate coverage
            coverage = covered_dates / total_dates if total_dates > 0 else 0

            return {
                "coverage": coverage,
                "total_dates": total_dates,
                "covered_dates": covered_dates
            }

        except Exception as e:
            logger.error(f"Error getting date range coverage: {e}")
            return {"coverage": 0, "total_dates": 0, "covered_dates": 0}

    def get_stats(self) -> Dict[str, Any]:
        """
        Get database cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        try:
            # Count total assets
            total_assets = self.db.query(Asset).count()

            # Count total data points
            total_data_points = self.db.query(DailyStockData).count()

            # Get date range
            min_date = self.db.query(DailyStockData.trade_date).order_by(DailyStockData.trade_date.asc()).first()
            max_date = self.db.query(DailyStockData.trade_date).order_by(DailyStockData.trade_date.desc()).first()

            min_date_str = min_date[0].strftime("%Y-%m-%d") if min_date else None
            max_date_str = max_date[0].strftime("%Y-%m-%d") if max_date else None

            # Get top assets by data points
            # First, get count of data points for each asset
            asset_counts = self.db.query(
                DailyStockData.asset_id,
                func.count(DailyStockData.id).label('count')
            ).group_by(
                DailyStockData.asset_id
            ).subquery()

            # Then join with assets and order by count
            top_assets_query = self.db.query(
                Asset.symbol,
                Asset.name,
                Asset.asset_id,
                asset_counts.c.count
            ).join(
                asset_counts,
                Asset.asset_id == asset_counts.c.asset_id
            ).order_by(
                asset_counts.c.count.desc()
            ).limit(5)

            top_assets = []
            for symbol, name, asset_id, count in top_assets_query:
                top_assets.append({
                    "symbol": symbol,
                    "name": name,
                    "data_points": count
                })

            return {
                "total_assets": total_assets,
                "total_data_points": total_data_points,
                "date_range": {
                    "min_date": min_date_str,
                    "max_date": max_date_str
                },
                "top_assets": top_assets
            }

        except Exception as e:
            logger.error(f"Error getting database cache statistics: {e}")
            return {
                "error": str(e)
            }

    def _get_or_create_asset(self, symbol: str) -> Optional[Asset]:
        """
        Get or create an asset.

        Args:
            symbol: Stock symbol

        Returns:
            Asset object or None if failed
        """
        try:
            # Try to get existing asset
            asset = self.db.query(Asset).filter(Asset.symbol == symbol).first()

            if asset:
                return asset

            # Create new asset
            asset = Asset(
                symbol=symbol,
                name=f"Stock {symbol}",
                isin=f"CN{symbol}",
                asset_type="stock",
                exchange="CN",
                currency="CNY"
            )

            self.db.add(asset)
            self.db.commit()

            return asset

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error getting or creating asset: {e}")
            return None
