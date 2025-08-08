# QuantDB 文档

高性能、易用的股票数据开发者工具。QuantDB 通过本地 SQLite 智能缓存为 AKShare 带来 90%+ 的性能提升，导入名简洁为 `qdb`。

- PyPI: https://pypi.org/project/quantdb/
- 源码与 Issue: https://github.com/franksunye/quantdb

## 30 秒上手

```python
pip install quantdb

import qdb

# 获取最近 30 天数据（自动缓存）
df = qdb.get_stock_data("000001", days=30)

# 实时行情
tick = qdb.get_realtime_data("000001")

# 股票列表
stocks = qdb.get_stock_list()
```

更多使用示例见「快速开始」与「示例」。

## 为什么选择 QuantDB
- 90%+ 加速：缓存命中毫秒级响应
- AKShare 兼容：无缝迁移常用接口
- 简洁 API：qdb.get_stock_data / get_realtime_data 等
- 离线友好：本地缓存可离线访问

## 产品形态
- Python 包（qdb）：开发者首选
- API 服务（FastAPI）：企业级集成
- 云平台（Streamlit）：零安装可视化

## 文档导航
- 快速开始：安装、初始化、常见调用
- API 参考：公开函数说明与参数
- 示例：可运行脚本与输出
- 变更日志、架构：了解演进与设计

