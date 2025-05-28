# QuantDB API 路由文档

本文档描述了QuantDB API的路由结构和使用方法。

**最后更新**: 2025-05-28
**版本**: 简化架构版本
**状态**: SQLite开发版本，专注核心功能

## API前缀

所有API路由都使用统一的前缀：`/api/v1`
部分端点也支持 `/api/v2` 版本

## 根端点

### 根端点

```
GET /
```

返回API的欢迎信息和可用端点列表。

### 健康检查

```
GET /api/v1/health
```

返回API的健康状态信息。

### API版本信息

```
GET /api/v1
```

返回API的版本信息。

## 资产管理

资产管理API用于管理股票、指数等金融资产。

### 获取资产列表

```
GET /api/v1/assets/
```

参数：
- `skip`: 要跳过的资产数量（默认：0）
- `limit`: 要返回的最大资产数量（默认：100，最大：1000）
- `symbol`: 按符号筛选（可选）
- `name`: 按名称筛选（可选）
- `asset_type`: 按资产类型筛选（可选）
- `exchange`: 按交易所筛选（可选）

### 获取特定资产

```
GET /api/v1/assets/{asset_id}
```

参数：
- `asset_id`: 资产ID

### 按符号获取资产

```
GET /api/v1/assets/symbol/{symbol}
```

参数：
- `symbol`: 资产符号

## 价格数据

价格数据API用于获取股票的历史价格数据。使用简化架构，直接从 AKShare 获取数据并缓存到 SQLite 数据库。

### 获取股票价格数据

```
GET /api/v1/prices/stock/{symbol}
```

**描述**: 获取指定股票的价格数据。返回的数据格式为数组，包含价格对象列表。

**参数**:
- `symbol` (必需): 6位数字股票代码，如 "000001"
- `start_date` (可选): 开始日期，格式为 YYYYMMDD
- `end_date` (可选): 结束日期，格式为 YYYYMMDD
- `limit` (可选): 最大返回记录数，默认 100
- `adjust` (可选): 价格调整方法，默认 ""
- `period` (可选): 数据周期，默认 "daily"

**响应示例**:
```json
[
  {
    "id": 1,
    "asset_id": 1,
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
    "turnover_rate": 0.8,
    "created_at": "2025-05-28T10:30:00.000Z",
    "updated_at": "2025-05-28T10:30:00.000Z"
  }
]

## 数据导入

数据导入API用于从 AKShare 导入股票数据到本地 SQLite 数据库。导入操作会在后台异步执行。

### 导入股票数据

```
POST /api/v1/import/stock
```

**描述**: 启动后台任务从 AKShare 导入指定股票的历史数据。该操作是异步的，会立即返回任务状态。

**请求体**:
```json
{
  "symbol": "000001",
  "start_date": "20230101",
  "end_date": "20230131"
}
```

**参数说明**:
- `symbol` (必需): 6位数字股票代码
- `start_date` (必需): 开始日期，格式为 YYYYMMDD
- `end_date` (必需): 结束日期，格式为 YYYYMMDD

**响应示例**:
```json
{
  "status": "success",
  "message": "Import task for stock 000001 has been scheduled",
  "task_id": "import_stock_000001_20230101_20230131"
}
```

### 导入指数数据

```
POST /api/v1/import/index
```

**描述**: 启动后台任务从 AKShare 导入指定指数的历史数据。

**请求体**:
```json
{
  "symbol": "000001",
  "start_date": "20230101",
  "end_date": "20230131"
}
```

### 导入指数成分股

```
POST /api/v1/import/index/constituents
```

请求体：
```json
{
  "symbol": "000001"
}
```

## 缓存管理

缓存管理API用于管理和监控简化缓存系统。在简化架构中，我们使用 SQLite 数据库作为主要缓存。

### 获取缓存状态

```
GET /api/v1/cache/status
```

**描述**: 获取 SQLite 数据库缓存的状态和统计信息。

**响应示例**:
```json
{
  "database": {
    "assets_count": 150,
    "prices_count": 45000,
    "latest_update": "2025-05-28T10:30:00.000Z",
    "database_size_bytes": 2048000
  },
  "cache_type": "SQLite Database",
  "status": "active"
}
```

### 清除缓存数据

```
DELETE /api/v1/cache/clear
```

**描述**: 清除 SQLite 数据库中的缓存数据。

**参数**:
- `table` (可选): 要清除的表名
  - `"prices"`: 仅清除价格数据
  - `"assets"`: 清除资产和相关价格数据
  - 不提供: 清除所有数据

**响应示例**:
```json
{
  "status": "success",
  "message": "All cached data cleared successfully"
}
```

### 刷新缓存条目

```
POST /api/v1/cache/refresh
```

参数：
- `key`: 要刷新的缓存键

## 历史数据

历史数据API用于获取股票的历史数据。使用简化架构，直接从 AKShare 获取数据并缓存到 SQLite 数据库。

### 获取股票历史数据

```
GET /api/v1/historical/stock/{symbol}
```

**描述**: 获取指定股票的历史价格数据。系统会自动从数据库缓存中查找，如果数据不存在或过时，则从 AKShare 获取最新数据。

**参数**:
- `symbol` (必需): 6位数字股票代码，如 "000001"
- `start_date` (可选): 开始日期，格式为 YYYYMMDD，如 "20230101"
- `end_date` (可选): 结束日期，格式为 YYYYMMDD，如 "20231231"
- `adjust` (可选): 价格调整方法
  - `""` (默认): 无调整
  - `"qfq"`: 前复权
  - `"hfq"`: 后复权

**响应示例**:
```json
{
  "symbol": "000001",
  "name": "平安银行",
  "start_date": "20230101",
  "end_date": "20231231",
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
    "message": "Data retrieved successfully"
  }
}
```

## MCP查询

MCP（Market Context Protocol）查询API用于使用自然语言查询市场数据。

### 执行MCP查询

```
POST /api/v1/mcp/query
```

请求体：
```json
{
  "query": "查询平安银行最近一周的股价",
  "context": {
    "symbols": ["000001"],
    "timeframe": "1w"
  }
}
```

## 错误处理

所有API端点在发生错误时都会返回统一的错误响应格式：

### 标准错误响应格式

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "错误描述",
    "status_code": 400,
    "details": {},
    "path": "/api/v1/historical/stock/ABC",
    "timestamp": "2025-05-28T10:30:00.000Z"
  }
}
```

### 常见错误类型

**400 Bad Request** - 请求参数错误
```json
{
  "error": {
    "code": "BAD_REQUEST",
    "message": "Symbol must be a 6-digit number",
    "status_code": 400
  }
}
```

**404 Not Found** - 资源未找到
```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Asset not found",
    "status_code": 404
  }
}
```

**500 Internal Server Error** - 服务器内部错误
```json
{
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "Error fetching data: Connection timeout",
    "status_code": 500
  }
}
```

### HTTP状态码
- **200**: 成功
- **400**: 请求错误 (参数格式错误、缺少必需参数等)
- **404**: 资源未找到
- **422**: 验证错误 (请求体格式错误)
- **500**: 服务器内部错误 (数据获取失败、数据库错误等)
