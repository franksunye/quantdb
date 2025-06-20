# QuantDB 测试指南

**架构版本**: 2.0.0 (Core/API分离) | **测试状态**: 重构后验证中 | **覆盖率目标**: Core 95%+ | API 90%+ | **架构**: 模块化测试

## 快速测试

```bash
# 运行核心业务逻辑测试
python -m pytest tests/unit/ -v

# 运行API服务测试
python -m pytest tests/api/ -v

# 运行所有测试
python -m pytest tests/ -v

# 带覆盖率报告
python -m pytest tests/ --cov=core --cov=api --cov-report=html
```

## 测试架构 (重构后)

### 🏗️ 新架构测试分层

```
tests/
├── unit/           # 核心业务逻辑单元测试
│   ├── core/       # Core模块测试
│   └── api/        # API层单元测试
├── integration/    # 集成测试
├── api/           # API端点测试
├── e2e/           # 端到端测试
└── performance/   # 性能测试
```

### 1. Core模块单元测试
测试核心业务逻辑组件，独立于API层。

```bash
# 运行所有Core单元测试
python -m pytest tests/unit/ -v -k "core or service or cache or model"

# 运行特定Core模块测试
python -m pytest tests/unit/test_stock_data_service.py -v
```

**Core模块覆盖**:
- `test_stock_data_service.py` - 股票数据服务 (Core业务逻辑)
- `test_asset_info_service.py` - 资产信息服务 (Core业务逻辑)
- `test_database_cache.py` - 数据库缓存 (Core缓存层)
- `test_akshare_adapter.py` - AKShare适配器 (Core缓存层)
- `test_trading_calendar.py` - 交易日历 (Core工具)
- `test_monitoring_service.py` - 监控服务 (Core服务)
- `test_monitoring_middleware.py` - 监控中间件 (Core服务)

### 2. API服务测试
测试FastAPI应用和HTTP端点功能。

```bash
# 运行所有API测试
python -m pytest tests/api/ -v

# 运行特定API端点测试
python -m pytest tests/api/test_assets_api.py -v
```

**API端点覆盖**:
- `test_assets_api.py` - 资产API端点测试
- `test_historical_data.py` - 历史数据API测试
- `test_version_api.py` - 版本API测试
- `test_openapi.py` - OpenAPI文档测试

**API层单元测试**:
- 依赖注入测试
- 中间件测试
- 错误处理测试
- 响应格式验证

### 3. 集成测试 (91个)
测试组件间的协作。

```bash
# 运行集成测试
python scripts/test_runner.py --integration

# 运行资产档案增强集成测试
python scripts/test_runner.py --file tests/integration/test_asset_enhancement_integration.py
```

**覆盖模块**:
- `test_stock_data_flow.py` - 股票数据流集成
- `test_error_handling_integration.py` - 错误处理集成
- `test_logging_integration.py` - 日志集成
- `test_monitoring_integration.py` - 监控系统集成
- `test_asset_enhancement_integration.py` - 资产档案增强集成 (10个测试) 🆕

### 4. 端到端测试 (E2E)
测试完整用户场景，真实HTTP请求，自动环境管理。

```bash
# 运行E2E测试
python scripts/test_runner.py --e2e

# 性能分析
python tests/e2e/performance_analysis.py
```

**测试场景**:
- 新用户工作流程 (健康检查→资产→数据→缓存)
- 数据范围扩展 (部分缓存命中)
- 错误处理 (无效输入)
- 缓存管理 (一致性验证)

**性能基准**:
- 基础API: < 20ms ✅
- 首次数据请求: < 2秒 ✅
- 缓存命中: < 1秒 ✅
- 缓存性能提升: > 30% ✅

### 5. 资产档案增强测试 🆕

专门测试资产档案增强功能的完整性和正确性。

```bash
# 运行资产档案增强测试
python scripts/test_runner.py --file tests/unit/test_asset_info_service.py
python scripts/test_runner.py --file tests/api/test_assets_api.py
python scripts/test_runner.py --file tests/integration/test_asset_enhancement_integration.py

# 运行资产数据完整性验证
python -c "
from src.api.database import SessionLocal
from src.api.models import Asset
session = SessionLocal()
assets = session.query(Asset).all()
complete_count = sum(1 for a in assets if a.name and not a.name.startswith('Stock '))
print(f'数据完整性: {complete_count/len(assets)*100:.1f}% ({complete_count}/{len(assets)})')
session.close()
"
```

