# QuantDB API 使用示例

本文档提供了QuantDB API的使用示例，帮助开发者快速上手。

## 基本使用

所有API请求都应该发送到API的基础URL，例如：`http://localhost:8000`。

## 获取API信息

### 获取API欢迎信息

```bash
curl -X GET http://localhost:8000/
```

响应：
```json
{
  "message": "Welcome to QuantDB API v0.1.0",
  "documentation": "/docs",
  "endpoints": {
    "data_import": "/api/v1/data-import",
    "data_query": "/api/v1/data-query",
    "cache_management": "/api/v1/cache",
    "mcp": "/api/v1/mcp"
  }
}
```

### 获取API健康状态

```bash
curl -X GET http://localhost:8000/api/v1/health
```

响应：
```json
{
  "status": "healthy",
  "version": "0.1.0"
}
```

## 资产管理示例

### 获取资产列表

```bash
curl -X GET http://localhost:8000/api/v1/assets/
```

响应：
```json
{
  "items": [
    {
      "asset_id": 1,
      "symbol": "000001",
      "name": "平安银行",
      "isin": "CNE000000040",
      "asset_type": "stock",
      "exchange": "SZSE",
      "currency": "CNY"
    },
    {
      "asset_id": 2,
      "symbol": "600000",
      "name": "浦发银行",
      "isin": "CNE000000338",
      "asset_type": "stock",
      "exchange": "SSE",
      "currency": "CNY"
    }
  ],
  "total": 2,
  "page": 1,
  "size": 100
}
```

### 按符号获取资产

```bash
curl -X GET http://localhost:8000/api/v1/assets/symbol/000001
```

响应：
```json
{
  "asset_id": 1,
  "symbol": "000001",
  "name": "平安银行",
  "isin": "CNE000000040",
  "asset_type": "stock",
  "exchange": "SZSE",
  "currency": "CNY"
}
```

## 价格数据示例

### 获取资产的价格历史

```bash
curl -X GET "http://localhost:8000/api/v1/prices/asset/1?start_date=20230101&end_date=20230131"
```

响应：
```json
{
  "items": [
    {
      "price_id": 1,
      "asset_id": 1,
      "date": "2023-01-03",
      "open": 12.34,
      "high": 12.56,
      "low": 12.21,
      "close": 12.45,
      "volume": 123456789,
      "adjusted_close": 12.45
    },
    {
      "price_id": 2,
      "asset_id": 1,
      "date": "2023-01-04",
      "open": 12.45,
      "high": 12.67,
      "low": 12.32,
      "close": 12.56,
      "volume": 98765432,
      "adjusted_close": 12.56
    }
  ],
  "total": 20,
  "page": 1,
  "size": 100
}
```

### 按符号获取价格历史

```bash
curl -X GET "http://localhost:8000/api/v1/prices/symbol/000001?start_date=20230101&end_date=20230131"
```

响应与上面类似。

## 数据导入示例

### 导入股票数据

```bash
curl -X POST http://localhost:8000/api/v1/import/stock \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "000001",
    "start_date": "20230101",
    "end_date": "20230131"
  }'
```

响应：
```json
{
  "asset_id": 1,
  "symbol": "000001",
  "records_imported": 20,
  "start_date": "20230101",
  "end_date": "20230131",
  "success": true
}
```

### 导入指数数据

```bash
curl -X POST http://localhost:8000/api/v1/import/index \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "000001",
    "start_date": "20230101",
    "end_date": "20230131"
  }'
```

响应类似于导入股票数据的响应。

## 缓存管理示例

### 获取缓存状态

```bash
curl -X GET http://localhost:8000/api/v1/cache/status
```

响应：
```json
{
  "status": "active",
  "size": 1024,
  "items": 15,
  "hits": 150,
  "misses": 30,
  "hit_rate": 0.83
}
```

### 获取缓存键列表

```bash
curl -X GET http://localhost:8000/api/v1/cache/keys
```

响应：
```json
{
  "keys": [
    "get_stock_data_000001_20230101_20230131__daily",
    "get_stock_data_600000_20230101_20230131__daily",
    "import_stock_data_000001_20230101_20230131"
  ]
}
```

## 历史数据示例

### 获取股票历史数据

```bash
curl -X GET "http://localhost:8000/api/v1/historical/stock/000001?start_date=20230101&end_date=20230131"
```

响应：
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
      "open": 12.34,
      "high": 12.56,
      "low": 12.21,
      "close": 12.45,
      "volume": 123456789
    },
    {
      "date": "2023-01-04",
      "open": 12.45,
      "high": 12.67,
      "low": 12.32,
      "close": 12.56,
      "volume": 98765432
    }
  ],
  "metadata": {
    "count": 20,
    "source": "akshare",
    "cached": true
  }
}
```

## MCP查询示例

### 执行MCP查询

```bash
curl -X POST http://localhost:8000/api/v1/mcp/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "查询平安银行最近一周的股价",
    "context": {
      "symbols": ["000001"],
      "timeframe": "1w"
    }
  }'
```

响应：
```json
{
  "query": "查询平安银行最近一周的股价",
  "result": {
    "type": "price_data",
    "data": [
      {
        "date": "2023-01-03",
        "symbol": "000001",
        "name": "平安银行",
        "close": 12.45
      },
      {
        "date": "2023-01-04",
        "symbol": "000001",
        "name": "平安银行",
        "close": 12.56
      }
    ],
    "metadata": {
      "count": 5,
      "timeframe": "1w",
      "source": "akshare"
    }
  }
}
```

## 使用Python客户端

以下是使用Python请求库访问API的示例：

```python
import requests
import json

# 基础URL
base_url = "http://localhost:8000"

# 获取资产列表
response = requests.get(f"{base_url}/api/v1/assets/")
assets = response.json()
print(json.dumps(assets, indent=2))

# 导入股票数据
data = {
    "symbol": "000001",
    "start_date": "20230101",
    "end_date": "20230131"
}
response = requests.post(f"{base_url}/api/v1/import/stock", json=data)
result = response.json()
print(json.dumps(result, indent=2))

# 获取历史数据
response = requests.get(
    f"{base_url}/api/v1/historical/stock/000001",
    params={"start_date": "20230101", "end_date": "20230131"}
)
historical_data = response.json()
print(json.dumps(historical_data, indent=2))
```
