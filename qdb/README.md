# QDB - 智能缓存的股票数据库

🚀 **一行代码享受AKShare缓存加速**

**重要提示**: 从v2.2.0开始，请使用新的包名安装：
```bash
pip install quantdb  # 新包名
import qdb           # 导入名保持不变
```

QDB是一个智能缓存的AKShare包装器，通过本地SQLite缓存实现90%+的性能提升，让股票数据获取从秒级优化到毫秒级。

## ✨ 核心特性

- 🚀 **90%+性能提升**: 本地SQLite缓存避免重复网络请求
- 🧠 **智能增量更新**: 只获取缺失的数据，最大化缓存效率  
- ⚡ **毫秒级响应**: 缓存命中时响应时间 < 10ms
- 📅 **交易日历集成**: 基于真实交易日历的智能数据获取
- 🔧 **零配置启动**: 自动初始化本地缓存数据库
- 🔄 **完全兼容**: 保持AKShare相同的API接口

## 🚀 快速开始

### 安装
```bash
# 使用新的包名安装
pip install quantdb
```

### 基础使用
```python
import qdb

# 获取股票历史数据（自动缓存）
df = qdb.get_stock_data("000001", days=30)

# 批量获取多只股票
stocks = ["000001", "000002", "600000"]
data = qdb.get_multiple_stocks(stocks, days=30)

# 获取资产信息
info = qdb.get_asset_info("000001")
```

### 高级功能
```python
# 兼容AKShare的完整API
df = qdb.stock_zh_a_hist("000001", start_date="20240101", end_date="20240201")

# 缓存管理
stats = qdb.cache_stats()  # 查看缓存统计
qdb.clear_cache()         # 清除所有缓存
qdb.clear_cache("000001") # 清除特定股票缓存

# 配置缓存目录
qdb.set_cache_dir("./my_cache")
```

## 📊 性能对比

| 指标 | AKShare直接调用 | QDB缓存 | 性能提升 |
|------|----------------|---------|----------|
| **响应时间** | ~1000ms | ~10ms | **99%** ⬆️ |
| **重复请求** | 每次都请求 | 缓存命中 | **无网络请求** ✅ |
| **数据一致性** | 手动管理 | 智能更新 | **自动化** 🧠 |

## 🎯 使用场景

### 量化研究
```python
# 快速回测多只股票
symbols = ["000001", "000002", "600000", "600036"]
data = qdb.get_multiple_stocks(symbols, days=252)  # 一年数据

for symbol, df in data.items():
    # 进行策略回测
    returns = df['close'].pct_change()
    print(f"{symbol} 年化收益率: {returns.mean() * 252:.2%}")
```

### 数据分析
```python
# 获取股票数据进行分析
df = qdb.get_stock_data("000001", days=90)

# 计算技术指标
df['ma5'] = df['close'].rolling(5).mean()
df['ma20'] = df['close'].rolling(20).mean()

# 可视化分析
import matplotlib.pyplot as plt
df[['close', 'ma5', 'ma20']].plot()
plt.show()
```

## 🔧 配置选项

### 环境变量
```bash
export QDB_CACHE_DIR="./my_cache"    # 缓存目录
export QDB_LOG_LEVEL="INFO"          # 日志级别
export QDB_CACHE_TTL="86400"         # 缓存有效期（秒）
```

### 代码配置
```python
# 设置缓存目录
qdb.set_cache_dir("./custom_cache")

# 设置日志级别
qdb.set_log_level("DEBUG")

# 初始化时指定配置
qdb.init(cache_dir="./my_cache")
```

## 📈 缓存策略

QDB采用智能缓存策略：

1. **交易日历检查**: 只在交易日获取数据
2. **增量更新**: 检测缺失日期，只获取需要的数据
3. **自动过期**: 当日数据自动更新，历史数据长期缓存
4. **错误处理**: 网络异常时优雅降级到缓存数据

## 🛠️ 开发指南

### 本地开发
```bash
# 克隆项目
git clone https://github.com/franksunye/quantdb.git
cd quantdb

# 安装开发依赖
pip install -e .[dev]

# 运行测试
pytest tests/
```

### 贡献代码
1. Fork项目
2. 创建功能分支
3. 提交代码
4. 创建Pull Request

## 📚 API文档

### 核心函数

#### `get_stock_data(symbol, **kwargs)`
获取股票历史数据

**参数**:
- `symbol`: 股票代码
- `start_date`: 开始日期 (可选)
- `end_date`: 结束日期 (可选)  
- `days`: 最近N天 (可选)
- `adjust`: 复权类型 (可选)

#### `get_multiple_stocks(symbols, **kwargs)`
批量获取多只股票数据

#### `cache_stats()`
获取缓存统计信息

#### `clear_cache(symbol=None)`
清除缓存数据

## 🤝 技术支持

- 📖 **文档**: [GitHub Wiki](https://github.com/franksunye/quantdb/wiki)
- 🐛 **问题反馈**: [GitHub Issues](https://github.com/franksunye/quantdb/issues)
- 💬 **讨论交流**: [GitHub Discussions](https://github.com/franksunye/quantdb/discussions)

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

---

**QDB - 让股票数据获取更快更简单！** 🚀
