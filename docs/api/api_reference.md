# QuantDB API 参考文档 V2

## 文档信息
**文档类型**: API 参考
**文档编号**: quantdb-API-002
**版本**: 1.0.0
**创建日期**: 2025-06-07
**最后更新**: 2025-06-07
**状态**: 草稿
**负责人**: frank

## 1. 概述

本文档提供了 QuantDB API V2 的详细参考信息。API V2 使用了简化的缓存架构和智能数据获取策略，提供了更高效的数据访问方式。

## 2. 基本信息

- **基础 URL**: `/api/v2`
- **认证方式**: API Key（通过 `X-API-Key` 请求头传递）
- **响应格式**: JSON
- **错误处理**: 使用标准 HTTP 状态码和详细的错误消息

## 3. 端点

### 3.1 股票历史数据

#### 获取股票历史数据

```
GET /historical/stock/{symbol}
```

获取指定股票的历史交易数据。

**路径参数**:
- `symbol` (必填): 股票代码，6 位数字

**查询参数**:
- `start_date` (可选): 开始日期，格式为 YYYYMMDD
- `end_date` (可选): 结束日期，格式为 YYYYMMDD
- `adjust` (可选): 价格调整方式，可选值为 `""` (不调整)、`qfq` (前复权)、`hfq` (后复权)

**响应**:
```json
{
  "symbol": "600000",
  "name": "浦发银行",
  "start_date": "20230101",
  "end_date": "20230110",
  "adjust": "",
  "data": [
    {
      "date": "2023-01-01",
      "open": 10.5,
      "high": 10.8,
      "low": 10.3,
      "close": 10.6,
      "volume": 12345678,
      "turnover": 123456789.0,
      "amplitude": 4.76,
      "pct_change": 0.95,
      "change": 0.1,
      "turnover_rate": 0.5
    },
    // 更多数据...
  ],
  "metadata": {
    "count": 10,
    "status": "success",
    "message": "Successfully retrieved 10 data points"
  }
}
```

**示例**:
```
GET /api/v2/historical/stock/600000?start_date=20230101&end_date=20230110&adjust=qfq
```

**错误响应**:
- `400 Bad Request`: 参数错误，例如股票代码格式不正确
- `404 Not Found`: 找不到指定的股票
- `500 Internal Server Error`: 服务器内部错误

### 3.2 数据库缓存状态

#### 获取数据库缓存状态

```
GET /database/cache/status
```

获取数据库缓存的状态信息。

**查询参数**:
- `symbol` (可选): 股票代码，用于查询特定股票的缓存状态
- `start_date` (可选): 开始日期，格式为 YYYYMMDD
- `end_date` (可选): 结束日期，格式为 YYYYMMDD

**响应**:
```json
{
  "total_assets": 100,
  "total_data_points": 1000000,
  "date_range": {
    "min_date": "2020-01-01",
    "max_date": "2023-12-31"
  },
  "top_assets": [
    {
      "symbol": "600000",
      "name": "浦发银行",
      "data_points": 1000
    },
    // 更多数据...
  ]
}
```

**示例**:
```
GET /api/v2/database/cache/status
```

**特定股票的缓存状态**:
```
GET /api/v2/database/cache/status?symbol=600000&start_date=20230101&end_date=20230110
```

响应:
```json
{
  "symbol": "600000",
  "start_date": "20230101",
  "end_date": "20230110",
  "coverage": {
    "coverage": 0.8,
    "total_dates": 10,
    "covered_dates": 8
  }
}
```

**错误响应**:
- `400 Bad Request`: 参数错误
- `500 Internal Server Error`: 服务器内部错误

## 4. 数据模型

### 4.1 股票历史数据点

| 字段 | 类型 | 描述 |
|------|------|------|
| date | string | 交易日期，格式为 YYYY-MM-DD |
| open | number | 开盘价 |
| high | number | 最高价 |
| low | number | 最低价 |
| close | number | 收盘价 |
| volume | number | 成交量 |
| turnover | number | 成交额 |
| amplitude | number | 振幅 (%) |
| pct_change | number | 涨跌幅 (%) |
| change | number | 涨跌额 |
| turnover_rate | number | 换手率 (%) |

### 4.2 缓存状态

| 字段 | 类型 | 描述 |
|------|------|------|
| coverage | number | 覆盖率，范围 0-1 |
| total_dates | number | 总日期数 |
| covered_dates | number | 已覆盖的日期数 |

## 5. 最佳实践

### 5.1 数据获取策略

1. **使用合适的日期范围**:
   - 避免请求过大的日期范围，这可能导致性能问题
   - 对于长期数据分析，考虑分批获取数据

2. **利用缓存机制**:
   - 系统会自动缓存已获取的数据，后续请求相同数据时会直接从缓存返回
   - 可以使用缓存状态 API 检查数据的缓存情况

3. **错误处理**:
   - 实现适当的错误处理机制，处理可能的 API 错误
   - 对于临时性错误，实现重试逻辑

### 5.2 性能优化

1. **最小化请求数量**:
   - 合并多个小请求为一个大请求
   - 避免频繁请求小范围数据

2. **并行处理**:
   - 对于需要获取多只股票数据的场景，考虑并行请求
   - 注意控制并发请求数量，避免超过服务器限制

## 6. 版本历史

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| 1.0.0 | 2025-06-07 | 初始版本 |
