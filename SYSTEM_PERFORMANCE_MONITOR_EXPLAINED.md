# system_performance_monitor.py 工作原理详解

## 📋 **工具概述**

`system_performance_monitor.py` 是一个端到端的性能监控工具，它通过启动真实的API服务器并发送HTTP请求来测试系统的完整性能。

## 🔧 **核心实现原理**

### 1. **API服务器启动**
```python
def start_api_server():
    """启动API服务器"""
    import uvicorn
    from src.api.main import app
    uvicorn.run(app, host='127.0.0.1', port=8000, log_level='warning')

# 在后台线程中启动
server_thread = threading.Thread(target=start_api_server, daemon=True)
server_thread.start()
time.sleep(3)  # 等待服务器启动
```

**作用**: 启动一个真实的FastAPI服务器，模拟生产环境

### 2. **HTTP请求测试**
```python
response = requests.get(
    f"http://localhost:8000/api/v1/historical/stock/{symbol}",
    params={
        "start_date": "20240101",
        "end_date": "20240105"
    },
    timeout=30
)
```

**作用**: 发送真实的HTTP请求，测试完整的请求-响应流程

### 3. **性能数据收集**
```python
start_time = time.time()
# ... 执行请求 ...
request_time = time.time() - start_time

if response.status_code == 200:
    data = response.json()
    record_count = len(data.get("data", []))
    print(f"✅ 成功获取 {record_count} 条记录，耗时 {request_time:.2f}秒")
```

**作用**: 精确测量每个请求的响应时间和数据量

## 📊 **统计数据来源分析**

### **阶段1: 基线状态**
```bash
📊 数据库基础统计:
  💾 总股票数量: 5 只
  📈 总数据记录: 26 条
```

**数据来源**: 
- `water_pool_monitor.py` 调用 `MonitoringService.get_water_pool_status()`
- 查询 `Asset` 表: `db.query(func.count(Asset.asset_id)).scalar()`
- 查询 `DailyStockData` 表: `db.query(func.count(DailyStockData.id)).scalar()`

### **阶段2: 数据获取测试**
```bash
🔄 获取第 1 只股票数据: 000001
  ✅ 成功获取 4 条记录，耗时 1.48秒
  📊 数据来源: AKShare (首次获取)
```

**数据来源**:
1. **请求时间**: `time.time()` 前后测量
2. **记录数量**: `len(response.json().get("data", []))`
3. **数据来源判断**: 通过日志分析是否调用了AKShare

**完整调用链**:
```
HTTP请求 → FastAPI路由 → StockDataService → AKShareAdapter → AKShare API
```

### **阶段3: 缓存效果验证**
```bash
🔄 再次请求 000001 数据 (测试缓存命中):
  ✅ 缓存命中! 获取 4 条记录，耗时 0.03秒
  📊 数据来源: 数据库缓存
```

**缓存判断逻辑**:
1. **第一次请求**: 数据库为空 → 调用AKShare → 存储到数据库
2. **第二次请求**: 数据库有数据 → 直接返回 → 缓存命中

**性能提升计算**: `1.48秒 → 0.03秒 = 49倍提升`

### **阶段4: 智能范围扩展**
```bash
🔄 扩展 000001 数据范围 (测试智能补充):
  ✅ 智能扩展! 获取 7 条记录，耗时 1.32秒
  📊 数据来源: 部分缓存 + 部分AKShare
```

**智能策略原理**:
1. **请求范围**: 20240101-20240110 (7个交易日)
2. **已有数据**: 20240102-20240105 (4个交易日)
3. **缺失数据**: 20240108-20240110 (3个交易日)
4. **智能补充**: 只获取缺失的3个交易日

## 🔍 **监控数据记录机制**

### **自动监控记录**
每个API请求都会触发监控中间件：

```python
@monitor_stock_request(get_db)
async def get_historical_stock_data(...):
    # API处理逻辑
```

**监控装饰器工作流程**:
1. **请求开始**: 记录开始时间
2. **执行API**: 处理业务逻辑
3. **请求结束**: 计算响应时间
4. **记录数据**: 写入 `request_logs` 表

### **监控数据表结构**

**request_logs 表**:
```sql
- timestamp: 请求时间
- symbol: 股票代码
- start_date, end_date: 日期范围
- response_time_ms: 响应时间(毫秒)
- status_code: HTTP状态码
- record_count: 返回记录数
- cache_hit: 是否缓存命中
- akshare_called: 是否调用AKShare
- ip_address, user_agent: 用户信息
```

## 📈 **实时统计计算**

### **水池状态统计**
```python
def get_water_pool_status(self) -> Dict:
    # 数据库总体统计
    total_symbols = self.db.query(func.count(Asset.asset_id)).scalar() or 0
    total_records = self.db.query(func.count(DailyStockData.id)).scalar() or 0
    
    # 今日统计
    today_start = datetime.combine(today, datetime.min.time())
    today_requests = self.db.query(func.count(RequestLog.id)).filter(
        RequestLog.timestamp >= today_start
    ).scalar() or 0
    
    # 缓存命中率计算
    cache_hit_rate = (today_cache_hits / today_requests * 100) if today_requests > 0 else 0
```

### **性能趋势分析**
```python
def get_performance_trends(self, days: int = 7) -> Dict:
    # 按天统计
    daily_stats = self.db.query(
        func.date(RequestLog.timestamp).label('date'),
        func.count(RequestLog.id).label('total_requests'),
        func.sum(func.cast(RequestLog.akshare_called, Integer)).label('akshare_calls'),
        func.avg(RequestLog.response_time_ms).label('avg_response_time')
    ).filter(
        RequestLog.timestamp >= start_date
    ).group_by(func.date(RequestLog.timestamp)).all()
```

## 🎯 **关键性能指标**

### **缓存效果验证**
- **首次请求**: 1.48秒 (需要调用AKShare)
- **缓存命中**: 0.03秒 (直接从数据库读取)
- **性能提升**: 49倍 (1.48/0.03 = 49.33)

### **智能补充策略**
- **全新数据**: ~1.5秒 (需要完整AKShare调用)
- **智能扩展**: ~1.3秒 (部分缓存 + 部分AKShare)
- **完全缓存**: ~0.03秒 (纯数据库查询)

### **成本节省计算**
```
总请求数: 13次
AKShare调用: 9次
缓存命中: 4次
成本节省: 4次AKShare调用 = 30.8%节省率
```

## 🔧 **工具的价值**

1. **端到端验证**: 测试完整的请求处理流程
2. **真实性能数据**: 使用真实的HTTP请求和数据库操作
3. **缓存效果量化**: 精确测量缓存带来的性能提升
4. **智能策略验证**: 证明部分缓存命中的优化效果
5. **系统健康监控**: 持续跟踪系统性能指标

这个工具提供了一个完整的性能基准测试框架，所有统计数据都来自真实的系统运行，而不是模拟数据。
