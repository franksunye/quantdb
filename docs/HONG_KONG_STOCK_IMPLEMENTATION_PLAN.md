# QuantDB 港股支持实施计划

**版本**: v1.1.0-v1.3.0 | **状态**: 准备实施 | **更新**: 2025-06-15

## 🎯 项目目标

基于[港股支持技术可行性评估](./HONG_KONG_STOCK_ASSESSMENT.md)，实施港股支持功能，使QuantDB成为同时支持A股和港股的综合性金融数据平台。

### 核心价值
- **市场覆盖扩展**: 从A股扩展到A股+港股
- **用户体验一致**: 港股与A股完全一致的操作体验
- **技术架构优化**: 为后续多市场支持奠定基础
- **竞争力提升**: 成为多市场支持的量化数据平台

## 📋 实施路线图

### 🔴 阶段1: 基础港股支持 (v1.1.0)
**目标**: 实现港股历史数据查询的基础功能
**时间**: 1天 (5小时)
**风险**: 低
**优先级**: 最高

#### 技术改动清单

##### 1. 后端AKShare适配器扩展 (2小时)
**文件**: `src/cache/akshare_adapter.py`

```python
# 当前代码
def _validate_symbol(self, symbol: str) -> bool:
    return symbol.isdigit() and len(symbol) == 6

# 修改为
def _validate_symbol(self, symbol: str) -> bool:
    # A股: 6位数字 (000001, 600000)
    if symbol.isdigit() and len(symbol) == 6:
        return True
    # 港股: 5位数字 (02171, 00700)
    if symbol.isdigit() and len(symbol) == 5:
        return True
    return False

# 新增方法
def _detect_market(self, symbol: str) -> str:
    if len(symbol) == 6:
        return 'A_STOCK'
    elif len(symbol) == 5:
        return 'HK_STOCK'
    else:
        raise ValueError("Unsupported symbol format")

# 修改数据获取方法
def get_stock_data(self, symbol: str, start_date: str, end_date: str, adjust: str = ""):
    market = self._detect_market(symbol)
    if market == 'A_STOCK':
        return ak.stock_zh_a_hist(symbol=symbol, period="daily", 
                                  start_date=start_date, end_date=end_date, adjust=adjust)
    elif market == 'HK_STOCK':
        return ak.stock_hk_hist(symbol=symbol, period="daily",
                                start_date=start_date, end_date=end_date)
```

##### 2. 前端输入验证更新 (1小时)
**文件**: `quantdb_frontend/utils/config.py`

```python
# 更新验证函数
def validate_symbol(symbol: str) -> bool:
    """验证股票代码格式 - 支持A股和港股"""
    if not symbol:
        return False
    
    # A股: 6位数字
    if symbol.isdigit() and len(symbol) == 6:
        return True
    
    # 港股: 5位数字
    if symbol.isdigit() and len(symbol) == 5:
        return True
    
    return False

# 更新错误消息
ERROR_MESSAGES = {
    "invalid_symbol": "请输入有效的股票代码 (A股6位数字如600000，港股5位数字如02171)",
    # ... 其他消息
}
```

**文件**: `quantdb_frontend/pages/1_📈_股票数据查询.py`

```python
# 更新输入提示
symbol = st.text_input(
    "股票代码",
    value="600000",
    placeholder="A股: 600000 | 港股: 02171",
    help="支持A股代码(6位数字)和港股代码(5位数字)"
)
```

##### 3. 测试用例添加 (1小时)
**文件**: `tests/test_hong_kong_stock.py` (新建)

```python
import pytest
from src.cache.akshare_adapter import AKShareAdapter

class TestHongKongStockSupport:
    def test_hk_symbol_validation(self):
        adapter = AKShareAdapter()
        # 港股代码验证
        assert adapter._validate_symbol("02171") == True
        assert adapter._validate_symbol("00700") == True
        # A股代码验证 (确保兼容性)
        assert adapter._validate_symbol("600000") == True
        assert adapter._validate_symbol("000001") == True
        
    def test_market_detection(self):
        adapter = AKShareAdapter()
        assert adapter._detect_market("600000") == "A_STOCK"
        assert adapter._detect_market("02171") == "HK_STOCK"
        
    def test_hk_data_retrieval(self):
        adapter = AKShareAdapter()
        # 测试港股数据获取 (科济药业-B)
        data = adapter.get_stock_data("02171", "20240101", "20240131")
        assert data is not None
        assert len(data) > 0
```

##### 4. 文档更新 (1小时)
**文件**: `docs/20_API.md`

添加港股支持说明:
```markdown
## 港股支持

QuantDB现已支持港股历史数据查询，与A股使用完全相同的API接口。

### 支持的港股代码格式
- 5位数字代码 (如: 02171, 00700)
- 自动识别港股市场并调用对应数据源

### 示例
```bash
# 查询科济药业-B港股数据
curl "http://localhost:8000/api/v1/historical/stock/02171?start_date=20240101&end_date=20240131"
```
```

#### 验收标准
- [ ] 港股代码验证正确 (02171, 00700等)
- [ ] A股代码验证保持兼容 (600000, 000001等)
- [ ] 港股历史数据成功获取
- [ ] 前端界面支持港股代码输入
- [ ] 所有测试用例通过
- [ ] 文档更新完成

### 🟡 阶段2: 港股资产信息增强 (v1.2.0)
**目标**: 完善港股公司信息和财务指标支持
**时间**: 2天
**风险**: 中
**优先级**: 中

#### 主要任务
1. **港股公司信息API研究** (4小时)
   - 调研AKShare港股公司信息获取方式
   - 测试港股财务指标数据可用性
   - 设计港股资产信息数据模型

2. **港股资产信息服务实现** (8小时)
   - 扩展AssetInfoService支持港股
   - 实现港股公司信息获取和存储
   - 添加港股特有财务指标

3. **前端港股展示优化** (4小时)
   - 区分A股和港股的显示样式
   - 添加港股市场标识
   - 优化港股数据质量展示

### 🟢 阶段3: 多市场架构 (v1.3.0)
**目标**: 建立可扩展的多市场支持架构
**时间**: 1周
**风险**: 中
**优先级**: 低

#### 主要任务
1. **多市场架构设计** (2天)
   - 设计统一的市场配置系统
   - 实现市场特定的数据适配器
   - 建立可扩展的市场支持框架

2. **美股支持准备** (2天)
   - 研究美股数据源和API
   - 设计美股代码验证规则
   - 准备美股数据模型扩展

3. **市场管理功能** (1天)
   - 实现市场切换功能
   - 添加市场配置管理
   - 优化多市场用户体验

## 🚀 实施建议

### 立即可行的行动
1. **今天开始阶段1** - 基础港股支持，5小时完成
2. **快速验证** - 使用科济药业-B (02171) 测试功能
3. **用户反馈** - 收集港股功能的用户需求

### 风险控制
- **最小化改动** - 仅修改必要的适配层代码
- **保持兼容性** - 确保A股功能不受影响
- **渐进式实施** - 分阶段实施，降低风险

### 成功指标
- ✅ 港股历史数据查询成功率 > 95%
- ✅ A股功能完全不受影响
- ✅ 用户体验与A股完全一致
- ✅ 所有测试用例通过

## 📊 预期效果

实施完成后，QuantDB将具备：
- **双市场支持**: 同时支持A股和港股查询
- **统一体验**: 港股与A股完全一致的操作界面
- **扩展能力**: 为美股等其他市场支持奠定基础
- **竞争优势**: 成为多市场支持的量化数据平台

**用户价值**: 一个平台满足A股和港股的数据需求，显著提升产品价值和市场竞争力。
