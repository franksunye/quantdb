# QuantDB 港股支持快速开始指南

**目标**: 在1天内实现港股基础支持功能
**基于**: [港股支持技术可行性评估](./HONG_KONG_STOCK_ASSESSMENT.md)

## 🚀 快速实施步骤

### 步骤1: 扩展AKShare适配器 (2小时)

#### 1.1 修改股票代码验证
**文件**: `src/cache/akshare_adapter.py`

```python
def _validate_symbol(self, symbol: str) -> bool:
    """验证股票代码格式 - 支持A股和港股"""
    if not symbol or not symbol.isdigit():
        return False
    
    # A股: 6位数字 (000001, 600000)
    if len(symbol) == 6:
        return True
    
    # 港股: 5位数字 (02171, 00700)  
    if len(symbol) == 5:
        return True
    
    return False
```

#### 1.2 添加市场识别方法
```python
def _detect_market(self, symbol: str) -> str:
    """识别股票所属市场"""
    if len(symbol) == 6:
        return 'A_STOCK'
    elif len(symbol) == 5:
        return 'HK_STOCK'
    else:
        raise ValueError(f"Unsupported symbol format: {symbol}")
```

#### 1.3 修改数据获取方法
```python
def get_stock_data(self, symbol: str, start_date: str, end_date: str, adjust: str = ""):
    """获取股票历史数据 - 支持A股和港股"""
    market = self._detect_market(symbol)
    
    if market == 'A_STOCK':
        return ak.stock_zh_a_hist(
            symbol=symbol, 
            period="daily",
            start_date=start_date, 
            end_date=end_date, 
            adjust=adjust
        )
    elif market == 'HK_STOCK':
        return ak.stock_hk_hist(
            symbol=symbol,
            period="daily", 
            start_date=start_date,
            end_date=end_date
        )
```

### 步骤2: 更新前端验证 (1小时)

#### 2.1 修改配置文件
**文件**: `quantdb_frontend/utils/config.py`

```python
def validate_symbol(symbol: str) -> bool:
    """验证股票代码格式"""
    if not symbol or not symbol.isdigit():
        return False
    
    # A股: 6位数字
    if len(symbol) == 6:
        return True
    
    # 港股: 5位数字
    if len(symbol) == 5:
        return True
    
    return False

ERROR_MESSAGES = {
    "invalid_symbol": "请输入有效的股票代码 (A股: 600000, 港股: 02171)",
    # ... 其他消息保持不变
}
```

#### 2.2 更新前端页面提示
**文件**: `quantdb_frontend/pages/1_📈_股票数据查询.py`

找到股票代码输入部分，修改为：
```python
symbol = st.text_input(
    "股票代码",
    value="600000",
    placeholder="A股: 600000 | 港股: 02171",
    help="支持A股代码(6位数字)和港股代码(5位数字)"
)
```

### 步骤3: 添加测试用例 (1小时)

#### 3.1 创建港股测试文件
**文件**: `tests/test_hong_kong_stock.py`

```python
import pytest
from src.cache.akshare_adapter import AKShareAdapter

class TestHongKongStockSupport:
    
    def setup_method(self):
        self.adapter = AKShareAdapter()
    
    def test_hk_symbol_validation(self):
        """测试港股代码验证"""
        # 港股代码
        assert self.adapter._validate_symbol("02171") == True
        assert self.adapter._validate_symbol("00700") == True
        
        # A股代码 (确保兼容性)
        assert self.adapter._validate_symbol("600000") == True
        assert self.adapter._validate_symbol("000001") == True
        
        # 无效代码
        assert self.adapter._validate_symbol("1234") == False
        assert self.adapter._validate_symbol("1234567") == False
        
    def test_market_detection(self):
        """测试市场识别"""
        assert self.adapter._detect_market("600000") == "A_STOCK"
        assert self.adapter._detect_market("000001") == "A_STOCK"
        assert self.adapter._detect_market("02171") == "HK_STOCK"
        assert self.adapter._detect_market("00700") == "HK_STOCK"
        
        with pytest.raises(ValueError):
            self.adapter._detect_market("1234")
    
    @pytest.mark.integration
    def test_hk_data_retrieval(self):
        """测试港股数据获取 (集成测试)"""
        # 测试科济药业-B
        data = self.adapter.get_stock_data("02171", "20240101", "20240131")
        
        assert data is not None
        assert len(data) > 0
        assert '日期' in data.columns
        assert '开盘' in data.columns
        assert '收盘' in data.columns
```

