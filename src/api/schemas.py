"""
Pydantic schemas for the API
"""
from typing import List, Optional, Dict, Any, Union
from datetime import date, datetime
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict



# Asset schemas
class AssetBase(BaseModel):
    """Base schema for Asset"""
    symbol: str
    name: str
    asset_type: str
    exchange: str
    currency: str

class AssetCreate(AssetBase):
    """Schema for creating an Asset"""
    isin: str

class Asset(AssetBase):
    """Schema for returning an Asset"""
    asset_id: int
    isin: str

    model_config = ConfigDict(from_attributes=True)

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


