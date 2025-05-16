# QuantDB API 路由文档

本文档描述了QuantDB API的路由结构和使用方法。

## API前缀

所有API路由都使用统一的前缀：`/api/v1`

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

价格数据API用于获取资产的历史价格数据。

### 获取价格列表

```
GET /api/v1/prices/
```

参数：
- `asset_id`: 按资产ID筛选（可选）
- `symbol`: 按资产符号筛选（可选）
- `start_date`: 开始日期（可选）
- `end_date`: 结束日期（可选）
- `skip`: 要跳过的价格数量（默认：0）
- `limit`: 要返回的最大价格数量（默认：100，最大：1000）

### 获取资产的价格历史

```
GET /api/v1/prices/asset/{asset_id}
```

参数：
- `asset_id`: 资产ID
- `start_date`: 开始日期（可选）
- `end_date`: 结束日期（可选）
- `period`: 时间周期：daily, weekly, monthly（默认：daily）
- `limit`: 要返回的最大价格数量（默认：100，最大：1000）

### 按符号获取价格历史

```
GET /api/v1/prices/symbol/{symbol}
```

参数：
- `symbol`: 资产符号
- `start_date`: 开始日期（可选）
- `end_date`: 结束日期（可选）
- `limit`: 要返回的最大价格数量（默认：100，最大：1000）

## 数据导入

数据导入API用于从外部数据源导入数据。

### 导入股票数据

```
POST /api/v1/import/stock
```

请求体：
```json
{
  "symbol": "000001",
  "start_date": "20230101",
  "end_date": "20230131"
}
```

### 导入指数数据

```
POST /api/v1/import/index
```

请求体：
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

缓存管理API用于管理和监控缓存系统。

### 获取缓存状态

```
GET /api/v1/cache/status
```

返回缓存系统的状态和统计信息。

### 清除缓存

```
DELETE /api/v1/cache/clear
```

参数：
- `key`: 要清除的特定缓存键（可选，如果不提供则清除所有缓存）

### 获取缓存键列表

```
GET /api/v1/cache/keys
```

参数：
- `prefix`: 按前缀筛选键（可选）

### 获取缓存条目详情

```
GET /api/v1/cache/key/{key}
```

参数：
- `key`: 缓存键

### 刷新缓存条目

```
POST /api/v1/cache/refresh
```

参数：
- `key`: 要刷新的缓存键

## 历史数据

历史数据API用于获取股票的历史数据。

### 获取股票历史数据

```
GET /api/v1/historical/stock/{symbol}
```

参数：
- `symbol`: 股票符号
- `start_date`: 开始日期，格式为YYYYMMDD（可选）
- `end_date`: 结束日期，格式为YYYYMMDD（可选）
- `adjust`: 价格调整方法：'' (无调整), 'qfq' (前复权), 'hfq' (后复权)（可选，默认：''）

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

所有API端点在发生错误时都会返回标准的错误响应：

```json
{
  "detail": "错误描述",
  "message": "详细错误信息"
}
```

常见的HTTP状态码：
- 200: 成功
- 400: 请求错误
- 404: 资源未找到
- 500: 服务器内部错误
