# QuantDB 系统架构

**版本**: v2.0.0 | **状态**: 架构迁移完成 | **测试**: 259/259 通过

## 🎉 架构概述

QuantDB 已完成重大架构升级，从单体`src/`结构成功迁移到**模块化核心服务架构**。新架构实现了业务逻辑与API层的清晰分离，支持多种部署模式，为高性能股票数据缓存服务提供了更好的可维护性和扩展性。

### 🏗️ 架构演进成果
- ✅ **架构迁移完成**: 从`src/`单体结构迁移到`core/` + `api/`模块化架构
- ✅ **代码重构**: 77+文件完成导入路径更新，移除遗留代码
- ✅ **功能保持**: 100%功能完整性，零破坏性变更
- ✅ **测试验证**: 所有核心功能测试通过，集成测试正常

### 🎯 设计原则
- **模块化架构**: 清晰分离业务逻辑(`core/`)和API层(`api/`)
- **代码复用**: 核心业务逻辑在API、前端、云端部署间共享
- **依赖注入**: 使用FastAPI依赖注入系统，提高可测试性
- **多模式部署**: 支持API服务、前端界面、云端部署的灵活架构
- **数据质量第一**: 真实公司名称和财务指标，专业金融数据展示
- **性能优先**: 98.1%性能提升，响应时间优化到毫秒级

## 🏗️ 新架构结构

### 项目目录结构

```
quantdb/
├── core/                   ✅ 核心业务逻辑层
│   ├── models/            # 数据模型 (SQLAlchemy)
│   ├── services/          # 业务服务
│   ├── database/          # 数据库连接
│   ├── cache/             # 缓存层 (AKShare)
│   └── utils/             # 工具模块 (配置、日志、验证)
│
├── api/                    ✅ API服务层
│   ├── routes/            # FastAPI路由
│   ├── schemas/           # 请求/响应模式
│   ├── auth/              # 认证模块
│   ├── utils/             # API工具
│   └── main.py            # FastAPI应用
│
├── tests/                  ✅ 测试套件
│   ├── unit/              # 单元测试
│   ├── integration/       # 集成测试
│   └── e2e/               # 端到端测试
│
├── cloud/                  ✅ 云端部署
│   └── streamlit_cloud/   # Streamlit云端部署
│
├── quantdb_frontend/       ✅ 前端应用
│   └── app.py             # Streamlit前端
│
└── database/               ✅ 数据库文件
    └── stock_data.db      # SQLite数据库
```

### 架构层次图

