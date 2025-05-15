# "蓄水池" 缓存系统

## 概述

"蓄水池" 缓存系统是 QuantDB 项目的核心组件之一，用于存储和管理数据，提高系统性能和响应速度。该系统由两个主要组件组成：`CacheEngine` 和 `FreshnessTracker`。

- **CacheEngine**：负责数据的存储、检索和管理
- **FreshnessTracker**：负责跟踪数据的新鲜度和更新状态

## 设计目标

1. **高性能**：快速存储和检索数据
2. **可靠性**：确保数据的完整性和一致性
3. **灵活性**：支持各种数据类型和缓存策略
4. **可监控性**：提供详细的统计信息和监控功能
5. **可扩展性**：易于扩展和集成到其他系统中

## 核心组件

### CacheEngine

`CacheEngine` 类负责数据的存储、检索和管理。它提供以下主要功能：

- **数据存储**：将数据存储到缓存中，支持 TTL（生存时间）设置
- **数据检索**：从缓存中检索数据
- **缓存管理**：清理过期数据，管理缓存大小
- **缓存统计**：提供缓存使用情况的统计信息

#### 主要方法

- `set(cache_key, data, ttl=None)`: 将数据存储到缓存中
- `get(cache_key)`: 从缓存中检索数据
- `delete(cache_key)`: 删除缓存中的数据
- `invalidate(cache_key)`: 使缓存中的数据失效
- `clear()`: 清空缓存
- `get_keys(prefix=None)`: 获取所有缓存键
- `get_stats()`: 获取缓存统计信息

### FreshnessTracker

`FreshnessTracker` 类负责跟踪数据的新鲜度和更新状态。它提供以下主要功能：

- **新鲜度跟踪**：跟踪数据的新鲜度状态（新鲜、过时、过期）
- **更新调度**：调度数据更新任务
- **新鲜度统计**：提供数据新鲜度的统计信息

#### 主要方法

- `mark_updated(cache_key, ttl=None)`: 将数据标记为已更新并注册缓存键以进行新鲜度跟踪
- `mark_fresh(cache_key)`: 将数据标记为新鲜
- `mark_stale(cache_key)`: 将数据标记为过时
- `mark_expired(cache_key)`: 将数据标记为过期
- `schedule_update(cache_key, priority=0)`: 调度数据更新
- `cancel_update(cache_key)`: 取消数据更新
- `get_freshness_status(cache_key)`: 获取数据的新鲜度状态
- `get_stats()`: 获取新鲜度统计信息

## 缓存键生成策略

缓存键生成是缓存系统的关键部分，它决定了如何唯一标识缓存中的数据。`CacheEngine` 类提供了一个强大的键生成策略，支持以下特性：

- **命名空间**：使用 `namespace` 参数将缓存键分组
- **前缀**：使用 `prefix` 参数添加前缀
- **版本**：使用 `version` 参数添加版本信息
- **复杂数据类型**：支持 pandas DataFrame、日期时间对象等复杂数据类型

示例：

```python
# 生成带命名空间的缓存键
key = cache_engine.generate_key("stock_data", namespace="market_data")

# 生成带前缀的缓存键
key = cache_engine.generate_key("000001", prefix="stock")

# 生成带版本的缓存键
key = cache_engine.generate_key("stock_data", version="1.0")

# 生成包含复杂数据的缓存键
key = cache_engine.generate_key("stock_data", params={"symbol": "000001", "start_date": datetime(2023, 1, 1)})
```

## 缓存状态 API

缓存系统提供了一个 RESTful API，用于查询和管理缓存状态。API 端点包括：

### 主要端点

- `GET /api/cache/stats`: 获取缓存统计信息
- `GET /api/cache/freshness/stats`: 获取新鲜度统计信息
- `GET /api/cache/keys`: 获取所有缓存键
- `GET /api/cache/entry/{key}`: 获取特定缓存条目的详细信息
- `DELETE /api/cache/clear`: 清空缓存
- `DELETE /api/cache/entry`: 删除特定缓存条目
- `POST /api/cache/invalidate`: 使特定缓存条目失效

