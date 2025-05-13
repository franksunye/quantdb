# 系统架构概览

## 1. 系统概述

QuantDB是一个量化交易数据管理和分析系统，用于下载、存储、处理和分析股票市场数据，生成交易信号，并管理交易计划。系统采用模块化设计，各组件之间通过明确的接口进行交互，确保系统的可扩展性和可维护性。

## 2. 系统组件

### 2.1 数据获取层

**主要组件**:
- `downloader.py`: 负责从外部数据源下载股票和指数数据
- `updater.py`: 负责更新已有的股票和指数数据

**功能**:
- 下载股票日线数据
- 下载指数成分股数据
- 获取实时股票数据
- 增量更新历史数据

**数据流**:
- 从外部API获取数据 → 数据清洗和格式化 → 存储到数据库

### 2.2 数据存储层

**主要组件**:
- `database.py`: 提供数据库操作接口
- `SQLite数据库`: 存储所有系统数据

**主要表结构**:
- `assets`: 存储资产信息
- `prices`: 存储历史价格数据
- `index_constituents`: 存储指数成分股关系
- `indicators`: 存储技术指标数据
- `trade_signals`: 存储交易信号
- `trade_plans`: 存储交易计划
- `trades`: 存储实际交易记录
- `strategies`: 存储交易策略
- `orders`: 存储订单信息
- `portfolios`: 存储投资组合信息
- `portfolio_holdings`: 存储投资组合持仓
- `logs`: 存储系统日志
- `backtests`: 存储回测结果
- `optimization_results`: 存储优化结果
- `daily_stock_data`: 存储股票日线数据
- `intraday_stock_data`: 存储股票实时数据

### 2.3 业务逻辑层

**主要组件**:
- `processor.py`: 处理和分析数据
- `indicators.py`: 计算技术指标
- `signal_to_plan.py`: 将交易信号转换为交易计划
- `signal_sender.py`: 发送交易信号
- `calculate_ma_above_ratio.py`: 计算均线上方比例
- `import_optimization_results.py`: 导入优化结果
- `import_trade_signals.py`: 导入交易信号

**功能**:
- 数据分析和处理
- 技术指标计算
- 交易信号生成
- 交易计划管理
- 绩效分析

### 2.4 分析和报告层

**主要组件**:
- `entry_window_performance_analysis.py`: 分析入场窗口绩效
- `trade_plan_performance_analysis.py`: 分析交易计划绩效
- `update_trade_plan_metrics.py`: 更新交易计划指标

**功能**:
- 绩效指标计算
- 图表生成
- 报告输出

### 2.5 调度和控制层

**主要组件**:
- `main.py`: 系统入口点
- `scheduler.py`: 任务调度
- `config.py`: 系统配置
- `logger.py`: 日志记录

**功能**:
- 系统初始化
- 任务调度
- 配置管理
- 日志记录

## 3. 数据流

### 3.1 数据获取流程

1. 系统通过`downloader.py`从外部数据源获取股票和指数数据
2. 数据经过清洗和格式化
3. 通过`database.py`将数据存储到SQLite数据库

### 3.2 信号生成流程

1. 系统通过`processor.py`和`indicators.py`处理历史数据
2. 基于处理结果生成交易信号
3. 交易信号存储到`trade_signals`表
4. 通过`signal_sender.py`将信号发送到外部系统（如企业微信）

### 3.3 交易计划管理流程

1. 系统通过`signal_to_plan.py`将交易信号转换为交易计划
2. 交易计划存储到`trade_plans`表
3. 系统跟踪和更新交易计划的状态和绩效

### 3.4 绩效分析流程

1. 系统通过`entry_window_performance_analysis.py`和`trade_plan_performance_analysis.py`分析交易绩效
2. 生成绩效报告和图表
3. 更新交易计划的绩效指标

## 4. 技术架构

### 4.1 开发语言和框架

- **主要语言**: Python
- **数据处理**: Pandas
- **数据可视化**: Matplotlib
- **数据库**: SQLite

### 4.2 文件组织

- **src/**: 源代码目录
- **data/**: 数据存储目录
- **database/**: 数据库文件和脚本
- **logs/**: 日志文件
- **tests/**: 测试代码

### 4.3 部署架构

系统设计为单机部署，可以通过以下方式运行:

1. **命令行模式**: 通过`main.py`脚本运行特定任务
2. **定时任务**: 通过操作系统的定时任务（如cron）调度运行
3. **手动运行**: 直接运行特定的脚本执行特定功能

## 5. 接口设计

### 5.1 外部接口

- **数据源API**: 用于获取股票和指数数据
- **企业微信Webhook**: 用于发送交易信号通知

### 5.2 内部接口

- **数据库接口**: 通过`database.py`提供统一的数据访问接口
- **配置接口**: 通过`config.py`提供系统配置
- **日志接口**: 通过`logger.py`提供日志记录功能
