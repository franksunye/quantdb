# QuantDB 开发指南

**版本**: v0.8.0-asset-enhanced | **架构**: 智能缓存 + 统一日志 + 交易日历 + 增强资产档案 | **环境**: SQLite

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
├── src/                    # 源代码 (简化架构 + 资产档案增强)
│   ├── api/               # FastAPI应用和路由
│   ├── cache/             # AKShare适配器
│   ├── services/          # 业务逻辑服务
│   │   ├── stock_data_service.py      # 股票数据服务
│   │   ├── asset_info_service.py      # 资产信息服务 🆕
│   │   ├── trading_calendar.py        # 交易日历服务
│   │   └── monitoring_service.py      # 监控服务
│   ├── scripts/           # 数据库迁移和更新脚本
│   │   ├── migrate_asset_model.py     # 资产模型迁移 🆕
│   │   └── update_asset_completeness.py # 资产完整性更新 🆕
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

# 运行监控系统测试 (Core服务测试)
python scripts/test_runner.py --unit --verbose

# 运行完整测试套件
python scripts/test_runner.py --all --verbose
```

### 3. 系统监控
```bash
# 监控功能已迁移到 Streamlit Cloud
# 使用 Web 界面进行监控: cloud/streamlit_cloud/pages/3_System_Status.py

# 或直接调用核心服务
python -c "
from core.services.monitoring_service import MonitoringService
from core.database import get_db
db = next(get_db())
monitor = MonitoringService(db)
status = monitor.get_water_pool_status()
print(status)
"
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
# 浏览器打开: http://localhost:8000/api/v1/docs

# 3. 测试基础端点
curl http://localhost:8000/api/v1/health
curl http://localhost:8000/api/v1/version

# 4. 测试资产档案API (增强版)
curl "http://localhost:8000/api/v1/assets"
curl "http://localhost:8000/api/v1/assets/symbol/600000"  # 获取浦发银行完整信息

# 5. 测试股票数据API (显示真实公司名称)
curl "http://localhost:8000/api/v1/historical/stock/600000?start_date=20230103&end_date=20230105"

# 6. 测试资产信息刷新
curl -X PUT "http://localhost:8000/api/v1/assets/symbol/600000/refresh"
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

# 2. 查看资产档案数据 (增强版)
python -c "
from src.api.database import SessionLocal
from src.api.models import Asset, DailyStockData
session = SessionLocal()
assets = session.query(Asset).limit(5).all()
for asset in assets:
    print(f'{asset.symbol}: {asset.name} | 行业: {asset.industry} | PE: {asset.pe_ratio} | PB: {asset.pb_ratio}')
session.close()
"

# 3. 测试资产信息服务
python -c "
from src.api.database import SessionLocal
from src.services.asset_info_service import AssetInfoService
session = SessionLocal()
service = AssetInfoService(session)
try:
    asset = service.get_or_create_asset('600000')
    print(f'资产: {asset.symbol} - {asset.name}')
    print(f'行业: {asset.industry}')
    print(f'概念: {asset.concept}')
    print(f'PE: {asset.pe_ratio}, PB: {asset.pb_ratio}')
    print(f'数据源: {asset.data_source}')
    print(f'更新时间: {asset.last_updated}')
finally:
    session.close()
"
```

### 资产档案增强手工测试

```bash
# 1. 测试资产数据完整性
python -c "
from src.api.database import SessionLocal
from src.api.models import Asset
session = SessionLocal()
try:
    assets = session.query(Asset).all()
    print(f'总资产数量: {len(assets)}')

    complete_count = 0
    for asset in assets:
        missing_fields = []
        if not asset.name or asset.name.startswith('Stock '):
            missing_fields.append('name')
        if not asset.industry:
            missing_fields.append('industry')
        if not asset.concept:
            missing_fields.append('concept')
        if not asset.pe_ratio:
            missing_fields.append('pe_ratio')
        if not asset.pb_ratio:
            missing_fields.append('pb_ratio')

        if missing_fields:
            print(f'❌ {asset.symbol}: 缺失 {missing_fields}')
        else:
            print(f'✅ {asset.symbol}: {asset.name} - 数据完整')
            complete_count += 1

    completeness_rate = (complete_count / len(assets) * 100) if assets else 0
    print(f'数据完整性: {completeness_rate:.1f}% ({complete_count}/{len(assets)})')
finally:
    session.close()
"

# 2. 测试资产信息更新机制
python -c "
from src.api.database import SessionLocal
from src.services.asset_info_service import AssetInfoService
session = SessionLocal()
service = AssetInfoService(session)
try:
    # 测试按需更新
    print('测试按需更新机制...')
    asset = service.get_or_create_asset('600000')
    print(f'资产: {asset.name}')
    print(f'是否过期: {service._is_asset_data_stale(asset)}')

    # 测试强制更新
    print('\\n测试强制更新...')
    updated_asset = service.update_asset_info('600000')
    if updated_asset:
        print(f'更新成功: {updated_asset.name}')
        print(f'更新时间: {updated_asset.last_updated}')
    else:
        print('更新失败')
finally:
    session.close()
"

# 3. 运行资产完整性更新脚本
python src/scripts/update_asset_completeness.py
```

### 缓存性能手工测试

```bash
# 1. 运行性能测试 (使用真实AKShare数据)
python scripts/test_runner.py --performance --verbose

# 2. 手工测试缓存效果
python -c "
import time
from src.services.stock_data_service import StockDataService
from src.api.database import SessionLocal
from src.cache.akshare_adapter import AKShareAdapter

# 创建依赖
db = SessionLocal()
akshare_adapter = AKShareAdapter()
service = StockDataService(db=db, akshare_adapter=akshare_adapter)

try:
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
finally:
    db.close()
"
```

### 监控系统手工测试

```bash
# 1. 检查蓄水池状态
python tools/monitoring/water_pool_monitor.py

# 2. 查看监控数据
python -c "
from src.services.monitoring_service import MonitoringService
from src.api.database import SessionLocal

db = SessionLocal()
monitor = MonitoringService(db=db)
try:
    coverage = monitor.get_detailed_coverage()
    print('数据覆盖统计:', len(coverage), '个股票')
finally:
    db.close()
"

# 3. 测试监控中间件
python -c "
from src.services.monitoring_middleware import MonitoringMiddleware
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

### 4. Unicode编码错误 (Windows系统)
```bash
# 问题: UnicodeEncodeError: 'gbk' codec can't encode character
# 原因: Windows系统默认GBK编码，无法处理emoji字符
# 解决方案: 已在代码中修复，使用UTF-8编码和移除emoji字符

# 如果仍有问题，可以设置环境变量:
set PYTHONIOENCODING=utf-8  # Windows CMD
$env:PYTHONIOENCODING = "utf-8"  # Windows PowerShell
export PYTHONIOENCODING=utf-8  # Linux/Mac
```

### 5. 环境配置问题
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
