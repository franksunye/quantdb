# QuantDB API 文档

**版本**: v0.7.6-performance-optimized | **架构**: 统一架构 + 高性能缓存 | **数据库**: SQLite

## 重要更新 (v0.7.0)

🎉 **API重构完成**: 消除了价格数据重复，统一使用历史数据API

- ❌ **已移除**: `/api/v1/prices/` 端点（完全删除）
- ✅ **保留**: `/api/v1/historical/` 端点（与AKShare格式一致）
- 🔄 **统一**: 使用 `DailyStockData` 模型存储所有股票数据
- 📊 **一致性**: 与AKShare保持完全一致的数据格式

## 快速开始

```bash
# 启动API服务
uvicorn src.api.main:app --reload

# API文档: http://localhost:8000/api/v1/docs
# 健康检查: http://localhost:8000/api/v1/health
```

### 性能指标 (E2E测试验证)

**响应时间基准**:
- 健康检查: ~1ms ⚡
- 资产列表: ~9ms ⚡
- 首次数据请求: ~1.2秒 (含AKShare获取)
- 缓存命中: ~0.76秒 (平均32%性能提升)

### 🆕 实时监控系统

**重大升级**: 监控数据收集已激活，每个API请求自动记录！

**蓄水池状态监控**:
```bash
# 查看当前蓄水池状态 (显示真实数据)
python tools/monitoring/water_pool_monitor.py
```

**系统性能监控**:
```bash
# 完整性能基准测试 (端到端验证)
python tools/monitoring/system_performance_monitor.py
```

**实时监控指标**:
- 🏊‍♂️ 蓄水池容量: 缓存股票数量和数据记录数
- ⚡ 缓存效果: 实时命中率和性能提升比例
- 💰 成本节省: AKShare调用减少量化
- 📊 数据覆盖: 时间跨度和数据分布情况
- 🔄 请求统计: 每个API调用的详细记录
- 📈 性能趋势: 历史性能数据和趋势分析

**监控数据收集**:
- ✅ **自动收集**: 每个API请求都被记录
- ✅ **实时存储**: 数据存储在SQLite监控表中
- ✅ **性能跟踪**: 响应时间、缓存命中率、AKShare调用
- ✅ **用户行为**: IP地址、User-Agent、访问模式
- ✅ **测试保障**: 36个监控测试确保系统质量
- ✅ **性能优化**: 缓存性能比 AKShare 提升 98.1%

## 核心端点

### 资产管理

```bash
# 获取资产列表
GET /api/v1/assets

# 获取特定资产
GET /api/v1/assets/{asset_id}
GET /api/v1/assets/symbol/{symbol}
```

### 股票历史数据 (统一API)

```bash
# 获取股票历史数据 (与AKShare保持一致)
GET /api/v1/historical/stock/{symbol}?start_date=20230101&end_date=20231231

# 参数:
# - symbol: 6位股票代码 (如 000001)
# - start_date: 开始日期 YYYYMMDD (可选)
# - end_date: 结束日期 YYYYMMDD (可选)
# - adjust: 复权方式 "", "qfq", "hfq" (可选)
# - limit: 最大返回数量 (默认100)
```

**特点**:
- 🔄 **统一数据源**: 唯一的股票数据API端点
- 📊 **AKShare兼容**: 与AKShare保持完全一致的数据格式
- ⚡ **智能缓存**: 自动缓存和更新数据
- 💾 **持久化**: 数据存储在SQLite数据库中

**响应示例**:
```json
{
  "symbol": "000001",
  "name": "平安银行",
  "start_date": "20230101",
  "end_date": "20230131",
  "adjust": "",
  "data": [
    {
      "date": "2023-01-03",
      "open": 12.50,
      "high": 12.80,
      "low": 12.30,
      "close": 12.65,
      "volume": 1234567,
      "turnover": 15432100.50,
      "amplitude": 4.0,
      "pct_change": 1.2,
      "change": 0.15,
      "turnover_rate": 0.8
    }
  ],
  "metadata": {
    "count": 1,
    "status": "success",
    "message": "Successfully retrieved 1 data points"
  }
}
```

**数据字段说明** (与AKShare一致):
- `date`: 交易日期
- `open`: 开盘价
- `high`: 最高价
- `low`: 最低价
- `close`: 收盘价
- `volume`: 成交量
- `turnover`: 成交额
- `amplitude`: 振幅(%)
- `pct_change`: 涨跌幅(%)
- `change`: 涨跌额
- `turnover_rate`: 换手率(%)





### 缓存管理

```bash
# 获取缓存状态
GET /api/v1/cache/status

# 清除缓存数据 (更新后使用daily_stock_data表)
DELETE /api/v1/cache/clear?table=daily_stock_data

# 清除特定股票的缓存
DELETE /api/v1/cache/clear/symbol/{symbol}
```

## 错误处理

所有错误使用统一格式：

```json
{
  "error": {
    "code": "BAD_REQUEST",
    "message": "Symbol must be a 6-digit number",
    "status_code": 400
  }
}
```

**常见状态码**:
- 200: 成功
- 400: 请求错误 (参数格式错误)
- 404: 资源未找到
- 500: 服务器内部错误

## 使用示例

```bash
# 完整工作流程 - 获取股票历史数据
curl "http://localhost:8000/api/v1/historical/stock/000001?start_date=20230101&end_date=20230131"

# 获取最近10天数据
curl "http://localhost:8000/api/v1/historical/stock/000001?limit=10"

# 获取前复权数据
curl "http://localhost:8000/api/v1/historical/stock/000001?adjust=qfq&limit=20"



# 检查缓存状态
curl http://localhost:8000/api/v1/cache/status

# 清除特定股票缓存
curl -X DELETE http://localhost:8000/api/v1/cache/clear/symbol/000001
```

## 迁移指南

### 从 v0.6.0 升级到 v0.7.0

**重要变更**:
- ❌ **已移除**: `/api/v1/prices/` 所有端点
- ✅ **保留**: `/api/v1/historical/` 端点保持不变

**无需修改**:
- 如果您使用的是 `/api/v1/historical/` 端点，无需任何修改
- 数据格式和字段保持完全一致

**需要修改**:
- 如果您使用的是 `/api/v1/prices/` 端点，请更换为 `/api/v1/historical/`
- 新的统一API提供更丰富的数据和更好的性能
