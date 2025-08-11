"""
Monitoring API routes for QuantDB API service.

This module provides API endpoints for system monitoring and metrics.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

# Import API schemas
from api.schemas import SystemMetricsSchema

# Import core modules
from core.database.connection import get_db
from core.models.system_metrics import DataCoverage, RequestLog, SystemMetrics
from core.utils.logger import logger

# Create router
router = APIRouter(
    prefix="/monitoring",
    tags=["Monitoring"],
    responses={404: {"description": "Not found"}},
)


@router.get("/metrics", response_model=Dict[str, Any])
async def get_system_metrics(db: Session = Depends(get_db)):
    """
    Get current system metrics
    """
    try:
        # Get the latest system metrics
        latest_metrics = (
            db.query(SystemMetrics).order_by(SystemMetrics.timestamp.desc()).first()
        )

        if not latest_metrics:
            # If no metrics exist, create default ones
            return SystemMetricsSchema(
                total_symbols=0,
                total_records=0,
                db_size_mb=0.0,
                avg_response_time_ms=0.0,
                cache_hit_rate=0.0,
                akshare_requests_today=0,
                requests_today=0,
                active_symbols_today=0,
                performance_improvement=0.0,
                cost_savings=0.0,
            )

        return SystemMetricsSchema(
            total_symbols=latest_metrics.total_symbols or 0,
            total_records=latest_metrics.total_records or 0,
            db_size_mb=latest_metrics.db_size_mb or 0.0,
            avg_response_time_ms=latest_metrics.avg_response_time_ms or 0.0,
            cache_hit_rate=latest_metrics.cache_hit_rate or 0.0,
            akshare_requests_today=latest_metrics.akshare_requests_today or 0,
            requests_today=latest_metrics.requests_today or 0,
            active_symbols_today=latest_metrics.active_symbols_today or 0,
            performance_improvement=latest_metrics.performance_improvement or 0.0,
            cost_savings=latest_metrics.cost_savings or 0.0,
        )

    except Exception as e:
        logger.error(f"Error getting system metrics: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error getting system metrics: {str(e)}"
        )


@router.get("/requests")
async def get_request_logs(
    limit: int = Query(
        100, ge=1, le=1000, description="Maximum number of records to return"
    ),
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    start_time: Optional[datetime] = Query(None, description="Start time filter"),
    end_time: Optional[datetime] = Query(None, description="End time filter"),
    db: Session = Depends(get_db),
):
    """
    Get request logs with filtering

    - **limit**: Maximum number of records to return
    - **symbol**: Filter by symbol
    - **start_time**: Start time filter
    - **end_time**: End time filter
    """
    try:
        # Build query
        query = db.query(RequestLog)

        # Apply filters
        if symbol:
            query = query.filter(RequestLog.symbol == symbol)
        if start_time:
            query = query.filter(RequestLog.timestamp >= start_time)
        if end_time:
            query = query.filter(RequestLog.timestamp <= end_time)

        # Order by timestamp descending and limit
        logs = query.order_by(RequestLog.timestamp.desc()).limit(limit).all()

        # Convert to response format
        result = []
        for log in logs:
            result.append(
                {
                    "id": log.id,
                    "timestamp": log.timestamp.isoformat() if log.timestamp else None,
                    "symbol": log.symbol,
                    "start_date": log.start_date,
                    "end_date": log.end_date,
                    "endpoint": log.endpoint,
                    "response_time_ms": log.response_time_ms,
                    "status_code": log.status_code,
                    "record_count": log.record_count,
                    "cache_hit": log.cache_hit,
                    "akshare_called": log.akshare_called,
                    "cache_hit_ratio": log.cache_hit_ratio,
                    "user_agent": log.user_agent,
                    "ip_address": log.ip_address,
                }
            )

        return {
            "logs": result,
            "count": len(result),
            "filters": {
                "symbol": symbol,
                "start_time": start_time.isoformat() if start_time else None,
                "end_time": end_time.isoformat() if end_time else None,
                "limit": limit,
            },
        }

    except Exception as e:
        logger.error(f"Error getting request logs: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error getting request logs: {str(e)}"
        )


@router.get("/coverage")
async def get_data_coverage(
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    db: Session = Depends(get_db),
):
    """
    Get data coverage information

    - **symbol**: Optional symbol filter
    """
    try:
        # Build query
        query = db.query(DataCoverage)

        # Apply symbol filter if provided
        if symbol:
            query = query.filter(DataCoverage.symbol == symbol)

        # Get coverage data
        coverage_data = query.order_by(DataCoverage.last_accessed.desc()).all()

        # Convert to response format
        result = []
        for coverage in coverage_data:
            result.append(
                {
                    "symbol": coverage.symbol,
                    "earliest_date": coverage.earliest_date,
                    "latest_date": coverage.latest_date,
                    "total_records": coverage.total_records,
                    "first_requested": (
                        coverage.first_requested.isoformat()
                        if coverage.first_requested
                        else None
                    ),
                    "last_accessed": (
                        coverage.last_accessed.isoformat()
                        if coverage.last_accessed
                        else None
                    ),
                    "access_count": coverage.access_count,
                    "last_updated": (
                        coverage.last_updated.isoformat()
                        if coverage.last_updated
                        else None
                    ),
                }
            )

        return {"coverage": result, "count": len(result), "symbol_filter": symbol}

    except Exception as e:
        logger.error(f"Error getting data coverage: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error getting data coverage: {str(e)}"
        )


@router.get("/performance")
async def get_performance_stats(
    hours: int = Query(24, ge=1, le=168, description="Number of hours to analyze"),
    db: Session = Depends(get_db),
):
    """
    Get performance statistics for the specified time period

    - **hours**: Number of hours to analyze (1-168)
    """
    try:
        # Calculate time range
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)

        # Query request logs for the time period
        logs = (
            db.query(RequestLog)
            .filter(
                RequestLog.timestamp >= start_time, RequestLog.timestamp <= end_time
            )
            .all()
        )

        if not logs:
            return {
                "period": {
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                    "hours": hours,
                },
                "stats": {
                    "total_requests": 0,
                    "avg_response_time_ms": 0.0,
                    "cache_hit_rate": 0.0,
                    "akshare_requests": 0,
                    "unique_symbols": 0,
                    "total_records_served": 0,
                },
            }

        # Calculate statistics
        total_requests = len(logs)
        avg_response_time = (
            sum(log.response_time_ms or 0 for log in logs) / total_requests
        )
        cache_hits = sum(1 for log in logs if log.cache_hit)
        cache_hit_rate = cache_hits / total_requests if total_requests > 0 else 0
        akshare_requests = sum(1 for log in logs if log.akshare_called)
        unique_symbols = len(set(log.symbol for log in logs if log.symbol))
        total_records = sum(log.record_count or 0 for log in logs)

        return {
            "period": {
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "hours": hours,
            },
            "stats": {
                "total_requests": total_requests,
                "avg_response_time_ms": round(avg_response_time, 2),
                "cache_hit_rate": round(cache_hit_rate, 4),
                "akshare_requests": akshare_requests,
                "unique_symbols": unique_symbols,
                "total_records_served": total_records,
            },
        }

    except Exception as e:
        logger.error(f"Error getting performance stats: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error getting performance stats: {str(e)}"
        )