#### 3.2 运行测试
```bash
# 运行港股专项测试
python -m pytest tests/test_hong_kong_stock.py -v

# 运行所有测试确保兼容性
python -m pytest tests/ -v
```

### 步骤4: 更新文档 (1小时)

#### 4.1 更新API文档
**文件**: `docs/20_API.md`

在"使用示例"部分添加：
```markdown
## 港股支持

QuantDB现已支持港股历史数据查询，使用与A股完全相同的API接口。

### 港股代码格式
- 5位数字代码 (如: 02171, 00700, 00981)
- 系统自动识别港股市场并调用对应数据源

### 港股查询示例
```bash
# 查询科济药业-B (02171) 港股数据
curl "http://localhost:8000/api/v1/historical/stock/02171?start_date=20240101&end_date=20240131"

# 查询腾讯控股 (00700) 港股数据  
curl "http://localhost:8000/api/v1/historical/stock/00700?start_date=20240101&end_date=20240131"
```

### 支持的港股
- 科济药业-B (02171)
- 腾讯控股 (00700)
- 中芯国际 (00981)
- 以及其他在港交所交易的股票
```

#### 4.2 更新前端README
**文件**: `quantdb_frontend/README.md`

在功能特性部分添加：
```markdown
### 🌏 多市场支持
- **A股支持**: 沪深A股历史数据查询 (6位代码)
- **港股支持**: 港交所股票历史数据查询 (5位代码)
- **统一体验**: A股和港股完全一致的操作界面
- **智能识别**: 自动识别股票代码所属市场
```

## ✅ 验收检查清单

### 功能验证
- [ ] 港股代码验证正确 (02171, 00700等)
- [ ] A股代码验证保持兼容 (600000, 000001等)
- [ ] 港股历史数据成功获取
- [ ] 前端界面支持港股代码输入
- [ ] 错误提示信息准确

### 测试验证
- [ ] 所有新增测试用例通过
- [ ] 所有原有测试用例通过
- [ ] 集成测试验证港股数据获取
- [ ] 前端功能手动测试通过

### 文档验证
- [ ] API文档更新完成
- [ ] 前端使用指南更新
- [ ] 港股使用示例添加
- [ ] 错误信息文档更新

## 🧪 快速测试

### 后端测试
```bash
# 启动后端服务
cd src && python -m uvicorn main:app --reload

# 测试港股API
curl "http://localhost:8000/api/v1/historical/stock/02171?start_date=20240101&end_date=20240131"
```

### 前端测试
```bash
# 启动前端服务
cd quantdb_frontend && streamlit run app.py

# 手动测试
# 1. 进入"股票数据查询"页面
# 2. 输入港股代码: 02171
# 3. 选择日期范围: 2024-01-01 到 2024-01-31
# 4. 点击"查询数据"
# 5. 验证数据正确显示
```

## 🎯 成功标准

实施完成后，系统应该能够：
- ✅ 成功查询港股历史数据 (如科济药业-B 02171)
- ✅ 展示港股价格图表和技术指标
- ✅ 保持A股功能完全不受影响
- ✅ 提供与A股一致的用户体验
- ✅ 通过所有测试用例

**预计完成时间**: 5小时
**风险等级**: 🟢 低
**用户价值**: 🌟 高 - 扩展市场覆盖，提升平台竞争力