```
┌─────────────────────────────────────────────────────────────────┐
│                     QuantDB v2.0 架构                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │   API 服务   │  │  前端界面    │  │  云端部署    │              │
│  │  (api/)     │  │(quantdb_    │  │(cloud/      │              │
│  │             │  │ frontend/)  │  │streamlit_   │              │
│  │ • FastAPI   │  │ • Streamlit │  │cloud/)      │              │
│  │ • Routes    │  │ • API Client│  │ • Integrated│              │
│  │ • Schemas   │  │ • Charts    │  │ • SQLite    │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
│         │                 │                 │                   │
│         └─────────────────┼─────────────────┘                   │
│                           │                                     │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                 Core Business Layer (core/)                │ │
│  │                                                             │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │ │
│  │  │   Models    │  │  Services   │  │  Database   │        │ │
│  │  │             │  │             │  │             │        │ │
│  │  │ • Asset     │  │ • StockData │  │ • Connection│        │ │
│  │  │ • StockData │  │ • AssetInfo │  │ • Session   │        │ │
│  │  │ • Metrics   │  │ • Cache     │  │ • Migration │        │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘        │ │
│  │                                                             │ │
│  │  ┌─────────────┐  ┌─────────────┐                         │ │
│  │  │    Cache    │  │    Utils    │                         │ │
│  │  │             │  │             │                         │ │
│  │  │ • AKShare   │  │ • Config    │                         │ │
│  │  │   Adapter   │  │ • Logger    │                         │ │
│  │  │             │  │ • Validator │                         │ │
│  │  └─────────────┘  └─────────────┘                         │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                           │                                     │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                    Data Layer                              │ │
│  │                                                             │ │
│  │  ┌─────────────┐              ┌─────────────┐              │ │
│  │  │   SQLite    │              │  AKShare    │              │ │
│  │  │  Database   │◄─────────────┤   API       │              │ │
│  │  │             │              │             │              │ │
│  │  │ • Assets    │              │ • 股票数据   │              │ │
│  │  │ • StockData │              │ • 资产信息   │              │ │
│  │  │ • Metrics   │              │ • 财务指标   │              │ │
│  │  └─────────────┘              └─────────────┘              │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## 🚀 部署模式

### 1. API 服务模式 (`api/`)
- **FastAPI应用**: 独立的RESTful API服务
- **模块化路由**: 清晰的路由组织结构
- **依赖注入**: 使用FastAPI依赖注入系统
- **数据验证**: 使用Pydantic进行请求/响应验证
- **错误处理**: 统一的错误响应格式和中间件
- **文档生成**: 自动生成OpenAPI文档
- **核心服务集成**: 直接使用`core/`层业务逻辑

### 2. 前端界面模式 (`quantdb_frontend/`)
- **Streamlit应用**: 本地前端界面
- **API客户端**: 调用后端API服务
- **图表展示**: 基于Plotly的数据可视化
- **用户交互**: 股票查询、资产信息、性能监控
- **数据导出**: CSV/Excel格式数据导出
- **模块化组件**: 页面、工具、测试分离

### 3. 云端部署模式 (`cloud/streamlit_cloud/`)
- **集成应用**: 直接使用核心服务，无需独立API
- **SQLite持久化**: 预构建数据库文件
- **Streamlit Cloud**: 优化的云端部署配置
- **完整功能**: 包含所有核心功能的单体应用
- **核心服务复用**: 使用统一的`core/`业务逻辑

## 🔧 核心服务层详解 (`core/`)

### 1. 数据模型层 (`core/models/`)
```python
from core.models import Asset, DailyStockData, IntradayStockData
```
- **Asset**: 股票资产信息模型，包含公司名称、财务指标
- **DailyStockData**: 日线数据模型，包含OHLCV和技术指标
- **IntradayStockData**: 分时数据模型，实时价格和成交数据
- **RequestLog**: 请求日志模型，API调用记录
- **DataCoverage**: 数据覆盖统计模型，数据质量跟踪
- **SystemMetrics**: 系统指标模型，性能监控数据

### 2. 业务服务层 (`core/services/`)
```python
from core.services import StockDataService, AssetInfoService, DatabaseCache
```
- **StockDataService**: 股票数据获取、存储、查询的核心服务
- **AssetInfoService**: 资产信息管理，从AKShare获取真实公司名称和财务指标
- **DatabaseCache**: 数据库缓存管理，智能缓存策略实现
- **TradingCalendar**: 交易日历服务，确保数据准确性
- **QueryService**: 统一查询服务，提供高级查询功能

### 3. 数据库层 (`core/database/`)
```python
from core.database import get_db, Base, engine
```
- **Connection**: SQLAlchemy数据库连接管理
- **Session**: 数据库会话管理和依赖注入
- **Base**: SQLAlchemy声明式基类
- **Migration**: 数据库迁移和初始化工具

### 4. 缓存层 (`core/cache/`)
```python
from core.cache import AKShareAdapter
```
- **AKShareAdapter**: AKShare数据源适配器，统一数据获取接口
- **智能缓存**: 基于交易日历的智能数据获取策略
- **错误处理**: 完善的异常处理和重试机制

### 5. 工具层 (`core/utils/`)
```python
from core.utils import config, logger, validators, helpers
```
- **Config**: 统一配置管理，支持多环境配置
- **Logger**: 统一日志系统，结构化日志记录
- **Validators**: 数据验证工具，股票代码、日期格式验证
- **Helpers**: 通用辅助函数，格式化、装饰器等

## 📊 数据流程和架构优势

### 核心服务数据流程
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  应用层      │    │  核心服务层   │    │   数据层     │
│             │    │             │    │             │
│ • api/      │───▶│ • core/     │───▶│ • SQLite    │
│ • frontend/ │    │   services/ │    │ • AKShare   │
│ • cloud/    │    │   models/   │    │             │
└─────────────┘    └─────────────┘    └─────────────┘
```

### 新架构数据获取流程
```
1. 应用请求 → 2. 核心服务 → 3. 检查数据库缓存
                     ↓
4. 返回数据 ← 5. 合并数据 ← 6. 调用AKShare (如需要)
```

### 智能缓存策略
1. **检查现有数据**: 查询数据库中已有的数据范围
2. **确定缺失数据**: 计算需要从AKShare获取的日期范围
3. **批量获取**: 分组连续日期，减少API调用
4. **存储数据**: 将新数据保存到数据库
5. **返回结果**: 合并缓存和新数据

### 多模式部署流程
- **API模式**: HTTP请求 → `api/` → `core/services` → 数据库
- **前端模式**: Streamlit界面 → API客户端 → `api/` → `core/services`
- **云端模式**: Streamlit界面 → 直接调用 `core/services` → 数据库

## 🎯 架构迁移优势

