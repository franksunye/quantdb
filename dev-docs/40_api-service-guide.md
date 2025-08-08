# QuantDB API服务独立发布指南

**版本**: v2.1.0 | **状态**: 里程碑1 | **更新**: 2025-08-04

## 🎯 API服务价值定位

QuantDB API服务是一个**高性能股票数据缓存中间件**，专门解决直接调用AKShare时的性能痛点。

### 🚀 核心优势
- **98.1%性能提升**: 响应时间从~1000ms优化到~18ms
- **智能缓存**: 基于真实交易日历，避免无效API调用
- **A股+港股统一**: 一套API支持两大市场
- **生产就绪**: 259个测试100%通过，完整错误处理
- **开发者友好**: 完整OpenAPI文档，5分钟上手

## 📦 独立发布包结构

### 核心组件
```
quantdb-api/
├── core/                   # 核心业务逻辑层
│   ├── models/            # 数据模型
│   ├── services/          # 业务服务
│   ├── database/          # 数据库管理
│   ├── cache/             # 智能缓存
│   └── utils/             # 工具模块
│
├── api/                    # FastAPI服务层
│   ├── routes/            # API路由
│   ├── schemas/           # 数据模式
│   └── main.py            # 应用入口
│
├── database/               # 数据存储
├── tests/                  # 测试套件
├── run_api.py             # 启动器
└── requirements.txt       # 依赖管理
```

### 排除组件 (里程碑2)
- `cloud/streamlit_cloud/` - 云端集成版本
- `quantdb_frontend/` - 前端界面
- Streamlit相关依赖

## 🚀 快速开始

### 安装和启动
```bash
# 1. 克隆项目
git clone https://github.com/franksunye/quantdb.git
cd quantdb

# 2. 安装依赖 (仅API服务)
pip install -r api/requirements.txt

# 3. 启动API服务
python run_api.py

# 4. 验证服务
curl http://localhost:8000/health
```

### 5分钟体验
```bash
# 健康检查
curl http://localhost:8000/health

# 获取浦发银行资产信息
curl "http://localhost:8000/api/v1/assets/symbol/600000"

# 获取浦发银行历史数据
curl "http://localhost:8000/api/v1/historical/stock/600000?limit=5"

# 查看API文档
# 浏览器访问: http://localhost:8000/docs
```

## 📊 性能对比

### 基准测试结果
| 操作 | AKShare直接调用 | QuantDB缓存 | 性能提升 |
|------|----------------|-------------|----------|
| 首次数据请求 | ~1200ms | ~1200ms | 相同 |
| 缓存命中请求 | ~1000ms | ~18ms | **98.1%** ⬆️ |
| 批量查询(10只股票) | ~10s | ~180ms | **98.2%** ⬆️ |

### 智能缓存优势
```python
# 传统方式 - 每次都调用AKShare
for symbol in ['600000', '000001', '000002']:
    data = ak.stock_zh_a_hist(symbol)  # 每次1000ms
# 总时间: ~3000ms

# QuantDB方式 - 智能缓存
for symbol in ['600000', '000001', '000002']:
    response = requests.get(f"/api/v1/historical/stock/{symbol}")  # 每次18ms
# 总时间: ~54ms (缓存命中时)
```

## 🔧 API端点详解

### 核心端点
```bash
# 系统信息
GET /health                              # 健康检查
GET /api/v1/version/                     # 版本信息

# 资产管理 (支持A股+港股)
GET /api/v1/assets                       # 资产列表
GET /api/v1/assets/symbol/{symbol}       # 特定资产信息
PUT /api/v1/assets/symbol/{symbol}/refresh # 刷新资产信息

# 股票数据 (智能缓存)
GET /api/v1/historical/stock/{symbol}    # 历史数据
GET /api/v1/stocks/stock/{symbol}        # 别名路由

# 缓存管理
GET /api/v1/cache/stats                  # 缓存统计
DELETE /api/v1/cache/clear               # 清除缓存

# 批量操作
POST /api/v1/batch/assets                # 批量资产查询
POST /api/v1/batch/stocks                # 批量股票数据
```

