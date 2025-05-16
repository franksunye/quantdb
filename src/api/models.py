"""
SQLAlchemy models for the API
"""
import enum
import json
from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, Text, Boolean, DateTime, Enum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.ext.mutable import MutableDict

from src.api.database import Base


class ImportTaskStatus(enum.Enum):
    """Enum for import task status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class Asset(Base):
    """Asset model representing stocks, indices, etc."""
    __tablename__ = "assets"

    asset_id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, nullable=False)
    name = Column(String, nullable=False)
    isin = Column(String, nullable=False, unique=True)
    asset_type = Column(String, nullable=False)
    exchange = Column(String, nullable=False)
    currency = Column(String, nullable=False)

    # Relationships
    prices = relationship("Price", back_populates="asset")
    daily_data = relationship("DailyStockData", back_populates="asset")
    intraday_data = relationship("IntradayStockData", back_populates="asset")

class Price(Base):
    """Price model for historical price data"""
    __tablename__ = "prices"

    price_id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.asset_id"), nullable=False)
    date = Column(Date, nullable=False)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Float)
    adjusted_close = Column(Float)

    # Relationships
    asset = relationship("Asset", back_populates="prices")

class DailyStockData(Base):
    """Daily stock data model"""
    __tablename__ = "daily_stock_data"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.asset_id"))
    trade_date = Column(Date)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Integer)
    turnover = Column(Float)
    amplitude = Column(Float)
    pct_change = Column(Float)
    change = Column(Float)
    turnover_rate = Column(Float)

    # Relationships
    asset = relationship("Asset", back_populates="daily_data")

class IntradayStockData(Base):
    """Intraday stock data model"""
    __tablename__ = "intraday_stock_data"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.asset_id"))
    capture_time = Column(DateTime)
    trade_date = Column(Date)
    latest_price = Column(Float)
    pct_change = Column(Float)
    change = Column(Float)
    volume = Column(Integer)
    turnover = Column(Float)
    amplitude = Column(Float)
    high = Column(Float)
    low = Column(Float)
    open = Column(Float)
    prev_close = Column(Float)
    volume_ratio = Column(Float)
    turnover_rate = Column(Float)
    pe_ratio_dynamic = Column(Float)
    pb_ratio = Column(Float)
    total_market_cap = Column(Float)
    circulating_market_cap = Column(Float)
    speed_of_increase = Column(Float)
    five_min_pct_change = Column(Float)
    sixty_day_pct_change = Column(Float)
    ytd_pct_change = Column(Float)
    is_final = Column(Boolean)

    # Relationships
    asset = relationship("Asset", back_populates="intraday_data")


class ImportTask(Base):
    """Import task model for tracking data import tasks"""
    __tablename__ = "import_tasks"

    task_id = Column(Integer, primary_key=True, index=True)
    task_type = Column(String, nullable=False)
    parameters = Column(MutableDict.as_mutable(JSON), nullable=True)
    status = Column(String, nullable=False, default="pending")
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    result = Column(MutableDict.as_mutable(JSON), nullable=True)
    error_message = Column(Text, nullable=True)

    def __repr__(self):
        return f"<ImportTask(task_id={self.task_id}, task_type='{self.task_type}', status={self.status})>"
