"""
Index data service for QuantDB.

This service provides index data with intelligent caching strategy:
- Historical data cached in database
- Realtime data with 1-5 minute cache during trading hours
- Efficient batch processing
"""

from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
from sqlalchemy import and_, desc, func
from sqlalchemy.orm import Session

from ..cache.akshare_adapter import AKShareAdapter
from ..models.index_data import (
    IndexData,
    IndexListCache,
    IndexListCacheManager,
    RealtimeIndexData,
)
from ..utils.logger import logger


class IndexDataService:
    """
    Service for managing index data operations.

    This service handles both historical and realtime index data with
    intelligent caching strategies.
    """

    def __init__(self, db: Session, akshare_adapter: AKShareAdapter):
        """
        Initialize the index data service.

        Args:
            db: Database session
            akshare_adapter: AKShare adapter instance
        """
        self.db = db
        self.akshare_adapter = akshare_adapter
        logger.info("Index data service initialized")

    def get_index_data(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        period: str = "daily",
        force_refresh: bool = False,
    ) -> pd.DataFrame:
        """
        Get historical index data with intelligent caching.

        Args:
            symbol: Index symbol
            start_date: Start date in YYYYMMDD format
            end_date: End date in YYYYMMDD format
            period: Data frequency ("daily", "weekly", "monthly")
            force_refresh: If True, bypass cache and fetch fresh data

        Returns:
            DataFrame with index data
        """
        try:
            logger.info(
                f"Getting index data for {symbol}, period={period}, force_refresh={force_refresh}"
            )

            # Parse dates
            if start_date:
                start_dt = datetime.strptime(start_date, "%Y%m%d").date()
            else:
                start_dt = (datetime.now() - timedelta(days=365)).date()

            if end_date:
                end_dt = datetime.strptime(end_date, "%Y%m%d").date()
            else:
                end_dt = datetime.now().date()

            # Check cache first (unless force refresh)
            if not force_refresh:
                cached_data = self._get_cached_index_data(symbol, start_dt, end_dt)
                if not cached_data.empty:
                    logger.info(f"Using cached index data for {symbol}")
                    return cached_data

            # Fetch fresh data from AKShare
            logger.info(f"Fetching fresh index data from AKShare for {symbol}")
            df = self.akshare_adapter.get_index_data(
                symbol=symbol, start_date=start_date, end_date=end_date, period=period
            )

            if df.empty:
                logger.warning(f"No index data available for {symbol}")
                return df

            # Save to cache
            self._save_index_data_to_cache(symbol, df)

            logger.info(
                f"Successfully retrieved {len(df)} rows of index data for {symbol}"
            )
            return df

        except Exception as e:
            logger.error(f"Error getting index data for {symbol}: {e}")
            raise

    def get_realtime_index_data(
        self, symbol: str, force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        Get realtime index data with intelligent caching.

        Args:
            symbol: Index symbol
            force_refresh: If True, bypass cache and fetch fresh data

        Returns:
            Dictionary with realtime index data
        """
        try:
            logger.info(
                f"Getting realtime index data for {symbol}, force_refresh={force_refresh}"
            )

            # Check cache first (unless force refresh)
            if not force_refresh:
                cached_data = self._get_cached_realtime_index_data(symbol)
                if cached_data:
                    logger.info(f"Using cached realtime index data for {symbol}")
                    return cached_data

            # Fetch fresh data from AKShare
            logger.info(f"Fetching fresh realtime index data from AKShare for {symbol}")
            df = self.akshare_adapter.get_index_realtime_data(symbol)

            if df.empty:
                logger.warning(f"No realtime index data available for {symbol}")
                return {
                    "symbol": symbol,
                    "error": "No data available",
                    "cache_hit": False,
                    "timestamp": datetime.now().isoformat(),
                }

            # Convert to dictionary
            data = df.iloc[0].to_dict()
            data["cache_hit"] = False
            data["timestamp"] = datetime.now().isoformat()
            data["is_trading_hours"] = self._is_trading_hours()

            # Save to cache
            self._save_realtime_index_data_to_cache(symbol, data)

            logger.info(f"Successfully retrieved realtime index data for {symbol}")
            return data

        except Exception as e:
            logger.error(f"Error getting realtime index data for {symbol}: {e}")
            return {
                "symbol": symbol,
                "error": str(e),
                "cache_hit": False,
                "timestamp": datetime.now().isoformat(),
            }

    def get_index_list(
        self, category: Optional[str] = None, force_refresh: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get index list with intelligent caching.

        Args:
            category: Index category filter
            force_refresh: If True, bypass cache and fetch fresh data

        Returns:
            List of dictionaries containing index information
        """
        try:
            logger.info(
                f"Getting index list for category: {category or 'all'}, force_refresh={force_refresh}"
            )

            # Check if cache is fresh (unless force refresh)
            if not force_refresh and self._is_index_list_cache_fresh():
                logger.info("Using cached index list data")
                return self._get_cached_index_list(category)

            # Cache is stale or force refresh - fetch from AKShare
            logger.info(
                "Cache is stale or force refresh requested, fetching from AKShare"
            )

            # Fetch fresh data from AKShare
            df = self.akshare_adapter.get_index_list(
                category=None
            )  # Get all categories first

            if df.empty:
                logger.warning("No index list data available from AKShare")
                # Return cached data if available
                return self._get_cached_index_list(category)

            # Clear old cache and save new data
            self._clear_old_index_list_cache()
            self._save_index_list_to_cache(df)

            # Return filtered data
            return self._get_cached_index_list(category)

        except Exception as e:
            logger.error(f"Error getting index list: {e}")
            # Try to return cached data as fallback
            try:
                logger.info("Attempting to return cached data as fallback")
                return self._get_cached_index_list(category)
            except Exception as fallback_error:
                logger.error(f"Fallback to cached data also failed: {fallback_error}")
                raise e

    def _get_cached_index_data(
        self, symbol: str, start_date: date, end_date: date
    ) -> pd.DataFrame:
        """Get cached index data from database."""
        try:
            query = (
                self.db.query(IndexData)
                .filter(
                    and_(
                        IndexData.symbol == symbol,
                        IndexData.date >= start_date,
                        IndexData.date <= end_date,
                    )
                )
                .order_by(IndexData.date)
            )

            results = query.all()

            if not results:
                return pd.DataFrame()

            # Convert to DataFrame
            data = [result.to_dict() for result in results]
            df = pd.DataFrame(data)

            logger.info(f"Retrieved {len(df)} cached index data rows for {symbol}")
            return df

        except Exception as e:
            logger.error(f"Error getting cached index data: {e}")
            return pd.DataFrame()

    def _save_index_data_to_cache(self, symbol: str, df: pd.DataFrame):
        """Save index data to database cache."""
        try:
            if df.empty:
                return

            # Get index name from first row if available
            index_name = (
                df.iloc[0].get("name", f"Index {symbol}")
                if "name" in df.columns
                else f"Index {symbol}"
            )

            for _, row in df.iterrows():
                # Parse date
                trade_date = pd.to_datetime(row["date"]).date()

                # Check if record already exists
                existing = (
                    self.db.query(IndexData)
                    .filter(
                        and_(IndexData.symbol == symbol, IndexData.date == trade_date)
                    )
                    .first()
                )

                if existing:
                    # Update existing record
                    existing.name = index_name
                    existing.open_price = row.get("open")
                    existing.high_price = row.get("high")
                    existing.low_price = row.get("low")
                    existing.close_price = row.get("close")
                    existing.volume = row.get("volume")
                    existing.turnover = row.get("turnover")
                    existing.change = row.get("change")
                    existing.pct_change = row.get("pct_change")
                    existing.amplitude = row.get("amplitude")
                    existing.updated_at = datetime.utcnow()
                else:
                    # Create new record
                    index_data = IndexData(
                        symbol=symbol,
                        name=index_name,
                        date=trade_date,
                        open_price=row.get("open"),
                        high_price=row.get("high"),
                        low_price=row.get("low"),
                        close_price=row.get("close"),
                        volume=row.get("volume"),
                        turnover=row.get("turnover"),
                        change=row.get("change"),
                        pct_change=row.get("pct_change"),
                        amplitude=row.get("amplitude"),
                    )
                    self.db.add(index_data)

            self.db.commit()
            logger.info(f"Saved {len(df)} index data rows to cache for {symbol}")

        except Exception as e:
            logger.error(f"Error saving index data to cache: {e}")
            self.db.rollback()
            raise

    def _get_cached_realtime_index_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get cached realtime index data."""
        try:
            cached = (
                self.db.query(RealtimeIndexData)
                .filter(RealtimeIndexData.symbol == symbol)
                .order_by(desc(RealtimeIndexData.timestamp))
                .first()
            )

            if cached and cached.is_cache_valid():
                data = cached.to_dict()
                logger.info(f"Using cached realtime index data for {symbol}")
                return data

            return None

        except Exception as e:
            logger.error(f"Error getting cached realtime index data: {e}")
            return None

    def _save_realtime_index_data_to_cache(self, symbol: str, data: Dict[str, Any]):
        """Save realtime index data to cache."""
        try:
            # Delete old cache for this symbol
            self.db.query(RealtimeIndexData).filter(
                RealtimeIndexData.symbol == symbol
            ).delete()

            # Determine cache TTL based on trading hours
            is_trading = self._is_trading_hours()
            cache_ttl = (
                1 if is_trading else 30
            )  # 1 minute during trading, 30 minutes outside

            # Create new cache entry
            realtime_data = RealtimeIndexData(
                symbol=symbol,
                name=data.get("name", f"Index {symbol}"),
                price=data.get("price", 0.0),
                open_price=data.get("open"),
                high_price=data.get("high"),
                low_price=data.get("low"),
                prev_close=data.get("prev_close"),
                change=data.get("change"),
                pct_change=data.get("pct_change"),
                amplitude=data.get("amplitude"),
                volume=data.get("volume"),
                turnover=data.get("turnover"),
                timestamp=datetime.utcnow(),
                cache_ttl_minutes=cache_ttl,
                is_trading_hours=is_trading,
            )

            self.db.add(realtime_data)
            self.db.commit()

            logger.info(f"Saved realtime index data to cache for {symbol}")

        except Exception as e:
            logger.error(f"Error saving realtime index data to cache: {e}")
            self.db.rollback()

    def _is_index_list_cache_fresh(self) -> bool:
        """Check if index list cache is fresh (same day)."""
        try:
            manager = (
                self.db.query(IndexListCacheManager)
                .filter(IndexListCacheManager.is_current == True)
                .first()
            )

            return manager and manager.is_cache_fresh() if manager else False

        except Exception as e:
            logger.error(f"Error checking index list cache freshness: {e}")
            return False

    def _get_cached_index_list(
        self, category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get cached index list data."""
        try:
            query = self.db.query(IndexListCache).filter(
                IndexListCache.cache_date == date.today(),
                IndexListCache.is_active == True,
            )

            if category:
                query = query.filter(IndexListCache.category == category)

            results = query.order_by(IndexListCache.symbol).all()

            data = [result.to_dict() for result in results]
            logger.info(f"Retrieved {len(data)} cached index list entries")
            return data

        except Exception as e:
            logger.error(f"Error getting cached index list: {e}")
            return []

    def _clear_old_index_list_cache(self):
        """Clear old index list cache."""
        try:
            # Mark old cache managers as not current
            self.db.query(IndexListCacheManager).update(
                {IndexListCacheManager.is_current: False}
            )

            # Delete old cache entries (keep last 7 days)
            cutoff_date = date.today() - timedelta(days=7)
            self.db.query(IndexListCache).filter(
                IndexListCache.cache_date < cutoff_date
            ).delete()

            self.db.commit()
            logger.info("Cleared old index list cache")

        except Exception as e:
            logger.error(f"Error clearing old index list cache: {e}")
            self.db.rollback()

    def _save_index_list_to_cache(self, df: pd.DataFrame):
        """Save index list to cache."""
        try:
            if df.empty:
                return

            today = date.today()

            for _, row in df.iterrows():
                index_cache = IndexListCache(
                    symbol=row.get("symbol", ""),
                    name=row.get("name", ""),
                    category=row.get("category", "Unknown"),
                    price=row.get("price"),
                    pct_change=row.get("pct_change"),
                    change=row.get("change"),
                    volume=row.get("volume"),
                    turnover=row.get("turnover"),
                    cache_date=today,
                    is_active=True,
                )
                self.db.add(index_cache)

            # Create cache manager entry
            cache_manager = IndexListCacheManager(
                cache_date=today, total_count=len(df), is_current=True
            )
            self.db.add(cache_manager)

            self.db.commit()
            logger.info(f"Saved {len(df)} index list entries to cache")

        except Exception as e:
            logger.error(f"Error saving index list to cache: {e}")
            self.db.rollback()
            raise

    def _is_trading_hours(self) -> bool:
        """Check if current time is within trading hours."""
        try:
            now = datetime.now()
            current_time = now.time()

            # A-share trading hours: 9:30-11:30, 13:00-15:00 (Monday-Friday)
            if now.weekday() >= 5:  # Weekend
                return False

            morning_start = datetime.strptime("09:30", "%H:%M").time()
            morning_end = datetime.strptime("11:30", "%H:%M").time()
            afternoon_start = datetime.strptime("13:00", "%H:%M").time()
            afternoon_end = datetime.strptime("15:00", "%H:%M").time()

            return (morning_start <= current_time <= morning_end) or (
                afternoon_start <= current_time <= afternoon_end
            )

        except Exception as e:
            logger.error(f"Error checking trading hours: {e}")
            return True  # Default to trading hours for safety

    def get_index_data_by_days(self, symbol: str, days: int) -> pd.DataFrame:
        """
        Get index data for the last N trading days.

        Args:
            symbol: Index symbol
            days: Number of recent trading days to fetch

        Returns:
            DataFrame with index data for the last N trading days
        """
        from datetime import datetime, timedelta

        # Calculate date range with buffer to ensure enough trading days
        end_date = datetime.now().date()
        start_date = (datetime.now() - timedelta(days=days * 2)).date()

        logger.info(f"Getting last {days} trading days for index {symbol}")

        # Get data for the calculated range
        df = self.get_index_data(symbol, start_date, end_date)

        # Return only the last N trading days
        if len(df) > days:
            df = df.tail(days)

        logger.info(f"Returned {len(df)} trading days for index {symbol}")
        return df
