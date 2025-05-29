"""
监控服务

追踪系统使用情况和"水池蓄水"状态
"""

import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from src.api.models import RequestLog, DataCoverage, SystemMetrics, DailyStockData
from src.logger import setup_logger

logger = setup_logger("monitoring_service")

class MonitoringService:
    """监控服务类"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def log_request(self, 
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
                   user_agent: str = "",
                   ip_address: str = ""):
        """记录API请求日志"""
        
        log_entry = RequestLog(
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
            ip_address=ip_address
        )
        
        self.db.add(log_entry)
        self.db.commit()
        
        # 更新数据覆盖统计
        self._update_data_coverage(symbol)
    
    def _update_data_coverage(self, symbol: str):
        """更新数据覆盖统计"""
        
        # 查询该股票的数据范围
        data_stats = self.db.query(
            func.min(DailyStockData.date).label('earliest'),
            func.max(DailyStockData.date).label('latest'),
            func.count(DailyStockData.id).label('total')
        ).filter(DailyStockData.symbol == symbol).first()
        
        if not data_stats or not data_stats.total:
            return
        
        # 查找或创建覆盖记录
        coverage = self.db.query(DataCoverage).filter(
            DataCoverage.symbol == symbol
        ).first()
        
        if not coverage:
            coverage = DataCoverage(
                symbol=symbol,
                first_requested=datetime.now(),
                access_count=1
            )
            self.db.add(coverage)
        else:
            coverage.access_count += 1
        
        # 更新统计信息
        coverage.earliest_date = data_stats.earliest
        coverage.latest_date = data_stats.latest
        coverage.total_records = data_stats.total
        coverage.last_accessed = datetime.now()
        coverage.last_updated = datetime.now()
        
        self.db.commit()
    
    def get_water_pool_status(self) -> Dict:
        """获取"水池蓄水"状态"""
        
        # 数据库总体统计
        total_symbols = self.db.query(func.count(func.distinct(DailyStockData.symbol))).scalar() or 0
        total_records = self.db.query(func.count(DailyStockData.id)).scalar() or 0
        
        # 今日统计
        today = datetime.now().date()
        today_start = datetime.combine(today, datetime.min.time())
        
        today_requests = self.db.query(func.count(RequestLog.id)).filter(
            RequestLog.timestamp >= today_start
        ).scalar() or 0
        
        today_akshare_calls = self.db.query(func.count(RequestLog.id)).filter(
            RequestLog.timestamp >= today_start,
            RequestLog.akshare_called == True
        ).scalar() or 0
        
        today_cache_hits = self.db.query(func.count(RequestLog.id)).filter(
            RequestLog.timestamp >= today_start,
            RequestLog.cache_hit == True
        ).scalar() or 0
        
        # 计算缓存命中率
        cache_hit_rate = (today_cache_hits / today_requests * 100) if today_requests > 0 else 0
        
        # 平均响应时间
        avg_response_time = self.db.query(func.avg(RequestLog.response_time_ms)).filter(
            RequestLog.timestamp >= today_start
        ).scalar() or 0
        
        # 热门股票 (今日访问最多的前10只)
        hot_stocks = self.db.query(
            RequestLog.symbol,
            func.count(RequestLog.id).label('requests')
        ).filter(
            RequestLog.timestamp >= today_start
        ).group_by(RequestLog.symbol).order_by(desc('requests')).limit(10).all()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "water_pool": {
                "total_symbols": total_symbols,
                "total_records": total_records,
                "data_coverage": f"{total_symbols} 只股票，{total_records:,} 条记录"
            },
            "today_performance": {
                "total_requests": today_requests,
                "akshare_calls": today_akshare_calls,
                "cache_hits": today_cache_hits,
                "cache_hit_rate": f"{cache_hit_rate:.1f}%",
                "avg_response_time_ms": f"{avg_response_time:.1f}",
                "cost_savings": f"节省 {today_requests - today_akshare_calls} 次AKShare调用"
            },
            "hot_stocks": [
                {"symbol": stock.symbol, "requests": stock.requests}
                for stock in hot_stocks
            ]
        }
    
    def get_detailed_coverage(self) -> List[Dict]:
        """获取详细的数据覆盖情况"""
        
        coverages = self.db.query(DataCoverage).order_by(
            desc(DataCoverage.access_count)
        ).limit(20).all()
        
        result = []
        for coverage in coverages:
            # 计算数据跨度天数
            if coverage.earliest_date and coverage.latest_date:
                start_date = datetime.strptime(coverage.earliest_date, '%Y-%m-%d')
                end_date = datetime.strptime(coverage.latest_date, '%Y-%m-%d')
                span_days = (end_date - start_date).days + 1
            else:
                span_days = 0
            
            result.append({
                "symbol": coverage.symbol,
                "data_range": f"{coverage.earliest_date} ~ {coverage.latest_date}",
                "span_days": span_days,
                "total_records": coverage.total_records,
                "access_count": coverage.access_count,
                "first_requested": coverage.first_requested.strftime('%Y-%m-%d %H:%M') if coverage.first_requested else "",
                "last_accessed": coverage.last_accessed.strftime('%Y-%m-%d %H:%M') if coverage.last_accessed else ""
            })
        
        return result
    
    def get_performance_trends(self, days: int = 7) -> Dict:
        """获取性能趋势 (最近N天)"""
        
        start_date = datetime.now() - timedelta(days=days)
        
        # 按天统计
        daily_stats = self.db.query(
            func.date(RequestLog.timestamp).label('date'),
            func.count(RequestLog.id).label('total_requests'),
            func.sum(func.cast(RequestLog.akshare_called, Integer)).label('akshare_calls'),
            func.avg(RequestLog.response_time_ms).label('avg_response_time'),
            func.count(func.distinct(RequestLog.symbol)).label('active_symbols')
        ).filter(
            RequestLog.timestamp >= start_date
        ).group_by(func.date(RequestLog.timestamp)).order_by('date').all()
        
        trends = []
        for stat in daily_stats:
            cache_hit_rate = ((stat.total_requests - stat.akshare_calls) / stat.total_requests * 100) if stat.total_requests > 0 else 0
            
            trends.append({
                "date": stat.date.strftime('%Y-%m-%d'),
                "total_requests": stat.total_requests,
                "akshare_calls": stat.akshare_calls,
                "cache_hit_rate": f"{cache_hit_rate:.1f}%",
                "avg_response_time_ms": f"{stat.avg_response_time:.1f}",
                "active_symbols": stat.active_symbols,
                "efficiency": f"节省 {stat.total_requests - stat.akshare_calls} 次调用"
            })
        
        return {
            "period": f"最近 {days} 天",
            "trends": trends
        }
