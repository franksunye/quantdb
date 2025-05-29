# QuantDB: 面向Agent时代的开源金融智能中间件平台

![Version](https://img.shields.io/badge/version-0.7.1--simplified-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![API](https://img.shields.io/badge/API-FastAPI-009688)
![Database](https://img.shields.io/badge/Database-SQLite-4169E1)
![Tests](https://img.shields.io/badge/Tests-Passing-success)
![Architecture](https://img.shields.io/badge/Architecture-Unified-brightgreen)

## 项目概述

QuantDB是一个面向Agent时代的开源金融智能中间件平台，通过MCP（Model Context Protocol）协议标准化自然语言与金融数据之间的接口，提供结构化的金融数据服务。作为一个数据提供者，QuantDB专注于高质量的数据API服务，让外部系统（如Agent或LLM）能够轻松获取和处理金融数据。

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

### MCP协议 (未来功能)

```bash
# 使用自然语言查询数据 (开发中)
curl -X POST http://localhost:8000/api/v1/mcp/query \
  -H "Content-Type: application/json" \
  -d '{"query": "显示上证指数最近30天的走势"}'
```

> ℹ️ **注意**: MCP协议支持将在未来版本中实现，当前版本专注于核心数据API功能的稳定性。

## 项目结构

```
/
├── data/                          # 数据存储目录
│   ├── raw/                       # 原始数据
│   └── processed/                 # 处理过的数据
│
├── database/                      # 数据库相关文件
│   ├── schema.sql                 # 数据库初始化的SQL脚本
│   ├── migrations/                # 数据库迁移文件
│   └── stock_data.db              # SQLite数据库文件
│
├── docs/                          # 项目文档
│   ├── 00_backlog.md              # 待办事项清单
│   ├── 00_document_standards.md   # 文档标准
│   ├── 01_requirements.md         # 需求文档
│   ├── 02_design.md               # 设计文档
│   ├── 03_system_architecture.md  # 系统架构文档
│   ├── 04_cache_system.md         # 缓存系统设计
│   ├── ci_cd_setup.md             # CI/CD设置指南
│   ├── database_schema.md         # 数据库架构文档
│   ├── development_environment.md # 开发环境设置
│   ├── supabase_setup.md          # Supabase设置指南
│   ├── vercel_setup.md            # Vercel设置指南
│   ├── archive/                   # 归档文档
│   └── project_management/        # 项目管理文档
│       ├── quantdb_01_PLAN_mvp.md # MVP计划
│       ├── quantdb_02_BOARD_mvp_sprint3.md # Sprint 3任务板
│       ├── quantdb_02_BOARD_mvp_sprint4.md # Sprint 4任务板
│       └── completed/             # 已完成的Sprint文档
│
├── logs/                          # 日志目录
│
├── src/                           # 源代码目录 (简化架构)
│   ├── api/                       # API模块
│   │   ├── __init__.py
│   │   ├── database.py            # 数据库连接
│   │   ├── main.py                # FastAPI应用
│   │   ├── models.py              # SQLAlchemy模型
│   │   ├── schemas.py             # Pydantic模式
│   │   ├── errors.py              # 统一错误处理
│   │   └── routes/                # API路由
│   │       ├── __init__.py
│   │       ├── assets.py          # 资产路由
│   │       ├── historical_data.py # 历史数据路由
│   │       └── cache.py           # 缓存管理路由
│   ├── cache/                     # 简化缓存模块
│   │   ├── __init__.py
│   │   └── akshare_adapter.py     # AKShare适配器
│   ├── services/                  # 服务模块
│   │   ├── __init__.py
│   │   ├── stock_data_service.py  # 股票数据服务
│   │   └── database_cache.py      # 数据库缓存服务
│   ├── mcp/                       # MCP协议模块 (未来功能)
│   │   ├── __init__.py
│   │   ├── interpreter.py         # MCP解释器
│   │   └── schemas.py             # MCP模式
│   ├── config.py                  # 配置文件
│   ├── logger.py                  # 增强日志记录
│   └── cli_main.py                # CLI主程序入口
│
├── scripts/                       # 项目管理脚本
│   ├── test_runner.py             # 统一测试运行器
│   ├── update_imports.py          # 自动更新引用
│   └── remove_trace_logger.py     # 清理过时代码
│
├── tools/                         # 分析工具
│   └── analysis/                  # 数据分析工具
│       ├── ma_ratio_calculator.py # MA比率计算器
│       ├── entry_window_analyzer.py # 入场窗口分析
│       └── trade_plan_analyzer.py  # 交易计划分析
│
├── examples/                      # 示例代码
│   └── trading/                   # 交易示例
│       ├── trade_log_generator.py  # 交易日志生成器
│       ├── optimization_importer.py # 优化结果导入器
│       └── signal_sender.py        # 信号发送器
│
├── tests/                         # 测试目录
│   ├── __init__.py
│   ├── e2e/                       # 端到端测试
│   │   ├── __init__.py
│   │   ├── test_stock_data_api_simplified.py # 简化API测试
│   │   └── test_stock_data_http_api.py # HTTP API测试
│   ├── integration/               # 集成测试
│   │   ├── __init__.py
│   │   └── test_akshare_adapter.py # AKShare适配器测试
│   └── unit/                      # 单元测试
│       ├── __init__.py
│       └── test_stock_data_service.py # 股票数据服务测试
│
├── .env                           # 环境变量
├── .env.example                   # 环境变量示例
├── .github/                       # GitHub配置
│   └── workflows/                 # GitHub Actions工作流
│       └── ci.yml                 # CI配置
├── .gitignore                     # Git忽略文件
├── check_database.py              # 数据库检查工具
├── fix_deprecation_warnings.py    # 修复弃用警告工具
├── import_gen_plan.bat            # 导入生成计划批处理文件
├── requirements.txt               # 项目依赖
├── run_stock_data_e2e_tests.py    # 运行端到端测试脚本
├── setup_dev_env.py               # 开发环境设置脚本
├── start_test_server.py           # 启动测试服务器脚本
└── README.md                      # 项目说明
```

## 核心功能

- **数据API服务**：提供结构化的金融数据API接口
- **数据获取与管理**：下载、存储和更新股票和指数数据
- **MCP协议支持**：支持自然语言到结构化查询的转换
- **数据库抽象**：支持本地SQLite和云端PostgreSQL数据库
- **认证与授权**：安全的API访问控制
- **云原生部署**：支持部署到Vercel和Supabase等云服务

## 文档

详细文档请参阅[docs目录](./docs)：

### 架构文档
- [系统架构概览](./docs/03_system_architecture.md)
- [缓存系统设计](./docs/04_cache_system.md)
- [数据库架构](./docs/database_schema.md)

### 开发指南
- [开发环境设置](./docs/development_environment.md)
- [Supabase设置指南](./docs/supabase_setup.md)
- [Vercel设置指南](./docs/vercel_setup.md)
- [CI/CD设置指南](./docs/ci_cd_setup.md)

### 项目管理文档
- [MVP计划](./docs/project_management/quantdb_01_PLAN_mvp.md)
- [MVP发布计划](./docs/project_management/quantdb_03_PLAN_mvp_release.md)
- [Sprint 3任务板](./docs/project_management/quantdb_02_BOARD_mvp_sprint3.md)
- [Sprint 4任务板](./docs/project_management/quantdb_02_BOARD_mvp_sprint4.md)
- [已完成Sprint文档](./docs/project_management/completed/)
- [项目状态评估](./docs/project_status_assessment.md)
- [代码整理计划](./docs/code_cleanup_plan.md)

## 开发路线图

### Sprint 1: 基础设施搭建 (已完成)
- 设置本地开发环境
- 创建FastAPI应用框架
- 设计数据库模型
- 实现基本API端点
- 配置CI/CD流程

### Sprint 2: 数据服务开发 (已完成)
- 实现资产API
- 开发历史数据API
- 实现数据缓存服务
- 开发数据查询功能

### Sprint 2.5: 缓存系统优化 (已完成)
- 简化缓存架构
- 实现智能数据获取策略
- 优化数据库查询
- 实现日期范围分段处理
- 完善端到端测试

### Sprint 2.6: 测试与稳定性 (已完成)
- 增强端到端测试
- 实现HTTP API测试
- 优化错误处理
- 改进日志记录
- 修复已知问题

### Sprint 3: API增强与文档 (进行中)
- 增强API功能
- 开发API文档系统
- 实现API版本控制
- 增强MCP协议功能
- 开发API测试套件

### Sprint 4: 部署与优化 (计划中)
- 部署API服务
- 配置Supabase数据库
- 实现API监控系统
- 进行端到端测试
- 性能优化

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