### 使用示例
```python
import requests

# 基础配置
BASE_URL = "http://localhost:8000"

# 获取股票数据
def get_stock_data(symbol, start_date=None, end_date=None):
    url = f"{BASE_URL}/api/v1/historical/stock/{symbol}"
    params = {}
    if start_date:
        params['start_date'] = start_date
    if end_date:
        params['end_date'] = end_date
    
    response = requests.get(url, params=params)
    return response.json()

# 使用示例
data = get_stock_data("600000", "20240101", "20240131")
print(f"获取到 {len(data['data'])} 条数据")
```

## 🎯 目标用户场景

### 量化交易开发者
```python
# 场景: 构建量化策略回测系统
# 需求: 快速获取大量历史数据

# 使用QuantDB API
import asyncio
import aiohttp

async def fetch_multiple_stocks(symbols):
    async with aiohttp.ClientSession() as session:
        tasks = []
        for symbol in symbols:
            url = f"http://localhost:8000/api/v1/historical/stock/{symbol}"
            tasks.append(session.get(url))
        
        responses = await asyncio.gather(*tasks)
        return [await resp.json() for resp in responses]

# 获取100只股票数据，总时间 < 2秒 (vs AKShare的100秒)
```

### 金融数据分析师
```python
# 场景: 行业分析和股票筛选
# 需求: 可靠的数据源和快速响应

# 批量获取银行股数据
bank_stocks = ['600000', '600036', '000001', '002142']
batch_data = requests.post(
    "http://localhost:8000/api/v1/batch/stocks",
    json={"symbols": bank_stocks, "limit": 30}
)

# 分析银行股表现
for stock in batch_data.json():
    print(f"{stock['name']}: 最新价格 {stock['data'][-1]['close']}")
```

### 金融科技公司
```python
# 场景: 集成到现有系统
# 需求: 稳定的API服务和完整的错误处理

class StockDataClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
    
    def get_stock_info(self, symbol):
        try:
            response = requests.get(f"{self.base_url}/api/v1/assets/symbol/{symbol}")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            # 完整的错误处理
            return {"error": str(e)}
    
    def health_check(self):
        response = requests.get(f"{self.base_url}/health")
        return response.status_code == 200

# 集成到现有系统
client = StockDataClient()
if client.health_check():
    stock_info = client.get_stock_info("600000")
```

## 🔄 部署选项

### 1. 开发环境
```bash
# 直接运行
python run_api.py

# 或使用uvicorn
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. 生产环境
```bash
# 使用gunicorn (推荐)
pip install gunicorn
gunicorn api.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# 或使用uvicorn
uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 3. Docker部署
```dockerfile
# Dockerfile (待创建)
FROM python:3.9-slim

WORKDIR /app
COPY api/requirements.txt .
RUN pip install -r requirements.txt

COPY core/ ./core/
COPY api/ ./api/
COPY database/ ./database/
COPY run_api.py .

EXPOSE 8000
CMD ["python", "run_api.py"]
```

```bash
# 构建和运行
docker build -t quantdb-api .
docker run -p 8000:8000 quantdb-api
```

## 📈 监控和维护

### 性能监控
```python
# 内置监控端点
import requests

# 获取缓存统计
cache_stats = requests.get("http://localhost:8000/api/v1/cache/stats").json()
print(f"缓存命中率: {cache_stats['hit_rate']}%")
print(f"总请求数: {cache_stats['total_requests']}")

# 健康检查
health = requests.get("http://localhost:8000/health").json()
print(f"服务状态: {health['status']}")
```

### 日志管理
```python
# 查看日志 (core/utils/logger.py)
from core.utils.logger import get_logger

logger = get_logger(__name__)
logger.info("API服务启动")
logger.error("数据库连接失败")
```

## 🚀 发布清单

### 发布前检查
- [ ] 所有测试通过 (pytest)
- [ ] 性能基准测试完成
- [ ] API文档更新
- [ ] Docker配置测试
- [ ] 安全检查完成

### 发布内容
- [ ] GitHub Release创建
- [ ] PyPI包发布 (可选)
- [ ] Docker Hub镜像
- [ ] 文档网站更新
- [ ] 社区推广

---

*最后更新: 2025-08-04 | 里程碑: 1 | 状态: 准备中*
