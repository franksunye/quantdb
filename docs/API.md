# QuantDB API 文档

**版本**: v0.6.0-sqlite | **架构**: 简化架构 | **数据库**: SQLite

## 快速开始

```bash
# 启动API服务
uvicorn src.api.main:app --reload

# API文档: http://localhost:8000/api/v1/docs
# 健康检查: http://localhost:8000/api/v1/health
```

## 核心端点

### 资产管理

```bash
# 获取资产列表
GET /api/v1/assets

# 获取特定资产
GET /api/v1/assets/{asset_id}
GET /api/v1/assets/symbol/{symbol}
```

### 历史数据

```bash
# 获取股票历史数据
GET /api/v1/historical/stock/{symbol}?start_date=20230101&end_date=20231231

# 参数:
# - symbol: 6位股票代码 (如 000001)
# - start_date: 开始日期 YYYYMMDD (可选)
# - end_date: 结束日期 YYYYMMDD (可选)
# - adjust: 复权方式 "", "qfq", "hfq" (可选)
```

**响应示例**:
```json
{
  "symbol": "000001",
  "name": "平安银行",
  "data": [
    {
      "date": "2023-01-03",
      "open": 12.50,
      "high": 12.80,
      "low": 12.30,
      "close": 12.65,
      "volume": 1234567,
      "turnover": 15432100.50
    }
  ],
  "metadata": {
    "count": 1,
    "status": "success"
  }
}
```



### 数据导入

```bash
# 导入股票数据 (异步后台任务)
POST /api/v1/import/stock
Content-Type: application/json

{
  "symbol": "000001",
  "start_date": "20230101",
  "end_date": "20230131"
}
```

### 缓存管理

```bash
# 获取缓存状态
GET /api/v1/cache/status

# 清除缓存数据
DELETE /api/v1/cache/clear?table=prices
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
# 完整工作流程
curl "http://localhost:8000/api/v1/historical/stock/000001?start_date=20230101&end_date=20230131"

# 导入数据
curl -X POST http://localhost:8000/api/v1/import/stock \
  -H "Content-Type: application/json" \
  -d '{"symbol": "000001", "start_date": "20230101", "end_date": "20230131"}'

# 检查缓存状态
curl http://localhost:8000/api/v1/cache/status
```
