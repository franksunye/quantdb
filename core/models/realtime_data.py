"""
Realtime stock data models for QuantDB.

This module defines the database models for storing realtime stock data
with appropriate caching and indexing strategies.
"""

from datetime import datetime, timedelta
from typing import Any, Dict

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.orm import relationship

from ..database.connection import Base


class RealtimeStockData(Base):
    """
    Model for storing realtime stock data.

    This table stores current stock prices and related metrics with
    a short TTL for caching purposes (1-5 minutes).
    """

    __tablename__ = "realtime_stock_data"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Stock identification
    symbol = Column(String(20), nullable=False, index=True)
    asset_id = Column(Integer, ForeignKey("assets.asset_id"), nullable=True, index=True)

    # Basic price information
    price = Column(Float, nullable=False, comment="Current price")
    open_price = Column(Float, nullable=True, comment="Opening price")
    high_price = Column(Float, nullable=True, comment="Highest price of the day")
    low_price = Column(Float, nullable=True, comment="Lowest price of the day")
    prev_close = Column(Float, nullable=True, comment="Previous closing price")

    # Change information
    change = Column(Float, nullable=True, comment="Price change amount")
    pct_change = Column(Float, nullable=True, comment="Price change percentage")

    # Volume and turnover
    volume = Column(Float, nullable=True, comment="Trading volume")
    turnover = Column(Float, nullable=True, comment="Trading turnover amount")
    turnover_rate = Column(Float, nullable=True, comment="Turnover rate percentage")

    # Market metrics
    market_cap = Column(Float, nullable=True, comment="Market capitalization")
    pe_ratio = Column(Float, nullable=True, comment="Price-to-earnings ratio")
    pb_ratio = Column(Float, nullable=True, comment="Price-to-book ratio")

    # Timestamp information
    timestamp = Column(
        DateTime, nullable=False, default=datetime.utcnow, comment="Data timestamp"
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

    # Cache metadata
    cache_ttl_minutes = Column(
        Integer, nullable=False, default=5, comment="Cache TTL in minutes"
    )
    is_trading_hours = Column(
        Boolean,
        nullable=False,
        default=True,
        comment="Whether data was fetched during trading hours",
    )

    # Relationship
    asset = relationship("Asset", back_populates="realtime_data")

    # Indexes for performance
    __table_args__ = (
        Index("idx_realtime_symbol_timestamp", "symbol", "timestamp"),
        Index("idx_realtime_asset_timestamp", "asset_id", "timestamp"),
        Index("idx_realtime_created_at", "created_at"),
    )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert model instance to dictionary.

        Returns:
            Dictionary representation of the realtime data
        """
        return {
            "symbol": self.symbol,
            "name": self.asset.name if self.asset else f"Stock {self.symbol}",
            "price": self.price,
            "open": self.open_price,
            "high": self.high_price,
            "low": self.low_price,
            "prev_close": self.prev_close,
            "change": self.change,
            "pct_change": self.pct_change,
            "volume": self.volume,
            "turnover": self.turnover,
            "turnover_rate": self.turnover_rate,
            "market_cap": self.market_cap,
            "pe_ratio": self.pe_ratio,
            "pb_ratio": self.pb_ratio,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "is_trading_hours": self.is_trading_hours,
            "cache_ttl_minutes": self.cache_ttl_minutes,
        }

    def is_cache_valid(self) -> bool:
        """
        Check if the cached data is still valid based on TTL.

        Returns:
            True if cache is valid, False if expired
        """
        if not self.timestamp:
            return False

        time_diff = datetime.utcnow() - self.timestamp
        return time_diff.total_seconds() < (self.cache_ttl_minutes * 60)

    @classmethod
    def from_akshare_data(
        cls, symbol: str, akshare_row: Dict[str, Any], asset_id: int = None
    ) -> "RealtimeStockData":
        """
        Create RealtimeStockData instance from AKShare data.

        Args:
            symbol: Stock symbol
            akshare_row: Row data from AKShare stock_zh_a_spot
            asset_id: Optional asset ID for relationship

        Returns:
            RealtimeStockData instance
        """
        # Map AKShare fields to our model
        # Note: Field names may vary based on AKShare version
        return cls(
            symbol=symbol,
            asset_id=asset_id,
            price=float(akshare_row.get("最新价", akshare_row.get("price", 0))),
            open_price=float(akshare_row.get("今开", akshare_row.get("open", 0))),
            high_price=float(akshare_row.get("最高", akshare_row.get("high", 0))),
            low_price=float(akshare_row.get("最低", akshare_row.get("low", 0))),
            prev_close=float(akshare_row.get("昨收", akshare_row.get("prev_close", 0))),
            change=float(akshare_row.get("涨跌额", akshare_row.get("change", 0))),
            pct_change=float(
                akshare_row.get("涨跌幅", akshare_row.get("pct_change", 0))
            ),
            volume=float(akshare_row.get("成交量", akshare_row.get("volume", 0))),
            turnover=float(akshare_row.get("成交额", akshare_row.get("turnover", 0))),
            turnover_rate=float(
                akshare_row.get("换手率", akshare_row.get("turnover_rate", 0))
            ),
            market_cap=float(
                akshare_row.get("总市值", akshare_row.get("market_cap", 0))
            ),
            pe_ratio=float(akshare_row.get("市盈率", akshare_row.get("pe_ratio", 0))),
            pb_ratio=float(akshare_row.get("市净率", akshare_row.get("pb_ratio", 0))),
            timestamp=datetime.utcnow(),
            is_trading_hours=cls._is_trading_hours(),
            cache_ttl_minutes=(
                5 if cls._is_trading_hours() else 60
            ),  # Longer cache outside trading hours
        )

    @staticmethod
    def _is_trading_hours() -> bool:
        """
        Check if current time is within trading hours.

        Returns:
            True if within trading hours, False otherwise
        """
        now = datetime.now()
        weekday = now.weekday()  # 0=Monday, 6=Sunday

        # Skip weekends
        if weekday >= 5:  # Saturday or Sunday
            return False

        # Trading hours: 9:30-11:30, 13:00-15:00 (Beijing time)
        hour = now.hour
        minute = now.minute

        morning_start = (
            (hour == 9 and minute >= 30)
            or (hour == 10)
            or (hour == 11 and minute <= 30)
        )
        afternoon_start = hour >= 13 and hour < 15

        return morning_start or afternoon_start

    def __repr__(self):
        return f"<RealtimeStockData(symbol='{self.symbol}', price={self.price}, timestamp='{self.timestamp}')>"


class RealtimeDataCache:
    """
    Cache management for realtime stock data.

    This class provides methods for managing the realtime data cache,
    including cleanup of expired records and cache statistics.
    """

    def __init__(self, db_session):
        """
        Initialize cache manager.

        Args:
            db_session: Database session
        """
        self.db = db_session

    def cleanup_expired_cache(self) -> int:
        """
        Remove expired cache entries.

        Returns:
            Number of records deleted
        """
        cutoff_time = datetime.utcnow() - timedelta(
            hours=1
        )  # Remove data older than 1 hour

        deleted_count = (
            self.db.query(RealtimeStockData)
            .filter(RealtimeStockData.timestamp < cutoff_time)
            .delete()
        )

        self.db.commit()
        return deleted_count

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        total_records = self.db.query(RealtimeStockData).count()
        valid_records = (
            self.db.query(RealtimeStockData)
            .filter(
                RealtimeStockData.timestamp > datetime.utcnow() - timedelta(minutes=5)
            )
            .count()
        )

        unique_symbols = self.db.query(RealtimeStockData.symbol).distinct().count()

        return {
            "total_records": total_records,
            "valid_records": valid_records,
            "unique_symbols": unique_symbols,
            "cache_hit_ratio": (
                (valid_records / total_records * 100) if total_records > 0 else 0
            ),
        }
