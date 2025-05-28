# AKShare 使用指南

## 概述

本文档提供了在 QuantDB 和 QuantAgent 项目中使用 AKShare 的最佳实践和标准方法。为了确保一致性和可靠性，所有开发人员在使用 AKShare 时应严格遵循本文档中的指导。

## 最佳实践原则

1. **使用 `AKShareAdapter` 类**：始终通过 `AKShareAdapter` 类进行所有 AKShare 调用，而不是直接调用 AKShare 函数
2. **参数标准化**：使用标准化的参数格式，特别是股票代码和日期格式
3. **错误处理**：依赖 `AKShareAdapter` 类提供的错误处理和重试逻辑
4. **数据标准化**：使用 `AKShareAdapter` 类的标准化方法确保返回的数据格式一致
5. **避免直接依赖**：不要在代码中直接依赖特定的 AKShare 函数，因为它们的实现可能会变化

## 股票历史数据获取

### 使用 `AKShareAdapter` 类

在项目中，我们使用 `AKShareAdapter` 类来获取股票历史数据，而不是直接调用 AKShare 函数。以下是正确的使用方式：

```python
from src.cache.akshare_adapter import AKShareAdapter

# 初始化适配器
adapter = AKShareAdapter()

# 获取股票数据
df = adapter.get_stock_data(
    symbol="000001",  # 股票代码，不带市场前缀
    start_date="20230101",  # 开始日期，格式为 YYYYMMDD
    end_date="20230110",    # 结束日期，格式为 YYYYMMDD
    adjust="",        # 复权方式：""(不复权), "qfq"(前复权), "hfq"(后复权)
    period="daily"    # 周期：daily, weekly, monthly
)
```

#### 参数说明

| 参数 | 类型 | 说明 | 示例 |
|------|------|------|------|
| symbol | str | 股票代码，不带市场前缀 | "000001" |
| start_date | str | 开始日期，格式为 YYYYMMDD | "20230101" |
| end_date | str | 结束日期，格式为 YYYYMMDD | "20230110" |
| adjust | str | 复权方式 | ""(不复权), "qfq"(前复权), "hfq"(后复权) |
| period | str | 数据周期 | "daily", "weekly", "monthly" |

#### 返回数据

返回的 DataFrame 包含以下标准化列名：

- date (日期)
- open (开盘价)
- close (收盘价)
- high (最高价)
- low (最低价)
- volume (成交量)
- turnover (成交额，如果可用)
- amplitude (振幅，如果可用)
- pct_change (涨跌幅，如果可用)
- change (涨跌额，如果可用)
- turnover_rate (换手率，如果可用)

## 重要说明

`AKShareAdapter` 类内部优先使用 `stock_zh_a_hist` 函数获取股票数据，这是官方推荐的方法，并且在当前环境中可以正常工作。为了提高可靠性，`AKShareAdapter` 还实现了备选方案：

1. 首先使用 `stock_zh_a_hist` 函数（首选方法）
2. 如果首选方法失败，会自动尝试使用 `stock_zh_a_hist_tx` 函数（需要带市场前缀的代码，内部会自动转换）
3. 对于指数数据，会尝试使用 `stock_zh_index_daily` 函数

**开发人员不需要关心这些细节**，只需要使用 `AKShareAdapter.get_stock_data()` 方法，它会处理所有的复杂性和错误情况。这种设计确保了即使 AKShare 库的实现发生变化，我们的代码也能继续正常工作。

## `AKShareAdapter` 类的优势

`AKShareAdapter` 类提供以下优势：

1. **错误处理和重试**：自动处理 AKShare API 调用中的错误，并使用指数退避策略进行重试
2. **缓存机制**：缓存结果以减少 API 调用，提高性能
3. **数据标准化**：统一不同数据源的列名和格式，确保一致的数据结构
4. **自动回退**：当首选方法失败时，自动尝试备选方法
5. **日期过滤**：自动处理日期范围过滤，即使底层 API 不直接支持

## 常见问题和解决方案

### 1. 获取数据失败

**问题**：使用 `AKShareAdapter.get_stock_data()` 方法获取数据失败。

**解决方案**：
- 确保股票代码格式正确（不带市场前缀）
- 检查日期范围是否有效
- 确保网络连接正常
- 如果问题持续存在，请联系团队成员

### 2. 数据不一致

**问题**：不同时间获取的数据可能存在不一致。

**解决方案**：
- 使用 `AKShareAdapter` 类的缓存机制，避免频繁请求
- 在数据分析过程中统一使用相同的复权方式
- 记录数据获取的时间戳，以便追踪数据来源

### 3. 性能问题

**问题**：获取大量数据时可能会遇到性能问题。

**解决方案**：
- 尽量缩小日期范围，只获取必要的数据
- 利用 `AKShareAdapter` 的缓存机制
- 对于批量处理，考虑使用异步方法或分批获取

## 结论

在使用 AKShare 时，应严格遵循本文档中的最佳实践。如需使用本文档未涵盖的 AKShare 功能，请先咨询团队成员，并在确认后更新本文档。

## 参考资料

- QuantDB 项目中的 `AKShareAdapter` 类实现
- 项目中的测试文件：`test_akshare_correct.py`, `test_akshare_api.py`, `test_stock_zh_a_hist_detailed.py`
- 最新的测试结果：`test_stock_zh_a_hist_simple.py`, `test_akshare_adapter_simple.py`
