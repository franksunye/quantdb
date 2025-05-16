# QuantDB 开发指南 V2

## 文档信息
**文档类型**: 开发指南
**文档编号**: quantdb-DEV-002
**版本**: 1.0.0
**创建日期**: 2025-06-07
**最后更新**: 2025-06-07
**状态**: 草稿
**负责人**: frank

## 1. 概述

本文档为 QuantDB 开发人员提供指南，重点介绍简化的缓存架构和智能数据获取策略的使用方法。

## 2. 环境设置

### 2.1 开发环境

- Python 3.8+
- FastAPI
- SQLAlchemy
- AKShare
- 其他依赖项（见 requirements.txt）

### 2.2 安装依赖

```bash
pip install -r requirements.txt
```

### 2.3 数据库设置

```bash
# 创建数据库
python src/api/database.py

# 初始化数据
python src/api/init_db.py
```

## 3. 项目结构

```
src/
├── api/
│   ├── main.py                # FastAPI 应用
│   ├── database.py            # 数据库连接
│   ├── models.py              # 数据库模型
│   ├── schemas.py             # Pydantic 模型
│   └── routes/
│       ├── historical_data.py         # 历史数据路由（旧版）
│       └── historical_data_simplified.py  # 历史数据路由（新版）
├── cache/
│   ├── akshare_adapter.py             # AKShare 适配器（旧版）
│   ├── akshare_adapter_simplified.py  # AKShare 适配器（新版）
│   ├── cache_engine.py                # 缓存引擎（旧版）
│   └── freshness_tracker.py           # 新鲜度跟踪器（旧版）
├── services/
│   ├── stock_data_service.py          # 股票数据服务
│   └── database_cache.py              # 数据库缓存
└── logger.py                          # 日志配置

tests/
├── unit/                      # 单元测试
├── integration/               # 集成测试
└── e2e/                       # 端到端测试

docs/
├── api_reference_v2.md        # API 参考
├── 03_system_architecture_v2.md  # 系统架构
└── developer_guide_v2.md      # 开发指南
```

## 4. 核心组件

### 4.1 StockDataService

`StockDataService` 是新架构的核心组件，提供股票历史数据的获取、存储和查询功能。

#### 主要功能

- 检查数据库缓存中是否有请求的数据
- 确定缺失的数据范围
- 将缺失的日期分组为连续的日期范围
- 调用 AKShare 适配器获取缺失的数据
- 将获取的数据保存到数据库缓存
- 合并缓存数据和新获取的数据，返回完整结果

#### 使用示例

```python
from src.services.stock_data_service import StockDataService
from src.cache.akshare_adapter_simplified import AKShareAdapter
from src.api.database import get_db

# 获取数据库会话
db = next(get_db())

# 创建 AKShare 适配器
akshare_adapter = AKShareAdapter(db)

# 创建股票数据服务
stock_data_service = StockDataService(db, akshare_adapter)

# 获取股票历史数据
data = stock_data_service.get_stock_data(
    symbol="600000",
    start_date="20230101",
    end_date="20230110",
    adjust=""
)

# 处理数据
print(data)
```

### 4.2 DatabaseCache

`DatabaseCache` 提供数据库缓存接口，使用主数据库作为持久化缓存。

#### 主要功能

- 从数据库获取数据
- 保存数据到数据库
- 获取日期范围的覆盖情况
- 获取缓存统计信息

#### 使用示例

```python
from src.services.database_cache import DatabaseCache
from src.api.database import get_db

# 获取数据库会话
db = next(get_db())

# 创建数据库缓存
database_cache = DatabaseCache(db)

# 获取数据
data = database_cache.get(
    symbol="600000",
    dates=["20230101", "20230102", "20230103"]
)

# 获取日期范围的覆盖情况
coverage = database_cache.get_date_range_coverage(
    symbol="600000",
    start_date="20230101",
    end_date="20230110"
)

# 获取缓存统计信息
stats = database_cache.get_stats()
```

### 4.3 AKShareAdapter

`AKShareAdapter` 封装 AKShare API 调用，提供错误处理和重试逻辑。

#### 主要功能

