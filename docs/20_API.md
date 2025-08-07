# QuantDB API 文档

**当前版本**: v2.2.6 | **状态**: 生产就绪 | **性能**: 98.1% 提升 | **多市场支持**: A股+港股 | **响应时间**: ~18ms
**新增功能**: ✅ 实时行情 + 股票列表 + 财务数据 + 指数数据 | **发布状态**: 已完成

## 🚀 核心亮点

- ✅ **多市场支持**: 统一API支持A股和港股数据查询
- ✅ **真实公司名称**: "浦发银行"、"腾讯控股"等真实公司信息
- ✅ **财务指标集成**: PE、PB、ROE等关键指标，来自AKShare实时数据
- ✅ **智能资产服务**: AssetInfoService专业资产信息管理
- ✅ **极致性能**: 缓存响应时间 ~18ms，比 AKShare 快 98.1%
- ✅ **智能缓存**: 基于真实交易日历，避免无效 API 调用
- ✅ **数据准确**: 100% 准确的交易日识别，确保数据完整性
- ✅ **完整测试**: 259个测试100%通过，确保API稳定性
- ✅ **云端集成**: 与Streamlit Cloud版本完全集成
- 🆕 **实时数据**: 实时股票行情和批量查询支持
- 🆕 **财务数据**: 完整的财务摘要和指标数据
- 🆕 **指数数据**: 主要市场指数历史和实时数据
- 🆕 **股票列表**: 完整的股票列表和筛选功能

## 快速开始

```bash
# 方式1: 启动独立API服务
python run_api.py
# 或
uvicorn api.main:app --reload

# 方式2: 启动集成版本 (推荐)
cd cloud/streamlit_cloud
streamlit run app.py

# API文档: http://localhost:8000/docs
# 健康检查: http://localhost:8000/health
```

## 📊 API版本信息

**当前版本**: v2.0.1 (生产版本)
**API版本**: v1 (当前) / v2 (计划中)
**发布日期**: 2025-06-23

### 版本端点

```bash
# 获取版本信息
GET /api/v1/version/
GET /api/v1/version/latest
GET /api/v1/version/v1

# 健康检查
GET /health
GET /api/v1/health
GET /api/v2/health
```

### 性能指标 (E2E测试验证)

**响应时间基准**:
- 健康检查: ~1ms ⚡
- 资产列表: ~9ms ⚡
- 首次数据请求: ~1.2秒 (含AKShare获取)
- 缓存命中: ~18ms (98.1%性能提升)

## 🔍 实时监控系统

**监控状态**: ✅ 完全集成到Streamlit Cloud版本

**访问监控功能**:
```bash
# Streamlit Cloud 监控界面 (推荐)
cd cloud/streamlit_cloud
streamlit run app.py

# 访问监控页面:
# - 系统状态: http://localhost:8501/System_Status
# - 性能监控: http://localhost:8501/Performance

# 直接调用监控服务 (开发用)
python -c "
from core.services.monitoring_service import MonitoringService
from core.database import get_db
db = next(get_db())
monitor = MonitoringService(db)
status = monitor.get_water_pool_status()
print(status)
"
```

**监控功能特性**:
- 🏊‍♂️ **蓄水池监控**: 缓存股票数量和数据记录数
- ⚡ **性能监控**: 实时响应时间和缓存命中率
- 💰 **成本分析**: AKShare调用减少量化
- 📊 **数据覆盖**: 时间跨度和数据分布情况
- 🔄 **请求统计**: 每个API调用的详细记录
- 📈 **趋势分析**: 历史性能数据和趋势图表
- 🎯 **实时测试**: 在线性能测试和基准对比

**监控数据收集**:
- ✅ **RequestLog**: 自动收集每个API请求
- ✅ **DataCoverage**: 跟踪数据范围和访问模式
- ✅ **性能跟踪**: 响应时间、缓存命中率、AKShare调用
- ✅ **用户行为**: IP地址、User-Agent、访问模式
- ✅ **可视化图表**: 性能对比、缓存命中率饼图、趋势图

## 🔗 API端点概览

### ✅ 当前可用端点 (v2.2.3)

#### 系统信息

```bash
# 健康检查
GET /health
GET /api/v1/health

# 版本信息
GET /api/v1/version/
GET /api/v1/version/latest

# API文档
GET /docs                    # Swagger UI
GET /api/v1/docs            # V1 API文档
```

