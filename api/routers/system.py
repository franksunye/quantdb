"""
System API routes for QuantDB API service.

This module provides API endpoints for system information and health checks.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import time
import os
import psutil

# Import core modules
from core.database.connection import get_db, engine
from core.utils.config import is_development, is_production
from core.utils.logger import logger
from core.services.trading_calendar import get_trading_calendar

# Import API schemas
from ..schemas import HealthResponse

# Create router
router = APIRouter(
    prefix="/system",
    tags=["System"],
)


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint
    """
    return HealthResponse(
        status="healthy", timestamp=time.time(), service="quantdb-api", version="2.1.0"
    )


@router.get("/info")
async def get_system_info(db: Session = Depends(get_db)):
    """
    Get system information
    """
    try:
        # Get database info
        try:
            # Test database connection
            db.execute("SELECT 1")
            db_status = "connected"
            db_error = None
        except Exception as e:
            db_status = "error"
            db_error = str(e)

        # Get trading calendar info
        try:
            trading_calendar = get_trading_calendar()
            calendar_info = trading_calendar.get_calendar_info()
            calendar_status = "available"
        except Exception as e:
            calendar_info = {"error": str(e)}
            calendar_status = "error"

        # Get system resources
        try:
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")
            cpu_percent = psutil.cpu_percent(interval=1)

            system_resources = {
                "cpu_percent": cpu_percent,
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "percent": memory.percent,
                },
                "disk": {
                    "total": disk.total,
                    "free": disk.free,
                    "percent": (disk.used / disk.total) * 100,
                },
            }
        except Exception as e:
            system_resources = {"error": str(e)}

        return {
            "service": {
                "name": "QuantDB API",
                "version": "2.0.0-alpha",
                "environment": "development" if is_development() else "production",
                "timestamp": time.time(),
            },
            "database": {
                "status": db_status,
                "error": db_error,
                "engine": str(engine.url).split("@")[0] + "@***",  # Hide credentials
            },
            "trading_calendar": {"status": calendar_status, "info": calendar_info},
            "system_resources": system_resources,
        }

    except Exception as e:
        logger.error(f"Error getting system info: {e}")
        return {
            "service": {
                "name": "QuantDB API",
                "version": "2.0.0-alpha",
                "environment": "development" if is_development() else "production",
                "timestamp": time.time(),
            },
            "error": str(e),
        }


@router.get("/version")
async def get_version():
    """
    Get API version information
    """
    return {
        "name": "QuantDB API",
        "version": "2.1.0",
        "core_version": "2.1.0",
        "build_time": time.time(),
        "environment": "development" if is_development() else "production",
    }


@router.get("/config")
async def get_config():
    """
    Get system configuration (development only)
    """
    if not is_development():
        return {"error": "Configuration endpoint only available in development mode"}

    try:
        from core.utils.config import (
            DATABASE_URL,
            DB_TYPE,
            API_HOST,
            API_PORT,
            LOG_LEVEL,
            CACHE_TTL,
            ENABLE_CACHE,
        )

        return {
            "database": {
                "type": DB_TYPE,
                "url": DATABASE_URL.split("@")[0] + "@***" if "@" in DATABASE_URL else DATABASE_URL,
            },
            "api": {"host": API_HOST, "port": API_PORT},
            "logging": {"level": LOG_LEVEL},
            "cache": {"enabled": ENABLE_CACHE, "ttl": CACHE_TTL},
            "environment": {"development": is_development(), "production": is_production()},
        }

    except Exception as e:
        logger.error(f"Error getting config: {e}")
        return {"error": str(e)}


@router.post("/cache/clear")
async def clear_cache():
    """
    Clear system cache (development only)
    """
    if not is_development():
        return {"error": "Cache clear endpoint only available in development mode"}

    try:
        # Clear trading calendar cache
        trading_calendar = get_trading_calendar()
        trading_calendar.refresh_calendar()

        return {
            "status": "success",
            "message": "Cache cleared successfully",
            "timestamp": time.time(),
        }

    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        return {"status": "error", "message": str(e), "timestamp": time.time()}
