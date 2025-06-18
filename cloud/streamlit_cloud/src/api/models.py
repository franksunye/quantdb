"""
SQLAlchemy models for the API
"""
import enum
import json
from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, Text, Boolean, DateTime, Enum, JSON, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.sql import func

from src.api.database import Base



class Asset(Base):
    """Asset model representing stocks, indices, etc."""
    __tablename__ = "assets"
    __table_args__ = {'extend_existing': True}

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

    # Relationships - commented out to avoid circular import issues in cloud version
    # daily_data = relationship("DailyStockData", back_populates="asset", lazy="dynamic")
    # intraday_data = relationship("IntradayStockData", back_populates="asset", lazy="dynamic")

class DailyStockData(Base):
    """Daily stock data model - 统一的股票数据模型"""
    __tablename__ = "daily_stock_data"
    __table_args__ = {'extend_existing': True}

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

    # Relationships - commented out to avoid circular import issues in cloud version
    # asset = relationship("Asset", back_populates="daily_data")

class IntradayStockData(Base):
    """Intraday stock data model"""
    __tablename__ = "intraday_stock_data"
    __table_args__ = {'extend_existing': True}

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

    # Relationships - commented out to avoid circular import issues in cloud version
    # asset = relationship("Asset", back_populates="intraday_data")

# 监控相关模型
class RequestLog(Base):
    """API请求日志"""
    __tablename__ = "request_logs"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    # 请求信息
    symbol = Column(String(10), index=True)
    start_date = Column(String(8))
    end_date = Column(String(8))
    endpoint = Column(String(100))

    # 响应信息
    response_time_ms = Column(Float)  # 响应时间(毫秒)
    status_code = Column(Integer)
    record_count = Column(Integer)  # 返回记录数

    # 缓存信息
    cache_hit = Column(Boolean, default=False)  # 是否缓存命中
    akshare_called = Column(Boolean, default=False)  # 是否调用了AKShare
    cache_hit_ratio = Column(Float)  # 缓存命中比例(0-1)

    # 用户信息
    user_agent = Column(String(500))
    ip_address = Column(String(45))

class DataCoverage(Base):
    """数据覆盖情况统计"""
    __tablename__ = "data_coverage"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(10), unique=True, index=True)

    # 数据范围
    earliest_date = Column(String(8))  # 最早数据日期
    latest_date = Column(String(8))    # 最新数据日期
    total_records = Column(Integer)    # 总记录数

    # 统计信息
    first_requested = Column(DateTime(timezone=True))  # 首次请求时间
    last_accessed = Column(DateTime(timezone=True))    # 最后访问时间
    access_count = Column(Integer, default=0)          # 访问次数

    # 更新信息
    last_updated = Column(DateTime(timezone=True), server_default=func.now())

class SystemMetrics(Base):
    """系统指标快照"""
    __tablename__ = "system_metrics"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    # 数据库统计
    total_symbols = Column(Integer)      # 总股票数量
    total_records = Column(Integer)      # 总数据记录数
    db_size_mb = Column(Float)          # 数据库大小(MB)

    # 性能统计
    avg_response_time_ms = Column(Float)  # 平均响应时间
    cache_hit_rate = Column(Float)        # 缓存命中率
    akshare_requests_today = Column(Integer)  # 今日AKShare请求数

    # 使用统计
    requests_today = Column(Integer)      # 今日总请求数
    active_symbols_today = Column(Integer)  # 今日活跃股票数

    # 计算字段
    performance_improvement = Column(Float)  # 性能提升比例
    cost_savings = Column(Float)            # 成本节省(请求数减少)