### 1. 模块化改进
- ✅ **清晰分离**: 业务逻辑(`core/`)与API层(`api/`)完全分离
- ✅ **代码复用**: 核心服务在多种部署模式间共享
- ✅ **依赖管理**: 清晰的模块依赖关系，避免循环依赖
- ✅ **测试友好**: 更容易进行单元测试和集成测试

### 2. 开发体验提升
- ✅ **导入清晰**: 从`src.*`到`core.*`和`api.*`的清晰导入路径
- ✅ **IDE支持**: 更好的代码补全和导航支持
- ✅ **调试便利**: 模块化结构便于问题定位和调试
- ✅ **文档生成**: 自动生成的API文档更加准确

### 3. 生产就绪性
- ✅ **可扩展性**: 支持独立扩展API服务和核心服务
- ✅ **部署灵活**: 支持多种部署模式和容器化
- ✅ **监控友好**: 更好的性能监控和错误追踪
- ✅ **维护性**: 降低代码维护成本和复杂度

## 🗄️ 数据模型

### 核心数据表结构

**Assets (资产表) - 增强版**
```sql
CREATE TABLE assets (
    asset_id INTEGER PRIMARY KEY,
    symbol VARCHAR(10) UNIQUE NOT NULL,
    name VARCHAR(100),                  -- 真实公司名称
    asset_type VARCHAR(20),
    exchange VARCHAR(20),
    currency VARCHAR(10),

    -- 增强字段
    industry VARCHAR(100),              -- 行业分类
    concept VARCHAR(200),               -- 概念分类
    listing_date DATE,                  -- 上市日期
    total_shares BIGINT,                -- 总股本
    circulating_shares BIGINT,          -- 流通股
    market_cap BIGINT,                  -- 总市值
    pe_ratio REAL,                      -- 市盈率
    pb_ratio REAL,                      -- 市净率
    roe REAL,                           -- 净资产收益率
    last_updated DATETIME,              -- 最后更新时间
    data_source VARCHAR(20)             -- 数据来源
);
```

**DailyStockData (日线数据表)**
```sql
CREATE TABLE daily_stock_data (
    id INTEGER PRIMARY KEY,
    asset_id INTEGER REFERENCES assets(asset_id),
    trade_date DATE NOT NULL,
    open REAL,
    high REAL,
    low REAL,
    close REAL,
    volume INTEGER,
    adjusted_close REAL,                    -- 复权价格
    turnover REAL,                          -- 成交额
    amplitude REAL,                         -- 振幅
    pct_change REAL,                        -- 涨跌幅
    change REAL,                            -- 涨跌额
    turnover_rate REAL                      -- 换手率
);
```

**IntradayStockData (分时数据表)**
```sql
CREATE TABLE intraday_stock_data (
    id INTEGER PRIMARY KEY,
    asset_id INTEGER REFERENCES assets(asset_id),
    capture_time DATETIME,
    trade_date DATE,
    latest_price REAL,
    pct_change REAL,
    change REAL,
    volume INTEGER,
    turnover REAL,
    amplitude REAL,
    high REAL,
    low REAL,
    open REAL,
    prev_close REAL,
    volume_ratio REAL,
    turnover_rate REAL,
    pe_ratio_dynamic REAL,
    pb_ratio REAL,
    total_market_cap REAL,
    circulating_market_cap REAL,
    speed_of_increase REAL,
    five_min_pct_change REAL,
    sixty_day_pct_change REAL,
    ytd_pct_change REAL,
    is_final BOOLEAN
);
```

**监控系统表**
```sql
-- 请求日志表
CREATE TABLE request_logs (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME,
    symbol VARCHAR(10),
    start_date VARCHAR(8),
    end_date VARCHAR(8),
    endpoint VARCHAR(100),
    response_time_ms REAL,
    status_code INTEGER,
    record_count INTEGER,
    cache_hit BOOLEAN,
    akshare_called BOOLEAN,
    cache_hit_ratio REAL,
    user_agent VARCHAR(500),
    ip_address VARCHAR(45)
);

-- 数据覆盖统计表
CREATE TABLE data_coverage (
    id INTEGER PRIMARY KEY,
    symbol VARCHAR(10) UNIQUE,
    earliest_date VARCHAR(8),
    latest_date VARCHAR(8),
    total_records INTEGER,
    first_requested DATETIME,
    last_accessed DATETIME,
    access_count INTEGER,
    last_updated DATETIME
);

-- 系统指标表
CREATE TABLE system_metrics (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME,
    total_symbols INTEGER,
    total_records INTEGER,
    db_size_mb REAL,
    avg_response_time_ms REAL,
    cache_hit_rate REAL,
    akshare_requests_today INTEGER,
    requests_today INTEGER,
    active_symbols_today INTEGER,
    performance_improvement REAL,
    cost_savings REAL
);
```

