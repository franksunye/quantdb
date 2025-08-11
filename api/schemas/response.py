"""
Pydantic schemas for the API
"""

from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field


# Asset schemas
class AssetBase(BaseModel):
    """Base schema for Asset"""

    symbol: str
    name: str
    asset_type: str
    exchange: str
    currency: str

    # 新增基本信息字段
    industry: Optional[str] = None
    concept: Optional[str] = None
    listing_date: Optional[date] = None

    # 新增市场数据字段
    total_shares: Optional[int] = None
    circulating_shares: Optional[int] = None
    market_cap: Optional[int] = None

    # 新增财务指标字段
    pe_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None
    roe: Optional[float] = None

    # 元数据
    last_updated: Optional[datetime] = None
    data_source: Optional[str] = None


class AssetCreate(AssetBase):
    """Schema for creating an Asset"""

    isin: str


class Asset(AssetBase):
    """Schema for returning an Asset"""

    asset_id: int
    isin: str

    model_config = ConfigDict(from_attributes=True)


# Asset aliases for backward compatibility
AssetInfo = Asset  # AssetInfo is an alias for Asset


# Asset response with cache metadata
class AssetWithMetadata(BaseModel):
    """Schema for returning an Asset with cache metadata"""

    asset: Asset
    metadata: Dict[str, Any]


# AssetResponse alias for backward compatibility
AssetResponse = AssetWithMetadata


# Daily stock data schemas
class DailyStockDataBase(BaseModel):
    """Base schema for DailyStockData"""

    trade_date: date
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    close: Optional[float] = None
    volume: Optional[int] = None
    adjusted_close: Optional[float] = None  # 新增字段，从Price模型迁移
    turnover: Optional[float] = None
    amplitude: Optional[float] = None
    pct_change: Optional[float] = None
    change: Optional[float] = None
    turnover_rate: Optional[float] = None


class DailyStockDataCreate(DailyStockDataBase):
    """Schema for creating DailyStockData"""

    asset_id: int


class DailyStockData(DailyStockDataBase):
    """Schema for returning DailyStockData"""

    id: int
    asset_id: int

    model_config = ConfigDict(from_attributes=True)


# Intraday stock data schemas
class IntradayStockDataBase(BaseModel):
    """Base schema for IntradayStockData"""

    capture_time: datetime
    trade_date: date
    latest_price: Optional[float] = None
    pct_change: Optional[float] = None
    change: Optional[float] = None
    volume: Optional[int] = None
    turnover: Optional[float] = None
    amplitude: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    open: Optional[float] = None
    prev_close: Optional[float] = None
    volume_ratio: Optional[float] = None
    turnover_rate: Optional[float] = None
    pe_ratio_dynamic: Optional[float] = None
    pb_ratio: Optional[float] = None
    total_market_cap: Optional[float] = None
    circulating_market_cap: Optional[float] = None
    speed_of_increase: Optional[float] = None
    five_min_pct_change: Optional[float] = None
    sixty_day_pct_change: Optional[float] = None
    ytd_pct_change: Optional[float] = None
    is_final: Optional[bool] = False


class IntradayStockDataCreate(IntradayStockDataBase):
    """Schema for creating IntradayStockData"""

    asset_id: int


class IntradayStockData(IntradayStockDataBase):
    """Schema for returning IntradayStockData"""

    id: int
    asset_id: int

    model_config = ConfigDict(from_attributes=True)


# Historical data schemas
class HistoricalDataPoint(BaseModel):
    """Schema for a single historical data point"""

    date: Union[date, str]
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    close: Optional[float] = None
    volume: Optional[float] = None
    turnover: Optional[float] = None
    amplitude: Optional[float] = None
    pct_change: Optional[float] = None
    change: Optional[float] = None
    turnover_rate: Optional[float] = None


class HistoricalDataResponse(BaseModel):
    """Schema for historical data response"""

    symbol: str
    name: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    adjust: Optional[str] = None
    data: List[HistoricalDataPoint]
    metadata: Dict[str, Any]


# Health check schema
class HealthResponse(BaseModel):
    """Schema for health check response"""

    status: str
    timestamp: float
    service: str
    version: str


# System metrics schema
class SystemMetricsSchema(BaseModel):
    """Schema for system metrics response"""

    total_symbols: int = Field(default=0, description="Total number of symbols")
    total_records: int = Field(default=0, description="Total number of records")
    db_size_mb: float = Field(default=0.0, description="Database size in MB")
    avg_response_time_ms: float = Field(
        default=0.0, description="Average response time in milliseconds"
    )
    cache_hit_rate: float = Field(default=0.0, description="Cache hit rate (0-1)")
    akshare_requests_today: int = Field(default=0, description="AKShare requests today")
    requests_today: int = Field(default=0, description="Total requests today")
    active_symbols_today: int = Field(default=0, description="Active symbols today")
    performance_improvement: float = Field(default=0.0, description="Performance improvement ratio")
    cost_savings: float = Field(default=0.0, description="Cost savings (request reduction)")
