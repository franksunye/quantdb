"""
监控中间件

自动记录API请求和性能指标
"""

import time
from functools import wraps
from typing import Any, Callable, Optional

try:
    from fastapi import Request
except ImportError:
    Request = None

from sqlalchemy.orm import Session

from core.services.monitoring_service import MonitoringService
from core.utils.logger import get_logger

logger = get_logger("monitoring_middleware")


class RequestMonitor:
    """请求监控器"""

    def __init__(self, db: Session):
        self.db = db
        self.monitoring_service = MonitoringService(db)

    def log_stock_request(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        endpoint: str,
        response_time_ms: float,
        status_code: int,
        record_count: int,
        cache_hit: bool,
        akshare_called: bool,
        cache_hit_ratio: float = 0.0,
        request: Optional[Any] = None,
    ):
        """记录股票数据请求"""

        user_agent = ""
        ip_address = ""

        if request:
            user_agent = request.headers.get("user-agent", "")
            # 获取真实IP (考虑代理)
            ip_address = (
                request.headers.get("x-forwarded-for", "").split(",")[0].strip()
                or request.headers.get("x-real-ip", "")
                or request.client.host
                if request.client
                else ""
            )

        try:
            self.monitoring_service.log_request(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                endpoint=endpoint,
                response_time_ms=response_time_ms,
                status_code=status_code,
                record_count=record_count,
                cache_hit=cache_hit,
                akshare_called=akshare_called,
                cache_hit_ratio=cache_hit_ratio,
                user_agent=user_agent,
                ip_address=ip_address,
            )
        except Exception as e:
            logger.error(f"Failed to log request: {e}")


def monitor_stock_request(db_getter: Callable[[], Session]):
    """
    装饰器：监控股票数据请求

    Args:
        db_getter: 获取数据库会话的函数
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()

            # 提取请求参数
            symbol = kwargs.get("symbol", "unknown")
            start_date = kwargs.get("start_date", "")
            end_date = kwargs.get("end_date", "")
            request = kwargs.get("request")

            # 确定端点名称
            endpoint = f"/api/v1/historical/stock/{symbol}"

            try:
                # 执行原函数
                result = await func(*args, **kwargs)

                # 计算响应时间
                response_time_ms = (time.time() - start_time) * 1000

                # 分析结果
                status_code = 200
                record_count = 0
                cache_hit = False
                akshare_called = False
                cache_hit_ratio = 0.0

                if isinstance(result, dict):
                    data = result.get("data", [])
                    record_count = len(data) if data else 0

                    # 从metadata中获取缓存信息
                    metadata = result.get("metadata", {})
                    cache_info = metadata.get("cache_info", {})

                    if cache_info:
                        cache_hit = cache_info.get("cache_hit", False)
                        akshare_called = cache_info.get("akshare_called", False)
                        cache_hit_ratio = cache_info.get("cache_hit_ratio", 0.0)

                # 记录监控数据
                db_session = next(db_getter())
                monitor = RequestMonitor(db_session)
                monitor.log_stock_request(
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date,
                    endpoint=endpoint,
                    response_time_ms=response_time_ms,
                    status_code=status_code,
                    record_count=record_count,
                    cache_hit=cache_hit,
                    akshare_called=akshare_called,
                    cache_hit_ratio=cache_hit_ratio,
                    request=request,
                )

                return result

            except Exception as e:
                # 记录错误请求
                response_time_ms = (time.time() - start_time) * 1000

                db_session = next(db_getter())
                monitor = RequestMonitor(db_session)
                monitor.log_stock_request(
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date,
                    endpoint=endpoint,
                    response_time_ms=response_time_ms,
                    status_code=500,
                    record_count=0,
                    cache_hit=False,
                    akshare_called=False,
                    cache_hit_ratio=0.0,
                    request=request,
                )

                raise e

        return wrapper

    return decorator
