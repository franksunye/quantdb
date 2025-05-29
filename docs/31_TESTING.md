# QuantDB 测试指南

**测试状态**: 95/95 通过 (100%) | **覆盖率**: 核心功能全覆盖 | **工具**: 统一测试运行器

## 快速测试

```bash
# 运行核心功能测试
python scripts/test_runner.py --unit --api

# 运行所有测试
python scripts/test_runner.py --all

# 带覆盖率报告
python scripts/test_runner.py --coverage
```

## 测试分类

### 1. 单元测试 (77个)
测试独立组件的功能逻辑。

```bash
# 运行所有单元测试
python scripts/test_runner.py --unit

# 运行特定模块测试
python scripts/test_runner.py --file tests/unit/test_stock_data_service.py
```

**覆盖模块**:
- `test_akshare_adapter.py` - AKShare适配器 (15个测试)
- `test_database_cache.py` - 数据库缓存 (13个测试)
- `test_stock_data_service.py` - 股票数据服务 (11个测试)
- `test_enhanced_logger.py` - 增强日志 (8个测试)
- `test_error_handling.py` - 错误处理 (13个测试)
- `test_monitoring_service.py` - 监控服务 (12个测试)
- `test_monitoring_middleware.py` - 监控中间件 (8个测试)
- `test_monitoring_tools.py` - 监控工具 (7个测试)

### 2. API测试 (18个)
测试HTTP API端点的功能。

```bash
# 运行所有API测试
python scripts/test_runner.py --api
```

**覆盖端点**:
- `test_assets_api.py` - 资产API (4个测试)
- `test_historical_data.py` - 历史数据API (6个测试)
- `test_api.py` - 基础API (2个测试)
- `test_version_api.py` - 版本API (6个测试)

### 3. 集成测试
测试组件间的协作。

```bash
# 运行集成测试
python scripts/test_runner.py --integration
```

**覆盖模块**:
- `test_stock_data_flow.py` - 股票数据流集成
- `test_error_handling_integration.py` - 错误处理集成
- `test_logging_integration.py` - 日志集成
- `test_monitoring_integration.py` - 监控系统集成

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

### 5. 监控系统测试

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

## 测试运行器选项

### 基础选项
```bash
--unit          # 单元测试
--api           # API测试
--integration   # 集成测试
--monitoring    # 监控系统测试
--all           # 所有测试
```

### 高级选项
```bash
--coverage      # 生成覆盖率报告
--performance   # 性能测试
--verbose       # 详细输出
--file <path>   # 运行特定文件
```

### 示例用法
```bash
# 详细输出的单元测试
python scripts/test_runner.py --unit --verbose

# 监控系统测试
python scripts/test_runner.py --monitoring --verbose

# 特定文件的测试
python scripts/test_runner.py --file tests/unit/test_monitoring_service.py

# 带覆盖率的完整测试
python scripts/test_runner.py --all --coverage
```

## 编写测试

### 单元测试模板
```python
import unittest
from unittest.mock import patch, MagicMock
from src.services.your_service import YourService

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
    
    @patch('src.services.your_service.external_dependency')
    def test_with_mock(self, mock_dependency):
        # 配置mock
        mock_dependency.return_value = "mocked_result"
        
        # 执行测试
        result = self.service.method_with_dependency()
        
        # 验证调用和结果
        mock_dependency.assert_called_once()
        self.assertEqual(result, "expected_result")
```

### API测试模板
```python
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

def test_api_endpoint():
    # 发送请求
    response = client.get("/api/v1/your-endpoint")
    
    # 验证响应
    assert response.status_code == 200
    data = response.json()
    assert "expected_field" in data
    assert data["expected_field"] == "expected_value"

def test_api_error_handling():
    # 测试错误情况
    response = client.get("/api/v1/invalid-endpoint")
    
    # 验证错误响应
    assert response.status_code == 404
    error_data = response.json()
    assert "error" in error_data
    assert error_data["error"]["code"] == "NOT_FOUND"
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
# 运行缓存性能测试
python scripts/test_runner.py --performance

# 生成详细性能报告
python tools/performance/cache_performance_report.py
```

### 性能指标
- **响应时间**：各场景下的平均响应时间
- **性能提升**：缓存相比首次获取的提升幅度
- **缓存效率**：智能缓存策略的效果验证

### 预期结果
- **测试环境**：可能显示缓存性能与首次获取相当
- **生产环境**：缓存通常比 AKShare 调用快 50-80%
- **核心价值**：减少 API 调用，提供数据持久化

### 性能测试示例
```python
@pytest.mark.performance
def test_cache_vs_fresh_data():
    """测试缓存性能 vs 首次数据获取"""
    symbol = "000001"
    start_date = "20240101"
    end_date = "20240131"

    # 清除缓存
    clear_cache(symbol)

    # 测试首次获取
    fresh_time = measure_api_performance(symbol, start_date, end_date)

    # 测试缓存命中
    cached_time = measure_api_performance(symbol, start_date, end_date)

    # 分析性能
    improvement = (fresh_time - cached_time) / fresh_time * 100
    print(f"缓存性能提升: {improvement:.1f}%")
```
