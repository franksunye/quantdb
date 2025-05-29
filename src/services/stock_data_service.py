# src/services/stock_data_service.py
"""
Stock data service for the QuantDB system.

This module provides a unified interface for retrieving stock data,
with intelligent data fetching strategy and database caching.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union, Any

import pandas as pd
from sqlalchemy.orm import Session

from src.api.models import Asset, DailyStockData
from src.logger import logger
from src.services.database_cache import DatabaseCache
from src.services.trading_calendar import get_trading_calendar

class StockDataService:
    """
    Stock data service that provides stock historical data with intelligent data fetching.

    This service implements a smart data retrieval strategy that:
    1. Checks the database for existing data
    2. Only fetches missing data from external sources
    3. Efficiently handles date ranges
    """

    def __init__(self, db: Session, akshare_adapter: Any):
        """
        Initialize the stock data service.

        Args:
            db: Database session
            akshare_adapter: AKShare adapter for fetching data from external sources
        """
        self.db = db
        self.akshare_adapter = akshare_adapter
        self.db_cache = DatabaseCache(db)
        logger.info("Stock data service initialized")

    def get_stock_data(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        adjust: str = "",
    ) -> pd.DataFrame:
        """
        Get stock historical data for a specific symbol and date range.

        This method implements an intelligent data fetching strategy:
        1. Checks the database for existing data in the requested date range
        2. Identifies missing date ranges
        3. Fetches only the missing data from external sources
        4. Combines existing and new data

        Args:
            symbol: Stock symbol
            start_date: Start date in format YYYYMMDD
            end_date: End date in format YYYYMMDD
            adjust: Price adjustment method

        Returns:
            DataFrame with stock data
        """
        logger.info(f"Getting stock data for {symbol} from {start_date} to {end_date} with adjust={adjust}")

        # Validate and standardize parameters
        symbol = self._standardize_stock_symbol(symbol)
        start_date = self._validate_and_format_date(start_date)
        end_date = self._validate_and_format_date(end_date)

        # Get trading days in the requested date range (now excludes weekends and holidays)
        trading_days = self._get_trading_days(start_date, end_date)
        logger.info(f"Identified {len(trading_days)} trading days for {symbol} from {start_date} to {end_date}")

        # Check database for existing data
        existing_data = self.db_cache.get(symbol, trading_days)
        existing_dates = set(existing_data.keys())
        logger.info(f"Found {len(existing_dates)} existing records in database for {symbol}")

        # Find missing dates (only among actual trading days)
        missing_dates = [day for day in trading_days if day not in existing_dates]

        # If there are missing dates, fetch them from external sources
        if missing_dates:
            logger.info(f"Found {len(missing_dates)} missing trading days for {symbol}")

            # Group consecutive dates to minimize API calls
            date_groups = self._group_consecutive_dates(missing_dates)
            logger.info(f"Grouped into {len(date_groups)} date ranges for {symbol}")

            for group_start, group_end in date_groups:
                logger.info(f"Fetching data for {symbol} from {group_start} to {group_end}")

                # Fetch data from AKShare
                akshare_data = self.akshare_adapter.get_stock_data(
                    symbol=symbol,
                    start_date=group_start,
                    end_date=group_end,
                    adjust=adjust
                )

                if not akshare_data.empty:
                    logger.info(f"Successfully fetched {len(akshare_data)} rows for {symbol}")

                    # Convert DataFrame to dictionary format for database storage
                    data_dict = self._dataframe_to_dict(akshare_data)

                    # Save to database
                    self.db_cache.save(symbol, data_dict)

                    # Update existing data
                    existing_data.update(data_dict)
                else:
                    logger.warning(f"No data returned from AKShare for {symbol} from {group_start} to {group_end}")

                    # Check if this is a future date range
                    today = datetime.now().strftime('%Y%m%d')
                    if group_start > today and group_end > today:
                        logger.info(f"Date range {group_start} to {group_end} is in the future. No data expected.")
                    else:
                        logger.info(f"Date range {group_start} to {group_end} may be a holiday or have no trading data.")
        else:
            logger.info(f"✅ All requested trading day data for {symbol} already exists in database - CACHE HIT!")

        # Convert dictionary to DataFrame
        if existing_data:
            result_df = self._dict_to_dataframe(existing_data)

            # Filter to requested date range
            result_df = self._filter_dataframe_by_date_range(result_df, start_date, end_date)

            # Sort by date
            result_df = result_df.sort_values('date')

            logger.info(f"Returning {len(result_df)} rows for {symbol}")
            return result_df
        else:
            logger.warning(f"No data found for {symbol} in requested date range")
            return pd.DataFrame()

    def _standardize_stock_symbol(self, symbol: str) -> str:
        """
        Standardize stock symbol format.

        Args:
            symbol: Stock symbol

        Returns:
            Standardized symbol
        """
        # Remove market prefix if present
        if symbol.lower().startswith("sh") or symbol.lower().startswith("sz"):
            symbol = symbol[2:]

        # Remove suffix if present
        if "." in symbol:
            symbol = symbol.split(".")[0]

        return symbol

    def _validate_and_format_date(self, date_str: Optional[str]) -> str:
        """
        Validate and format date string.

        Args:
            date_str: Date string in format YYYYMMDD

        Returns:
            Formatted date string
        """
        if date_str is None:
            # Default to current date if end_date, or 1 year ago if start_date
            if not hasattr(self, '_last_date_was_start'):
                self._last_date_was_start = True
                return (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
            else:
                self._last_date_was_start = not self._last_date_was_start
                return datetime.now().strftime('%Y%m%d')

        # Ensure date is in YYYYMMDD format
        if len(date_str) != 8 or not date_str.isdigit():
            raise ValueError(f"Invalid date format: {date_str}. Expected YYYYMMDD.")

        return date_str

    def _get_trading_days(self, start_date: str, end_date: str) -> List[str]:
        """
        Get list of trading days in the given date range.

        This method uses AKShare's official trading calendar to accurately
        identify trading days, avoiding unnecessary API calls for non-trading days.

        Args:
            start_date: Start date in format YYYYMMDD
            end_date: End date in format YYYYMMDD

        Returns:
            List of actual trading days based on official calendar
        """
        try:
            # Use the official trading calendar service
            trading_calendar = get_trading_calendar()
            trading_days = trading_calendar.get_trading_days(start_date, end_date)

            logger.info(f"Using official trading calendar: found {len(trading_days)} trading days")
            return trading_days

        except Exception as e:
            logger.warning(f"Failed to get trading calendar, using fallback: {e}")

            # Fallback to simple weekend filtering
            start_dt = datetime.strptime(start_date, '%Y%m%d')
            end_dt = datetime.strptime(end_date, '%Y%m%d')

            trading_days = []
            current_dt = start_dt

            while current_dt <= end_dt:
                # Simple fallback: only skip weekends
                if current_dt.weekday() < 5:  # Monday = 0, Friday = 4
                    trading_days.append(current_dt.strftime('%Y%m%d'))
                current_dt += timedelta(days=1)

            logger.warning(f"Using fallback calendar: found {len(trading_days)} potential trading days")
            return trading_days



    def _group_consecutive_dates(self, dates: List[str]) -> List[Tuple[str, str]]:
        """
        Group consecutive dates into ranges to minimize API calls.

        Args:
            dates: List of dates in format YYYYMMDD

        Returns:
            List of (start_date, end_date) tuples
        """
        if not dates:
            return []

        # Sort dates
        sorted_dates = sorted(dates)

        # Initialize result and current group
        result = []
        current_group = [sorted_dates[0]]

        # Iterate through sorted dates
        for i in range(1, len(sorted_dates)):
            current_date = datetime.strptime(sorted_dates[i], "%Y%m%d")
            prev_date = datetime.strptime(sorted_dates[i-1], "%Y%m%d")

            # If dates are consecutive (allowing for weekends), add to current group
            if (current_date - prev_date).days <= 3:
                current_group.append(sorted_dates[i])
            else:
                # Otherwise, end current group and start a new one
                result.append((current_group[0], current_group[-1]))
                current_group = [sorted_dates[i]]

        # Add the last group
        result.append((current_group[0], current_group[-1]))

        return result

    def _dataframe_to_dict(self, df: pd.DataFrame) -> Dict[str, Dict]:
        """
        Convert DataFrame to dictionary format for database storage.

        Args:
            df: DataFrame with stock data

        Returns:
            Dictionary with date as key and row data as value
        """
        result = {}

        for _, row in df.iterrows():
            date_str = row['date'].strftime('%Y%m%d') if isinstance(row['date'], datetime) else row['date']
            result[date_str] = row.to_dict()

        return result

    def _dict_to_dataframe(self, data_dict: Dict[str, Dict]) -> pd.DataFrame:
        """
        Convert dictionary to DataFrame.

        Args:
            data_dict: Dictionary with date as key and row data as value

        Returns:
            DataFrame with stock data
        """
        return pd.DataFrame(list(data_dict.values()))

    def _filter_dataframe_by_date_range(self, df: pd.DataFrame, start_date: str, end_date: str) -> pd.DataFrame:
        """
        Filter DataFrame by date range.

        Args:
            df: DataFrame with stock data
            start_date: Start date in format YYYYMMDD
            end_date: End date in format YYYYMMDD

        Returns:
            Filtered DataFrame
        """
        if df.empty:
            return df

        # Convert date column to datetime if it's not already
        if not pd.api.types.is_datetime64_dtype(df['date']):
            df['date'] = pd.to_datetime(df['date'])

        # Convert start_date and end_date to datetime
        start_dt = datetime.strptime(start_date, '%Y%m%d')
        end_dt = datetime.strptime(end_date, '%Y%m%d')

        # Filter DataFrame
        return df[(df['date'] >= start_dt) & (df['date'] <= end_dt)]

    def _is_weekend_or_holiday(self, start_date: str, end_date: str) -> bool:
        """
        Check if date range contains weekends or holidays.

        Args:
            start_date: Start date in format YYYYMMDD
            end_date: End date in format YYYYMMDD

        Returns:
            True if date range contains weekends or holidays, False otherwise
        """
        start_dt = datetime.strptime(start_date, '%Y%m%d')
        end_dt = datetime.strptime(end_date, '%Y%m%d')

        # Check if start or end date is a weekend
        if start_dt.weekday() >= 5 or end_dt.weekday() >= 5:
            return True

        # Check if date range spans a weekend
        current_dt = start_dt
        while current_dt <= end_dt:
            if current_dt.weekday() >= 5:  # 5 = Saturday, 6 = Sunday
                return True
            current_dt += timedelta(days=1)

        # For simplicity, we're not checking for holidays
        # A more complete implementation would check against a list of market holidays

        return False
