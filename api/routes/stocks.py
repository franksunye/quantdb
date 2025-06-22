# src/api/routes/historical_data_simplified.py
"""
Historical stock data API routes with simplified cache architecture.

This module provides API endpoints for retrieving historical stock data,
using the simplified cache architecture with database as persistent cache.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from datetime import date, datetime
import pandas as pd

from core.database import get_db
from core.models import Asset
from api.schemas import HistoricalDataResponse, HistoricalDataPoint
from core.cache.akshare_adapter import AKShareAdapter
from core.services.stock_data_service import StockDataService
from core.services.database_cache import DatabaseCache
from core.services.asset_info_service import AssetInfoService
from core.services.monitoring_middleware import monitor_stock_request
from core.utils.logger import get_logger

# Create dependencies for services
def get_akshare_adapter(db: Session = Depends(get_db)):
    """Get AKShare adapter instance."""
    return AKShareAdapter(db)

def get_stock_data_service(
    db: Session = Depends(get_db),
    akshare_adapter: AKShareAdapter = Depends(get_akshare_adapter)
):
    """Get stock data service instance."""
    return StockDataService(db, akshare_adapter)

def get_asset_info_service(db: Session = Depends(get_db)):
    """Get asset info service instance."""
    return AssetInfoService(db)

# Setup logger
logger = get_logger(__name__)

# Create router
router = APIRouter(
    tags=["historical"],
    responses={404: {"description": "Not found"}},
)

@router.get("/stock/{symbol}", response_model=HistoricalDataResponse)
@monitor_stock_request(get_db)
async def get_historical_stock_data(
    symbol: str,
    request: Request,
    start_date: Optional[str] = Query(None, description="Start date in format YYYYMMDD"),
    end_date: Optional[str] = Query(None, description="End date in format YYYYMMDD"),
    adjust: Optional[str] = Query("", description="Price adjustment: '' for no adjustment, 'qfq' for forward adjustment, 'hfq' for backward adjustment"),
    db: Session = Depends(get_db),
    stock_data_service: StockDataService = Depends(get_stock_data_service),
    asset_info_service: AssetInfoService = Depends(get_asset_info_service)
):
    """
    Get historical stock data for a specific symbol

    - **symbol**: Stock symbol (6-digit for A-shares, 5-digit for Hong Kong stocks)
    - **start_date**: Optional start date in format YYYYMMDD
    - **end_date**: Optional end date in format YYYYMMDD
    - **adjust**: Price adjustment method ('' for no adjustment, 'qfq' for forward adjustment, 'hfq' for backward adjustment)
    """
    try:
        # Validate symbol format - support both A-shares and Hong Kong stocks
        if not symbol.isdigit() or (len(symbol) != 6 and len(symbol) != 5):
            raise HTTPException(status_code=400, detail="Symbol must be a 6-digit number")

        # Get or create asset with enhanced information
        asset, asset_metadata = asset_info_service.get_or_create_asset(symbol)

        # Set default dates if not provided
        if end_date is None:
            end_date = datetime.now().strftime("%Y%m%d")

        # Fetch data using the stock data service
        logger.info(f"Fetching historical data for {symbol} from {start_date} to {end_date} with adjust={adjust}")
        try:
            df = stock_data_service.get_stock_data(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                adjust=adjust
            )

            if df.empty:
                logger.warning(f"No historical data found for {symbol} from {start_date} to {end_date}")

                # 提供更详细的错误分析
                error_analysis = _analyze_empty_data_reason(symbol, start_date, end_date)

                return {
                    "symbol": symbol,
                    "name": asset.name if asset else f"Stock {symbol}",
                    "start_date": start_date,
                    "end_date": end_date,
                    "adjust": adjust,
                    "data": [],
                    "metadata": {
                        "count": 0,
                        "status": "success",
                        "message": "No data found for the specified parameters",
                        "error_analysis": error_analysis,
                        "suggestions": [
                            "Try extending the date range to 30 days or more",
                            "Verify the stock code is correct and still trading",
                            "Check if the selected dates include trading days",
                            "Try querying active stocks like 600000, 000001, or 600519"
                        ]
                    }
                }

            # Convert DataFrame to response format
            data_points = []
            for _, row in df.iterrows():
                data_point = HistoricalDataPoint(
                    date=row.get('date', None),
                    open=row.get('open', None),
                    high=row.get('high', None),
                    low=row.get('low', None),
                    close=row.get('close', None),
                    volume=row.get('volume', None),
                    turnover=row.get('turnover', None),
                    amplitude=row.get('amplitude', None),
                    pct_change=row.get('pct_change', None),
                    change=row.get('change', None),
                    turnover_rate=row.get('turnover_rate', None)
                )
                data_points.append(data_point)

            # 获取真实的缓存状态信息
            cache_info = _get_cache_info(symbol, start_date, end_date, df, stock_data_service)

            # Create response
            response = {
                "symbol": symbol,
                "name": asset.name if asset else f"Stock {symbol}",
                "start_date": start_date,
                "end_date": end_date,
                "adjust": adjust,
                "data": data_points,
                "metadata": {
                    "count": len(data_points),
                    "status": "success",
                    "message": f"Successfully retrieved {len(data_points)} data points",
                    "cache_info": cache_info
                }
            }

            return response

        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {e}")
            raise HTTPException(status_code=500, detail=f"Error fetching data: {str(e)}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_historical_stock_data: {e}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


def _get_cache_info(symbol: str, start_date: str, end_date: str, df, stock_data_service) -> dict:
    """
    获取真实的缓存状态信息

    Args:
        symbol: 股票代码
        start_date: 开始日期
        end_date: 结束日期
        df: 返回的数据DataFrame
        stock_data_service: 股票数据服务实例

    Returns:
        包含缓存信息的字典
    """
    try:
        from core.services.trading_calendar import get_trading_calendar

        # 获取交易日历
        trading_calendar = get_trading_calendar()
        trading_days = trading_calendar.get_trading_days(start_date, end_date)
        total_trading_days = len(trading_days)

        # 检查数据库中已有的数据
        db_cache = stock_data_service.db_cache
        existing_data = db_cache.get(symbol, trading_days)
        cached_days = len(existing_data)

        # 计算缓存命中率
        cache_hit_ratio = cached_days / total_trading_days if total_trading_days > 0 else 0.0

        # 判断是否调用了AKShare
        akshare_called = cached_days < total_trading_days

        # 判断是否为缓存命中（如果所有请求的数据都在缓存中）
        cache_hit = cached_days == total_trading_days and total_trading_days > 0

        logger.info(f"Cache info for {symbol}: hit={cache_hit}, ratio={cache_hit_ratio:.2f}, "
                   f"cached_days={cached_days}, total_days={total_trading_days}, akshare_called={akshare_called}")

        return {
            "cache_hit": cache_hit,
            "akshare_called": akshare_called,
            "cache_hit_ratio": cache_hit_ratio,
            "cached_days": cached_days,
            "total_trading_days": total_trading_days,
            "response_time_ms": 0  # 这个会在middleware中设置
        }

    except Exception as e:
        logger.error(f"Error getting cache info: {e}")
        # 返回默认值
        return {
            "cache_hit": False,
            "akshare_called": True,
            "cache_hit_ratio": 0.0,
            "cached_days": 0,
            "total_trading_days": 0,
            "response_time_ms": 0
        }


def _analyze_empty_data_reason(symbol: str, start_date: str, end_date: str) -> dict:
    """
    分析为什么没有获取到数据的原因

    Args:
        symbol: 股票代码
        start_date: 开始日期
        end_date: 结束日期

    Returns:
        包含错误分析的字典
    """
    analysis = {
        "possible_reasons": [],
        "stock_status": "unknown",
        "date_range_info": {},
        "recommendations": []
    }

    try:
        from datetime import datetime, timedelta
        from core.services.trading_calendar import get_trading_calendar

        # 分析日期范围
        if start_date is None or end_date is None:
            analysis["possible_reasons"].append("日期参数缺失")
            analysis["recommendations"].append("提供有效的开始和结束日期")
            return analysis

        start_dt = datetime.strptime(start_date, '%Y%m%d')
        end_dt = datetime.strptime(end_date, '%Y%m%d')
        date_diff = (end_dt - start_dt).days

        analysis["date_range_info"] = {
            "days_requested": date_diff,
            "start_date": start_date,
            "end_date": end_date
        }

        # 检查是否有交易日
        try:
            trading_calendar = get_trading_calendar()
            trading_days = trading_calendar.get_trading_days(start_date, end_date)
            analysis["date_range_info"]["trading_days"] = len(trading_days)

            if len(trading_days) == 0:
                analysis["possible_reasons"].append("所选日期范围内没有交易日")
                analysis["recommendations"].append("选择包含工作日的日期范围")
            elif len(trading_days) < 3:
                analysis["possible_reasons"].append("交易日数量太少")
                analysis["recommendations"].append("扩大日期范围以包含更多交易日")

        except Exception as e:
            logger.warning(f"Error checking trading calendar: {e}")
            analysis["possible_reasons"].append("无法验证交易日历")

        # 特殊股票代码分析
        problematic_stocks = {
            '600001': '邯郸钢铁 - 可能已停牌或退市',
            '600002': '齐鲁石化 - 可能已停牌或退市',
            '600003': '东北高速 - 可能已停牌或退市'
        }

        if symbol in problematic_stocks:
            analysis["possible_reasons"].append(f"已知问题股票: {problematic_stocks[symbol]}")
            analysis["recommendations"].append("尝试查询活跃股票如600000、000001、600519")

        # 日期范围建议
        if date_diff < 7:
            analysis["recommendations"].append("建议查询至少30天的数据以获得更好的结果")

    except Exception as e:
        logger.error(f"Error analyzing empty data reason: {e}")
        analysis["possible_reasons"].append("数据分析过程中出现错误")

    return analysis


def get_database_cache(db: Session = Depends(get_db)):
    """Get database cache instance."""
    return DatabaseCache(db)

@router.get("/database/cache/status")
async def get_database_cache_status(
    symbol: Optional[str] = Query(None, description="Stock symbol"),
    start_date: Optional[str] = Query(None, description="Start date in format YYYYMMDD"),
    end_date: Optional[str] = Query(None, description="End date in format YYYYMMDD"),
    database_cache: DatabaseCache = Depends(get_database_cache)
):
    """
    Get database cache status

    - **symbol**: Optional stock symbol to check coverage for
    - **start_date**: Optional start date for coverage check
    - **end_date**: Optional end date for coverage check
    """
    try:
        # If symbol and date range provided, get coverage information
        if symbol and start_date and end_date:
            coverage_info = database_cache.get_date_range_coverage(symbol, start_date, end_date)
            return {
                "symbol": symbol,
                "start_date": start_date,
                "end_date": end_date,
                "coverage": coverage_info
            }

        # Otherwise, get general cache statistics
        stats = database_cache.get_stats()
        return stats

    except Exception as e:
        logger.error(f"Error getting database cache status: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting cache status: {str(e)}")
