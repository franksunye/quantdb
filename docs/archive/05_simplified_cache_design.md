# 简化缓存设计与智能数据获取策略

## 文档信息
**文档类型**: 架构设计
**文档编号**: quantdb-ARCH-005
**版本**: 1.0.0
**创建日期**: 2025-06-07
**最后更新**: 2025-06-07
**状态**: 草稿
**负责人**: frank

## 1. 概述

本文档描述了QuantDB项目中缓存架构的简化设计和智能数据获取策略。基于对当前架构的分析和业务需求的理解，我们提出了一种更简洁、更高效的缓存机制，特别针对股票历史数据的特性进行了优化。

### 1.1 背景

在之前的实现中，我们采用了"蓄水池"缓存机制，包括CacheEngine和FreshnessTracker组件。然而，通过分析我们发现：

1. 对于股票历史数据，一旦产生就不会改变，不存在"过期"的问题
2. 当前的缓存实现使用SQLite数据库存储缓存数据，与主数据库（也是SQLite）功能重叠
3. 缓存键的粒度不够细，导致无法有效利用已有数据

### 1.2 设计目标

1. 简化缓存架构，减少不必要的复杂性
2. 优化数据获取逻辑，实现智能数据获取策略
3. 为股票历史数据实现专用的缓存机制，考虑其不可变特性
4. 保留架构的扩展性，为未来支持可变数据类型做准备
5. 提高系统性能和可维护性

## 2. 当前架构分析

### 2.1 现有组件

1. **CacheEngine**: 负责数据的存储、检索和管理，使用SQLite数据库存储缓存数据
2. **FreshnessTracker**: 负责跟踪数据的新鲜度和更新状态
3. **AKShareAdapter**: 封装AKShare API调用，与缓存机制集成

### 2.2 现有数据流

1. 用户请求股票历史数据
2. 系统生成缓存键
3. 检查缓存中是否有对应的数据
   - 如果有且新鲜，直接返回缓存数据
   - 如果没有或不新鲜，继续下一步
4. 检查数据库中是否有对应的数据
   - 如果有，从数据库获取数据，存入缓存，然后返回
   - 如果没有，继续下一步
5. 从AKShare获取数据
6. 将获取的数据存入数据库和缓存
7. 返回数据给用户

### 2.3 问题分析

1. **缓存层冗余**: 缓存数据存储在SQLite数据库中，与主数据库功能重叠
2. **缓存键粒度**: 缓存键基于完整查询参数，无法利用部分已有数据
3. **新鲜度跟踪不必要**: 对于不可变的股票历史数据，新鲜度跟踪是不必要的
4. **数据获取策略不智能**: 当数据库中只有部分数据时，系统会尝试获取整个范围的数据

## 3. 简化缓存设计

### 3.1 核心理念

1. **数据库作为持久化缓存**: 直接使用主数据库作为持久化缓存，不再使用单独的缓存层
2. **智能数据获取**: 实现智能数据获取策略，只获取缺失的数据
3. **专注于股票历史数据**: 为股票历史数据实现专用的缓存机制，考虑其不可变特性
4. **保留扩展性**: 设计接口时考虑未来支持可变数据类型的需求

### 3.2 简化后的组件

1. **StockDataService**: 负责股票历史数据的获取、存储和查询
2. **DatabaseCache**: 使用主数据库作为持久化缓存
3. **AKShareAdapter**: 优化后的AKShare适配器，实现智能数据获取

### 3.3 简化后的数据流

1. 用户请求股票历史数据（指定股票代码、开始日期和结束日期）
2. StockDataService接收请求，生成日期范围
3. 查询数据库，检查哪些日期的数据已存在
4. 对于缺失的日期：
   - 将连续的缺失日期分组，减少API调用
   - 从AKShare获取缺失的数据
   - 将获取的数据保存到数据库
5. 从数据库获取完整的请求日期范围数据
6. 返回数据给用户

## 4. 智能数据获取策略

### 4.1 日期范围分段处理

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

### 4.2 连续日期分组算法

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

### 4.3 数据库查询优化

```python
def query_db_for_dates(symbol, dates):
    """
    查询数据库中特定日期的数据。
    
    Args:
        symbol: 股票代码
        dates: 日期列表
        
    Returns:
        包含查询结果的字典，键为日期，值为数据
    """
    results = {}
    
    try:
        # 获取资产ID
        asset = db.query(Asset).filter(Asset.symbol == symbol).first()
        if not asset:
            return results
        
        # 将日期列表转换为日期对象
        date_objects = [datetime.strptime(date, "%Y%m%d").date() for date in dates]
        
        # 使用IN查询，一次性获取所有日期的数据
        query_results = db.query(DailyStockData).filter(
            DailyStockData.asset_id == asset.asset_id,
            DailyStockData.trade_date.in_(date_objects)
        ).all()
        
        # 转换为字典格式
        for result in query_results:
            date_str = result.trade_date.strftime("%Y%m%d")
            results[date_str] = {
                "date": date_str,
                "open": result.open,
                "high": result.high,
                "low": result.low,
                "close": result.close,
                "volume": result.volume,
                # 其他字段...
            }
    except Exception as e:
        logger.error(f"查询数据库失败: {e}")
    
    return results
```

## 5. 架构扩展性

### 5.1 支持可变数据类型

虽然当前设计专注于不可变的股票历史数据，但我们保留了支持可变数据类型（如公司档案、指数等）的能力：

1. **数据服务接口**: 定义通用的数据服务接口，可以为不同数据类型实现不同的服务
2. **数据新鲜度策略**: 为可变数据类型保留新鲜度跟踪的能力
3. **缓存策略接口**: 定义缓存策略接口，可以为不同数据类型实现不同的缓存策略

### 5.2 未来扩展示例

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

## 6. 实施计划

### 6.1 阶段一：基础架构调整

1. 创建StockDataService类，实现基本功能
2. 修改AKShareAdapter，适应新的架构
3. 调整API接口，使用新的服务

### 6.2 阶段二：智能数据获取实现

1. 实现日期范围分段处理
2. 实现连续日期分组算法
3. 优化数据库查询

### 6.3 阶段三：测试与优化

1. 编写单元测试和集成测试
2. 进行性能测试
3. 根据测试结果进行优化

### 6.4 阶段四：文档与部署

1. 更新架构文档
2. 更新API文档
3. 部署到测试环境

## 7. 总结

通过简化缓存架构和实现智能数据获取策略，我们可以显著提高系统性能和可维护性。新的设计专注于股票历史数据的特性，同时保留了支持其他数据类型的扩展能力。

## 更新记录

| 版本 | 日期 | 更新者 | 更新内容 |
|------|------|--------|----------|
| 1.0.0 | 2025-06-07 | frank | 初始版本 |
