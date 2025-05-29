# QuantDB

![Version](https://img.shields.io/badge/version-0.7.6--performance--optimized-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![API](https://img.shields.io/badge/API-FastAPI-009688)
![Database](https://img.shields.io/badge/Database-SQLite-4169E1)
![Tests](https://img.shields.io/badge/Tests-116/116-success)
![Performance](https://img.shields.io/badge/Cache-98.1%25_faster-brightgreen)

高性能股票数据缓存服务，基于 AKShare 数据源，提供智能缓存和 RESTful API。

## 🎯 核心价值

- **🚀 极致性能**: 智能缓存比 AKShare 直接调用快 **98.1%**，响应时间 ~18ms
- **📊 数据准确**: 基于官方交易日历，确保股票数据的完整性和准确性
- **⚡ 智能缓存**: 自动识别交易日，避免无效 API 调用，显著提升效率
- **🔄 实时监控**: 完整的性能监控和数据覆盖跟踪
- **🛡️ 生产就绪**: 完整的错误处理、测试覆盖和文档体系

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

```bash
# 启动 API 服务
uvicorn src.api.main:app --reload

# 访问 API 文档
# http://localhost:8000/docs
```

### 3. 使用 API

```bash
# 健康检查
curl http://localhost:8000/api/v1/health

# 获取股票数据（自动缓存）
curl "http://localhost:8000/api/v1/historical/stock/000001?start_date=20240101&end_date=20240131"

# 查看缓存状态
curl http://localhost:8000/api/v1/cache/status
```

### 4. 运行测试

```bash
# 运行所有测试
python scripts/test_runner.py --all

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
│   │   ├── trading_calendar.py    # 交易日历服务 🆕
│   │   └── database_cache.py      # 数据库缓存
│   └── cache/                     # 缓存适配器
│       └── akshare_adapter.py     # AKShare 适配器
├── tests/                         # 测试套件
│   ├── unit/                      # 单元测试
│   ├── integration/               # 集成测试
│   ├── api/                       # API 测试
│   ├── e2e/                       # 端到端测试
│   ├── monitoring/                # 监控测试
│   └── performance/               # 性能测试 🆕
├── docs/                          # 项目文档
├── tools/                         # 开发工具
└── scripts/                       # 管理脚本
```

## 🔧 技术栈

- **后端**: FastAPI + SQLAlchemy + SQLite
- **数据源**: AKShare (官方股票数据)
- **缓存**: 智能数据库缓存 + 交易日历
- **测试**: pytest (116个测试，100%通过)
- **监控**: 实时性能监控和数据跟踪

## 📚 文档

| 文档 | 描述 |
|------|------|
| [📋 项目状态](./docs/00_BACKLOG.md) | 当前进展和优先级 |
| [📅 更新日志](./docs/01_CHANGELOG.md) | 版本历史和变更 |
| [🏗️ 系统架构](./docs/10_ARCHITECTURE.md) | 架构设计和组件 |
| [📊 API 文档](./docs/20_API.md) | 完整 API 使用指南 |
| [🛠️ 开发指南](./docs/30_DEVELOPMENT.md) | 开发环境和流程 |
| [🧪 测试指南](./docs/31_TESTING.md) | 测试运行和编写 |

## 🎯 项目状态

**当前版本**: v0.7.6-performance-optimized
**MVP 评分**: 10/10 (完美实现核心价值)
**测试覆盖**: 116/116 通过
**核心突破**: 智能缓存性能提升 98.1%

### ✅ 最新成就 (v0.7.6)

- **🎯 智能缓存优化**: 基于官方交易日历，性能提升 98.1%
- **📊 数据准确性**: 100% 准确的交易日识别
- **⚡ 极致性能**: 缓存响应时间优化到 ~18ms
- **🧪 完整测试**: 包含性能测试和价值场景验证
- **📚 文档完善**: 全面更新项目文档

### 🔮 下一步计划

- **实时行情数据**: 支持实时股价查询
- **多周期数据**: 分钟线、周线、月线数据
- **财务数据**: 基础财务报表 API

## 📄 许可证

本项目采用 MIT 许可证 - 详情请参阅 [LICENSE](LICENSE) 文件

## 🔗 链接

- **GitHub**: [https://github.com/franksunye/quantdb](https://github.com/franksunye/quantdb)
- **API 文档**: http://localhost:8000/docs (启动服务后访问)
- **项目维护者**: frank

---

⭐ 如果这个项目对你有帮助，请给个 Star！