### 资产管理

```bash
# 获取资产列表 (支持筛选)
GET /api/v1/assets?limit=100&symbol=600000&exchange=SHSE

# 获取特定资产 (包含财务指标)
GET /api/v1/assets/{asset_id}
GET /api/v1/assets/symbol/{symbol}

# 刷新资产信息 (从AKShare更新)
PUT /api/v1/assets/symbol/{symbol}/refresh
```

**资产信息响应示例**:
```json
{
  "asset_id": 1,
  "symbol": "600000",
  "name": "浦发银行",
  "isin": "CN600000",
  "asset_type": "stock",
  "exchange": "SHSE",
  "currency": "CNY",
  "industry": "银行",
  "concept": "银行股",
  "listing_date": "1999-11-10",
  "total_shares": 29352000000,
  "circulating_shares": 29352000000,
  "market_cap": 350000000000,
  "pe_ratio": 5.15,
  "pb_ratio": 0.55,
  "roe": 10.8,
  "last_updated": "2025-01-30T10:30:00",
  "data_source": "akshare"
}
```

**新增字段说明**:
- `industry`: 行业分类
- `concept`: 概念分类
- `listing_date`: 上市日期
- `total_shares`: 总股本
- `circulating_shares`: 流通股
- `market_cap`: 总市值
- `pe_ratio`: 市盈率
- `pb_ratio`: 市净率
- `roe`: 净资产收益率
- `last_updated`: 最后更新时间
- `data_source`: 数据来源

### 股票历史数据 (多市场统一API)

```bash
# 获取股票历史数据 (支持A股和港股)
GET /api/v1/historical/stock/{symbol}
GET /api/v1/stocks/stock/{symbol}  # 别名路由

# 查询参数:
# - symbol: 股票代码 (A股6位如600000，港股5位如00700)
# - start_date: 开始日期 YYYYMMDD (可选)
# - end_date: 结束日期 YYYYMMDD (可选)
# - adjust: 复权方式 "", "qfq", "hfq" (可选)
# - limit: 最大返回数量 (默认100)

# 示例:
GET /api/v1/historical/stock/600000?start_date=20240101&end_date=20240131
GET /api/v1/historical/stock/00700?limit=30  # 港股腾讯
```

**多市场支持特性**:
- 🌏 **A股+港股**: 统一API支持两大市场
- 🔄 **智能识别**: 自动识别股票代码所属市场
- 🧠 **统一格式**: 与AKShare保持完全一致的数据格式
- ⚡ **智能缓存**: 自动缓存和增量更新
- 💾 **持久化存储**: SQLite数据库持久化
- 📊 **真实公司信息**: 显示真实公司名称和财务指标

**A股响应示例**:
```json
{
  "symbol": "600000",
  "name": "浦发银行",
  "start_date": "20240101",
  "end_date": "20240131",
  "adjust": "",
  "data": [
    {
      "date": "2024-01-03",
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
    "message": "Successfully retrieved 1 data points",
    "market": "A股",
    "cache_hit": true
  }
}
```

**港股响应示例**:
```json
{
  "symbol": "00700",
  "name": "腾讯控股",
  "start_date": "20240101",
  "end_date": "20240131",
  "data": [
    {
      "date": "2024-01-03",
      "open": 320.0,
      "high": 325.0,
      "low": 318.0,
      "close": 322.5,
      "volume": 8765432,
      "turnover": 2821543210.0
    }
  ],
  "metadata": {
    "count": 1,
    "status": "success",
    "market": "港股",
    "cache_hit": false
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

### 🚀 计划新增端点 (v2.3.0 - 本月发布)

#### 实时行情数据 (🌟最高优先级)

```bash
# 获取单只股票实时行情
GET /api/v1/realtime/stock/{symbol}

# 批量获取实时行情
POST /api/v1/batch/realtime
```

#### 股票列表数据 (🌟高优先级)

```bash
# 获取所有股票列表
GET /api/v1/stocks/list

# 按市场筛选
GET /api/v1/stocks/list/{market}
```



### 缓存管理

```bash
# 获取缓存统计
GET /api/v1/cache/stats

# 缓存健康检查
GET /api/v1/cache/health

# 清除所有缓存数据 (保留资产信息)
DELETE /api/v1/cache/clear

