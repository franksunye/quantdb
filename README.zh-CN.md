# QuantDB

*[English](README.md) | 中文版本*

![Version](https://img.shields.io/badge/version-2.2.7-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Python Package](https://img.shields.io/badge/PyPI-quantdb-blue)
![API](https://img.shields.io/badge/API-FastAPI-009688)
![Database](https://img.shields.io/badge/Database-SQLite-4169E1)
![Tests](https://img.shields.io/badge/Tests-259/259-success)
![Frontend](https://img.shields.io/badge/Frontend-Streamlit-FF4B4B)
![Cloud](https://img.shields.io/badge/Cloud-Ready-brightgreen)
![Performance](https://img.shields.io/badge/Cache-90%25_faster-brightgreen)
![Integration](https://img.shields.io/badge/Integration-Complete-success)
![Status](https://img.shields.io/badge/Status-Production_Ready-success)

**智能缓存的AKShare包装器，90%+性能提升** - 专为中国金融市场设计的完整股票数据生态系统，具备智能SQLite缓存功能。

**🎉 PyPI正式发布！**
[![PyPI version](https://badge.fury.io/py/quantdb.svg)](https://pypi.org/project/quantdb/)
[![Downloads](https://pepy.tech/badge/quantdb)](https://pepy.tech/project/quantdb)

```bash
pip install quantdb  # 一行命令，瞬间90%+速度提升！
```

```python
import qdb  # 注意：导入名是'qdb'，简洁易用
df = qdb.get_stock_data("000001", days=30)

# v2.2.7新功能：
realtime = qdb.get_realtime_data("000001")  # 实时行情
stocks = qdb.get_stock_list()  # 完整股票列表
financials = qdb.get_financial_summary("000001")  # 财务数据
```

**三种产品形态**：Python包、API服务、云平台，满足不同用户需求。

## 🎯 产品矩阵

### 📦 **QuantDB Python包** - 开发者首选
```bash
pip install quantdb
```
```python
import qdb  # 注意：包名是quantdb，导入名是qdb
df = qdb.get_stock_data("000001", days=30)  # 比AKShare快90%+！
```
**适用于**: 量化研究者、Python开发者、数据科学家
**导入说明**: 安装用`quantdb`，导入用`qdb`（类似scikit-learn → sklearn）

### 🚀 **API服务** - 企业级解决方案
```bash
curl "https://your-api.com/api/v1/stocks/000001/data?days=30"
```
**适用于**: 企业团队、多用户应用、生产系统

### ☁️ **云平台** - 个人投资者工具
访问: [QuantDB云平台](https://quantdb-cloud.streamlit.app)
**适用于**: 个人投资者、数据分析、可视化

## ✨ 核心特性

- **🚀 90%+性能提升**: 智能SQLite缓存，毫秒级响应
- **📦 多产品形态**: Python包、API服务、云平台
- **🔄 完全兼容AKShare**: 相同API接口，无缝替换
- **💾 本地缓存**: 离线可用，智能增量更新
- **📅 交易日历集成**: 基于真实交易日的智能数据获取
- **🛠️ 零配置启动**: pip安装即可使用
- **☁️ 云端部署就绪**: 支持Railway、Render、阿里云等
- **🧠 智能更新**: 自动检测缺失数据并获取
- **🛡️ 生产就绪**: 完整的错误处理、259个测试100%通过、文档体系完善
- **📱 专业前端**: 本地和云端双版本，支持多种图表、性能监控、资产信息展示
- **🔧 后端集成**: Cloud版本直接使用后端服务，查询真实数据库数据

## ⚡ 性能亮点

| 指标 | AKShare 直接调用 | QuantDB 缓存 | 性能提升 |
|------|------------------|--------------|----------|
| **响应时间** | ~1000ms | ~18ms | **98.1%** ⬆️ |
| **缓存命中** | 不适用 | 100% | **完美缓存** ✅ |
| **交易日识别** | 手动判断 | 自动识别 | **智能化** 🧠 |

## 📦 安装和导入

**重要说明**: 包名和导入名不同（Python生态系统中的常见做法）

```bash
# 安装包
pip install quantdb
```

```python
# 导入包（注意：导入名是'qdb'）
import qdb

# 立即开始使用
df = qdb.get_stock_data("000001", days=30)
stats = qdb.cache_stats()
```

**为什么使用不同的名称？**
- **包名**: `quantdb`（描述性强，便于在PyPI搜索）
- **导入名**: `qdb`（简洁，易于输入）
- **类似案例**: `scikit-learn` → `sklearn`, `beautifulsoup4` → `bs4`

## 🚀 快速开始

### 选项1: 云端访问 (推荐)
直接访问已部署的Streamlit Cloud版本：
- **前端界面**: [QuantDB Cloud](https://quantdb-cloud.streamlit.app)
- **功能完整**: 股票数据查询、资产信息、缓存监控、自选股管理

### 选项2: 本地部署

#### 1. 安装和设置

```bash
# 克隆仓库
git clone https://github.com/franksunye/quantdb.git
cd quantdb

# 安装依赖
pip install -r requirements.txt

# 初始化数据库
python src/scripts/init_db.py
```

#### 2. 启动服务

**方法1: 一键启动 (推荐)**
```bash
# 进入前端目录并运行启动脚本
cd quantdb_frontend
python start.py
# 脚本会自动启动后端API和前端界面
```

**方法2: 手动启动**
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

**方法3: 云端版本本地运行**
```bash
# 运行Streamlit Cloud版本 (集成后端服务)
cd cloud/streamlit_cloud
streamlit run app.py
# 访问地址: http://localhost:8501
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

## 🏗️ 架构概览

QuantDB 采用现代化的微服务架构，包含以下核心组件：

- **🔧 Core Services**: 统一的业务逻辑层，支持多种部署模式
- **📡 FastAPI Backend**: 高性能 REST API 服务
- **📱 Streamlit Frontend**: 交互式数据分析界面
- **☁️ Cloud Deployment**: 云端部署版本，支持 Streamlit Cloud
- **🧪 Comprehensive Testing**: 完整的测试套件，覆盖单元、集成、API、E2E测试
- **📊 Smart Caching**: 基于交易日历的智能缓存系统

详细的架构设计请参考 [系统架构文档](./docs/10_ARCHITECTURE.md)。

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
| [🗄️ 数据库架构](./docs/11_DATABASE_ARCHITECTURE.md) | 数据库设计和模型 |
| [📊 API 文档](./docs/20_API.md) | 完整 API 使用指南 |
| [🛠️ 开发指南](./docs/30_DEVELOPMENT.md) | 开发环境和流程 |
| [🧪 测试指南](./docs/31_TESTING.md) | 测试运行和编写 |

## 💬 反馈与支持（Support & Feedback）

- 问题/需求（Issues）：https://github.com/franksunye/quantdb/issues
- 讨论（Discussions：问答/Q&A、想法/Ideas、展示/Show & Tell）：https://github.com/franksunye/quantdb/discussions
- 社区与调研：见 docs/community/（入群指引、满意度调查）
- 推广链接与截图：见 docs/promo/links.md 和 docs/promo/screenshots/


## 🎯 项目状态

**当前版本**: v2.0.1 (已完整支持港股)
**下一版本**: v2.1.0 (监控和分析功能增强)
**MVP 评分**: 10/10 (核心功能完成，云端部署就绪)
**测试覆盖**: 259/259 通过 (100%) - 222个后端 + 37个前端
**数据质量**: ⭐⭐⭐⭐⭐ (5/5) - 真实公司名称和财务指标
**前端体验**: ⭐⭐⭐⭐⭐ (5/5) - 专业量化数据平台界面
**集成状态**: ✅ 前后端完全集成，云端部署就绪
**生产就绪**: ⭐⭐⭐⭐⭐ (5/5) - 云端部署版本完成
**云端部署**: ✅ Streamlit Cloud版本，直接使用后端服务

### ✅ 最新成就 (v2.0.1 - 港股支持完成)

**🇭🇰 港股支持功能完成 (2025-06-23)**:
- **🔍 港股代码识别**: 自动识别5位港股代码（00700、09988等）
- **📊 港股数据获取**: 完整支持港股历史数据查询和实时数据
- **🏢 港股资产信息**: 腾讯控股、阿里巴巴等知名港股公司信息
- **☁️ 云端港股支持**: Streamlit Cloud版本完整支持港股查询
- **🧪 港股测试覆盖**: 8个专门的港股测试用例，100%通过
- **🎯 混合市场支持**: A股和港股统一处理，无缝切换

**🚀 云端部署完成 (2025-06-20)**:
- **☁️ Streamlit Cloud版本**: 完整的云端部署解决方案，无需本地环境
- **🔧 后端服务集成**: Cloud版本直接使用后端服务，查询真实数据库数据
- **📊 功能完整性**: 股票数据查询、资产信息、缓存监控、自选股管理全部功能
- **⚡ 性能优化**: 浏览已有股票/资产功能使用QueryService查询真实数据
- **🎯 快速查询**: 资产信息页面添加快速查询按钮，提升用户体验
- **🧹 代码清理**: 移除无用的integrated_service.py，保持代码整洁
- **📱 双版本支持**: 本地开发版本和云端部署版本并行维护

### 🎉 前期成就 (v0.9.0-beta)

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

**当前阶段 - 云端部署优化 (V2.0.1)**:
- **🌐 Streamlit Cloud发布**: 正式发布云端访问地址
- **📊 云端监控**: 添加云端版本的性能监控和错误跟踪
- **🔧 用户反馈**: 收集云端版本使用体验并优化
- **📚 部署文档**: 完善云端部署和维护文档

**第二阶段 - 监控和分析功能增强 (V2.1)**:
- **📊 实时性能监控**: 增强的性能监控和数据跟踪
- **🔔 智能告警系统**: 数据异常和性能问题告警
- **📈 高级分析功能**: 技术指标、趋势分析、相关性分析
- **🎯 用户体验优化**: 界面优化和交互改进

**第三阶段 - 高级功能扩展 (V2.2-V2.3)**:
- **🔍 搜索和筛选**: 高级股票搜索和筛选功能
- **📱 移动端优化**: 响应式设计和移动端体验
- **💾 数据导出**: 多格式数据导出和报告生成
- **🔗 API扩展**: 更多API端点和第三方集成

**第四阶段 - 高级功能 (V3.0+)**:
- **🐳 容器化部署**: Docker + docker-compose
- **🔐 安全认证**: API Key + JWT
- **📊 监控告警**: 健康检查和性能监控
- **🔄 多云支持**: Vercel前端 + Supabase后端选项

## 📄 许可证

本项目采用 MIT 许可证 - 详情请参阅 [LICENSE](LICENSE) 文件

## 🔗 链接

- **GitHub**: [https://github.com/franksunye/quantdb](https://github.com/franksunye/quantdb)
- **API 文档**: http://localhost:8000/docs (启动服务后访问)
- **项目维护者**: frank

---

⭐ 如果这个项目对你有帮助，请给个 Star！
