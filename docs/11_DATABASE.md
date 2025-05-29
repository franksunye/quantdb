# QuantDB 数据库文档

**数据库**: SQLite | **版本**: 简化架构 + 监控系统 | **状态**: 生产就绪

## 数据库概述

QuantDB 使用 SQLite 作为主要数据存储，同时作为智能缓存层。数据库设计专注于股票历史数据的高效存储和查询，并集成了实时监控系统。

## 核心表结构

### 业务数据表

### Assets (资产表)
存储股票、指数等金融资产的基本信息。

```sql
CREATE TABLE assets (
    asset_id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol VARCHAR(10) UNIQUE NOT NULL,
    name VARCHAR(100),
    isin VARCHAR(20),
    asset_type VARCHAR(20) DEFAULT 'stock',
    exchange VARCHAR(20),
    currency VARCHAR(10) DEFAULT 'CNY',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_assets_symbol ON assets(symbol);
CREATE INDEX idx_assets_type ON assets(asset_type);
```

### Prices (价格表)
存储历史价格数据，支持日线、周线、月线数据。

```sql
CREATE TABLE prices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id INTEGER NOT NULL,
    date DATE NOT NULL,
    open DECIMAL(10,4),
    high DECIMAL(10,4),
    low DECIMAL(10,4),
    close DECIMAL(10,4),
    volume BIGINT,
    turnover DECIMAL(15,2),
    amplitude DECIMAL(8,4),
    pct_change DECIMAL(8,4),
    change DECIMAL(10,4),
    turnover_rate DECIMAL(8,4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (asset_id) REFERENCES assets(asset_id),
    UNIQUE(asset_id, date)
);

-- 关键索引
CREATE INDEX idx_prices_asset_date ON prices(asset_id, date);
CREATE INDEX idx_prices_date ON prices(date);
CREATE INDEX idx_prices_symbol_date ON prices(asset_id, date DESC);
```

### 🆕 监控数据表

### RequestLog (请求日志表)
记录每个API请求的详细信息，用于性能监控和用户行为分析。

```sql
CREATE TABLE request_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,

    -- 请求信息
    symbol VARCHAR(10),
    start_date VARCHAR(8),
    end_date VARCHAR(8),
    endpoint VARCHAR(100),

    -- 响应信息
    response_time_ms REAL,
    status_code INTEGER,
    record_count INTEGER,

    -- 缓存信息
    cache_hit BOOLEAN DEFAULT 0,
    akshare_called BOOLEAN DEFAULT 0,
    cache_hit_ratio REAL,

    -- 用户信息
    user_agent VARCHAR(500),
    ip_address VARCHAR(45)
);

-- 索引
CREATE INDEX idx_request_logs_timestamp ON request_logs(timestamp);
CREATE INDEX idx_request_logs_symbol ON request_logs(symbol);
CREATE INDEX idx_request_logs_endpoint ON request_logs(endpoint);
```

### DataCoverage (数据覆盖表)
跟踪每只股票的数据覆盖情况和访问统计。

```sql
CREATE TABLE data_coverage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol VARCHAR(10) UNIQUE,

    -- 数据范围
    earliest_date VARCHAR(8),
    latest_date VARCHAR(8),
    total_records INTEGER,

    -- 统计信息
    first_requested DATETIME,
    last_accessed DATETIME,
    access_count INTEGER DEFAULT 0,

    -- 更新信息
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_data_coverage_symbol ON data_coverage(symbol);
CREATE INDEX idx_data_coverage_last_accessed ON data_coverage(last_accessed);
```

### SystemMetrics (系统指标表)
存储系统整体性能快照，用于趋势分析。

```sql
CREATE TABLE system_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,

    -- 数据库统计
    total_symbols INTEGER,
    total_records INTEGER,
    db_size_mb REAL,

    -- 性能统计
    avg_response_time_ms REAL,
    cache_hit_rate REAL,
    akshare_requests_today INTEGER,

    -- 使用统计
    requests_today INTEGER,
    active_symbols_today INTEGER,

    -- 计算字段
    performance_improvement REAL,
    cost_savings REAL
);

-- 索引
CREATE INDEX idx_system_metrics_timestamp ON system_metrics(timestamp);
```

## 关键查询

### 1. 获取股票历史数据
```sql
-- 获取指定股票的历史数据
SELECT p.date, p.open, p.high, p.low, p.close, p.volume, p.turnover
FROM prices p
JOIN assets a ON p.asset_id = a.asset_id
WHERE a.symbol = '000001'
  AND p.date BETWEEN '2023-01-01' AND '2023-12-31'
ORDER BY p.date;
```

### 2. 检查数据完整性
```sql
-- 检查指定日期范围内的数据缺失
WITH date_range AS (
    SELECT date('2023-01-01') + (ROW_NUMBER() OVER() - 1) || ' days' as check_date
    FROM (SELECT 1 UNION SELECT 2 UNION SELECT 3) -- 生成日期序列
)
SELECT dr.check_date
FROM date_range dr
LEFT JOIN prices p ON p.date = dr.check_date AND p.asset_id = 1
WHERE p.id IS NULL
  AND dr.check_date <= '2023-12-31';
```

### 3. 缓存状态查询
```sql
-- 获取数据库统计信息
SELECT 
    COUNT(DISTINCT a.asset_id) as assets_count,
    COUNT(p.id) as prices_count,
    MIN(p.date) as earliest_date,
    MAX(p.date) as latest_date,
    MAX(p.updated_at) as last_update
FROM assets a
LEFT JOIN prices p ON a.asset_id = p.asset_id;
```

## 数据管理

### 初始化数据库
```bash
# 创建表结构
python -m src.scripts.init_db

# 检查数据库状态
python check_database.py
```

### 数据获取
```bash
# 获取股票历史数据 (自动缓存到数据库)
curl "http://localhost:8000/api/v1/historical/stock/000001?start_date=20230101&end_date=20230131"
```

### 数据清理
```bash
# 清理价格数据
curl -X DELETE "http://localhost:8000/api/v1/cache/clear?table=daily_stock_data"

# 清理特定股票数据
curl -X DELETE "http://localhost:8000/api/v1/cache/clear/symbol/000001"
```

## 性能优化

### 索引策略
- **主键索引**: 自动创建，用于快速行查找
- **复合索引**: asset_id + date，优化时间序列查询
- **单列索引**: symbol, date，支持常见查询模式

### 查询优化
- **批量插入**: 使用事务批量插入数据
- **分页查询**: 大结果集使用 LIMIT/OFFSET
- **日期范围**: 使用索引优化的日期范围查询

### 存储优化
- **数据类型**: 使用合适的数据类型减少存储空间
- **VACUUM**: 定期清理数据库碎片
- **WAL模式**: 提高并发读写性能

## 备份和恢复

### 备份
```bash
# 备份数据库文件
cp database/stock_data.db database/stock_data_backup_$(date +%Y%m%d).db

# 导出SQL
sqlite3 database/stock_data.db .dump > backup.sql
```

### 恢复
```bash
# 从备份文件恢复
cp database/stock_data_backup_20231201.db database/stock_data.db

# 从SQL文件恢复
sqlite3 database/stock_data.db < backup.sql
```

## 监控和维护

### 数据库大小监控
```sql
-- 检查数据库大小
SELECT page_count * page_size as size_bytes 
FROM pragma_page_count(), pragma_page_size();
```

### 表统计信息
```sql
-- 获取表行数统计
SELECT name, COUNT(*) as row_count 
FROM sqlite_master 
WHERE type='table' 
GROUP BY name;
```
