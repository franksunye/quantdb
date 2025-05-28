# QuantDB: 面向Agent时代的开源金融智能中间件平台

![Version](https://img.shields.io/badge/version-0.3.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![API](https://img.shields.io/badge/API-FastAPI-009688)
![Database](https://img.shields.io/badge/Database-SQLite%2FPostgreSQL-4169E1)

## 项目概述

QuantDB是一个面向Agent时代的开源金融智能中间件平台，通过MCP（Model Context Protocol）协议标准化自然语言与金融数据之间的接口，提供结构化的金融数据服务。作为一个数据提供者，QuantDB专注于高质量的数据API服务，让外部系统（如Agent或LLM）能够轻松获取和处理金融数据。

### 核心特点

- **高质量数据服务**：提供结构化、标准化的金融数据API
- **MCP协议支持**：将自然语言请求转化为结构化查询
- **Agent友好接口**：设计适合Agent和LLM调用的API结构
- **开放式数据服务**：整合多种金融数据源，提供统一的数据访问接口

### 设计理念

- **专注数据，不含图表**：专注于提供高质量的数据服务，图表生成由外部调用方实现
- **API优先**：以API为中心的设计，提供完整的数据访问能力
- **云原生部署**：设计用于部署在Supabase和Vercel等现代云服务上

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

### API使用示例

```bash
# 获取API信息
curl http://localhost:8000/

# 健康检查
curl http://localhost:8000/api/v1/health
```

### 数据API（Sprint 2将实现）

```bash
# 获取资产列表
curl http://localhost:8000/api/v1/assets

# 获取特定资产详情
curl http://localhost:8000/api/v1/assets/1

# 获取资产价格历史
curl http://localhost:8000/api/v1/assets/1/prices
```

### MCP协议（Sprint 2将实现）

```bash
# 使用自然语言查询数据
curl -X POST http://localhost:8000/api/v1/mcp/query \
  -H "Content-Type: application/json" \
  -d '{"query": "显示上证指数最近30天的走势"}'
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
│   ├── migrations/                # 数据库迁移文件
│   └── stock_data.db              # SQLite数据库文件
│
├── docs/                          # 项目文档
│   ├── 00_document_standards.md   # 文档标准
│   ├── ci_cd_setup.md             # CI/CD设置指南
│   ├── database_schema.md         # 数据库架构文档
│   ├── development_environment.md # 开发环境设置
│   ├── supabase_setup.md          # Supabase设置指南
│   ├── vercel_setup.md            # Vercel设置指南
│   └── project_management/        # 项目管理文档
│       ├── quantdb_01_PLAN_mvp.md # MVP计划
│       └── quantdb_02_BOARD_mvp_sprint3.md # Sprint 3任务板
│
├── src/                           # 源代码目录
│   ├── api/                       # API模块
│   │   ├── __init__.py
│   │   ├── database.py            # 数据库连接
│   │   ├── main.py                # FastAPI应用
│   │   ├── models.py              # SQLAlchemy模型
│   │   └── schemas.py             # Pydantic模式
│   ├── mcp/                       # MCP协议模块
│   │   ├── __init__.py
│   │   ├── interpreter.py         # MCP解释器
│   │   └── schemas.py             # MCP模式
│   ├── scripts/                   # 工具脚本
│   │   ├── __init__.py
│   │   └── init_db.py             # 数据库初始化
│   ├── config.py                  # 配置文件
│   ├── database.py                # 旧数据库模块
│   ├── downloader.py              # 数据下载
│   ├── logger.py                  # 日志记录
│   ├── main.py                    # 主程序入口
│   └── updater.py                 # 数据更新
│
├── tests/                         # 测试目录
│   ├── __init__.py
│   └── test_api.py                # API测试
│
├── .env                           # 环境变量
├── .env.example                   # 环境变量示例
├── .github/                       # GitHub配置
│   └── workflows/                 # GitHub Actions工作流
│       └── ci.yml                 # CI配置
├── .gitignore                     # Git忽略文件
├── requirements.txt               # 项目依赖
├── setup_dev_env.py               # 开发环境设置脚本
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

- [开发环境设置](./docs/development_environment.md)
- [数据库架构](./docs/database_schema.md)
- [Supabase设置指南](./docs/supabase_setup.md)
- [Vercel设置指南](./docs/vercel_setup.md)
- [CI/CD设置指南](./docs/ci_cd_setup.md)
- [系统架构概览](./docs/03_system_architecture.md)

项目管理文档：

- [MVP计划](./docs/project_management/quantdb_01_PLAN_mvp.md)
- [Sprint 3任务板](./docs/project_management/quantdb_02_BOARD_mvp_sprint3.md)
- [项目状态评估](./docs/project_status_assessment.md)
- [代码整理计划](./docs/code_cleanup_plan.md)

## 开发路线图

### Sprint 1: 基础设施搭建 (已完成)
- 设置本地开发环境
- 创建FastAPI应用框架
- 设计数据库模型
- 实现基本API端点
- 配置CI/CD流程

### Sprint 2: 数据服务开发 (进行中)
- 实现资产API
- 开发价格数据API
- 创建数据导入服务
- 实现基本的MCP协议解析
- 开发数据查询功能

### Sprint 3: API增强与文档
- 增强API功能
- 开发API文档系统
- 实现API版本控制
- 增强MCP协议功能
- 开发API测试套件

### Sprint 4: 部署与优化
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
