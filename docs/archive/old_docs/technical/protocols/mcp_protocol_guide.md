# MCP (Model Context Protocol) 使用指南

## 文档信息
**文档类型**: 技术指南
**文档编号**: quantdb-TECH-005
**版本**: 1.0.0
**创建日期**: 2025-07-01
**最后更新**: 2025-07-01
**状态**: 已发布
**负责人**: frank

## 1. 概述

MCP (Model Context Protocol) 是 QuantDB 的核心协议，用于将自然语言查询转换为结构化数据响应。它允许用户使用自然语言查询金融数据，而不需要了解底层 API 的具体细节。

MCP 协议的主要特点：

- **自然语言理解**：支持中英文自然语言查询
- **意图识别**：能够识别用户查询的意图
- **实体提取**：从查询中提取关键实体，如股票代码、日期范围等
- **上下文感知**：能够在会话中保持上下文
- **结构化响应**：返回结构化的 JSON 数据，便于前端展示

## 2. 基本用法

### 2.1 API 端点

MCP 协议的主要 API 端点为：

```
POST /api/v1/mcp/query
```

### 2.2 请求格式

请求体应为 JSON 格式，包含以下字段：

```json
{
  "query": "查询平安银行最近一周的股价",
  "context": {
    "symbols": ["000001"],
    "timeframe": "1w"
  },
  "session_id": "user_session_123",
  "response_type": "structured"
}
```

字段说明：

- `query`：自然语言查询（必填）
- `context`：上下文信息（可选）
- `session_id`：会话 ID，用于跟踪上下文（可选）
- `response_type`：响应类型，目前支持 "structured"（可选，默认为 "structured"）

### 2.3 响应格式

响应体为 JSON 格式，包含以下字段：

```json
{
  "query": "查询平安银行最近一周的股价",
  "intent": "get_price",
  "data": {
    "asset": {
      "asset_id": 1,
      "symbol": "000001",
      "name": "平安银行",
      "exchange": "SZSE"
    },
    "date_range": {
      "start_date": "2025-06-24",
      "end_date": "2025-07-01"
    },
    "prices": [
      {
        "date": "2025-07-01",
        "open": 15.2,
        "high": 15.5,
        "low": 15.1,
        "close": 15.3,
        "volume": 12345678,
        "adjusted_close": 15.3
      },
      // ...更多价格数据
    ],
    "message": "平安银行 (000001) 从 2025-06-24 到 2025-07-01 的价格数据。"
  },
  "context": {
    "last_entities": {
      "symbol": "000001",
      "asset_name": "平安银行",
      "days": 7,
      "start_date": "2025-06-24",
      "end_date": "2025-07-01"
    }
  },
  "session_id": "user_session_123",
  "metadata": {
    "status": "success",
    "processed_at": "2025-07-01T10:30:45.123456",
    "processing_metrics": {
      "intent_identification_time": 0.0012,
      "entity_extraction_time": 0.0034,
      "intent_processing_time": 0.1234,
      "total_time": 0.128
    }
  }
}
```

字段说明：

- `query`：原始查询
- `intent`：识别出的意图
- `data`：结构化数据响应
- `context`：更新后的上下文信息
- `session_id`：会话 ID
- `metadata`：元数据，包含处理时间等信息

## 3. 支持的意图

MCP 协议目前支持以下意图：

### 3.1 获取价格 (get_price)

获取特定资产的价格数据。

示例查询：
- "查询平安银行的股价"
- "显示贵州茅台最近一周的价格"
- "获取 000001 从 2025-01-01 到 2025-06-30 的股价"
- "What is the price of Apple stock?"
- "Show me AAPL prices for the last month"

### 3.2 获取趋势 (get_trend)

获取特定资产的价格趋势。

示例查询：
- "查询平安银行的走势"
- "显示贵州茅台最近一个月的趋势"
- "How is Tesla stock performing?"
- "Show me the trend of MSFT for the last quarter"

