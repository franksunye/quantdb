"""
Stock list models for QuantDB core.

This module provides database models for caching stock list data
with daily update strategy.
"""

from datetime import date, datetime
from typing import Any, Dict, Optional

from sqlalchemy import Boolean, Column, Date, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Session

from ..database.connection import Base
from ..utils.logger import logger


class StockListCache(Base):
    """
    Stock list cache model for daily stock list data.

    This model stores the complete stock list with market classification
    and is updated daily to ensure fresh data.
    """

    __tablename__ = "stock_list_cache"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False, index=True, comment="Stock symbol")
    name = Column(String(100), nullable=False, comment="Stock name")
    market = Column(
        String(10), nullable=False, index=True, comment="Market code (SHSE/SZSE/HKEX)"
    )

    # Market data (optional, from stock_zh_a_spot_em)
    price = Column(Float, comment="Latest price")
    pct_change = Column(Float, comment="Percentage change")
    change = Column(Float, comment="Price change")
    volume = Column(Float, comment="Trading volume")
    turnover = Column(Float, comment="Trading turnover")
    amplitude = Column(Float, comment="Price amplitude")
    high = Column(Float, comment="Highest price")
    low = Column(Float, comment="Lowest price")
    open = Column(Float, comment="Opening price")
    prev_close = Column(Float, comment="Previous close price")
    volume_ratio = Column(Float, comment="Volume ratio")
    turnover_rate = Column(Float, comment="Turnover rate")
    pe_ratio = Column(Float, comment="PE ratio")
    pb_ratio = Column(Float, comment="PB ratio")
    market_cap = Column(Float, comment="Market capitalization")
    circulating_market_cap = Column(Float, comment="Circulating market cap")

    # Cache metadata
    cache_date = Column(
        Date, nullable=False, default=date.today, comment="Date when data was cached"
    )
    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment="Record creation time",
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        comment="Record update time",
    )
    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        comment="Whether the stock is actively traded",
    )

    @classmethod
    def from_akshare_row(cls, row: Dict[str, Any]) -> "StockListCache":
        """
        Create StockListCache instance from AKShare data row.

        Args:
            row: Dictionary containing stock data from AKShare

        Returns:
            StockListCache instance
        """

        def safe_float(value, default=None):
            """Safely convert value to float."""
            if value is None or value == "" or str(value).strip() == "":
                return default
            try:
                return float(value)
            except (ValueError, TypeError):
                return default

        return cls(
            symbol=str(row.get("symbol", "")).strip(),
            name=str(row.get("name", "Unknown")).strip(),
            market=str(row.get("market", "UNKNOWN")).strip(),
            price=safe_float(row.get("price")),
            pct_change=safe_float(row.get("pct_change")),
            change=safe_float(row.get("change")),
            volume=safe_float(row.get("volume")),
            turnover=safe_float(row.get("turnover")),
            amplitude=safe_float(row.get("amplitude")),
            high=safe_float(row.get("high")),
            low=safe_float(row.get("low")),
            open=safe_float(row.get("open")),
            prev_close=safe_float(row.get("prev_close")),
            volume_ratio=safe_float(row.get("volume_ratio")),
            turnover_rate=safe_float(row.get("turnover_rate")),
            pe_ratio=safe_float(row.get("pe_ratio")),
            pb_ratio=safe_float(row.get("pb_ratio")),
            market_cap=safe_float(row.get("market_cap")),
            circulating_market_cap=safe_float(row.get("circulating_market_cap")),
            cache_date=date.today(),
            is_active=True,
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert model instance to dictionary.

        Returns:
            Dictionary representation of the stock data
        """
        return {
            "symbol": self.symbol,
            "name": self.name,
            "market": self.market,
            "price": self.price,
            "pct_change": self.pct_change,
            "change": self.change,
            "volume": self.volume,
            "turnover": self.turnover,
            "amplitude": self.amplitude,
            "high": self.high,
            "low": self.low,
            "open": self.open,
            "prev_close": self.prev_close,
            "volume_ratio": self.volume_ratio,
            "turnover_rate": self.turnover_rate,
            "pe_ratio": self.pe_ratio,
            "pb_ratio": self.pb_ratio,
            "market_cap": self.market_cap,
            "circulating_market_cap": self.circulating_market_cap,
            "cache_date": self.cache_date.isoformat() if self.cache_date else None,
            "is_active": self.is_active,
        }


class StockListCacheManager:
    """
    Cache manager for stock list data.

    This class provides methods for managing the stock list cache,
    including daily updates and cleanup operations.
    """

    def __init__(self, db_session: Session):
        """
        Initialize cache manager.

        Args:
            db_session: Database session
        """
        self.db = db_session

    def is_cache_fresh(self) -> bool:
        """
        Check if the stock list cache is fresh (updated today).

        Returns:
            True if cache is from today, False otherwise
        """
        today = date.today()

        # Check if we have any records from today
        count = (
            self.db.query(StockListCache)
            .filter(StockListCache.cache_date == today)
            .count()
        )

        return count > 0

    def clear_old_cache(self) -> int:
        """
        Remove old cache entries (older than today).

        Returns:
            Number of records deleted
        """
        today = date.today()

        deleted_count = (
            self.db.query(StockListCache)
            .filter(StockListCache.cache_date < today)
            .delete()
        )

        self.db.commit()
        logger.info(f"Cleared {deleted_count} old stock list cache entries")
        return deleted_count

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        today = date.today()

        total_records = self.db.query(StockListCache).count()
        fresh_records = (
            self.db.query(StockListCache)
            .filter(StockListCache.cache_date == today)
            .count()
        )

        # Count by market
        market_counts = {}
        for market in ["SHSE", "SZSE", "HKEX"]:
            count = (
                self.db.query(StockListCache)
                .filter(
                    StockListCache.market == market, StockListCache.cache_date == today
                )
                .count()
            )
            market_counts[market] = count

        return {
            "total_records": total_records,
            "fresh_records": fresh_records,
            "cache_date": today.isoformat(),
            "is_fresh": fresh_records > 0,
            "market_breakdown": market_counts,
        }

    def update_cache_stats(self, total_count: int):
        """
        Update cache statistics.

        Args:
            total_count: Total number of stocks cached
        """
        try:
            # This method can be used to update cache statistics
            # For now, we just log the update
            logger.info(f"Cache stats updated: {total_count} stocks cached")
        except Exception as e:
            logger.error(f"Error updating cache stats: {e}")
            raise
