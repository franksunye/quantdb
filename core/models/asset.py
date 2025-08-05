"""
Asset data model for QuantDB core
"""
import enum
from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, Text, Boolean, DateTime, Enum, JSON, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database.connection import Base


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

    # Basic information fields
    industry = Column(String)  # Industry classification
    concept = Column(String)   # Concept classification
    listing_date = Column(Date)  # Listing date

    # Market data fields
    total_shares = Column(BigInteger)  # Total shares outstanding
    circulating_shares = Column(BigInteger)  # Circulating shares
    market_cap = Column(BigInteger)  # Market capitalization

    # Financial indicator fields
    pe_ratio = Column(Float)  # Price-to-earnings ratio
    pb_ratio = Column(Float)  # Price-to-book ratio
    roe = Column(Float)       # Return on equity

    # Metadata
    last_updated = Column(DateTime, default=func.now())
    data_source = Column(String, default="akshare")

    # Relationships
    daily_data = relationship("DailyStockData", back_populates="asset")
    intraday_data = relationship("IntradayStockData", back_populates="asset")
