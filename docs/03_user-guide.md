# 用户指南

## 🎯 概述

QuantDB 是一个高性能的股票数据工具包，通过智能缓存机制为 AKShare 提供 90%+ 的性能提升。

## 🚀 核心特性

### 智能缓存
- 自动缓存股票数据，避免重复API调用
- 支持多种缓存策略和过期时间设置
- 显著提升数据获取速度

### 简单易用
- 与 AKShare 完全兼容的API
- 导入即用，无需修改现有代码
- 支持所有 AKShare 的股票数据接口

## 📊 基本用法

### 获取股票历史数据

```python
import qdb

# 获取平安银行历史数据
data = qdb.stock_zh_a_hist("000001")
print(data.head())

# 指定时间范围
data = qdb.stock_zh_a_hist(
    symbol="000001",
    start_date="20240101",
    end_date="20241231"
)
```

### 获取实时行情

```python
# 获取实时行情
realtime = qdb.stock_zh_a_spot_em()
print(realtime.head())

# 获取特定股票实时数据
stock_info = qdb.stock_individual_info_em(symbol="000001")
print(stock_info)
```

### 获取财务数据

```python
# 获取财务指标
financial = qdb.stock_financial_em(symbol="000001")
print(financial.head())

# 获取资产负债表
balance = qdb.stock_balance_sheet_by_report_em(symbol="000001")
print(balance.head())
```

## ⚙️ 高级配置

### 缓存设置

```python
import qdb

# 设置缓存过期时间（秒）
qdb.set_cache_expire(3600)  # 1小时

# 清理缓存
qdb.clear_cache()

# 禁用缓存
qdb.disable_cache()

# 启用缓存
qdb.enable_cache()
```

### 数据库配置

```python
# 自定义数据库路径
qdb.set_database_path("./my_stock_data.db")

# 查看缓存统计
stats = qdb.get_cache_stats()
print(f"缓存命中率: {stats['hit_rate']:.2%}")
```

## 🔧 性能优化

### 批量数据获取

```python
# 批量获取多只股票数据
symbols = ["000001", "000002", "600000", "600036"]
data_dict = {}

for symbol in symbols:
    data_dict[symbol] = qdb.stock_zh_a_hist(symbol)
    
print(f"获取了 {len(data_dict)} 只股票的数据")
```

### 缓存预热

```python
# 预先缓存常用数据
popular_stocks = ["000001", "000002", "600000", "600036", "000858"]

for symbol in popular_stocks:
    qdb.stock_zh_a_hist(symbol)  # 预热缓存
    
print("缓存预热完成")
```

## 📈 实际应用场景

### 投资组合分析

```python
import pandas as pd
import qdb

# 定义投资组合
portfolio = {
    "000001": 0.3,  # 平安银行 30%
    "600000": 0.4,  # 浦发银行 40%
    "000858": 0.3   # 五粮液 30%
}

# 获取各股票数据
portfolio_data = {}
for symbol, weight in portfolio.items():
    data = qdb.stock_zh_a_hist(symbol)
    portfolio_data[symbol] = {
        'data': data,
        'weight': weight,
        'latest_price': data['收盘'].iloc[-1]
    }

# 计算投资组合表现
total_value = sum(info['latest_price'] * info['weight'] 
                 for info in portfolio_data.values())
print(f"投资组合当前价值: {total_value:.2f}")
```

### 技术指标计算

```python
import qdb
import pandas as pd

# 获取股票数据
data = qdb.stock_zh_a_hist("000001")

# 计算移动平均线
data['MA5'] = data['收盘'].rolling(window=5).mean()
data['MA20'] = data['收盘'].rolling(window=20).mean()

# 计算RSI
def calculate_rsi(prices, window=14):
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

data['RSI'] = calculate_rsi(data['收盘'])

print(data[['收盘', 'MA5', 'MA20', 'RSI']].tail())
```

## 🚨 注意事项

1. **数据更新频率**：缓存数据可能不是最新的，根据需要调整缓存过期时间
2. **网络依赖**：首次获取数据需要网络连接
3. **存储空间**：长期使用会积累大量缓存数据，定期清理
4. **API限制**：遵守数据源的使用条款和频率限制

## 📚 更多资源

- [API参考](04_api-reference.md) - 完整的API文档
- [示例代码](05_examples.md) - 更多实用示例
- [常见问题](06_faq.md) - 问题解答
- [更新日志](99_changelog.md) - 版本历史