**测试覆盖**:
- 🏢 **AssetInfoService单元测试** (19个测试)
  - 符号标准化、数据过期检查、默认值映射
  - AKShare集成、容错机制、数据解析
  - 资产创建、更新、缓存机制
- 🌐 **资产API增强测试** (12个测试)
  - 资产信息获取、刷新功能、错误处理
  - 响应格式验证、数据完整性检查
  - 真实公司名称验证、服务集成测试
- 🔗 **资产增强集成测试** (10个测试)
  - 端到端资产创建流程、数据库事务完整性
  - 缓存行为验证、并发访问测试
  - 行业概念数据集成、完整增强流程

**验证指标**:
- 📊 **数据完整性**: 100% 资产显示真实公司名称
- 🏭 **行业分类**: 已知股票包含行业信息
- 💡 **概念分类**: 已知股票包含概念信息
- 📈 **财务指标**: PE、PB、ROE等关键指标
- 🔄 **更新机制**: 1天缓存策略，自动刷新
- 🛡️ **容错机制**: AKShare失败时的fallback处理

### 6. 监控系统测试

专门测试监控系统的功能和集成。

```bash
# 运行监控系统测试
python scripts/test_runner.py --monitoring

# 运行监控工具
python tools/monitoring/water_pool_monitor.py
python tools/monitoring/system_performance_monitor.py
```

**测试覆盖**:
- 🔍 监控服务单元测试 - 请求日志、数据覆盖、性能趋势
- 🔧 监控中间件测试 - 装饰器、请求拦截、错误处理
- 🛠️ 监控工具测试 - 水池监控、性能监控、输出验证
- 🔗 监控集成测试 - 端到端监控流程、数据库集成

**监控指标**:
- 🏊‍♂️ 蓄水池容量和数据覆盖
- ⚡ 缓存命中率和性能提升
- 💰 AKShare调用减少和成本节省
- 📊 系统健康度和运行状态

## 测试运行器选项 (v2.0)

### 新架构测试运行器
```bash
# 使用新的测试运行器 v2.0
python scripts/test_runner_v2.py --help
```

### 基础选项
```bash
--core          # Core模块测试 (业务逻辑)
--api           # API层测试 (FastAPI服务)
--unit          # 所有单元测试
--integration   # 集成测试
--all           # 所有测试
--performance   # 性能测试
```

### 高级选项
```bash
--coverage      # 生成覆盖率报告
--verbose       # 详细输出
--file <path>   # 运行特定文件
--list          # 列出可用测试
--validate      # 验证测试结构
```

### 示例用法
```bash
# Core模块测试
python scripts/test_runner_v2.py --core --verbose
python scripts/test_runner_v2.py --core --coverage

# API层测试
python scripts/test_runner_v2.py --api --verbose

# 集成测试
python scripts/test_runner_v2.py --integration

# 特定文件测试
python scripts/test_runner_v2.py --file tests/unit/test_core_models.py

# 完整测试套件
python scripts/test_runner_v2.py --all --coverage

# 列出所有可用测试
python scripts/test_runner_v2.py --list
```

## 编写测试

### Core模块单元测试模板
```python
import unittest
from unittest.mock import patch, MagicMock
from core.services.your_service import YourService

class TestYourService(unittest.TestCase):
    def setUp(self):
        self.service = YourService()

    def test_your_method(self):
        # 准备测试数据
        test_input = "test_data"
        expected_output = "expected_result"

        # 执行测试
        result = self.service.your_method(test_input)

        # 验证结果
        self.assertEqual(result, expected_output)

    @patch('core.services.your_service.external_dependency')
    def test_with_mock(self, mock_dependency):
        # 配置mock
        mock_dependency.return_value = "mocked_result"

        # 执行测试
        result = self.service.method_with_dependency()

        # 验证调用和结果
        mock_dependency.assert_called_once()
        self.assertEqual(result, "expected_result")
```

### Core模型测试模板
```python
import unittest
from datetime import date
from decimal import Decimal
from core.models import Asset, DailyStockData

class TestAssetModel(unittest.TestCase):
    def test_asset_creation(self):
        asset = Asset(
            symbol="600000",
            name="测试公司",
            asset_type="stock",
            exchange="SHSE",
            currency="CNY"
        )

        self.assertEqual(asset.symbol, "600000")
        self.assertEqual(asset.name, "测试公司")
        self.assertEqual(asset.asset_type, "stock")
```

