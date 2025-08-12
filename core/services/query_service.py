"""
Data query service for QuantDB core
"""

from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

from sqlalchemy import and_, asc, desc, func, or_
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import BinaryExpression

from ..models.asset import Asset
from ..models.stock_data import DailyStockData
from ..utils.logger import logger


class QueryService:
    """
    Service for querying financial data
    """

    def __init__(self, db: Session):
        """
        Initialize the query service

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def query_assets(
        self,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: Optional[str] = None,
        sort_order: str = "asc",
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[Asset], int]:
        """
        Query assets with filtering, sorting, and pagination

        Args:
            filters: Dictionary of filter conditions
            sort_by: Field to sort by
            sort_order: Sort order ("asc" or "desc")
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            Tuple of (list of assets, total count)
        """
        try:
            # Start with base query
            query = self.db.query(Asset)

            # Apply filters
            if filters:
                query = self._apply_asset_filters(query, filters)

            # Get total count before pagination
            total_count = query.count()

            # Apply sorting
            if sort_by:
                if sort_by not in Asset.__table__.columns:
                    logger.warning(f"Invalid sort field: {sort_by}")
                else:
                    sort_column = getattr(Asset, sort_by)
                    if sort_order.lower() == "desc":
                        query = query.order_by(desc(sort_column))
                    else:
                        query = query.order_by(asc(sort_column))

            # Apply pagination
            query = query.offset(skip).limit(limit)

            # Execute query
            assets = query.all()

            return assets, total_count

        except Exception as e:
            logger.error(f"Error querying assets: {e}")
            raise

    def query_prices(
        self,
        asset_id: Optional[int] = None,
        symbol: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        period: str = "daily",
        sort_order: str = "desc",
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[DailyStockData], int]:
        """
        Query daily stock data with filtering, sorting, and pagination

        Args:
            asset_id: Asset ID to filter by
            symbol: Asset symbol to filter by
            start_date: Start date for price data
            end_date: End date for price data
            period: Time period ("daily", "weekly", "monthly")
            sort_order: Sort order ("asc" or "desc")
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            Tuple of (list of daily stock data, total count)
        """
        try:
            # Start with base query
            query = self.db.query(DailyStockData)

            # Apply asset filter
            if asset_id:
                query = query.filter(DailyStockData.asset_id == asset_id)
            elif symbol:
                # Join with Asset table to filter by symbol
                query = query.join(Asset).filter(Asset.symbol == symbol)

            # Apply date filters
            if start_date:
                query = query.filter(DailyStockData.trade_date >= start_date)

            if end_date:
                query = query.filter(DailyStockData.trade_date <= end_date)

            # Get total count before pagination
            total_count = query.count()

            # Apply sorting
            if sort_order.lower() == "desc":
                query = query.order_by(desc(DailyStockData.trade_date))
            else:
                query = query.order_by(asc(DailyStockData.trade_date))

            # Apply period aggregation (simplified version)
            if period == "weekly" or period == "monthly":
                logger.info(f"Period aggregation for {period} is not fully implemented")

            # Apply pagination
            query = query.offset(skip).limit(limit)

            # Execute query
            prices = query.all()

            return prices, total_count

        except Exception as e:
            logger.error(f"Error querying prices: {e}")
            raise

    def query_daily_stock_data(
        self,
        asset_id: Optional[int] = None,
        symbol: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        sort_order: str = "desc",
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[DailyStockData], int]:
        """
        Query daily stock data with filtering, sorting, and pagination

        Args:
            asset_id: Asset ID to filter by
            symbol: Asset symbol to filter by
            start_date: Start date for stock data
            end_date: End date for stock data
            sort_order: Sort order ("asc" or "desc")
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            Tuple of (list of daily stock data, total count)
        """
        try:
            # Start with base query
            query = self.db.query(DailyStockData)

            # Apply asset filter
            if asset_id:
                query = query.filter(DailyStockData.asset_id == asset_id)
            elif symbol:
                # Join with Asset table to filter by symbol
                query = query.join(Asset).filter(Asset.symbol == symbol)

            # Apply date filters
            if start_date:
                query = query.filter(DailyStockData.trade_date >= start_date)

            if end_date:
                query = query.filter(DailyStockData.trade_date <= end_date)

            # Get total count before pagination
            total_count = query.count()

            # Apply sorting
            if sort_order.lower() == "desc":
                query = query.order_by(desc(DailyStockData.trade_date))
            else:
                query = query.order_by(asc(DailyStockData.trade_date))

            # Apply pagination
            query = query.offset(skip).limit(limit)

            # Execute query
            daily_data = query.all()

            return daily_data, total_count

        except Exception as e:
            logger.error(f"Error querying daily stock data: {e}")
            raise

    def _apply_asset_filters(self, query, filters: Dict[str, Any]):
        """
        Apply filters to an asset query

        Args:
            query: SQLAlchemy query object
            filters: Dictionary of filter conditions

        Returns:
            Updated query with filters applied
        """
        for field, value in filters.items():
            if field not in Asset.__table__.columns:
                logger.warning(f"Ignoring invalid filter field: {field}")
                continue

            column = getattr(Asset, field)

            if isinstance(value, dict):
                # Handle complex filters (e.g., range, like, in)
                for op, op_value in value.items():
                    if op == "eq":
                        query = query.filter(column == op_value)
                    elif op == "ne":
                        query = query.filter(column != op_value)
                    elif op == "gt":
                        query = query.filter(column > op_value)
                    elif op == "lt":
                        query = query.filter(column < op_value)
                    elif op == "ge":
                        query = query.filter(column >= op_value)
                    elif op == "le":
                        query = query.filter(column <= op_value)
                    elif op == "like":
                        query = query.filter(column.ilike(f"%{op_value}%"))
                    elif op == "in":
                        query = query.filter(column.in_(op_value))
                    else:
                        logger.warning(f"Ignoring invalid filter operator: {op}")
            else:
                # Simple equality filter
                query = query.filter(column == value)

        return query

    def _apply_price_filters(self, query, asset_id=None, start_date=None, end_date=None):
        """
        Apply filters to a price query

        Args:
            query: SQLAlchemy query object
            asset_id: Asset ID to filter by
            start_date: Start date for price data
            end_date: End date for price data

        Returns:
            Updated query with filters applied
        """
        if asset_id:
            query = query.filter(DailyStockData.asset_id == asset_id)

        if start_date:
            query = query.filter(DailyStockData.trade_date >= start_date)

        if end_date:
            query = query.filter(DailyStockData.trade_date <= end_date)

        return query
