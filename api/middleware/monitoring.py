"""
Monitoring middleware for QuantDB API service.

This middleware tracks API requests and performance metrics.
"""

import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session

# Import core modules
from core.database.connection import SessionLocal
from core.models.system_metrics import RequestLog
from core.utils.logger import logger


class MonitoringMiddleware(BaseHTTPMiddleware):
    """
    Middleware to monitor API requests and log performance metrics
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and log metrics
        """
        start_time = time.time()
        
        # Extract request information
        method = request.method
        url = str(request.url)
        path = request.url.path
        user_agent = request.headers.get("user-agent", "")
        ip_address = self._get_client_ip(request)
        
        # Process request
        response = await call_next(request)
        
        # Calculate response time
        process_time = time.time() - start_time
        response_time_ms = process_time * 1000
        
        # Add response time header
        response.headers["X-Process-Time"] = str(response_time_ms)
        
        # Log request if it's an API endpoint
        if path.startswith("/api/"):
            try:
                await self._log_request(
                    request=request,
                    response=response,
                    response_time_ms=response_time_ms,
                    user_agent=user_agent,
                    ip_address=ip_address
                )
            except Exception as e:
                logger.error(f"Error logging request: {e}")
        
        return response

    def _get_client_ip(self, request: Request) -> str:
        """
        Get client IP address from request
        """
        # Check for forwarded headers first (for reverse proxy setups)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fall back to direct client IP
        if hasattr(request, "client") and request.client:
            return request.client.host
        
        return "unknown"

    async def _log_request(
        self,
        request: Request,
        response: Response,
        response_time_ms: float,
        user_agent: str,
        ip_address: str
    ):
        """
        Log request to database
        """
        try:
            # Create database session
            db = SessionLocal()
            
            try:
                # Extract request parameters
                symbol = None
                start_date = None
                end_date = None
                endpoint = request.url.path
                
                # Extract symbol from path or query parameters
                if "/stock-data/" in endpoint:
                    path_parts = endpoint.split("/")
                    if len(path_parts) > 3:
                        symbol = path_parts[-1]
                
                # Extract query parameters
                query_params = dict(request.query_params)
                if "start_date" in query_params:
                    start_date = query_params["start_date"]
                if "end_date" in query_params:
                    end_date = query_params["end_date"]
                if "symbol" in query_params:
                    symbol = query_params["symbol"]
                
                # Determine cache information from response
                cache_hit = False
                akshare_called = False
                cache_hit_ratio = 0.0
                record_count = 0
                
                # Try to extract cache info from response if available
                # This would be set by the actual API endpoints
                if hasattr(response, "cache_info"):
                    cache_info = response.cache_info
                    cache_hit = cache_info.get("cache_hit", False)
                    akshare_called = cache_info.get("akshare_called", False)
                    cache_hit_ratio = cache_info.get("cache_hit_ratio", 0.0)
                
                # Create request log entry
                request_log = RequestLog(
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date,
                    endpoint=endpoint,
                    response_time_ms=response_time_ms,
                    status_code=response.status_code,
                    record_count=record_count,
                    cache_hit=cache_hit,
                    akshare_called=akshare_called,
                    cache_hit_ratio=cache_hit_ratio,
                    user_agent=user_agent,
                    ip_address=ip_address
                )
                
                db.add(request_log)
                db.commit()
                
                logger.debug(f"Logged request: {endpoint} - {response_time_ms:.2f}ms - {response.status_code}")
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error logging request to database: {e}")


def monitor_stock_request(get_db_func):
    """
    Decorator to monitor stock data requests (for backward compatibility)
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # This is now handled by the middleware
            return await func(*args, **kwargs)
        return wrapper
    return decorator
