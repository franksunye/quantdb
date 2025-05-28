# QuantDB 缓存系统设计

## 文档信息
**文档类型**: 架构设计
**文档编号**: quantdb-ARCH-004
**版本**: 3.0.0
**创建日期**: 2025-06-07
**最后更新**: 2025-05-28
**状态**: 已实现并投入使用
**负责人**: frank

## 1. 概述

本文档描述了QuantDB项目的缓存系统设计，包括简化的缓存架构和智能数据获取策略。基于对业务需求的理解和系统特性的分析，我们采用了一种简洁、高效的缓存机制，特别针对股票历史数据的不可变特性进行了优化。

### 1.1 背景

在项目早期，我们设计了"蓄水池"缓存机制，包括CacheEngine和FreshnessTracker组件。然而，通过分析我们发现：

1. 对于股票历史数据，一旦产生就不会改变，不存在"过期"的问题
2. 当前的缓存实现使用SQLite数据库存储缓存数据，与主数据库功能重叠
3. 缓存键的粒度不够细，导致无法有效利用已有数据

### 1.2 设计目标

1. **简化缓存架构**：减少不必要的复杂性
2. **优化数据获取**：实现智能数据获取策略，减少不必要的API调用
3. **提高性能**：快速存储和检索数据
4. **保持可扩展性**：为未来支持可变数据类型做准备
5. **提高可维护性**：减少组件之间的依赖，提高代码可读性

## 2. 简化缓存设计

### 2.1 核心理念

1. **数据库作为持久化缓存**：直接使用主数据库作为持久化缓存，不再使用单独的缓存层
2. **智能数据获取**：实现智能数据获取策略，只获取缺失的数据
3. **专注于股票历史数据**：为股票历史数据实现专用的缓存机制，考虑其不可变特性
4. **保留扩展性**：设计接口时考虑未来支持可变数据类型的需求

### 2.2 简化后的组件

1. **StockDataService**：负责股票历史数据的获取、存储和查询
2. **DatabaseCache**：使用主数据库作为持久化缓存
3. **AKShareAdapter**：优化后的AKShare适配器，实现智能数据获取

### 2.3 简化后的数据流

```
┌─────────┐     ┌───────────────┐     ┌──────────────┐     ┌──────────────┐
│  客户端  │────▶│    API 层     │────▶│  服务层      │────▶│ 数据库缓存   │
└─────────┘     └───────────────┘     └──────────────┘     └──────────────┘
                                            │                     │
                                            │                     │
                                            ▼                     ▼
                                      ┌──────────────┐     ┌──────────────┐
                                      │ AKShare 适配器│     │   数据库     │
                                      └──────────────┘     └──────────────┘
```

1. 用户请求股票历史数据（指定股票代码、开始日期和结束日期）
2. StockDataService接收请求，生成日期范围
3. 查询数据库，检查哪些日期的数据已存在
4. 对于缺失的日期：
   - 将连续的缺失日期分组，减少API调用
   - 从AKShare获取缺失的数据
   - 将获取的数据保存到数据库
5. 从数据库获取完整的请求日期范围数据
6. 返回数据给用户

## 3. 智能数据获取策略

### 3.1 日期范围分段处理

智能数据获取策略的核心是日期范围分段处理，只获取缺失的数据：

```python
def get_stock_data(symbol, start_date, end_date):
    """
    获取指定日期范围的股票数据。

    Args:
        symbol: 股票代码
        start_date: 开始日期（格式：YYYYMMDD）
        end_date: 结束日期（格式：YYYYMMDD）

    Returns:
        包含请求日期范围数据的DataFrame
    """
    # 生成日期范围内的所有交易日
    trading_days = get_trading_days(start_date, end_date)

    # 查询数据库，检查哪些日期的数据已存在
    existing_data = query_db_for_dates(symbol, trading_days)
    existing_dates = set(existing_data.keys())

    # 找出缺失的日期
    missing_dates = [day for day in trading_days if day not in existing_dates]

    # 如果有缺失的日期，从AKShare获取
    if missing_dates:
        # 将缺失的日期分组为连续的日期范围
        date_groups = group_consecutive_dates(missing_dates)

        for group_start, group_end in date_groups:
            # 从AKShare获取数据
            akshare_data = akshare_adapter.get_stock_data(
                symbol=symbol,
                start_date=group_start,
                end_date=group_end
            )

            # 将获取的数据保存到数据库
            save_to_database(symbol, akshare_data)

            # 更新已有数据
            for date, data in akshare_data.items():
                existing_data[date] = data

    # 按日期排序并返回
    return sort_by_date(existing_data.values())
```