- 调用 AKShare API 获取股票历史数据
- 处理 API 错误和异常
- 实现重试逻辑
- 生成模拟数据（用于测试）

#### 使用示例

```python
from src.cache.akshare_adapter_simplified import AKShareAdapter
from src.api.database import get_db

# 获取数据库会话
db = next(get_db())

# 创建 AKShare 适配器
akshare_adapter = AKShareAdapter(db)

# 获取股票历史数据
data = akshare_adapter.get_stock_data(
    symbol="600000",
    start_date="20230101",
    end_date="20230110",
    adjust=""
)

# 处理数据
print(data)
```

## 5. API 路由

### 5.1 历史数据路由

`historical_data_simplified.py` 提供了新的 API 端点，使用新的服务组件。

#### 主要端点

- `GET /api/v2/historical/stock/{symbol}`: 获取股票历史数据
- `GET /api/v2/database/cache/status`: 获取数据库缓存状态

#### 使用示例

```python
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from src.api.database import get_db
from src.services.stock_data_service import StockDataService
from src.cache.akshare_adapter_simplified import AKShareAdapter

app = FastAPI()

# 依赖项
def get_akshare_adapter(db: Session = Depends(get_db)):
    return AKShareAdapter(db)

def get_stock_data_service(
    db: Session = Depends(get_db),
    akshare_adapter: AKShareAdapter = Depends(get_akshare_adapter)
):
    return StockDataService(db, akshare_adapter)

# 路由
@app.get("/api/v2/historical/stock/{symbol}")
async def get_historical_stock_data(
    symbol: str,
    start_date: str = None,
    end_date: str = None,
    adjust: str = "",
    stock_data_service: StockDataService = Depends(get_stock_data_service)
):
    data = stock_data_service.get_stock_data(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        adjust=adjust
    )
    return {
        "symbol": symbol,
        "start_date": start_date,
        "end_date": end_date,
        "adjust": adjust,
        "data": data.to_dict(orient="records")
    }
```

## 6. 测试

### 6.1 单元测试

```bash
# 运行所有单元测试
python -m unittest discover tests/unit

# 运行特定测试
python -m unittest tests/unit/test_stock_data_service.py
```

### 6.2 集成测试

```bash
# 运行所有集成测试
python -m unittest discover tests/integration

# 运行特定测试
python -m unittest tests/integration/test_stock_data_flow.py
```

### 6.3 端到端测试

```bash
# 运行所有端到端测试
python -m unittest discover tests/e2e

# 运行特定测试
python -m unittest tests/e2e/test_stock_data_api.py
```

## 7. 最佳实践

### 7.1 数据获取

- 使用 `StockDataService` 获取股票历史数据，而不是直接使用 `AKShareAdapter`
- 使用合适的日期范围，避免请求过大的日期范围
- 对于长期数据分析，考虑分批获取数据

### 7.2 错误处理

- 实现适当的错误处理机制，处理可能的 API 错误
- 对于临时性错误，实现重试逻辑
- 记录详细的错误信息，便于排查问题

### 7.3 性能优化

- 使用批量操作，减少数据库交互次数
- 使用适当的索引，提高查询性能
- 使用连接池，减少连接开销

### 7.4 代码风格

- 遵循 PEP 8 代码风格
- 使用类型注解，提高代码可读性
- 编写详细的文档字符串，说明函数和类的用途
- 使用有意义的变量名和函数名

## 8. 常见问题

### 8.1 数据不一致

**问题**: 从 API 获取的数据与数据库中的数据不一致。

**解决方案**:
- 检查数据库中的数据是否过期
- 检查 API 调用参数是否正确
- 检查数据转换逻辑是否正确

### 8.2 性能问题

**问题**: API 响应时间过长。

**解决方案**:
- 检查数据库查询性能
- 检查 API 调用频率
- 考虑使用更细粒度的缓存策略

### 8.3 API 错误

**问题**: AKShare API 调用失败。

**解决方案**:
- 检查网络连接
- 检查 API 参数是否正确
- 实现重试逻辑
- 考虑使用模拟数据进行测试

## 9. 版本历史

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| 1.0.0 | 2025-06-07 | 初始版本 |
