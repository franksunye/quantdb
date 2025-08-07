# QuantDB 指数数据API使用指南

## 概述

QuantDB 指数数据API提供了完整的中国股票指数数据服务，包括：

- **指数历史数据** - 获取指数的历史价格数据
- **指数实时数据** - 获取指数的实时价格数据  
- **指数列表** - 支持主要指数（上证指数、深证成指、创业板指等）

## 支持的指数

### 主要指数类别

- **沪深重要指数**: 上证指数、深证成指、创业板指、沪深300等
- **上证系列指数**: 上证50、上证180、上证380等
- **深证系列指数**: 深证100、中小板指等
- **中证系列指数**: 中证500、中证1000等

### 常用指数代码

| 指数代码 | 指数名称 | 类别 |
|---------|---------|------|
| 000001 | 上证指数 | 沪深重要指数 |
| 399001 | 深证成指 | 沪深重要指数 |
| 399006 | 创业板指 | 沪深重要指数 |
| 000300 | 沪深300 | 沪深重要指数 |
| 000016 | 上证50 | 上证系列指数 |
| 000905 | 中证500 | 中证系列指数 |

## API接口

### 1. 获取指数历史数据

```http
GET /api/v1/index/historical/{symbol}
```

**参数:**
- `symbol` (必需): 指数代码，如 '000001'
- `start_date` (可选): 开始日期，格式 YYYYMMDD
- `end_date` (可选): 结束日期，格式 YYYYMMDD  
- `period` (可选): 数据频率，可选 'daily', 'weekly', 'monthly'，默认 'daily'
- `force_refresh` (可选): 是否强制刷新缓存，默认 false

**示例:**
```bash
curl "http://localhost:8000/api/v1/index/historical/000001?start_date=20240101&end_date=20240201"
```

**响应:**
```json
{
  "symbol": "000001",
  "name": "上证指数",
  "start_date": "20240101",
  "end_date": "20240201",
  "period": "daily",
  "data": [
    {
      "date": "2024-01-02",
      "open": 2974.93,
      "high": 2996.92,
      "low": 2974.93,
      "close": 2974.93,
      "volume": 285455945,
      "turnover": 321018391310,
      "change": 0.0,
      "pct_change": 0.0,
      "amplitude": 0.74
    }
  ],
  "metadata": {
    "count": 22,
    "status": "success",
    "message": "Successfully retrieved 22 data points"
  }
}
```

### 2. 获取指数实时数据

```http
GET /api/v1/index/realtime/{symbol}
```

**参数:**
- `symbol` (必需): 指数代码
- `force_refresh` (可选): 是否强制刷新缓存，默认 false

**示例:**
```bash
curl "http://localhost:8000/api/v1/index/realtime/000001"
```

**响应:**
```json
{
  "symbol": "000001",
  "name": "上证指数",
  "price": 2967.25,
  "open": 2967.25,
  "high": 2967.25,
  "low": 2967.25,
  "prev_close": 2967.25,
  "change": 0.0,
  "pct_change": 0.0,
  "amplitude": 0.0,
  "volume": 285455945,
  "turnover": 321018391310,
  "timestamp": "2025-08-07T10:30:00",
  "cache_hit": false,
  "is_trading_hours": true,
  "metadata": {
    "status": "success",
    "message": "Successfully retrieved realtime data for 000001"
  }
}
```

### 3. 获取指数列表

```http
GET /api/v1/index/list
```

**参数:**
- `category` (可选): 指数类别筛选
- `force_refresh` (可选): 是否强制刷新缓存，默认 false

**示例:**
```bash
curl "http://localhost:8000/api/v1/index/list?category=沪深重要指数"
```

### 4. 获取指数类别

```http
GET /api/v1/index/categories
```

**示例:**
```bash
curl "http://localhost:8000/api/v1/index/categories"
```

## Python包使用

### 安装

```bash
pip install quantdb
```

### 基础使用