### 3.2 连续日期分组算法

为了减少API调用次数，我们实现了连续日期分组算法：

```python
def group_consecutive_dates(dates):
    """
    将日期列表分组为连续的日期范围。

    Args:
        dates: 日期列表（格式：YYYYMMDD）

    Returns:
        连续日期范围的列表，每个元素为(start_date, end_date)元组
    """
    if not dates:
        return []

    # 按日期排序
    sorted_dates = sorted(dates)

    # 初始化结果和当前组
    result = []
    current_group = [sorted_dates[0]]

    # 遍历排序后的日期
    for i in range(1, len(sorted_dates)):
        current_date = datetime.strptime(sorted_dates[i], "%Y%m%d")
        prev_date = datetime.strptime(sorted_dates[i-1], "%Y%m%d")

        # 如果日期连续，添加到当前组
        if (current_date - prev_date).days <= 3:  # 允许最多2天的间隔（考虑周末）
            current_group.append(sorted_dates[i])
        else:
            # 否则，结束当前组并开始新组
            result.append((current_group[0], current_group[-1]))
            current_group = [sorted_dates[i]]

    # 添加最后一组
    result.append((current_group[0], current_group[-1]))

    return result
```

## 4. 接口设计

### 4.1 服务接口

#### StockDataService

```python
class StockDataService:
    def get_stock_data(symbol, start_date, end_date, adjust=""):
        """获取股票历史数据"""
        pass
```

#### DatabaseCache

```python
class DatabaseCache:
    def get(symbol, dates):
        """从数据库获取数据"""
        pass

    def save(symbol, data):
        """保存数据到数据库"""
        pass

    def get_date_range_coverage(symbol, start_date, end_date):
        """获取日期范围的覆盖情况"""
        pass

    def get_stats():
        """获取缓存统计信息"""
        pass
```

#### AKShareAdapter

```python
class AKShareAdapter:
    def get_stock_data(symbol, start_date, end_date, adjust="", use_mock_data=False, period="daily"):
        """获取股票历史数据"""
        pass
```

## 5. 架构扩展性

虽然当前设计专注于不可变的股票历史数据，但我们保留了支持可变数据类型的能力：

```python
class DataService(ABC):
    """数据服务抽象基类"""

    @abstractmethod
    def get_data(self, **kwargs):
        """获取数据"""
        pass

    @abstractmethod
    def save_data(self, data, **kwargs):
        """保存数据"""
        pass

    @abstractmethod
    def is_data_fresh(self, **kwargs):
        """检查数据是否新鲜"""
        pass


class StockDataService(DataService):
    """股票历史数据服务，针对不可变数据优化"""

    def get_data(self, symbol, start_date, end_date):
        # 实现智能数据获取策略
        pass

    def save_data(self, data, symbol):
        # 保存到数据库
        pass

    def is_data_fresh(self, **kwargs):
        # 对于股票历史数据，只要存在就是新鲜的
        return True


class CompanyProfileService(DataService):
    """公司档案数据服务，处理可变数据"""

    def get_data(self, symbol):
        # 实现数据获取逻辑
        pass

    def save_data(self, data, symbol):
        # 保存到数据库
        pass

    def is_data_fresh(self, symbol, max_age_days=30):
        # 检查数据是否新鲜
        last_update = self.get_last_update_time(symbol)
        if not last_update:
            return False

        age_days = (datetime.now() - last_update).days
        return age_days <= max_age_days
```

## 6. 总结

通过简化缓存架构和实现智能数据获取策略，我们显著提高了系统性能和可维护性。新的设计专注于股票历史数据的特性，同时保留了支持其他数据类型的扩展能力。

## 更新记录

| 版本 | 日期 | 更新者 | 更新内容 |
|------|------|--------|----------|
| 1.0.0 | 2025-05-15 | frank | 初始版本（蓄水池设计） |
| 2.0.0 | 2025-06-16 | frank | 简化缓存设计，整合多个文档 |
