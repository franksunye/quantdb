"""
Index data models for QuantDB.

This module defines the database models for storing index data
with appropriate caching and indexing strategies.
"""

from datetime import date, datetime, timedelta
from typing import Any, Dict

from sqlalchemy import Boolean, Column, Date, DateTime, Float, ForeignKey, Index, Integer, String
from sqlalchemy.orm import relationship

from ..database.connection import Base


class IndexData(Base):
    """
    Model for storing historical index data.

    This table stores daily index price data with appropriate indexing
    for efficient querying by symbol and date range.
    """

    __tablename__ = "index_data"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Index identification
    symbol = Column(
        String(20), nullable=False, index=True, comment="Index symbol (e.g., '000001', '399001')"
    )
    name = Column(String(100), nullable=True, comment="Index name")

    # Date information
    date = Column(Date, nullable=False, index=True, comment="Trading date")

    # Price information
    open_price = Column(Float, nullable=True, comment="Opening price")
    high_price = Column(Float, nullable=True, comment="Highest price of the day")
    low_price = Column(Float, nullable=True, comment="Lowest price of the day")
    close_price = Column(Float, nullable=False, comment="Closing price")

    # Volume and turnover information
    volume = Column(Float, nullable=True, comment="Trading volume")
    turnover = Column(Float, nullable=True, comment="Trading turnover")

    # Change information
    change = Column(Float, nullable=True, comment="Price change amount")
    pct_change = Column(Float, nullable=True, comment="Price change percentage")
    amplitude = Column(Float, nullable=True, comment="Price amplitude percentage")

    # Metadata
    created_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, comment="Record creation time"
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        comment="Record update time",
    )

    # Indexes for efficient querying
    __table_args__ = (
        Index("idx_index_symbol_date", "symbol", "date"),
        Index("idx_index_date", "date"),
    )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert model instance to dictionary.

        Returns:
            Dictionary representation of the index data
        """
        return {
            "symbol": self.symbol,
            "name": self.name,
            "date": self.date.isoformat() if self.date else None,
            "open": self.open_price,
            "high": self.high_price,
            "low": self.low_price,
            "close": self.close_price,
            "volume": self.volume,
            "turnover": self.turnover,
            "change": self.change,
            "pct_change": self.pct_change,
            "amplitude": self.amplitude,
        }


class RealtimeIndexData(Base):
    """
    Model for storing realtime index data.

    This table stores current index prices and related metrics with
    a short TTL for caching purposes (1-5 minutes).
    """

    __tablename__ = "realtime_index_data"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Index identification
    symbol = Column(String(20), nullable=False, index=True, comment="Index symbol")
    name = Column(String(100), nullable=False, comment="Index name")

    # Basic price information
    price = Column(Float, nullable=False, comment="Current price")
    open_price = Column(Float, nullable=True, comment="Opening price")
    high_price = Column(Float, nullable=True, comment="Highest price of the day")
    low_price = Column(Float, nullable=True, comment="Lowest price of the day")
    prev_close = Column(Float, nullable=True, comment="Previous closing price")

    # Change information
    change = Column(Float, nullable=True, comment="Price change amount")
    pct_change = Column(Float, nullable=True, comment="Price change percentage")
    amplitude = Column(Float, nullable=True, comment="Price amplitude percentage")

    # Volume information
    volume = Column(Float, nullable=True, comment="Trading volume")
    turnover = Column(Float, nullable=True, comment="Trading turnover")

    # Timestamp information
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, comment="Data timestamp")
    created_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, comment="Record creation time"
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        comment="Record update time",
    )

    # Cache metadata
    cache_ttl_minutes = Column(Integer, nullable=False, default=5, comment="Cache TTL in minutes")
    is_trading_hours = Column(
        Boolean,
        nullable=False,
        default=True,
        comment="Whether data was fetched during trading hours",
    )

    # Indexes for efficient querying
    __table_args__ = (
        Index("idx_realtime_index_symbol", "symbol"),
        Index("idx_realtime_index_timestamp", "timestamp"),
    )

    def is_cache_valid(self) -> bool:
        """
        Check if the cached data is still valid.

        Returns:
            True if cache is valid, False otherwise
        """
        if not self.timestamp:
            return False

        cache_duration = timedelta(minutes=self.cache_ttl_minutes)
        return datetime.utcnow() - self.timestamp < cache_duration

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert model instance to dictionary.

        Returns:
            Dictionary representation of the realtime index data
        """
        return {
            "symbol": self.symbol,
            "name": self.name,
            "price": self.price,
            "open": self.open_price,
            "high": self.high_price,
            "low": self.low_price,
            "prev_close": self.prev_close,
            "change": self.change,
            "pct_change": self.pct_change,
            "amplitude": self.amplitude,
            "volume": self.volume,
            "turnover": self.turnover,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "is_trading_hours": self.is_trading_hours,
            "cache_hit": True,
        }


class IndexListCache(Base):
    """
    Index list cache model for daily index list data.

    This model stores the complete index list with classification
    and is updated daily to ensure fresh data.
    """

    __tablename__ = "index_list_cache"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False, index=True, comment="Index symbol")
    name = Column(String(100), nullable=False, comment="Index name")
    category = Column(String(50), nullable=False, index=True, comment="Index category")

    # Latest market data (optional)
    price = Column(Float, comment="Latest price")
    pct_change = Column(Float, comment="Percentage change")
    change = Column(Float, comment="Price change")
    volume = Column(Float, comment="Trading volume")
    turnover = Column(Float, comment="Trading turnover")

    # Cache metadata
    cache_date = Column(
        Date, nullable=False, default=date.today, comment="Date when data was cached"
    )
    created_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, comment="Record creation time"
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        comment="Record update time",
    )
    is_active = Column(
        Boolean, nullable=False, default=True, comment="Whether the index is actively tracked"
    )

    # Indexes for efficient querying
    __table_args__ = (
        Index("idx_index_list_symbol", "symbol"),
        Index("idx_index_list_category", "category"),
        Index("idx_index_list_cache_date", "cache_date"),
    )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert model instance to dictionary.

        Returns:
            Dictionary representation of the index data
        """
        return {
            "symbol": self.symbol,
            "name": self.name,
            "category": self.category,
            "price": self.price,
            "pct_change": self.pct_change,
            "change": self.change,
            "volume": self.volume,
            "turnover": self.turnover,
            "cache_date": self.cache_date.isoformat() if self.cache_date else None,
            "is_active": self.is_active,
        }


class IndexListCacheManager(Base):
    """
    Manager for index list cache operations.

    This model tracks cache status and manages cache lifecycle.
    """

    __tablename__ = "index_list_cache_manager"

    id = Column(Integer, primary_key=True, index=True)
    cache_date = Column(Date, nullable=False, default=date.today, comment="Cache date")
    total_count = Column(
        Integer, nullable=False, default=0, comment="Total number of indexes cached"
    )
    created_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, comment="Cache creation time"
    )
    is_current = Column(
        Boolean, nullable=False, default=True, comment="Whether this is the current cache"
    )

    def is_cache_fresh(self) -> bool:
        """
        Check if the cache is fresh (same day).

        Returns:
            True if cache is fresh, False otherwise
        """
        return self.cache_date == date.today()
