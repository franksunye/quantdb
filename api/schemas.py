"""
API Schemas for QuantDB API service.

This module contains Pydantic models for request/response validation.
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class HistoricalDataPoint(BaseModel):
    """Single historical data point"""

    date: Optional[datetime] = Field(None, description="Trading date")
    open: Optional[float] = Field(None, description="Opening price")
    high: Optional[float] = Field(None, description="Highest price")
    low: Optional[float] = Field(None, description="Lowest price")
    close: Optional[float] = Field(None, description="Closing price")
    volume: Optional[int] = Field(None, description="Trading volume")
    turnover: Optional[float] = Field(None, description="Trading turnover")
    amplitude: Optional[float] = Field(None, description="Price amplitude")
    pct_change: Optional[float] = Field(None, description="Percentage change")
    change: Optional[float] = Field(None, description="Price change")
    turnover_rate: Optional[float] = Field(None, description="Turnover rate")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat() if v else None}


class HistoricalDataResponse(BaseModel):
    """Historical data response"""

    symbol: str = Field(..., description="Stock symbol")
    name: str = Field(..., description="Stock name")
    start_date: Optional[str] = Field(None, description="Start date")
    end_date: Optional[str] = Field(None, description="End date")
    adjust: str = Field("", description="Price adjustment method")
    data: List[HistoricalDataPoint] = Field(..., description="Historical data points")
    metadata: Dict[str, Any] = Field(..., description="Response metadata")


class AssetInfo(BaseModel):
    """Asset information"""

    asset_id: int = Field(..., description="Asset ID")
    symbol: str = Field(..., description="Stock symbol")
    name: str = Field(..., description="Stock name")
    isin: str = Field(..., description="ISIN code")
    asset_type: str = Field(..., description="Asset type")
    exchange: str = Field(..., description="Exchange")
    currency: str = Field(..., description="Currency")
    industry: Optional[str] = Field(None, description="Industry")
    concept: Optional[str] = Field(None, description="Concept")
    listing_date: Optional[date] = Field(None, description="Listing date")
    total_shares: Optional[int] = Field(None, description="Total shares")
    circulating_shares: Optional[int] = Field(None, description="Circulating shares")
    market_cap: Optional[int] = Field(None, description="Market capitalization")
    pe_ratio: Optional[float] = Field(None, description="P/E ratio")
    pb_ratio: Optional[float] = Field(None, description="P/B ratio")
    roe: Optional[float] = Field(None, description="Return on equity")
    last_updated: Optional[datetime] = Field(None, description="Last updated")
    data_source: Optional[str] = Field(None, description="Data source")

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
            date: lambda v: v.isoformat() if v else None,
        }


class AssetResponse(BaseModel):
    """Asset response with metadata"""

    asset: AssetInfo = Field(..., description="Asset information")
    metadata: Dict[str, Any] = Field(..., description="Response metadata")


class CacheInfo(BaseModel):
    """Cache information"""

    cache_hit: bool = Field(..., description="Whether cache was hit")
    akshare_called: bool = Field(..., description="Whether AKShare was called")
    cache_hit_ratio: float = Field(..., description="Cache hit ratio")
    cached_days: int = Field(..., description="Number of cached days")
    total_trading_days: int = Field(..., description="Total trading days")
    response_time_ms: float = Field(..., description="Response time in milliseconds")


class CacheStatusResponse(BaseModel):
    """Cache status response"""

    symbol: Optional[str] = Field(None, description="Stock symbol")
    start_date: Optional[str] = Field(None, description="Start date")
    end_date: Optional[str] = Field(None, description="End date")
    coverage: Optional[Dict[str, Any]] = Field(None, description="Coverage information")
    total_assets: Optional[int] = Field(None, description="Total assets")
    total_data_points: Optional[int] = Field(None, description="Total data points")
    date_range: Optional[Dict[str, str]] = Field(None, description="Date range")
    top_assets: Optional[List[Dict[str, Any]]] = Field(None, description="Top assets")


class SystemMetrics(BaseModel):
    """System metrics"""

    total_symbols: int = Field(..., description="Total number of symbols")
    total_records: int = Field(..., description="Total number of records")
    db_size_mb: float = Field(..., description="Database size in MB")
    avg_response_time_ms: float = Field(..., description="Average response time")
    cache_hit_rate: float = Field(..., description="Cache hit rate")
    akshare_requests_today: int = Field(..., description="AKShare requests today")
    requests_today: int = Field(..., description="Total requests today")
    active_symbols_today: int = Field(..., description="Active symbols today")
    performance_improvement: float = Field(..., description="Performance improvement")
    cost_savings: float = Field(..., description="Cost savings")


class ErrorResponse(BaseModel):
    """Error response"""

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    timestamp: float = Field(..., description="Error timestamp")
    details: Optional[Dict[str, Any]] = Field(None, description="Error details")


class HealthResponse(BaseModel):
    """Health check response"""

    status: str = Field(..., description="Service status")
    timestamp: float = Field(..., description="Check timestamp")
    service: str = Field(..., description="Service name")
    version: Optional[str] = Field(None, description="Service version")
