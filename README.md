# QuantDB

![Version](https://img.shields.io/badge/version-0.9.0--beta-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![API](https://img.shields.io/badge/API-FastAPI-009688)
![Database](https://img.shields.io/badge/Database-SQLite-4169E1)
![Tests](https://img.shields.io/badge/Tests-259/259-success)
![Frontend](https://img.shields.io/badge/Frontend-Streamlit-FF4B4B)
![Performance](https://img.shields.io/badge/Cache-98.1%25_faster-brightgreen)
![Integration](https://img.shields.io/badge/Integration-Complete-success)
![Status](https://img.shields.io/badge/Status-Beta_Ready-orange)

高性能股票数据缓存服务，基于 AKShare 数据源，提供智能缓存、RESTful API 和专业前端界面。

**🎉 前后端集成完成！** 现已提供完整的端到端解决方案，包括高性能后端API和专业的Streamlit前端界面。

## 🎯 核心价值

- **🚀 极致性能**: 智能缓存比 AKShare 直接调用快 **98.1%**，响应时间 ~18ms
- **📊 数据准确**: 基于官方交易日历，确保股票数据的完整性和准确性
- **🏢 真实资产信息**: 显示真实公司名称（如"浦发银行"）而非技术代码（如"Stock 600000"）
- **💰 财务指标集成**: PE、PB、ROE等关键财务指标，来自AKShare实时数据
- **⚡ 智能缓存**: 自动识别交易日，避免无效 API 调用，显著提升效率
- **🔄 实时监控**: 完整的性能监控和数据覆盖跟踪
- **📝 统一日志**: 完全统一的日志系统，消除双重日志不一致性
- **🧹 简洁结构**: 敏捷开发清理，项目文件减少47%，维护更简单
- **🛡️ 生产就绪**: 完整的错误处理、186个测试100%通过、文档体系完善
- **📱 专业前端**: Streamlit界面，支持多种图表、性能监控、资产信息展示

## ⚡ 性能亮点

| 指标 | AKShare 直接调用 | QuantDB 缓存 | 性能提升 |
|------|------------------|--------------|----------|
| **响应时间** | ~1000ms | ~18ms | **98.1%** ⬆️ |
| **缓存命中** | 不适用 | 100% | **完美缓存** ✅ |
| **交易日识别** | 手动判断 | 自动识别 | **智能化** 🧠 |

## 🚀 快速开始

### 1. 安装和设置

```bash
# 克隆仓库
git clone https://github.com/franksunye/quantdb.git
cd quantdb

# 安装依赖
pip install -r requirements.txt

# 初始化数据库
python src/scripts/init_db.py
```

### 2. 启动服务

#### 方法1: 一键启动 (推荐)
```bash
# 进入前端目录并运行启动脚本
cd quantdb_frontend
python start.py
# 脚本会自动启动后端API和前端界面
```

#### 方法2: 手动启动
```bash
# 1. 启动后端API (在项目根目录)
python src/api/main.py

# 2. 启动前端界面 (在新终端)
cd quantdb_frontend
streamlit run app.py

# 访问地址
# 前端界面: http://localhost:8501
# API 文档: http://localhost:8000/docs
```

### 3. 使用 API

```bash
# 健康检查
curl http://localhost:8000/api/v1/health

# 获取股票数据（自动缓存，显示真实公司名称）
curl "http://localhost:8000/api/v1/historical/stock/600000?start_date=20240101&end_date=20240131"

# 获取资产信息（包含财务指标）
curl "http://localhost:8000/api/v1/assets/symbol/600000"

# 查看缓存状态
curl http://localhost:8000/api/v1/cache/status
```

### 4. 运行测试

```bash
# 运行后端测试
python scripts/test_runner.py --all

# 运行前端测试
cd quantdb_frontend
python run_tests.py

# 运行性能测试
python scripts/test_runner.py --performance
```

## 📁 核心架构

```
quantdb/
├── src/                           # 核心源码
│   ├── api/                       # FastAPI 应用
│   │   ├── main.py                # API 入口
│   │   ├── models.py              # 数据模型
│   │   └── routes/                # API 路由
│   ├── services/                  # 业务服务
│   │   ├── stock_data_service.py  # 股票数据服务
│   │   ├── asset_info_service.py  # 资产信息服务
│   │   ├── trading_calendar.py    # 交易日历服务
│   │   └── database_cache.py      # 数据库缓存
│   └── cache/                     # 缓存适配器
│       └── akshare_adapter.py     # AKShare 适配器
├── quantdb_frontend/              # 前端应用 🆕
│   ├── app.py                     # Streamlit 主应用
│   ├── pages/                     # 功能页面
│   ├── utils/                     # 工具模块
│   ├── tests/                     # 前端测试
│   └── start.py                   # 一键启动脚本
├── tests/                         # 后端测试套件
│   ├── unit/                      # 单元测试
│   ├── integration/               # 集成测试
│   ├── api/                       # API 测试
│   ├── e2e/                       # 端到端测试
│   └── performance/               # 性能测试
├── docs/                          # 项目文档
├── tools/                         # 开发工具
└── scripts/                       # 管理脚本
```

## 🔧 技术栈

- **后端**: FastAPI + SQLAlchemy + SQLite
- **前端**: Streamlit + Plotly + Pandas
- **数据源**: AKShare (官方股票数据)
- **缓存**: 智能数据库缓存 + 交易日历
- **测试**: pytest + unittest (259个测试，100%通过)
- **监控**: 实时性能监控和数据跟踪
- **日志**: 统一日志系统，完全一致的记录方式
- **集成**: 完整的前后端集成解决方案

## 📚 文档

| 文档 | 描述 |
|------|------|
| [📋 项目状态](./docs/00_BACKLOG.md) | 当前进展和优先级 |
| [📅 更新日志](./docs/01_CHANGELOG.md) | 版本历史和变更 |
| [🏗️ 系统架构](./docs/10_ARCHITECTURE.md) | 架构设计和组件 |
| [📊 API 文档](./docs/20_API.md) | 完整 API 使用指南 |
| [🛠️ 开发指南](./docs/30_DEVELOPMENT.md) | 开发环境和流程 |
| [🧪 测试指南](./docs/31_TESTING.md) | 测试运行和编写 |
| [📱 前端规划](./docs/40_FRONTEND.md) | 前端开发设计和规划 |
| [📋 前端任务](./docs/41_FRONTEND_BACKLOG.md) | 前端开发任务清单 |

## 🎯 项目状态

**当前版本**: v0.9.0-beta
**MVP 评分**: 9/10 (核心功能完成，需要人工端到端测试)
**测试覆盖**: 259/259 通过 (100%) - 222个后端 + 37个前端
**数据质量**: ⭐⭐⭐⭐⭐ (5/5) - 真实公司名称和财务指标
**前端体验**: ⭐⭐⭐⭐⭐ (5/5) - 专业量化数据平台界面
**集成状态**: ✅ 前后端完全集成
**生产就绪**: ⭐⭐⭐⭐☆ (4/5) - 需要人工验证

### ✅ 最新成就 (v0.9.0-beta)

**🎉 前后端集成完成 (2025-06-15)**:
- **📱 完整前端应用**: 基于Streamlit的专业量化数据平台界面
- **🔗 端到端集成**: 前后端完全集成，数据流验证通过
- **📈 多种图表支持**: 价格趋势、K线图、成交量、收益率分析、性能对比
- **📊 资产信息展示**: 真实公司名称、财务指标、数据覆盖情况完整展示
- **⚡ 性能监控**: 缓存命中率、响应时间对比、实时性能测试
- **🧪 完整测试**: 259个测试全部通过，包含前后端集成测试
- **🚀 一键启动**: 自动化启动脚本，完整的部署文档

**🔥 资产档案增强 (2025-01-30)**:
- **🏢 真实公司名称**: "浦发银行"替代"Stock 600000"，用户体验显著提升
- **💰 财务指标集成**: PE、PB、ROE等关键指标，来自AKShare实时数据
- **📊 市场数据完善**: 总股本、流通股、市值等完整信息
- **🔧 服务层增强**: AssetInfoService专业资产信息管理
- **🗄️ 数据库扩展**: Asset模型新增11个字段，自动迁移脚本
- **⚡ 智能缓存**: 资产信息缓存，避免重复API调用

**🎯 核心技术成就**:
- **智能缓存优化**: 基于官方交易日历，性能提升 98.1%
- **数据准确性**: 100% 准确的交易日识别
- **极致性能**: 缓存响应时间优化到 ~18ms
- **日志系统统一**: 完全统一的日志系统，消除双重日志不一致性
- **敏捷开发清理**: 项目结构简化，文件数量减少47%
- **完整测试**: 223个测试100%通过，包含后端、前端、性能测试和价值场景验证

### 🔮 下一步计划

**当前阶段 - 1.0版本准备**:
- **🧪 人工端到端测试**: 完整的用户场景验证
- **🐛 问题修复**: 修复测试中发现的问题
- **📚 文档完善**: 用户手册和部署指南
- **🔧 性能优化**: 首次查询体验优化

**第二阶段 - 功能增强 (V1.1-V1.3)**:
- **🎯 自选股管理**: 用户自定义股票清单和批量查询
- **📊 高级图表**: 技术指标、财务指标趋势分析
- **📤 数据导出**: CSV/Excel格式导出功能
- **🔍 智能搜索**: 按名称、行业、概念搜索股票

**第三阶段 - 生产部署**:
- **🐳 容器化部署**: Docker + docker-compose
- **🔐 安全认证**: API Key + JWT
- **📊 监控告警**: 健康检查和性能监控
- **☁️ 云端部署**: Vercel前端 + Supabase后端

## 📄 许可证

本项目采用 MIT 许可证 - 详情请参阅 [LICENSE](LICENSE) 文件

## 🔗 链接

- **GitHub**: [https://github.com/franksunye/quantdb](https://github.com/franksunye/quantdb)
- **API 文档**: http://localhost:8000/docs (启动服务后访问)
- **项目维护者**: frank

---

⭐ 如果这个项目对你有帮助，请给个 Star！
