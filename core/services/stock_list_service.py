"""
Stock list service for QuantDB.

This service provides stock list data with intelligent daily caching strategy:
- Daily cache refresh for stock list data
- Market-based filtering (SHSE/SZSE/HKEX)
- Efficient data management and cleanup
"""

from datetime import date
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, desc
from sqlalchemy.orm import Session

from ..cache.akshare_adapter import AKShareAdapter
from ..models.stock_list import StockListCache, StockListCacheManager
from ..utils.logger import logger


class StockListService:
    """
    Service for managing stock list data with intelligent caching.

    This service provides methods for retrieving stock lists with
    daily cache refresh and market filtering capabilities.
    """

    def __init__(self, db_session: Session, akshare_adapter: AKShareAdapter):
        """
        Initialize stock list service.

        Args:
            db_session: Database session
            akshare_adapter: AKShare adapter instance
        """
        self.db = db_session
        self.akshare_adapter = akshare_adapter
        self.cache_manager = StockListCacheManager(db_session)

    def get_stock_list(
        self, market: Optional[str] = None, force_refresh: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get stock list with intelligent caching.

        Args:
            market: Market filter ('SHSE', 'SZSE', 'HKEX', or None for all)
            force_refresh: If True, bypass cache and fetch fresh data

        Returns:
            List of dictionaries containing stock data
        """
        try:
            logger.info(
                f"Getting stock list for market: {market or 'all'}, force_refresh={force_refresh}"
            )

            # Check if cache is fresh (unless force refresh)
            if not force_refresh and self.cache_manager.is_cache_fresh():
                logger.info("Using cached stock list data")
                return self._get_cached_stock_list(market)

            # Cache is stale or force refresh - fetch from AKShare
            logger.info(
                "Cache is stale or force refresh requested, fetching from AKShare"
            )

            # Fetch fresh data from AKShare
            df = self.akshare_adapter.get_stock_list(
                market=None
            )  # Get all markets first

            if df.empty:
                logger.warning("No stock list data available from AKShare")
                # Return cached data if available
                return self._get_cached_stock_list(market)

            # Clear old cache and save new data
            self.cache_manager.clear_old_cache()
            self._save_stock_list_to_cache(df)

            # Return filtered data
            return self._get_cached_stock_list(market)

        except Exception as e:
            logger.error(f"Error getting stock list: {e}")
            # Try to return cached data as fallback
            try:
                logger.info("Attempting to return cached data as fallback")
                return self._get_cached_stock_list(market)
            except Exception as fallback_error:
                logger.error(f"Fallback to cached data also failed: {fallback_error}")
                raise e

    def _get_cached_stock_list(
        self, market: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get stock list from cache.

        Args:
            market: Market filter ('SHSE', 'SZSE', 'HKEX', or None for all)

        Returns:
            List of dictionaries containing cached stock data
        """
        today = date.today()

        # Build query
        query = self.db.query(StockListCache).filter(
            StockListCache.cache_date == today, StockListCache.is_active == True
        )

        # Apply market filter if specified
        if market:
            market_upper = market.upper()
            if market_upper in ["SHSE", "SZSE", "HKEX"]:
                query = query.filter(StockListCache.market == market_upper)
            else:
                logger.warning(f"Unknown market filter: {market}")

        # Order by symbol
        query = query.order_by(StockListCache.symbol)

        # Execute query and convert to dictionaries
        stocks = query.all()
        result = [stock.to_dict() for stock in stocks]

        logger.info(
            f"Retrieved {len(result)} stocks from cache for market: {market or 'all'}"
        )
        return result

    def _save_stock_list_to_cache(self, df) -> int:
        """
        Save stock list DataFrame to cache.

        Args:
            df: DataFrame containing stock list data

        Returns:
            Number of records saved
        """
        saved_count = 0

        try:
            for _, row in df.iterrows():
                try:
                    # Convert row to dictionary
                    row_dict = row.to_dict()

                    # Create cache entry
                    cache_entry = StockListCache.from_akshare_row(row_dict)

                    # Skip if symbol is empty
                    if not cache_entry.symbol:
                        continue

                    self.db.add(cache_entry)
                    saved_count += 1

                except Exception as e:
                    logger.warning(
                        f"Error saving stock {row.get('symbol', 'unknown')}: {e}"
                    )
                    continue

            # Commit all changes
            self.db.commit()
            logger.info(f"Successfully saved {saved_count} stocks to cache")

        except Exception as e:
            logger.error(f"Error saving stock list to cache: {e}")
            self.db.rollback()
            raise

        return saved_count

    def get_market_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics for all markets.

        Returns:
            Dictionary with market summary statistics
        """
        try:
            today = date.today()

            summary = {"date": today.isoformat(), "markets": {}, "total_stocks": 0}

            # Get statistics for each market
            for market in ["SHSE", "SZSE", "HKEX"]:
                market_stocks = (
                    self.db.query(StockListCache)
                    .filter(
                        StockListCache.market == market,
                        StockListCache.cache_date == today,
                        StockListCache.is_active == True,
                    )
                    .all()
                )

                if market_stocks:
                    # Calculate market statistics
                    prices = [s.price for s in market_stocks if s.price is not None]
                    pct_changes = [
                        s.pct_change for s in market_stocks if s.pct_change is not None
                    ]

                    market_summary = {
                        "count": len(market_stocks),
                        "avg_price": sum(prices) / len(prices) if prices else 0,
                        "avg_pct_change": (
                            sum(pct_changes) / len(pct_changes) if pct_changes else 0
                        ),
                        "gainers": len([p for p in pct_changes if p > 0]),
                        "losers": len([p for p in pct_changes if p < 0]),
                        "unchanged": len([p for p in pct_changes if p == 0]),
                    }
                else:
                    market_summary = {
                        "count": 0,
                        "avg_price": 0,
                        "avg_pct_change": 0,
                        "gainers": 0,
                        "losers": 0,
                        "unchanged": 0,
                    }

                summary["markets"][market] = market_summary
                summary["total_stocks"] += market_summary["count"]

            logger.info(
                f"Generated market summary for {summary['total_stocks']} stocks"
            )
            return summary

        except Exception as e:
            logger.error(f"Error generating market summary: {e}")
            raise

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        return self.cache_manager.get_cache_stats()

    def clear_cache(self) -> int:
        """
        Clear all stock list cache.

        Returns:
            Number of records deleted
        """
        try:
            deleted_count = self.db.query(StockListCache).delete()
            self.db.commit()
            logger.info(f"Cleared {deleted_count} stock list cache entries")
            return deleted_count
        except Exception as e:
            logger.error(f"Error clearing stock list cache: {e}")
            self.db.rollback()
            raise

    def clear_all_cache(self) -> int:
        """
        Clear all stock list cache (alias for clear_cache).

        Returns:
            Number of records deleted
        """
        return self.clear_cache()

    def get_stock_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get information for a specific stock.

        Args:
            symbol: Stock symbol

        Returns:
            Dictionary with stock information or None if not found
        """
        try:
            today = date.today()
            stock = (
                self.db.query(StockListCache)
                .filter(
                    StockListCache.symbol == symbol,
                    StockListCache.cache_date == today,
                    StockListCache.is_active == True,
                )
                .first()
            )

            if stock:
                return stock.to_dict()
            return None

        except Exception as e:
            logger.error(f"Error getting stock info for {symbol}: {e}")
            return None

    def is_stock_exists(self, symbol: str) -> bool:
        """
        Check if a stock exists in the cache.

        Args:
            symbol: Stock symbol

        Returns:
            True if stock exists, False otherwise
        """
        return self.get_stock_info(symbol) is not None

    def get_total_stock_count(self) -> int:
        """
        Get total number of stocks in cache.

        Returns:
            Total stock count
        """
        try:
            today = date.today()
            return (
                self.db.query(StockListCache)
                .filter(
                    StockListCache.cache_date == today,
                    StockListCache.is_active == True,
                )
                .count()
            )
        except Exception as e:
            logger.error(f"Error getting total stock count: {e}")
            return 0

    def get_stock_count_by_market(self, market: str) -> int:
        """
        Get stock count for a specific market.

        Args:
            market: Market code (SHSE, SZSE, HKEX)

        Returns:
            Stock count for the market
        """
        try:
            today = date.today()
            return (
                self.db.query(StockListCache)
                .filter(
                    StockListCache.market == market.upper(),
                    StockListCache.cache_date == today,
                    StockListCache.is_active == True,
                )
                .count()
            )
        except Exception as e:
            logger.error(f"Error getting stock count for market {market}: {e}")
            return 0

    def search_stocks_by_name(self, name_pattern: str) -> List[Dict[str, Any]]:
        """
        Search stocks by name pattern.

        Args:
            name_pattern: Name pattern to search for

        Returns:
            List of matching stocks
        """
        try:
            today = date.today()
            stocks = (
                self.db.query(StockListCache)
                .filter(
                    StockListCache.name.like(f"%{name_pattern}%"),
                    StockListCache.cache_date == today,
                    StockListCache.is_active == True,
                )
                .all()
            )

            return [stock.to_dict() for stock in stocks]

        except Exception as e:
            logger.error(f"Error searching stocks by name {name_pattern}: {e}")
            return []

    def search_stocks_by_symbol(self, symbol_pattern: str) -> List[Dict[str, Any]]:
        """
        Search stocks by symbol pattern.

        Args:
            symbol_pattern: Symbol pattern to search for

        Returns:
            List of matching stocks
        """
        try:
            today = date.today()
            stocks = (
                self.db.query(StockListCache)
                .filter(
                    StockListCache.symbol.like(f"%{symbol_pattern}%"),
                    StockListCache.cache_date == today,
                    StockListCache.is_active == True,
                )
                .all()
            )

            return [stock.to_dict() for stock in stocks]

        except Exception as e:
            logger.error(f"Error searching stocks by symbol {symbol_pattern}: {e}")
            return []

    def get_stocks_by_market(
        self, market: str, skip: int = 0, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get stocks by market with pagination.

        Args:
            market: Market code (SHSE, SZSE, HKEX)
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of stocks for the market
        """
        try:
            today = date.today()
            stocks = (
                self.db.query(StockListCache)
                .filter(
                    StockListCache.market == market.upper(),
                    StockListCache.cache_date == today,
                    StockListCache.is_active == True,
                )
                .offset(skip)
                .limit(limit)
                .all()
            )

            return [stock.to_dict() for stock in stocks]

        except Exception as e:
            logger.error(f"Error getting stocks by market {market}: {e}")
            return []

    def get_cache_info(self) -> Dict[str, Any]:
        """
        Get cache information.

        Returns:
            Dictionary with cache information
        """
        return self.get_cache_stats()

    def _clear_old_stock_list_cache(self):
        """Clear old stock list cache entries."""
        return self.cache_manager.clear_old_cache()

    def _convert_cache_to_dict_list(self, cache_data: List) -> List[Dict[str, Any]]:
        """
        Convert cache objects to dictionary list.

        Args:
            cache_data: List of cache objects

        Returns:
            List of dictionaries
        """
        return [item.to_dict() if hasattr(item, 'to_dict') else item for item in cache_data]

    def _update_cache_stats(self, total_count: int):
        """
        Update cache statistics.

        Args:
            total_count: Total number of stocks
        """
        try:
            self.cache_manager.update_cache_stats(total_count)
        except Exception as e:
            logger.error(f"Error updating cache stats: {e}")
