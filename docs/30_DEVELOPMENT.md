# QuantDB 开发指南

**版本**: v0.7.7-production-ready | **架构**: 智能缓存 + 统一日志 + 交易日历 | **环境**: SQLite

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
python scripts/test_runner.py --monitoring  # 监控系统测试
python scripts/test_runner.py --performance # 缓存性能测试

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

**当前测试状态**: 186/186 全功能测试通过 (100%) - 包含完整的单元/集成/API/E2E/监控/性能测试

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

# 运行监控系统测试
python scripts/test_runner.py --monitoring --verbose

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

## 手工测试指南

### 环境设置和诊断

```bash
# 1. 完整环境设置 (推荐首次使用)
python setup_dev_env.py

# 2. 诊断当前环境配置
python scripts/diagnose_environment.py

# 3. 强制本地SQLite配置 (解决Supabase连接问题)
python scripts/force_local_setup.py
```

### API手工测试

```bash
# 1. 启动API服务器
python -m src.api.main
# 或者使用uvicorn
uvicorn src.api.main:app --reload --port 8000

# 2. 访问API文档
# 浏览器打开: http://localhost:8000/docs

# 3. 测试基础端点
curl http://localhost:8000/api/v1/health
curl http://localhost:8000/api/v1/version

# 4. 测试股票数据API
curl "http://localhost:8000/api/v1/assets"
curl "http://localhost:8000/api/v1/historical-data/600000?start_date=2023-01-03&end_date=2023-01-05"
```

### 数据库手工测试

```bash
# 1. 检查数据库状态
python -c "
from src.api.database import engine
from sqlalchemy import text
with engine.connect() as conn:
    result = conn.execute(text('SELECT COUNT(*) FROM assets'))
    print(f'Assets count: {result.fetchone()[0]}')
"

# 2. 查看数据库内容
python -c "
from src.api.database import SessionLocal
from src.api.models import Asset, DailyStockData
session = SessionLocal()
assets = session.query(Asset).limit(5).all()
for asset in assets:
    print(f'{asset.symbol}: {asset.name}')
session.close()
"
```

### 缓存性能手工测试

```bash
# 1. 运行性能测试 (使用真实AKShare数据)
python scripts/test_runner.py --performance --verbose

# 2. 手工测试缓存效果
python -c "
import time
from src.services.stock_data_service import StockDataService

service = StockDataService()

# 第一次调用 (从AKShare获取)
start = time.time()
data1 = service.get_stock_data('600000', '20230103', '20230105')
time1 = time.time() - start

# 第二次调用 (从缓存获取)
start = time.time()
data2 = service.get_stock_data('600000', '20230103', '20230105')
time2 = time.time() - start

print(f'第一次调用: {time1:.3f}s ({len(data1)}条记录)')
print(f'第二次调用: {time2:.3f}s ({len(data2)}条记录)')
print(f'性能提升: {(time1/time2):.1f}x')
"
```

### 监控系统手工测试

```bash
# 1. 检查蓄水池状态
python tools/monitoring/water_pool_monitor.py

# 2. 查看监控数据
python -c "
from src.services.monitoring_service import MonitoringService
monitor = MonitoringService()
stats = monitor.get_data_coverage_stats()
print('数据覆盖统计:', stats)
"

# 3. 测试监控中间件
python -c "
from src.api.monitoring_middleware import MonitoringMiddleware
middleware = MonitoringMiddleware()
print('监控中间件已加载')
"
```

### 日志系统手工测试

```bash
# 1. 测试统一日志系统
python -c "
from src.logger_unified import get_logger
logger = get_logger('test_module')
logger.info('测试信息日志')
logger.warning('测试警告日志')
logger.error('测试错误日志')
print('日志测试完成，检查 logs/quantdb.log 文件')
"

# 2. 查看日志文件
tail -f logs/quantdb.log
```

## 常见问题

### 1. 数据库连接错误 (Supabase连接问题)
```bash
# 问题: 尝试连接Supabase而不是本地SQLite
# 解决方案:
python scripts/force_local_setup.py
# 或者手动设置环境变量:
export DATABASE_URL="sqlite:///./database/stock_data.db"  # Linux/Mac
$env:DATABASE_URL = "sqlite:///./database/stock_data.db"  # Windows PowerShell
```

### 2. 测试失败
```bash
# 清理并重新初始化数据库
rm database/stock_data.db  # Linux/Mac
del database\stock_data.db  # Windows
python setup_dev_env.py
```

### 3. API启动失败
```bash
# 检查端口占用
netstat -ano | findstr :8000  # Windows
lsof -i :8000  # Linux/Mac

# 检查依赖安装
pip install -r requirements.txt
```

### 4. 环境配置问题
```bash
# 运行完整诊断
python scripts/diagnose_environment.py

# 重新设置环境
python setup_dev_env.py
```

## 代码规范

- **测试**: 所有新功能必须有测试
- **文档**: 重要功能需要更新API文档
- **提交**: 使用语义化提交信息
- **架构**: 遵循简化架构原则，避免过度设计
