# QuantDB 开发指南

**版本**: v0.6.0-sqlite | **架构**: 简化架构 | **环境**: SQLite开发版本

## 快速设置

```bash
# 1. 克隆并设置环境
git clone https://github.com/franksunye/quantdb.git
cd quantdb
python setup_dev_env.py

# 2. 启动API服务
uvicorn src.api.main:app --reload

# 3. 运行测试
python scripts/test_runner.py --unit --api
```

## 测试系统

### 基础测试命令

```bash
# 运行所有核心测试
python scripts/test_runner.py --unit --api

# 运行特定类型测试
python scripts/test_runner.py --unit      # 单元测试
python scripts/test_runner.py --api       # API测试
python scripts/test_runner.py --integration # 集成测试

# 运行所有测试
python scripts/test_runner.py --all
```

### 高级测试选项

```bash
# 带覆盖率报告
python scripts/test_runner.py --coverage

# 运行特定文件
python scripts/test_runner.py --file tests/unit/test_stock_data_service.py

# 详细输出
python scripts/test_runner.py --unit --verbose
```

**当前测试状态**: 80/80 核心功能测试通过 (100%)

## 项目结构

```
quantdb/
├── src/                    # 源代码 (简化架构)
│   ├── api/               # FastAPI应用和路由
│   ├── cache/             # AKShare适配器
│   ├── services/          # 业务逻辑服务
│   ├── mcp/               # MCP协议 (未来功能)
│   └── config.py          # 配置管理
├── scripts/               # 项目管理脚本
│   └── test_runner.py     # 统一测试运行器
├── tests/                 # 测试文件
├── database/              # SQLite数据库
├── docs/                  # 文档 (精简版)
└── requirements.txt       # 依赖管理
```

## 开发工作流

### 1. 代码开发
```bash
# 创建功能分支
git checkout -b feature/new-feature

# 开发代码...
# 运行测试确保功能正常
python scripts/test_runner.py --unit --api
```

### 2. 测试验证
```bash
# 运行相关测试
python scripts/test_runner.py --file tests/unit/test_your_module.py

# 运行完整测试套件
python scripts/test_runner.py --all --verbose
```

### 3. 系统监控
```bash
# 检查蓄水池状态
python tools/monitoring/water_pool_monitor.py

# 性能基准测试 (开发完成后)
python tools/monitoring/system_performance_monitor.py
```

### 4. 提交代码
```bash
git add .
git commit -m "feat: add new feature"
git push origin feature/new-feature
```

## 环境配置

### 必需依赖
- Python 3.9+
- SQLite (内置)
- pip packages (见 requirements.txt)

### 环境变量 (.env)
```bash
# 数据库配置
DATABASE_URL=sqlite:///./database/stock_data.db

# API配置
API_PREFIX=/api/v1
DEBUG=True
ENVIRONMENT=development

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/quantdb.log
```

## 常见问题

### 1. 测试失败
```bash
# 清理并重新初始化数据库
rm database/stock_data.db
python -m src.scripts.init_db
python scripts/test_runner.py --unit --api
```

### 2. API启动失败
```bash
# 检查端口占用
lsof -i :8000

# 检查依赖安装
pip install -r requirements.txt
```

### 3. 数据库问题
```bash
# 检查数据库状态
python check_database.py

# 重新初始化数据库
python setup_dev_env.py
```

## 代码规范

- **测试**: 所有新功能必须有测试
- **文档**: 重要功能需要更新API文档
- **提交**: 使用语义化提交信息
- **架构**: 遵循简化架构原则，避免过度设计
