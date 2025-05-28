# Sprint 2.6 实施计划：缓存架构简化与数据获取优化

## 文档信息
**文档类型**: 实施计划
**文档编号**: quantdb-IMPL-001
**版本**: 1.0.0
**创建日期**: 2025-06-07
**最后更新**: 2025-06-07
**状态**: 草稿
**负责人**: frank

## 1. 概述

本文档提供了Sprint 2.6中缓存架构简化与数据获取优化的详细实施计划。基于[简化缓存设计与智能数据获取策略](../05_simplified_cache_design.md)文档中的设计，我们将分阶段实施这些变更，确保系统功能不受影响。

## 2. 实施阶段

### 2.1 阶段一：基础架构调整（3天）

#### 2.1.1 创建新组件

1. 创建`src/services/stock_data_service.py`
   ```python
   class StockDataService:
       """股票数据服务，提供股票历史数据的获取、存储和查询功能。"""
       
       def __init__(self, db, akshare_adapter):
           self.db = db
           self.akshare_adapter = akshare_adapter
       
       def get_stock_data(self, symbol, start_date, end_date, adjust=""):
           """
           获取指定日期范围的股票数据。
           
           Args:
               symbol: 股票代码
               start_date: 开始日期（格式：YYYYMMDD）
               end_date: 结束日期（格式：YYYYMMDD）
               adjust: 价格调整方法
               
           Returns:
               包含请求日期范围数据的DataFrame
           """
           # 实现将在后续阶段完成
           pass
   ```

2. 创建`src/services/database_cache.py`
   ```python
   class DatabaseCache:
       """数据库缓存接口，使用主数据库作为持久化缓存。"""
       
       def __init__(self, db):
           self.db = db
       
       def get(self, symbol, dates):
           """
           从数据库获取特定日期的数据。
           
           Args:
               symbol: 股票代码
               dates: 日期列表
               
           Returns:
               包含查询结果的字典，键为日期，值为数据
           """
           # 实现将在后续阶段完成
           pass
       
       def save(self, symbol, data):
           """
           将数据保存到数据库。
           
           Args:
               symbol: 股票代码
               data: 要保存的数据
           """
           # 实现将在后续阶段完成
           pass
   ```

#### 2.1.2 修改AKShare适配器

1. 更新`src/cache/akshare_adapter.py`，移除对CacheEngine和FreshnessTracker的依赖
   ```python
   class AKShareAdapter:
       """AKShare适配器，封装AKShare API调用。"""
       
       def __init__(self, db):
           self.db = db
       
       def get_stock_data(self, symbol, start_date=None, end_date=None, adjust="", use_mock_data=False, period="daily"):
           """
           获取股票历史数据。
           
           Args:
               symbol: 股票代码
               start_date: 开始日期（格式：YYYYMMDD）
               end_date: 结束日期（格式：YYYYMMDD）
               adjust: 价格调整方法
               use_mock_data: 是否使用模拟数据
               period: 数据频率
               
           Returns:
               包含股票数据的DataFrame
           """
           # 实现将在后续阶段完成
           pass
   ```

#### 2.1.3 调整API接口

1. 更新`src/api/routes/historical_data.py`，使用新的StockDataService
   ```python
   @router.get("/stocks/{symbol}/historical")
   def get_stock_historical_data(
       symbol: str,
       start_date: str,
       end_date: str,
       adjust: str = ""
   ):
       """获取股票历史数据。"""
       stock_data_service = StockDataService(db, akshare_adapter)
       data = stock_data_service.get_stock_data(symbol, start_date, end_date, adjust)
       return data
   ```

2. 添加数据库缓存状态API
   ```python
   @router.get("/database/cache/status")
   def get_database_cache_status(
       symbol: str = None,
       start_date: str = None,
       end_date: str = None,
       data_type: str = "stock"
   ):
       """获取数据库缓存状态。"""
       # 实现将在后续阶段完成
       pass
   ```

### 2.2 阶段二：智能数据获取实现（5天）

#### 2.2.1 实现日期范围分段处理

1. 在`src/services/stock_data_service.py`中实现`get_stock_data`方法
   ```python
   def get_stock_data(self, symbol, start_date, end_date, adjust=""):
       """
       获取指定日期范围的股票数据。
       
       Args:
           symbol: 股票代码
           start_date: 开始日期（格式：YYYYMMDD）
           end_date: 结束日期（格式：YYYYMMDD）
           adjust: 价格调整方法
           
       Returns:
           包含请求日期范围数据的DataFrame
       """
       # 生成日期范围内的所有交易日
       trading_days = self._get_trading_days(start_date, end_date)
       
       # 查询数据库，检查哪些日期的数据已存在
       existing_data = self.db_cache.get(symbol, trading_days)
       existing_dates = set(existing_data.keys())
       
       # 找出缺失的日期
       missing_dates = [day for day in trading_days if day not in existing_dates]
       
       # 如果有缺失的日期，从AKShare获取
       if missing_dates:
           # 将缺失的日期分组为连续的日期范围
           date_groups = self._group_consecutive_dates(missing_dates)
           
           for group_start, group_end in date_groups:
               # 从AKShare获取数据
               akshare_data = self.akshare_adapter.get_stock_data(
                   symbol=symbol,
                   start_date=group_start,
                   end_date=group_end,
                   adjust=adjust
               )
               
               # 将获取的数据保存到数据库
               self.db_cache.save(symbol, akshare_data)
               
               # 更新已有数据
               for date, data in akshare_data.items():
                   existing_data[date] = data
       
       # 按日期排序并返回
       return self._sort_by_date(existing_data.values())
   ```

#### 2.2.2 实现连续日期分组算法