### 简化端点

系统还提供了简化的缓存管理端点：

- `GET /cache/status`: 获取缓存和新鲜度的综合统计信息
- `DELETE /cache/clear`: 清空所有缓存或特定缓存键
- `GET /cache/key/{key}`: 获取特定缓存条目的详细信息
- `POST /cache/refresh`: 强制刷新特定缓存条目

## 缓存监控功能

缓存系统提供了丰富的监控功能，包括：

- **基本统计信息**：缓存条目数量、命中率、缓存大小等
- **热点键**：访问频率最高的缓存键
- **新鲜度指标**：新鲜数据比例、过期数据比例等
- **健康状态**：缓存系统的整体健康状态
- **性能指标**：平均访问时间、内存使用效率等

## 使用示例

### 基本使用

```python
from src.cache.cache_engine import CacheEngine
from src.cache.freshness_tracker import FreshnessTracker

# 初始化缓存引擎和新鲜度跟踪器
cache_engine = CacheEngine()
freshness_tracker = FreshnessTracker()

# 存储数据到缓存中
cache_key = "stock_data_000001"
data = {"open": 10.5, "close": 11.2, "high": 11.5, "low": 10.2}
ttl = 3600  # 1 小时
cache_engine.set(cache_key, data, ttl=ttl)

# 将数据标记为已更新并注册缓存键以进行新鲜度跟踪
freshness_tracker.mark_updated(cache_key, ttl=ttl)

# 从缓存中检索数据
cached_data = cache_engine.get(cache_key)

# 获取数据的新鲜度状态
freshness_info = freshness_tracker.get_freshness_status(cache_key)

# 标记数据为过时
freshness_tracker.mark_stale(cache_key)

# 调度数据更新
freshness_tracker.schedule_update(cache_key, priority=5)

# 更新数据后，标记为新鲜
cache_engine.set(cache_key, updated_data, ttl=ttl)
freshness_tracker.mark_fresh(cache_key)

# 获取缓存统计信息
cache_stats = cache_engine.get_stats()
freshness_stats = freshness_tracker.get_stats()
```

### 使用缓存状态 API

```python
import requests

# 获取缓存统计信息
response = requests.get("http://localhost:8000/api/cache/stats")
cache_stats = response.json()

# 获取新鲜度统计信息
response = requests.get("http://localhost:8000/api/cache/freshness/stats")
freshness_stats = response.json()

# 获取所有缓存键
response = requests.get("http://localhost:8000/api/cache/keys")
cache_keys = response.json()

# 获取特定缓存条目的详细信息
response = requests.get(f"http://localhost:8000/api/cache/entry/{cache_key}")
entry_details = response.json()

# 使特定缓存条目失效
response = requests.post("http://localhost:8000/api/cache/invalidate", json={"key": cache_key})
result = response.json()

# 删除特定缓存条目
response = requests.delete("http://localhost:8000/api/cache/entry", json={"key": cache_key})
result = response.json()

# 清空缓存
response = requests.delete("http://localhost:8000/api/cache/clear")
result = response.json()
```

## 最佳实践

1. **合理设置 TTL**：根据数据的更新频率和重要性设置合适的 TTL
2. **使用命名空间和前缀**：使用命名空间和前缀组织缓存键，避免冲突
3. **监控缓存状态**：定期检查缓存统计信息，及时发现问题
4. **定期清理过期数据**：设置定时任务清理过期数据，避免缓存过大
5. **使用新鲜度跟踪**：使用新鲜度跟踪器跟踪数据的新鲜度，确保数据的及时更新

## 总结

"蓄水池" 缓存系统是 QuantDB 项目的核心组件，提供了高性能、可靠、灵活的数据缓存和管理功能。通过合理使用缓存系统，可以显著提高系统性能和响应速度，降低外部数据源的访问频率，提升用户体验。
