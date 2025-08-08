# AKShare → QuantDB 迁移指南：零改动、可回滚

适用版本：v2.2.8 ｜ 最后更新：2025-08-08

## TL;DR（一分钟上手）
1. 安装：
```bash
pip install quantdb
```
2. 导入：
```python
import qdb  # 包名：quantdb；导入名：qdb
```
3. 替换调用（示例）：
```python
# Before (AKShare)
# from akshare import stock_zh_a_hist
# df = stock_zh_a_hist(symbol="000001", start_date="20240101", end_date="20240201")

# After (QuantDB, 完全兼容接口)
import qdb

df = qdb.stock_zh_a_hist("000001", start_date="20240101", end_date="20240201")
```
4. 其他常用调用：
```python
# 最近30天数据（简化API）
df = qdb.get_stock_data("000001", days=30)
# 实时
entry = qdb.get_realtime_data("000001")
# 股票列表
stocks = qdb.get_stock_list()
```

## 为什么迁移到 QuantDB？
- 98.1% 性能提升：缓存命中 ~18ms（从 ~1000ms 降到毫秒级）
- 100% AKShare 接口兼容：最小改动、保留原工作流
- 生产就绪：259 个测试 100% 通过，错误处理完善
- 多市场支持：A 股 + 港股统一 API

## 常见 API 映射
- 历史数据：
  - AKShare: `stock_zh_a_hist(symbol, start_date, end_date, ...)`
  - QuantDB: `qdb.stock_zh_a_hist(symbol, start_date, end_date, ...)`
  - QuantDB（简化）：`qdb.get_stock_data(symbol, days=30)`
- 实时数据：
  - QuantDB: `qdb.get_realtime_data(symbol)` / `qdb.get_realtime_data_batch(symbols)`
- 股票列表：
  - QuantDB: `qdb.get_stock_list(market=None)`
- 财务数据：
  - QuantDB: `qdb.get_financial_summary(symbol)` / `qdb.get_financial_indicators(symbol)`
- 指数数据：
  - QuantDB: `qdb.get_index_data(symbol, start_date, end_date)` 等

提示：QuantDB 保持与 AKShare 一致的数据结构和语义；不同之处在于缓存、性能与稳定性。

## 迁移路径选型

### 路径 A：最小变更（推荐）
- 在原有使用处，将 AKShare 的调用替换为 `qdb.*` 等价接口
- 优点：可控、渐进式；无需大规模重构
- 示例：
```python
# 原代码
# from akshare import stock_zh_a_hist
# df = stock_zh_a_hist("000001", start_date="20240101", end_date="20240201")

# 替换后
import qdb

df = qdb.stock_zh_a_hist("000001", start_date="20240101", end_date="20240201")
```

### 路径 B：适配器（别名兼容）
- 在边界层定义别名，尽量减少业务代码变更
```python
import qdb

# 在你项目的 data_api.py 边界层
stock_zh_a_hist = qdb.stock_zh_a_hist
get_realtime_data = qdb.get_realtime_data
get_stock_list = qdb.get_stock_list
```
- 业务层继续 `from data_api import stock_zh_a_hist`，实现平滑替换

## 性能与验证

### 验收清单
- [ ] 核心路径可用（历史/实时/列表）
- [ ] 首次请求 ~1-2s；重复请求 ~10-50ms
- [ ] 结果与 AKShare 一致（字段/语义）
- [ ] 日志与错误处理正常

### 基准测试示例
```python
import time
import qdb

symbol = "000001"

# 冷启动（会访问 AKShare）
start = time.time(); qdb.get_stock_data(symbol, days=30); cold = time.time() - start
# 缓存命中
start = time.time(); qdb.get_stock_data(symbol, days=30); warm = time.time() - start

print(f"首次: {cold:.3f}s, 缓存命中: {warm:.3f}s, 提升: {(cold-warm)/cold*100:.1f}%")
```

## 回退策略
- QuantDB 为兼容增强，不会破坏原流程；如需回退，只需将导入和调用切回 AKShare
- 保留一处“切换开关”（如环境变量/配置项），可快速切换数据层以便排障

## 常见问题（FAQ）
- 首次仍然较慢？正常，首次会请求 AKShare；后续命中缓存即为毫秒级
- 导入失败？请确认使用 `pip install quantdb`，且导入名为 `import qdb`
- 缓存目录权限（Windows）？建议使用项目内或用户目录路径

## 参考与资源
- 文档站：https://franksunye.github.io/quantdb/
- PyPI：https://pypi.org/project/quantdb/
- GitHub：https://github.com/franksunye/quantdb
- Issues：https://github.com/franksunye/quantdb/issues