# 清除特定股票的缓存
DELETE /api/v1/cache/clear/symbol/{symbol}

# 获取缓存详细信息
GET /api/v1/cache/info
```

### 批量操作

```bash
# 批量获取资产信息
POST /api/v1/batch/assets
# Body: {"symbols": ["600000", "000001", "00700"]}

# 批量获取股票数据
POST /api/v1/batch/stocks
# Body: {"symbols": ["600000", "000001"], "start_date": "20240101"}
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

## 📝 使用示例

### 系统检查

```bash
# 健康检查
curl http://localhost:8000/health

# 获取版本信息
curl http://localhost:8000/api/v1/version/

# 检查缓存状态
curl http://localhost:8000/api/v1/cache/stats
```

### A股查询示例

```bash
# 获取A股资产信息 (包含财务指标)
curl "http://localhost:8000/api/v1/assets/symbol/600000"

# 刷新A股资产信息
curl -X PUT "http://localhost:8000/api/v1/assets/symbol/600000/refresh"

# 获取A股历史数据 (显示真实公司名称)
curl "http://localhost:8000/api/v1/historical/stock/600000?start_date=20240101&end_date=20240131"

# 获取A股最近10天数据
curl "http://localhost:8000/api/v1/historical/stock/600000?limit=10"

# 获取A股前复权数据
curl "http://localhost:8000/api/v1/historical/stock/600000?adjust=qfq&limit=20"
```

### 港股查询示例

```bash
# 获取港股资产信息 (腾讯控股)
curl "http://localhost:8000/api/v1/assets/symbol/00700"

# 获取港股历史数据
curl "http://localhost:8000/api/v1/historical/stock/00700?start_date=20240101&end_date=20240131"

# 获取港股最近30天数据
curl "http://localhost:8000/api/v1/historical/stock/00700?limit=30"
```

### 批量操作示例

```bash
# 批量获取资产信息
curl -X POST "http://localhost:8000/api/v1/batch/assets" \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["600000", "000001", "00700"]}'

# 批量获取股票数据
curl -X POST "http://localhost:8000/api/v1/batch/stocks" \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["600000", "00700"], "start_date": "20240101", "limit": 10}'
```

## 🔄 版本升级指南

### 当前版本 v2.0.1 新特性

**✅ 新增功能**:
- 🇭🇰 **港股支持**: 完整支持港股数据查询 (5位代码)
- 📊 **监控集成**: 与Streamlit Cloud版本完全集成
- 🔗 **版本端点**: 新增版本信息API端点
- ⚡ **性能优化**: 缓存响应时间优化到18ms
- 🧪 **测试覆盖**: 259个测试100%通过

**🔧 API变更**:
- ✅ **保持兼容**: 所有现有端点保持向后兼容
- ✅ **新增路由**: `/api/v1/version/` 版本信息端点
- ✅ **增强响应**: 响应中新增 `market` 和 `cache_hit` 字段
- ✅ **批量操作**: 新增批量查询端点

### 从早期版本升级

**无需修改**:
- 所有 `/api/v1/historical/` 端点保持完全兼容
- 数据格式和字段保持一致
- 现有客户端代码无需修改

**建议升级**:
- 使用新的版本信息端点监控API状态
- 利用港股支持扩展数据覆盖
- 集成Streamlit Cloud版本获得更好的监控体验

## 🚀 部署和集成

### 独立API服务部署

```bash
# 克隆项目
git clone https://github.com/franksunye/quantdb.git
cd quantdb

# 安装依赖
pip install -r requirements.txt

# 启动API服务
python run_api.py
# 或
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

### Streamlit Cloud集成部署 (推荐)

```bash
# 启动集成版本
cd cloud/streamlit_cloud
streamlit run app.py

# 功能包含:
# - 完整API服务
# - Web界面
# - 实时监控
# - 性能测试
```

## 📚 相关资源

- **项目主页**: [GitHub Repository](https://github.com/franksunye/quantdb)
- **API文档**: http://localhost:8000/docs (启动后访问)
- **Streamlit界面**: http://localhost:8501 (集成版本)
- **监控页面**: http://localhost:8501/Performance
- **系统状态**: http://localhost:8501/System_Status

---

**最后更新**: 2025-06-23 | **文档版本**: v2.0.1
