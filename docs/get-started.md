# 快速开始

本页摘选并整合当前仓库的包使用指南，帮助你在数分钟内完成安装与调用。

## 安装
```bash
pip install quantdb
```

## 导入与初始化
```python
import quantdb as qdb  # 包名 quantdb，导入名 qdb

# 可选：指定缓存目录
db_dir = "./my_quantdb_cache"
qdb.init(cache_dir=db_dir)
```

提示：首次调用会自动初始化，无需显式调用 init。

## 基础使用
```python
import qdb

# 1) 股票历史数据（简化 API）
df = qdb.get_stock_data("000001", days=30)

# 2) 批量获取
data = qdb.get_multiple_stocks(["000001", "000002", "600000"], days=30)

# 3) 实时行情
rt = qdb.get_realtime_data("000001")

# 4) 股票列表（可按市场过滤）
all_stocks = qdb.get_stock_list()
```

## 高级使用
```python
# 兼容 AKShare 的接口（示例）
df = qdb.stock_zh_a_hist("000001", start_date="20240101", end_date="20240201")

# 缓存管理
stats = qdb.cache_stats()
qdb.clear_cache()            # 清除全部
qdb.clear_cache("000001")    # 清除特定标的

# 配置调整
qdb.set_cache_dir("./qdb_cache")
qdb.set_log_level("INFO")
```

更多能力（财务摘要、财务指标等）请参见 API 参考。

## 运行示例脚本
仓库 examples/ 目录包含可运行脚本：
```bash
python examples/basic_usage.py
python examples/realtime.py
python examples/stock_list.py
python examples/finance.py
python examples/cache_management.py
```

如遇问题，请查看 FAQ 或提交 Issue。