### API测试模板
```python
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def test_api_endpoint():
    # 发送请求
    response = client.get("/api/v1/assets/symbol/600000")

    # 验证响应
    assert response.status_code == 200
    data = response.json()
    assert "symbol" in data
    assert data["symbol"] == "600000"

def test_api_error_handling():
    # 测试错误情况
    response = client.get("/api/v1/assets/symbol/INVALID")

    # 验证错误响应
    assert response.status_code in [400, 404, 422]

@patch('core.services.asset_info_service.AssetInfoService.get_or_create_asset')
def test_api_with_core_service_mock(mock_service):
    # Mock core service
    mock_service.return_value = Asset(symbol="600000", name="测试公司")

    response = client.get("/api/v1/assets/symbol/600000")

    # 验证core service被调用
    mock_service.assert_called_once_with("600000")
    assert response.status_code == 200
```

### API依赖注入测试模板
```python
import unittest
from unittest.mock import patch, MagicMock
from api.dependencies import get_stock_data_service, get_asset_info_service

class TestAPIDependencies(unittest.TestCase):
    @patch('api.dependencies.get_db')
    def test_get_stock_data_service(self, mock_get_db):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        service = get_stock_data_service(db=mock_db, adapter=MagicMock())

        self.assertIsNotNone(service)
        self.assertEqual(service.db, mock_db)
```

## 测试数据管理

### 测试数据库
测试使用独立的数据库，避免影响开发数据。

```python
# 测试fixture示例
@pytest.fixture
def test_db():
    # 创建测试数据库
    engine = create_engine("sqlite:///test.db")
    TestingSessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        os.remove("test.db")
```

### Mock数据
```python
# 常用的mock数据
SAMPLE_STOCK_DATA = pd.DataFrame({
    'date': ['20230101', '20230102', '20230103'],
    'open': [10.0, 10.5, 11.0],
    'high': [11.0, 11.5, 12.0],
    'low': [9.5, 10.0, 10.5],
    'close': [10.5, 11.0, 11.5],
    'volume': [1000000, 1200000, 1100000]
})
```

## 持续集成

### 测试自动化
```bash
# 在CI/CD中运行的测试命令
python scripts/test_runner.py --all --coverage --verbose
```

### 质量门禁
- **测试通过率**: 100%
- **覆盖率要求**: 核心模块 > 80%
- **性能要求**: API响应 < 1秒

## 故障排除

### 常见问题

**1. 测试数据库冲突**
```bash
# 清理测试数据
rm -f test*.db
python scripts/test_runner.py --unit
```

**2. Mock对象问题**
```python
# 确保正确的mock路径
@patch('src.services.module.ClassName')  # 正确
@patch('module.ClassName')  # 错误
```

**3. 异步测试问题**
```python
# 使用pytest-asyncio
import pytest

@pytest.mark.asyncio
async def test_async_function():
    result = await async_function()
    assert result == expected_value
```

## 缓存性能测试

### 测试目标
验证 QuantDB 作为 AKShare 缓存服务的核心价值，量化性能提升。

### 测试场景
- **首次数据获取**：QuantDB + AKShare 调用的性能基准
- **缓存命中**：纯数据库查询的性能
- **部分缓存**：智能数据获取策略的效率

### 运行性能测试
```bash
# 运行缓存性能测试 (使用真实 AKShare 数据)
python scripts/test_runner.py --performance

# 生成详细性能报告
python tools/performance/cache_performance_report.py
```

### 性能指标
- **响应时间**：各场景下的平均响应时间
- **性能提升**：缓存相比首次获取的提升幅度
- **缓存效率**：智能缓存策略的效果验证

### 预期结果
- **真实数据测试**：缓存比 AKShare 调用快 98.1%
- **缓存命中性能**：20ms vs 1075ms (54倍提升)
- **核心价值验证**：显著减少 API 调用，提供高性能数据服务

### 性能测试示例
```python
@pytest.mark.performance
def test_cache_vs_akshare_real_data():
    """测试缓存性能 vs AKShare 真实数据"""
    symbol = "000001"
    start_date = "20240101"
    end_date = "20240131"

    # 清除缓存
    clear_cache(symbol)

    # 测试首次获取 (QuantDB + AKShare)
    fresh_time = measure_quantdb_performance(symbol, start_date, end_date)

    # 测试缓存命中 (纯数据库查询)
    cached_time = measure_quantdb_performance(symbol, start_date, end_date)

    # 测试直接 AKShare 调用
    akshare_time = measure_akshare_performance(symbol, start_date, end_date)

    # 分析性能
    cache_vs_akshare = (akshare_time - cached_time) / akshare_time * 100
    print(f"缓存 vs AKShare 性能提升: {cache_vs_akshare:.1f}%")
```
