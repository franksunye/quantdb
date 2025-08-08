# QuantDB Cheat Sheet（速查表）

最后更新：2025-08-08 | 适用版本：v2.2.8

## 安装与导入
```bash
pip install quantdb
```
```python
import qdb
```

## 快速开始
```python
# 最近30天历史数据（自动缓存）
df = qdb.get_stock_data("000001", days=30)

# 指定区间
df = qdb.get_stock_data("000001", start_date="20240101", end_date="20240201")

# 实时数据
rt = qdb.get_realtime_data("000001")

# 股票列表
stocks = qdb.get_stock_list()
```

## 批量与缓存
```python
# 批量获取多只股票
data = qdb.get_multiple_stocks(["000001", "000002", "600000"], days=30)

# 缓存统计
stats = qdb.cache_stats()

# 清除缓存
qdb.clear_cache()           # 全部
qdb.clear_cache("000001")   # 指定
```

## 配置与日志
```python
qdb.init(cache_dir="./qdb_cache")
qdb.set_cache_dir("./qdb_cache")
qdb.set_log_level("INFO")
```

## AKShare 兼容接口
```python
df = qdb.stock_zh_a_hist("000001", start_date="20240101", end_date="20240201")
```

## 常见问题（FAQ）
- 首次慢是正常：之后缓存命中为毫秒级
- 包名是 quantdb，导入名是 qdb
- Windows 建议使用虚拟环境并注意缓存目录权限

## 资源
- PyPI: https://pypi.org/project/quantdb/
- GitHub: https://github.com/franksunye/quantdb
- Docs: https://franksunye.github.io/quantdb/
- Issues: https://github.com/franksunye/quantdb/issues

