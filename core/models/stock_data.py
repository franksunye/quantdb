"""
Stock data models for QuantDB core
"""

from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import relationship

from ..database.connection import Base


class DailyStockData(Base):
    """Daily stock data model - unified stock data model"""

    __tablename__ = "daily_stock_data"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.asset_id"))
    trade_date = Column(Date)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Integer)
    adjusted_close = Column(Float)  # 新增字段，从Price模型迁移
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