## 👨‍💻 开发者指南

### 新架构导入模式

```python
# 核心业务逻辑
from core.models import Asset, DailyStockData, IntradayStockData
from core.services import StockDataService, AssetInfoService, DatabaseCache
from core.cache import AKShareAdapter
from core.database import get_db
from core.utils import logger, validators, config

# API层
from api.main import app
from api.dependencies import get_stock_data_service
from api.schemas import AssetResponse, StockDataResponse
```

### 服务使用示例

```python
# 初始化核心服务
from core.database import get_db
from core.cache import AKShareAdapter
from core.services import StockDataService

db = next(get_db())
adapter = AKShareAdapter()
service = StockDataService(db, adapter)

# 使用业务逻辑
stock_data = service.get_stock_data("000001", "20240101", "20240131")
asset_info = service.get_asset_info("000001")
```

### API开发示例

```python
# 在 api/routes/ 中创建新路由
from fastapi import APIRouter, Depends
from core.services import StockDataService
from api.dependencies import get_stock_data_service
from api.schemas import StockDataResponse

router = APIRouter()

@router.get("/stocks/{symbol}", response_model=StockDataResponse)
async def get_stock(
    symbol: str,
    service: StockDataService = Depends(get_stock_data_service)
):
    return service.get_stock_data(symbol)
```

## 📈 架构迁移成果

### 迁移指标

| 指标 | 迁移前 (src/) | 迁移后 (core/ + api/) | 改进 |
|------|---------------|----------------------|------|
| **架构层次** | 1层 (单体) | 2层 (模块化) | ✅ 清晰分离 |
| **代码组织** | 混合结构 | 模块化结构 | ✅ 可维护性提升 |
| **导入路径** | src.* | core.* + api.* | ✅ 清晰明确 |
| **测试覆盖** | 95%+ | 95%+ | ✅ 保持完整 |
| **功能完整性** | 100% | 100% | ✅ 零破坏性变更 |
| **文件迁移** | - | 77+ 文件更新 | ✅ 全面迁移 |

### 性能特性
- **响应时间**: ~18ms (缓存命中)
- **性能提升**: 比AKShare快 98.1%
- **缓存命中率**: 通常 > 90%
- **数据准确性**: 100% (基于官方交易日历)

### 数据质量
- **真实公司名称**: 100% 显示真实公司名称
- **财务指标完整性**: PE、PB、ROE等关键指标
- **数据覆盖**: 支持A股全市场数据
- **更新频率**: 按需更新，智能缓存策略

## 🛠️ 技术栈

### 核心技术
- **Web框架**: FastAPI 0.104+ (API层)
- **ORM**: SQLAlchemy 2.0+ (数据模型)
- **数据库**: SQLite 3.x (数据存储)
- **数据源**: AKShare 1.12+ (股票数据)
- **验证**: Pydantic 2.0+ (数据验证)

### 前端技术
- **框架**: Streamlit 1.28+ (用户界面)
- **图表**: Plotly 5.17+ (数据可视化)
- **数据处理**: Pandas 2.1+ (数据分析)
- **HTTP客户端**: httpx 0.25+ (API调用)

### 开发工具
- **测试**: pytest 7.4+ (测试框架)
- **代码质量**: black, flake8 (代码格式化)
- **类型检查**: mypy (静态类型检查)
- **文档**: 自动生成OpenAPI文档

## 🚀 部署架构

### 本地开发模式
```bash
# 启动后端API
cd quantdb
python api/main.py

# 启动前端 (新终端)
cd quantdb_frontend
streamlit run app.py
```

### 云端集成模式
```bash
# Streamlit Cloud部署
cd cloud/streamlit_cloud
streamlit run app.py
```

### 容器化部署 (规划中)
```yaml
# docker-compose.yml
version: '3.8'
services:
  api:
    build: ./api
    ports:
      - "8000:8000"
    volumes:
      - ./database:/app/database

  frontend:
    build: ./quantdb_frontend
    ports:
      - "8501:8501"
    depends_on:
      - api
```

---

## 🎉 总结

QuantDB v2.0 架构迁移已成功完成，实现了从单体`src/`结构到模块化`core/` + `api/`架构的重大升级。新架构提供了：

- ✅ **清晰的模块分离**: 业务逻辑与API层完全分离
- ✅ **更好的代码复用**: 核心服务在多种部署模式间共享
- ✅ **增强的可维护性**: 模块化结构便于开发和调试
- ✅ **生产就绪**: 支持多种部署模式和扩展需求

**架构迁移完成，项目进入v2.0时代！** 🚀

---

*最后更新: 2025-06-20 | 架构版本: v2.0.0*