### 3.3 获取资产信息 (get_asset_info)

获取特定资产的基本信息。

示例查询：
- "查询平安银行的信息"
- "显示贵州茅台的详细资料"
- "Tell me about Microsoft"
- "What is Apple Inc.?"

### 3.4 列出资产 (list_assets)

列出可用的资产。

示例查询：
- "列出所有股票"
- "显示可用的资产"
- "List all available stocks"
- "What stocks do you have?"

### 3.5 比较资产 (compare_assets)

比较两个资产的表现。

示例查询：
- "比较平安银行和招商银行"
- "对比贵州茅台和五粮液"
- "Compare Apple and Microsoft"
- "How does Tesla compare to Nvidia?"

### 3.6 市场概览 (market_summary)

获取市场概览信息。

示例查询：
- "查询市场概况"
- "显示上证指数的状态"
- "What is the market doing today?"
- "Show me the market summary"

### 3.7 历史数据 (get_historical_data)

获取资产的历史数据。

示例查询：
- "查询平安银行的历史数据"
- "显示贵州茅台过去一年的历史价格"
- "Get historical data for Apple"
- "Show me MSFT's price history for the last 2 years"

## 4. 实体提取

MCP 协议能够从查询中提取以下实体：

### 4.1 股票代码 (symbol)

- 中国股票：6 位数字代码，如 "000001"、"600519"
- 美国股票：字母代码，如 "AAPL"、"MSFT"

### 4.2 资产名称 (asset_name)

- 中文名称：如 "平安银行"、"贵州茅台"
- 英文名称：如 "Apple"、"Microsoft"

### 4.3 日期范围

- 开始日期 (start_date)
- 结束日期 (end_date)
- 支持多种日期格式：
  - ISO 格式：YYYY-MM-DD
  - 中文格式：YYYY年MM月DD日
  - 美式格式：MM/DD/YYYY

### 4.4 时间周期

- 天数 (days)：如 "最近 7 天"、"last 30 days"
- 周数 (weeks)：如 "最近 2 周"、"last 4 weeks"
- 月数 (months)：如 "最近 3 个月"、"last 6 months"
- 季度数 (quarters)：如 "最近 2 个季度"、"last 2 quarters"
- 年数 (years)：如 "最近 1 年"、"last 2 years"

### 4.5 市场和指数

- 市场 (market)：如 "上海市场"、"深圳市场"
- 指数 (index)：如 "上证指数"、"深证成指"

### 4.6 比较实体

- 用于比较的两个资产

## 5. 最佳实践

### 5.1 使用会话 ID

为了保持上下文，建议在多次查询中使用相同的会话 ID：

```json
{
  "query": "查询平安银行的股价",
  "session_id": "user_123"
}
```

后续查询：

```json
{
  "query": "那贵州茅台呢？",
  "session_id": "user_123"
}
```

### 5.2 提供明确的实体

虽然 MCP 协议能够从自然语言中提取实体，但提供明确的实体可以提高准确性：

```json
{
  "query": "查询股价",
  "context": {
    "symbol": "000001",
    "start_date": "2025-01-01",
    "end_date": "2025-06-30"
  }
}
```

### 5.3 处理错误

当 MCP 无法理解查询或找不到数据时，会返回适当的错误消息：

```json
{
  "query": "查询不存在的股票",
  "intent": "get_price",
  "data": {
    "message": "找不到匹配的资产。请提供有效的股票代码或名称。"
  },
  "context": {...},
  "session_id": "user_123",
  "metadata": {...}
}
```

## 6. 限制和注意事项

- MCP 协议目前仅支持基本的金融数据查询，不支持复杂的分析或交易操作
- 自然语言理解能力有限，建议使用简单明确的查询语句
- 数据可用性取决于底层数据源，某些历史数据可能不可用
- 处理时间可能因查询复杂度和数据量而异

## 7. 更多示例

更多示例查询请参见 [MCP 示例查询](../../examples/mcp_example_queries.md) 文档。