```python
import quantdb as qdb

# 初始化（可选）
qdb.init()

# 1. 获取指数历史数据
df = qdb.get_index_data("000001", start_date="20240101", end_date="20240201")
print(f"获取到 {len(df)} 条历史数据")
print(df.head())

# 2. 获取指数实时数据
realtime = qdb.get_index_realtime("000001")
print(f"上证指数当前价格: {realtime['price']}")
print(f"涨跌幅: {realtime['pct_change']}%")

# 3. 获取指数列表
index_list = qdb.get_index_list()
print(f"共有 {len(index_list)} 个指数")

# 按类别筛选
major_indexes = qdb.get_index_list(category="沪深重要指数")
print(f"主要指数: {len(major_indexes)} 个")
```

### 高级使用

```python
# 获取多个指数的实时数据
symbols = ["000001", "399001", "399006"]  # 上证指数、深证成指、创业板指
realtime_data = {}

for symbol in symbols:
    data = qdb.get_index_realtime(symbol)
    realtime_data[symbol] = data
    print(f"{data['name']}: {data['price']} ({data['pct_change']:+.2f}%)")

# 获取长期历史数据
import pandas as pd
from datetime import datetime, timedelta

# 获取过去一年的数据
end_date = datetime.now().strftime('%Y%m%d')
start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')

df = qdb.get_index_data("000300", start_date=start_date, end_date=end_date)
print(f"沪深300过去一年数据: {len(df)} 条")

# 计算简单统计
print(f"最高点: {df['high'].max():.2f}")
print(f"最低点: {df['low'].min():.2f}")
print(f"平均收盘价: {df['close'].mean():.2f}")
```

## 缓存策略

### 历史数据缓存
- **缓存位置**: 数据库
- **缓存时长**: 永久缓存，增量更新
- **更新策略**: 每日自动更新最新数据

### 实时数据缓存
- **交易时间内**: 1-5分钟缓存
- **非交易时间**: 30分钟缓存
- **缓存位置**: 数据库内存缓存

### 指数列表缓存
- **缓存时长**: 每日更新
- **更新时间**: 每天首次请求时自动更新

## 错误处理

### 常见错误码

- `400`: 参数错误（如指数代码格式不正确）
- `404`: 数据不存在（如指数代码不存在）
- `500`: 服务器内部错误

### Python包异常

```python
from qdb.exceptions import QDBError, DataError

try:
    df = qdb.get_index_data("INVALID")
except DataError as e:
    print(f"数据获取失败: {e}")
except QDBError as e:
    print(f"QDB错误: {e}")
```

## 性能优化

### 批量查询建议

```python
# 推荐：使用缓存，避免频繁请求
symbols = ["000001", "399001", "399006"]
data = {}

for symbol in symbols:
    # 使用缓存，只在必要时刷新
    data[symbol] = qdb.get_index_realtime(symbol, force_refresh=False)

# 避免：频繁强制刷新
# for symbol in symbols:
#     data[symbol] = qdb.get_index_realtime(symbol, force_refresh=True)  # 不推荐
```

### 数据量控制

```python
# 大量历史数据建议分批获取
import pandas as pd
from datetime import datetime, timedelta

def get_index_data_batch(symbol, days_back=365, batch_days=90):
    """分批获取大量历史数据"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    
    all_data = []
    current_start = start_date
    
    while current_start < end_date:
        current_end = min(current_start + timedelta(days=batch_days), end_date)
        
        batch_data = qdb.get_index_data(
            symbol,
            start_date=current_start.strftime('%Y%m%d'),
            end_date=current_end.strftime('%Y%m%d')
        )
        
        if not batch_data.empty:
            all_data.append(batch_data)
        
        current_start = current_end + timedelta(days=1)
    
    return pd.concat(all_data, ignore_index=True) if all_data else pd.DataFrame()

# 使用示例
df = get_index_data_batch("000001", days_back=1000)
print(f"获取到 {len(df)} 条数据")
```

## 更新日志

### v2.3.0 (2025-08-07)
- ✅ 新增指数历史数据API
- ✅ 新增指数实时数据API  
- ✅ 新增指数列表API
- ✅ 支持主要指数（上证/深证/创业板）
- ✅ 完整Python包集成
- ✅ 智能缓存策略
- ✅ 完整的错误处理和文档
