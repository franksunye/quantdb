"""
Financial data API routes for QuantDB API service.

This module provides API endpoints for retrieving financial summary and indicators data
with intelligent caching strategies.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.cache.akshare_adapter import AKShareAdapter

# Import core modules
from core.database.connection import get_db
from core.services.financial_data_service import FinancialDataService
from core.utils.logger import logger

# Create router
router = APIRouter(prefix="/api/v1/financial", tags=["financial"])


# Request/Response models
class BatchFinancialRequest(BaseModel):
    """Request model for batch financial data."""

    symbols: List[str]
    data_type: str = "summary"  # "summary" or "indicators"
    force_refresh: bool = False


class FinancialQuarterData(BaseModel):
    """Model for quarterly financial data."""

    period: str
    report_type: str
    net_profit: Optional[float] = None
    total_revenue: Optional[float] = None
    operating_cost: Optional[float] = None
    gross_profit: Optional[float] = None
    operating_profit: Optional[float] = None
    total_assets: Optional[float] = None
    total_liabilities: Optional[float] = None
    shareholders_equity: Optional[float] = None
    operating_cash_flow: Optional[float] = None
    roe: Optional[float] = None
    roa: Optional[float] = None
    gross_margin: Optional[float] = None
    net_margin: Optional[float] = None


class FinancialIndicatorData(BaseModel):
    """Model for financial indicator data."""

    period: str
    eps: Optional[float] = None
    pe_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None
    ps_ratio: Optional[float] = None
    revenue_growth: Optional[float] = None
    profit_growth: Optional[float] = None
    eps_growth: Optional[float] = None
    debt_to_equity: Optional[float] = None
    current_ratio: Optional[float] = None
    quick_ratio: Optional[float] = None
    asset_turnover: Optional[float] = None
    inventory_turnover: Optional[float] = None
    receivables_turnover: Optional[float] = None


class FinancialSummaryResponse(BaseModel):
    """Response model for financial summary data."""

    symbol: str
    data_type: str
    quarters: List[FinancialQuarterData]
    count: int
    cache_hit: bool
    timestamp: str
    metadata: Dict[str, Any]


class FinancialIndicatorsResponse(BaseModel):
    """Response model for financial indicators data."""

    symbol: str
    data_type: str
    periods: List[FinancialIndicatorData]
    count: int
    cache_hit: bool
    raw_data_shape: Optional[str] = None
    timestamp: str
    metadata: Dict[str, Any]


class BatchFinancialResponse(BaseModel):
    """Response model for batch financial data."""

    data: Dict[str, Dict[str, Any]]
    metadata: Dict[str, Any]


# Dependencies
def get_akshare_adapter(db: Session = Depends(get_db)):
    """Get AKShare adapter instance."""
    return AKShareAdapter(db)


def get_financial_service(
    db: Session = Depends(get_db), akshare_adapter: AKShareAdapter = Depends(get_akshare_adapter)
):
    """Get financial data service instance."""
    return FinancialDataService(db, akshare_adapter)


# API Endpoints
@router.get("/{symbol}/summary", response_model=FinancialSummaryResponse)
async def get_financial_summary(
    symbol: str,
    force_refresh: bool = Query(False, description="Force refresh data from source"),
    financial_service: FinancialDataService = Depends(get_financial_service),
):
    """
    Get financial summary data for a specific stock symbol.

    Args:
        symbol: Stock symbol (e.g., '000001', '600000')
        force_refresh: If True, bypass cache and fetch fresh data

    Returns:
        Financial summary data with quarterly metrics
    """
    try:
        logger.info(f"API request for financial summary: {symbol}")

        # Validate symbol format
        if not symbol or len(symbol.strip()) == 0:
            raise HTTPException(status_code=400, detail="Symbol cannot be empty")

        # Get financial summary data
        data = financial_service.get_financial_summary(symbol.strip(), force_refresh)

        # Check for errors
        if "error" in data:
            raise HTTPException(status_code=404, detail=data["error"])

        # Build response
        response = FinancialSummaryResponse(
            symbol=data["symbol"],
            data_type=data["data_type"],
            quarters=[FinancialQuarterData(**quarter) for quarter in data["quarters"]],
            count=data["count"],
            cache_hit=data.get("cache_hit", False),
            timestamp=data["timestamp"],
            metadata={
                "data_source": "akshare",
                "cache_strategy": "daily_ttl",
                "response_time_ms": 0,  # Will be set by middleware
            },
        )

        logger.info(f"Successfully returned financial summary for {symbol}")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting financial summary for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/{symbol}/indicators", response_model=FinancialIndicatorsResponse)
async def get_financial_indicators(
    symbol: str,
    force_refresh: bool = Query(False, description="Force refresh data from source"),
    financial_service: FinancialDataService = Depends(get_financial_service),
):
    """
    Get financial indicators data for a specific stock symbol.

    Args:
        symbol: Stock symbol (e.g., '000001', '600000')
        force_refresh: If True, bypass cache and fetch fresh data

    Returns:
        Financial indicators data with detailed metrics
    """
    try:
        logger.info(f"API request for financial indicators: {symbol}")

        # Validate symbol format
        if not symbol or len(symbol.strip()) == 0:
            raise HTTPException(status_code=400, detail="Symbol cannot be empty")

        # Get financial indicators data
        data = financial_service.get_financial_indicators(symbol.strip(), force_refresh)

        # Check for errors
        if "error" in data:
            raise HTTPException(status_code=404, detail=data["error"])

        # Build response
        response = FinancialIndicatorsResponse(
            symbol=data["symbol"],
            data_type=data["data_type"],
            periods=[FinancialIndicatorData(**period) for period in data["periods"]],
            count=data["count"],
            cache_hit=data.get("cache_hit", False),
            raw_data_shape=data.get("raw_data_shape"),
            timestamp=data["timestamp"],
            metadata={
                "data_source": "akshare",
                "cache_strategy": "weekly_ttl",
                "response_time_ms": 0,  # Will be set by middleware
            },
        )

        logger.info(f"Successfully returned financial indicators for {symbol}")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting financial indicators for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/{symbol}", response_model=FinancialSummaryResponse)
async def get_financial_data(
    symbol: str,
    force_refresh: bool = Query(False, description="Force refresh data from source"),
    financial_service: FinancialDataService = Depends(get_financial_service),
):
    """
    Get financial data for a specific stock symbol (defaults to summary).

    This is a convenience endpoint that returns financial summary data.
    For detailed indicators, use the /indicators endpoint.

    Args:
        symbol: Stock symbol (e.g., '000001', '600000')
        force_refresh: If True, bypass cache and fetch fresh data

    Returns:
        Financial summary data with quarterly metrics
    """
    return await get_financial_summary(symbol, force_refresh, financial_service)


@router.post("/batch", response_model=BatchFinancialResponse)
async def get_batch_financial_data(
    request: BatchFinancialRequest,
    financial_service: FinancialDataService = Depends(get_financial_service),
):
    """
    Get financial data for multiple stocks in a single request.

    Args:
        request: Batch request with list of symbols and data type

    Returns:
        Dictionary mapping symbols to their financial data
    """
    try:
        logger.info(
            f"API request for batch financial {request.data_type}: {len(request.symbols)} symbols"
        )

        # Validate request
        if not request.symbols:
            raise HTTPException(status_code=400, detail="Symbols list cannot be empty")

        if len(request.symbols) > 50:
            raise HTTPException(status_code=400, detail="Maximum 50 symbols per batch request")

        if request.data_type not in ["summary", "indicators"]:
            raise HTTPException(
                status_code=400, detail="data_type must be 'summary' or 'indicators'"
            )

        # Get batch financial data
        data = financial_service.get_financial_data_batch(
            request.symbols, request.data_type, request.force_refresh
        )

        # Build response
        response = BatchFinancialResponse(
            data=data,
            metadata={
                "symbols_requested": len(request.symbols),
                "symbols_returned": len(data),
                "data_type": request.data_type,
                "data_source": "akshare",
                "timestamp": (
                    data.get(list(data.keys())[0], {}).get("timestamp", "") if data else ""
                ),
                "response_time_ms": 0,  # Will be set by middleware
            },
        )

        logger.info(
            f"Successfully returned batch financial {request.data_type} for {len(data)} symbols"
        )
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting batch financial {request.data_type}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
