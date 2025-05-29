# QuantDB: 面向Agent时代的开源金融智能中间件平台

![Version](https://img.shields.io/badge/version-0.7.1--simplified-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![API](https://img.shields.io/badge/API-FastAPI-009688)
![Database](https://img.shields.io/badge/Database-SQLite-4169E1)
![Tests](https://img.shields.io/badge/Tests-Passing-success)
![Architecture](https://img.shields.io/badge/Architecture-Simplified-brightgreen)

## 项目概述

QuantDB是一个专注于金融数据服务的开源中间件平台，提供结构化的金融数据API服务。作为一个数据提供者，QuantDB专注于高质量的数据API服务，让外部系统能够轻松获取和处理金融数据。

### 🎉 当前版本状态 (v0.7.1-simplified)

**✅ 功能简化完成** - 2025-01-27
**✅ 移除导入功能**
**✅ 专注核心数据API**
**✅ 所有测试通过**
**✅ 系统运行稳定**

当前版本完成了重要的功能简化，移除了导入功能以专注于核心的数据查询和缓存功能。系统现在使用统一的 `DailyStockData` 模型，与AKShare保持完全一致的数据格式和字段命名，提供更加简洁、专注的API体验。

### 核心特点

- **📊 高质量数据服务**：提供结构化、标准化的金融数据API
- **🔄 统一数据模型**：使用统一的 `DailyStockData` 模型，消除数据重复
- **📊 AKShare兼容**：与AKShare保持完全一致的数据格式和字段命名
- **⚡ 简化架构**：移除复杂缓存层，使用SQLite数据库作为主要缓存
- **🛠️ 高可维护性**：清晰的代码结构，统一的错误处理，全面的测试覆盖
- **🚀 开发友好**：快速搭建开发环境，完整的API文档，统一的测试管理

### 设计理念

- **专注数据，不含图表**：专注于提供高质量的数据服务，图表生成由外部调用方实现
- **API优先**：以API为中心的设计，提供完整的数据访问能力
- **简化优先**：优先选择简单可靠的解决方案，避免过度设计
- **渐进式部署**：先在SQLite开发环境中稳定，未来考虑云原生部署

## 快速开始

### 安装

```bash
# 克隆仓库
git clone https://github.com/franksunye/quantdb.git
cd quantdb

# 设置开发环境（创建目录、安装依赖、初始化数据库）
python setup_dev_env.py
```

### 运行API服务

```bash
# 启动API服务
uvicorn src.api.main:app --reload

# API文档访问地址
# http://localhost:8000/api/v1/docs
```

### 运行测试

```bash
# 运行所有测试
python scripts/test_runner.py --all

# 运行核心功能测试
python scripts/test_runner.py --unit --api

# 运行带覆盖率的测试
python scripts/test_runner.py --coverage
```

### API使用示例

```bash
# 获取API信息
curl http://localhost:8000/

# 健康检查
curl http://localhost:8000/api/v1/health
```

### 数据API

```bash
# 获取资产列表
curl http://localhost:8000/api/v1/assets

# 获取特定资产详情
curl http://localhost:8000/api/v1/assets/1

# 获取股票历史数据 (自动缓存)
curl "http://localhost:8000/api/v1/historical/stock/000001?start_date=20230101&end_date=20230131"

# 获取缓存状态
curl http://localhost:8000/api/v1/cache/status

# 清理缓存数据
curl -X DELETE "http://localhost:8000/api/v1/cache/clear/symbol/000001"
```

### 系统监控

```bash
# 监控蓄水池状态
python tools/monitoring/water_pool_monitor.py

# 系统性能监控 (包含基准测试)
python tools/monitoring/system_performance_monitor.py
```

## 项目结构

```
/
├── data/                          # 数据存储目录
│   ├── raw/                       # 原始数据
│   └── processed/                 # 处理过的数据
│
├── database/                      # 数据库相关文件
│   ├── schema.sql                 # 数据库初始化的SQL脚本
│   └── stock_data.db              # SQLite数据库文件
│
├── docs/                          # 项目文档
│   ├── 00_BACKLOG.md              # 待办事项清单
│   ├── 01_CHANGELOG.md            # 更新日志
│   ├── 10_ARCHITECTURE.md         # 系统架构文档
│   ├── 11_DATABASE.md             # 数据库文档
│   ├── 20_API.md                  # API文档
│   ├── 30_DEVELOPMENT.md          # 开发指南
│   ├── 31_TESTING.md              # 测试指南
│   └── archive/                   # 归档文档
│
├── logs/                          # 日志目录
│
├── src/                           # 源代码目录
│   ├── api/                       # API模块
│   │   ├── __init__.py
│   │   ├── cache_api.py           # 缓存API
│   │   ├── database.py            # 数据库连接
│   │   ├── errors.py              # 统一错误处理
│   │   ├── main.py                # FastAPI应用
│   │   ├── models.py              # SQLAlchemy模型
│   │   ├── schemas.py             # Pydantic模式
│   │   ├── version.py             # 版本信息
│   │   └── routes/                # API路由
│   │       ├── __init__.py
│   │       ├── assets.py          # 资产路由
│   │       ├── cache.py           # 缓存管理路由
│   │       ├── historical_data.py # 历史数据路由
│   │       └── version.py         # 版本路由
│   ├── cache/                     # 缓存模块
│   │   ├── __init__.py
│   │   ├── akshare_adapter.py     # AKShare适配器
│   │   └── models.py              # 缓存模型
│   ├── services/                  # 服务模块
│   │   ├── __init__.py
│   │   ├── database_cache.py      # 数据库缓存服务
│   │   ├── query.py               # 查询服务
│   │   └── stock_data_service.py  # 股票数据服务
│   ├── scripts/                   # 脚本模块
│   │   ├── __init__.py
│   │   └── init_db.py             # 数据库初始化
│   ├── config.py                  # 配置文件
│   ├── enhanced_logger.py         # 增强日志记录
│   └── logger.py                  # 基础日志记录
│
├── scripts/                       # 项目管理脚本
│   └── test_runner.py             # 统一测试运行器
│
├── tools/                         # 开发和运维工具
│   ├── README.md                  # 工具集说明
│   └── monitoring/                # 系统监控工具
│       ├── water_pool_monitor.py  # 蓄水池状态监控
│       └── system_performance_monitor.py  # 系统性能监控
│
├── tests/                         # 测试目录
│   ├── __init__.py
│   ├── conftest.py                # 测试配置
│   ├── init_test_db.py            # 测试数据库初始化
│   ├── test_api.py                # 基础API测试
│   ├── test_assets_api.py         # 资产API测试
│   ├── api/                       # API测试
│   │   ├── test_historical_data.py # 历史数据API测试
│   │   └── test_version_api.py     # 版本API测试
│   ├── integration/               # 集成测试
│   │   ├── test_error_handling_integration.py # 错误处理集成测试
│   │   ├── test_logging_integration.py # 日志集成测试
│   │   └── test_stock_data_flow.py # 股票数据流程测试
│   └── unit/                      # 单元测试
│       ├── test_akshare_adapter.py # AKShare适配器测试
│       ├── test_database_cache.py  # 数据库缓存测试
│       ├── test_enhanced_logger.py # 增强日志测试
│       ├── test_error_handling.py  # 错误处理测试
│       └── test_stock_data_service.py # 股票数据服务测试
│
├── requirements.txt               # 项目依赖
├── LICENSE                        # 许可证
└── README.md                      # 项目说明
```

## 核心功能

- **📊 数据API服务**：提供结构化的金融数据API接口
- **💾 智能缓存**：自动缓存股票历史数据，避免重复获取
- **🔄 AKShare集成**：与AKShare保持数据格式一致
- **🗄️ SQLite存储**：轻量级数据库存储，适合开发和小规模部署
- **🏊‍♂️ 水池监控**：实时监控数据蓄水情况，可视化缓存效果
- **🧪 全面测试**：单元测试、集成测试、API测试、E2E测试全覆盖
- **📝 完整文档**：API文档、架构文档、开发指南齐全

## 文档

详细文档请参阅[docs目录](./docs)：

### 项目概览 (推荐阅读顺序)
- [📝 00_待办事项](./docs/00_BACKLOG.md) - 项目现状和优先级 **（建议首先阅读）**
- [📅 01_更新日志](./docs/01_CHANGELOG.md) - 版本更新记录

### 架构设计
- [🏗️ 10_系统架构](./docs/10_ARCHITECTURE.md) - 系统架构设计
- [🗄️ 11_数据库文档](./docs/11_DATABASE.md) - 数据库设计和使用

### API使用
- [📋 20_API文档](./docs/20_API.md) - 完整的API使用指南

### 开发指南
- [🛠️ 30_开发指南](./docs/30_DEVELOPMENT.md) - 开发环境设置和开发流程
- [🧪 31_测试指南](./docs/31_TESTING.md) - 测试运行和编写指南

## 开发历程

### ✅ 已完成阶段

#### Phase 1: 基础架构 (v0.5.0)
- ✅ FastAPI应用框架
- ✅ SQLite数据库集成
- ✅ 基础API端点
- ✅ AKShare数据源适配

#### Phase 2: 核心功能 (v0.6.0)
- ✅ 资产管理API
- ✅ 历史数据API
- ✅ 智能缓存系统
- ✅ 错误处理和日志

#### Phase 3: 架构简化 (v0.7.0)
- ✅ 统一数据模型
- ✅ 简化缓存架构
- ✅ 全面测试覆盖
- ✅ 完整文档体系

#### Phase 4: 功能精简 (v0.7.1)
- ✅ 移除导入功能
- ✅ 专注核心API
- ✅ 代码质量提升
- ✅ 文档同步更新

### 🔮 未来规划

#### 高优先级
- 🔄 实时行情数据支持
- 📊 多周期历史数据（分钟线、周线）
- 💰 基础财务数据API

#### 中优先级
- 🔍 股票搜索和筛选
- 📈 技术指标计算
- 🌐 多市场支持（港股、美股）

#### 低优先级
- 🤖 MCP协议支持
- ☁️ 云原生部署
- 📊 数据可视化接口

## 贡献指南

欢迎贡献代码、报告问题或提出新功能建议。请遵循以下步骤：

1. Fork 仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证 - 详情请参阅 [LICENSE](LICENSE) 文件

## 联系方式

项目维护者: frank

项目链接: [https://github.com/franksunye/quantdb](https://github.com/franksunye/quantdb)
