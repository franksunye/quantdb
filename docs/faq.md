# QuantDB FAQ（常见问题）

最后更新：2025-08-08 | 适用版本：v2.2.8

## 1. 如何安装？
```bash
pip install quantdb
```

## 2. 包名与导入名不一致？
- 包名：`quantdb`
- 导入名：`qdb`
- 示例：
```python
import qdb  # 正确
```

## 3. 首次调用很慢是正常的吗？
- 正常。首次获取会请求 AKShare，通常需要 1-2 秒；随后命中本地缓存为毫秒级（~18ms）。

## 4. 如何指定/查看缓存目录？
```python
import qdb
qdb.init(cache_dir="./my_qdb_cache")
# 或在任意时刻：
qdb.set_cache_dir("./my_qdb_cache")
```

## 5. 如何清除缓存？
```python
qdb.clear_cache()          # 清除所有缓存
qdb.clear_cache("000001")  # 清除指定股票缓存
```

## 6. 与 AKShare 是否兼容？
- 是。QuantDB 保持与 AKShare 一致的数据结构和语义，并提供同名接口：
```python
# 兼容接口示例
qdb.stock_zh_a_hist("000001", start_date="20240101", end_date="20240201")
```

## 7. 支持哪些市场？
- A 股与港股（自动识别代码格式，统一 API）。

## 8. 如何获取实时数据和股票列表？
```python
rt = qdb.get_realtime_data("000001")
all_stocks = qdb.get_stock_list()
```

## 9. 常见错误与排查
- ImportError: `ModuleNotFoundError: No module named 'qdb'`
  - 请确认已执行 `pip install quantdb`，并使用 `import qdb` 导入。
- 网络超时/数据为空：
  - 检查本地网络与 AKShare 源的连通性；稍后重试。
- 权限问题（Windows）：
  - 避免将缓存目录放在需要管理员权限的路径，建议使用用户目录或项目内路径。

## 10. 如何查看缓存统计与性能？
```python
stats = qdb.cache_stats()
print(stats)
```

## 11. 如何在 Windows PowerShell 使用？
- 建议使用虚拟环境：
```powershell
python -m venv .venv
. .venv\Scripts\Activate.ps1
pip install quantdb
```

## 12. 与企业/生产环境相关的问题
- 是否支持 API 服务化？支持，可参考 docs/03_API_SERVICE_GUIDE.md 与 Dockerfile。
- 是否支持指标监控？可通过 `cache_stats()` 获取基础指标，更多监控可在 API/云平台版本实现。

## 13. 获取帮助
- Issues: https://github.com/franksunye/quantdb/issues
- Discussions: https://github.com/franksunye/quantdb/discussions
- 文档站点: https://franksunye.github.io/quantdb/

