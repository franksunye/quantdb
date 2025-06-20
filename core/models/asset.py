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

    # 新增基本信息字段
    industry = Column(String)  # 行业分类
    concept = Column(String)   # 概念分类
    listing_date = Column(Date)  # 上市日期

    # 新增市场数据字段
    total_shares = Column(BigInteger)  # 总股本
    circulating_shares = Column(BigInteger)  # 流通股
    market_cap = Column(BigInteger)  # 总市值

    # 新增财务指标字段
    pe_ratio = Column(Float)  # 市盈率
    pb_ratio = Column(Float)  # 市净率
    roe = Column(Float)       # 净资产收益率

    # 元数据
    last_updated = Column(DateTime, default=func.now())
    data_source = Column(String, default="akshare")

    # Relationships
    daily_data = relationship("DailyStockData", back_populates="asset")
    intraday_data = relationship("IntradayStockData", back_populates="asset")
