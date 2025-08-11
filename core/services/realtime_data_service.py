"""
Realtime stock data service for QuantDB.

This service provides realtime stock data with intelligent caching strategy:
- 1-5 minute cache during trading hours
- Longer cache outside trading hours
- Efficient batch processing
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, desc
from sqlalchemy.orm import Session

from ..cache.akshare_adapter import AKShareAdapter
from ..models.asset import Asset
from ..models.realtime_data import RealtimeDataCache, RealtimeStockData
from ..utils.logger import logger


class RealtimeDataService:
    """
    Service for managing realtime stock data with caching.

    This service implements intelligent caching strategies:
    - Short TTL during trading hours (1-5 minutes)
    - Longer TTL outside trading hours (up to 60 minutes)
    - Efficient batch processing for multiple symbols
    """

    def __init__(self, db: Session, akshare_adapter: AKShareAdapter):
        """
        Initialize the realtime data service.

        Args:
            db: Database session
            akshare_adapter: AKShare adapter for data retrieval
        """
        self.db = db
        self.akshare_adapter = akshare_adapter
        self.cache_manager = RealtimeDataCache(db)
        logger.info("Realtime data service initialized")

    def get_realtime_data(
        self, symbol: str, force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        Get realtime data for a single stock with caching.

        Args:
            symbol: Stock symbol
            force_refresh: If True, bypass cache and fetch fresh data

        Returns:
            Dictionary with realtime stock data
        """
        try:
            logger.info(
                f"Getting realtime data for {symbol}, force_refresh={force_refresh}"
            )

            # Check cache first (unless force refresh)
            if not force_refresh:
                cached_data = self._get_cached_data(symbol)
                if cached_data:
                    logger.info(f"Cache hit for {symbol}")
                    cached_data["cache_hit"] = True
                    return cached_data

            # Cache miss or force refresh - fetch from AKShare
            logger.info(f"Cache miss for {symbol}, fetching from AKShare")

            df = self.akshare_adapter.get_realtime_data(symbol)

            if df.empty:
                logger.warning(f"No realtime data available for {symbol}")
                return {
                    "symbol": symbol,
                    "error": "No data available",
                    "cache_hit": False,
                    "timestamp": datetime.now().isoformat(),
                }

            # Convert to our format
            row = df.iloc[0]
            data = self._convert_akshare_to_dict(symbol, row)
            data["cache_hit"] = False

            # Save to cache
            self._save_to_cache(symbol, data)

            logger.info(f"Successfully retrieved realtime data for {symbol}")
            return data

        except Exception as e:
            logger.error(f"Error getting realtime data for {symbol}: {e}")
            return {
                "symbol": symbol,
                "error": str(e),
                "cache_hit": False,
                "timestamp": datetime.now().isoformat(),
            }

    def get_realtime_data_batch(
        self, symbols: List[str], force_refresh: bool = False
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get realtime data for multiple stocks efficiently.

        Args:
            symbols: List of stock symbols
            force_refresh: If True, bypass cache and fetch fresh data

        Returns:
            Dictionary with symbol as key and data as value
        """
        try:
            logger.info(f"Getting batch realtime data for {len(symbols)} symbols")

            result = {}
            symbols_to_fetch = []

            # Check cache for each symbol (unless force refresh)
            if not force_refresh:
                for symbol in symbols:
                    cached_data = self._get_cached_data(symbol)
                    if cached_data:
                        cached_data["cache_hit"] = True
                        result[symbol] = cached_data
                    else:
                        symbols_to_fetch.append(symbol)
            else:
                symbols_to_fetch = symbols.copy()

            # Fetch missing symbols from AKShare
            if symbols_to_fetch:
                logger.info(f"Fetching {len(symbols_to_fetch)} symbols from AKShare")

                batch_data = self.akshare_adapter.get_realtime_data_batch(
                    symbols_to_fetch
                )

                for symbol in symbols_to_fetch:
                    if symbol in batch_data:
                        data = batch_data[symbol]
                        data["cache_hit"] = False
                        result[symbol] = data

                        # Save to cache
                        self._save_to_cache(symbol, data)
                    else:
                        result[symbol] = {
                            "symbol": symbol,
                            "error": "No data available",
                            "cache_hit": False,
                            "timestamp": datetime.now().isoformat(),
                        }

            logger.info(
                f"Successfully retrieved batch realtime data for {len(result)} symbols"
            )
            return result

        except Exception as e:
            logger.error(f"Error getting batch realtime data: {e}")
            # Return error for all symbols
            return {
                symbol: {
                    "symbol": symbol,
                    "error": str(e),
                    "cache_hit": False,
                    "timestamp": datetime.now().isoformat(),
                }
                for symbol in symbols
            }

    def _get_cached_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get cached data for a symbol if valid.

        Args:
            symbol: Stock symbol

        Returns:
            Cached data dictionary or None if not found/expired
        """
        try:
            # Get the most recent cached data for this symbol
            cached_record = (
                self.db.query(RealtimeStockData)
                .filter(RealtimeStockData.symbol == symbol)
                .order_by(desc(RealtimeStockData.timestamp))
                .first()
            )

            if cached_record and cached_record.is_cache_valid():
                logger.debug(f"Found valid cached data for {symbol}")
                return cached_record.to_dict()

            return None

        except Exception as e:
            logger.error(f"Error getting cached data for {symbol}: {e}")
            return None

    def _save_to_cache(self, symbol: str, data: Dict[str, Any]) -> bool:
        """
        Save data to cache.

        Args:
            symbol: Stock symbol
            data: Data dictionary to cache

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get or create asset
            asset = self.db.query(Asset).filter(Asset.symbol == symbol).first()
            asset_id = asset.asset_id if asset else None

            # Create realtime data record
            realtime_data = RealtimeStockData(
                symbol=symbol,
                asset_id=asset_id,
                price=data.get("price", 0),
                open_price=data.get("open", 0),
                high_price=data.get("high", 0),
                low_price=data.get("low", 0),
                prev_close=data.get("prev_close", 0),
                change=data.get("change", 0),
                pct_change=data.get("pct_change", 0),
                volume=data.get("volume", 0),
                turnover=data.get("turnover", 0),
                timestamp=datetime.now(),
                is_trading_hours=RealtimeStockData._is_trading_hours(),
                cache_ttl_minutes=5 if RealtimeStockData._is_trading_hours() else 60,
            )

            self.db.add(realtime_data)
            self.db.commit()

            logger.debug(f"Saved realtime data to cache for {symbol}")
            return True

        except Exception as e:
            logger.error(f"Error saving to cache for {symbol}: {e}")
            self.db.rollback()
            return False

    def _convert_akshare_to_dict(self, symbol: str, row: Any) -> Dict[str, Any]:
        """
        Convert AKShare data row to our standard dictionary format.

        Args:
            symbol: Stock symbol
            row: AKShare data row

        Returns:
            Standardized data dictionary
        """
        return {
            "symbol": symbol,
            "name": row.get("名称", f"Stock {symbol}"),
            "price": float(row.get("最新价", 0)),
            "open": float(row.get("今开", 0)),
            "high": float(row.get("最高", 0)),
            "low": float(row.get("最低", 0)),
            "prev_close": float(row.get("昨收", 0)),
            "change": float(row.get("涨跌额", 0)),
            "pct_change": float(row.get("涨跌幅", 0)),
            "volume": float(row.get("成交量", 0)),
            "turnover": float(row.get("成交额", 0)),
            "turnover_rate": float(row.get("换手率", 0)),
            "market_cap": float(row.get("总市值", 0)),
            "timestamp": datetime.now().isoformat(),
            "is_trading_hours": RealtimeStockData._is_trading_hours(),
        }

    def cleanup_expired_cache(self) -> int:
        """
        Clean up expired cache entries.

        Returns:
            Number of records deleted
        """
        return self.cache_manager.cleanup_expired_cache()

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        return self.cache_manager.get_cache_stats()