1. 在`src/services/stock_data_service.py`中实现`_group_consecutive_dates`方法
   ```python
   def _group_consecutive_dates(self, dates):
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

#### 2.2.3 实现数据库缓存接口

1. 在`src/services/database_cache.py`中实现`get`和`save`方法
   ```python
   def get(self, symbol, dates):
       """
       从数据库获取特定日期的数据。
       
       Args:
           symbol: 股票代码
           dates: 日期列表
           
       Returns:
           包含查询结果的字典，键为日期，值为数据
       """
       results = {}
       
       try:
           # 获取资产ID
           asset = self.db.query(Asset).filter(Asset.symbol == symbol).first()
           if not asset:
               return results
           
           # 将日期列表转换为日期对象
           date_objects = [datetime.strptime(date, "%Y%m%d").date() for date in dates]
           
           # 使用IN查询，一次性获取所有日期的数据
           query_results = self.db.query(DailyStockData).filter(
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
   
   def save(self, symbol, data):
       """
       将数据保存到数据库。
       
       Args:
           symbol: 股票代码
           data: 要保存的数据
       """
       try:
           # 获取资产ID
           asset = self.db.query(Asset).filter(Asset.symbol == symbol).first()
           if not asset:
               # 创建新资产
               asset = Asset(
                   symbol=symbol,
                   name=f"Stock {symbol}",
                   isin=f"CN{symbol}",
                   asset_type="stock",
                   exchange="CN",
                   currency="CNY"
               )
               self.db.add(asset)
               self.db.commit()
           
           # 保存数据
           for date, item in data.items():
               date_obj = datetime.strptime(date, "%Y%m%d").date()
               
               # 检查数据是否已存在
               existing_data = self.db.query(DailyStockData).filter(
                   DailyStockData.asset_id == asset.asset_id,
                   DailyStockData.trade_date == date_obj
               ).first()
               
               if existing_data:
                   # 数据已存在，跳过
                   logger.info(f"数据已存在，跳过: {symbol} 在 {date}")
                   continue
               
               # 创建新数据记录
               stock_data = DailyStockData(
                   asset_id=asset.asset_id,
                   trade_date=date_obj,
                   open=item["open"],
                   high=item["high"],
                   low=item["low"],
                   close=item["close"],
                   volume=item["volume"],
                   # 其他字段...
               )
               self.db.add(stock_data)
           
           self.db.commit()
           logger.info(f"数据已保存到数据库: {symbol}")
       except Exception as e:
           self.db.rollback()
           logger.error(f"保存数据到数据库失败: {e}")
   ```

### 2.3 阶段三：测试与优化（3天）

#### 2.3.1 编写单元测试

1. 创建`tests/unit/test_stock_data_service.py`
   ```python
   def test_get_stock_data():
       """测试获取股票数据。"""
       # 测试代码
       pass
   
   def test_group_consecutive_dates():
       """测试连续日期分组算法。"""
       # 测试代码
       pass
   ```

2. 创建`tests/unit/test_database_cache.py`
   ```python
   def test_get():
       """测试从数据库获取数据。"""
       # 测试代码
       pass
   
   def test_save():
       """测试保存数据到数据库。"""
       # 测试代码
       pass
   ```

#### 2.3.2 编写集成测试

1. 创建`tests/integration/test_stock_data_flow.py`
   ```python
   def test_stock_data_flow():
       """测试股票数据流程。"""
       # 测试代码
       pass
   ```

#### 2.3.3 编写端到端测试

1. 创建`tests/e2e/test_stock_data_api.py`
   ```python
   def test_stock_data_api():
       """测试股票数据API。"""
       # 测试代码
       pass
   ```

#### 2.3.4 性能测试

1. 创建`tests/performance/test_stock_data_performance.py`
   ```python
   def test_stock_data_performance():
       """测试股票数据性能。"""
       # 测试代码
       pass
   ```

### 2.4 阶段四：文档与部署（2天）

#### 2.4.1 更新文档

1. 更新API文档
2. 更新架构文档
3. 更新开发指南

#### 2.4.2 部署到测试环境

1. 部署到测试环境
2. 进行系统测试
3. 收集反馈

## 3. 时间表

| 阶段 | 任务 | 开始日期 | 结束日期 | 负责人 |
|-----|-----|---------|---------|-------|
| 1 | 基础架构调整 | 2025-06-07 | 2025-06-09 | frank |
| 2 | 智能数据获取实现 | 2025-06-10 | 2025-06-14 | frank |
| 3 | 测试与优化 | 2025-06-15 | 2025-06-17 | frank |
| 4 | 文档与部署 | 2025-06-18 | 2025-06-19 | frank |

## 4. 风险与缓解策略

| 风险 | 影响 | 可能性 | 缓解策略 |
|-----|-----|-------|---------|
| 架构变更引入新问题 | 高 | 中 | 全面的测试覆盖；增量实施；详细记录变更；保留回退方案 |
| 性能下降 | 高 | 低 | 性能测试；基准测试；监控关键指标；优化数据库查询 |
| 数据一致性问题 | 中 | 低 | 事务管理；数据验证；日志记录；监控异常 |
| 未考虑到未来需求 | 中 | 中 | 设计文档考虑扩展性；保留关键抽象；定期架构评审 |

## 5. 总结

本实施计划提供了Sprint 2.6中缓存架构简化与数据获取优化的详细步骤。通过分阶段实施，我们将确保系统功能不受影响，同时提高系统性能和可维护性。

## 更新记录

| 版本 | 日期 | 更新者 | 更新内容 |
|------|------|--------|----------|
| 1.0.0 | 2025-06-07 | frank | 初始版本 |
