"""
System monitoring and metrics models for QuantDB core
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from sqlalchemy.sql import func

from ..database.connection import Base


class RequestLog(Base):
    """API请求日志"""

    __tablename__ = "request_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    # 请求信息
    symbol = Column(String(10), index=True)
    start_date = Column(String(8))
    end_date = Column(String(8))
    endpoint = Column(String(100))

    # 响应信息
    response_time_ms = Column(Float)  # 响应时间(毫秒)
    status_code = Column(Integer)
    record_count = Column(Integer)  # 返回记录数

    # 缓存信息
    cache_hit = Column(Boolean, default=False)  # 是否缓存命中
    akshare_called = Column(Boolean, default=False)  # 是否调用了AKShare
    cache_hit_ratio = Column(Float)  # 缓存命中比例(0-1)

    # 用户信息
    user_agent = Column(String(500))
    ip_address = Column(String(45))


class DataCoverage(Base):
    """数据覆盖情况统计"""

    __tablename__ = "data_coverage"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(10), unique=True, index=True)

    # 数据范围
    earliest_date = Column(String(8))  # 最早数据日期
    latest_date = Column(String(8))  # 最新数据日期
    total_records = Column(Integer)  # 总记录数

    # 统计信息
    first_requested = Column(DateTime(timezone=True))  # 首次请求时间
    last_accessed = Column(DateTime(timezone=True))  # 最后访问时间
    access_count = Column(Integer, default=0)  # 访问次数

    # 更新信息
    last_updated = Column(DateTime(timezone=True), server_default=func.now())


class SystemMetrics(Base):
    """系统指标快照"""

    __tablename__ = "system_metrics"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    # 数据库统计
    total_symbols = Column(Integer)  # 总股票数量
    total_records = Column(Integer)  # 总数据记录数
    db_size_mb = Column(Float)  # 数据库大小(MB)

    # 性能统计
    avg_response_time_ms = Column(Float)  # 平均响应时间
    cache_hit_rate = Column(Float)  # 缓存命中率
    akshare_requests_today = Column(Integer)  # 今日AKShare请求数

    # 使用统计
    requests_today = Column(Integer)  # 今日总请求数
    active_symbols_today = Column(Integer)  # 今日活跃股票数

    # 计算字段
    performance_improvement = Column(Float)  # 性能提升比例
    cost_savings = Column(Float)  # 成本节省(请求数减少)
