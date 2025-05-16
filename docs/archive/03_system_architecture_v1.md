# 系统架构概览

## 1. 系统概述

QuantDB是一个面向Agent时代的开源金融智能中间件平台，通过MCP（Model Context Protocol）协议标准化自然语言与金融数据之间的接口，支持AI原生、上下文感知、结构化响应的金融服务。系统采用模块化设计，各组件之间通过明确的接口进行交互，确保系统的可扩展性和可维护性。

系统的核心转变方向：
- 从查询型API转向交互式智能Agent接口
- 从静态数据管道转向动态上下文增强数据服务
- 从服务消费者转向Agent工具链提供者

## 2. 系统组件

### 2.1 API网关层

**主要组件**:
- `api_gateway.py`: 提供统一的API访问入口
- `mcp_interpreter.py`: 解析MCP协议请求
- `query_orchestrator.py`: 协调查询执行

**功能**:
- 接收和处理Agent/用户请求
- 解析自然语言查询为结构化请求
- 协调多个服务的调用
- 格式化响应结果

**数据流**:
- Agent/用户请求 → API网关 → MCP解释器 → 查询编排器 → 数据服务

### 2.2 MCP协议层

**主要组件**:
- `nlu_parser.py`: 自然语言理解解析器
- `intent_recognizer.py`: 意图识别器
- `query_builder.py`: 结构化查询构建器
- `context_manager.py`: 上下文管理器

**功能**:
- 解析自然语言请求
- 识别用户意图
- 构建结构化查询
- 管理会话上下文

**协议结构**:
```json
{
  "query": "展示上证指数近三个月的走势",
  "intent": "price_trend",
  "context": {
    "visualization": "candlestick",
    "timezone": "Asia/Shanghai"
  },
  "session_id": "xyz123",
  "response_type": "structured"
}
```

### 2.3 数据服务层

#### 2.3.1 数据获取层

**主要组件**:
- `downloader.py`: 负责从外部数据源下载股票和指数数据
- `updater.py`: 负责更新已有的股票和指数数据
- `data_adapter.py`: 适配不同数据源的接口

**功能**:
- 下载股票日线数据
- 下载指数成分股数据
- 获取实时股票数据
- 增量更新历史数据

**数据流**:
- 从外部API获取数据 → 数据清洗和格式化 → 存储到数据库/缓存

#### 2.3.2 智能数据服务层

**主要组件**:
- `stock_data_service.py`: 股票数据服务
- `database_cache.py`: 数据库缓存接口
- `akshare_adapter.py`: AKShare适配器

**功能**:
- 智能数据获取策略
- 数据库作为持久化缓存
- 日期范围分段处理
- 统一AKShare API调用
- 提供数据源降级回退

**性能指标**:
- 响应时间: 50ms (≥95%命中率)
- 数据库查询效率: ≥95%优化率
- 数据延迟: <10分钟
- 服务可用性: 99.9%

**注意**: 在MVP阶段，我们简化了缓存架构，直接使用数据库作为持久化缓存，特别针对股票历史数据的不可变特性进行了优化。未来可能会为可变数据类型（如公司档案、指数等）添加更复杂的缓存机制。

#### 2.3.3 数据存储层

**主要组件**:
- `database.py`: 提供数据库操作接口
- `SQLite数据库`: 存储所有系统数据
- `cache_db.py`: 缓存数据库接口

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
- `cache_metadata`: 存储缓存元数据
- `session_context`: 存储会话上下文

### 2.4 业务逻辑层

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

### 2.5 分析和报告层

**主要组件**:
- `entry_window_performance_analysis.py`: 分析入场窗口绩效
- `trade_plan_performance_analysis.py`: 分析交易计划绩效
- `update_trade_plan_metrics.py`: 更新交易计划指标
- `trend_analyzer.py`: 趋势分析器
- `backtest_engine.py`: 回测引擎
- `comparison_tool.py`: 比较工具

**功能**:
- 绩效指标计算
- 图表生成
- 报告输出
- 趋势分析
- 策略回测
- 多资产/策略比较

### 2.6 调度和控制层

**主要组件**:
- `main.py`: 系统入口点
- `scheduler.py`: 任务调度
- `config.py`: 系统配置
- `logger.py`: 日志记录
- `concurrent_scheduler.py`: 并发调度器
- `fallback_manager.py`: 降级回退管理器

**功能**:
- 系统初始化
- 任务调度
- 配置管理
- 日志记录
- 并发请求管理
- 服务降级管理

## 3. 数据流

### 3.1 Agent请求处理流程

1. Agent/用户通过API网关发送自然语言请求
2. MCP解释器解析请求，识别意图和上下文
3. 查询编排器构建结构化查询
4. 数据服务层执行查询，从缓存或数据库获取数据
5. 结果格式化后返回给Agent/用户

### 3.2 数据获取与缓存流程

1. 系统检查请求的数据是否已缓存
2. 如果已缓存且新鲜度符合要求，直接从缓存返回
3. 如果未缓存或需要更新，通过`downloader.py`从外部数据源获取数据
4. 数据经过清洗和格式化
5. 数据存储到缓存和数据库
6. 更新数据新鲜度标记

### 3.3 信号生成流程

1. 系统通过`processor.py`和`indicators.py`处理历史数据
2. 基于处理结果生成交易信号
3. 交易信号存储到`trade_signals`表
4. 通过`signal_sender.py`将信号发送到外部系统（如企业微信）

### 3.4 交易计划管理流程

1. 系统通过`signal_to_plan.py`将交易信号转换为交易计划
2. 交易计划存储到`trade_plans`表
3. 系统跟踪和更新交易计划的状态和绩效

### 3.5 绩效分析流程

1. 系统通过`entry_window_performance_analysis.py`和`trade_plan_performance_analysis.py`分析交易绩效
2. 生成绩效报告和图表
3. 更新交易计划的绩效指标

### 3.6 智能数据获取流程

1. 用户请求股票历史数据（指定股票代码、开始日期和结束日期）
2. 系统生成日期范围内的所有交易日
3. 查询数据库，检查哪些日期的数据已存在
4. 对于缺失的日期：
   - 将连续的缺失日期分组，减少API调用
   - 从AKShare获取缺失的数据
   - 将获取的数据保存到数据库
5. 从数据库获取完整的请求日期范围数据
6. 返回数据给用户
7. AKShare适配器统一处理所有外部数据源调用，提供错误处理和重试机制

## 4. 技术架构

### 4.1 开发语言和框架

- **主要语言**: Python
- **数据处理**: Pandas
- **数据可视化**: Matplotlib
- **数据库**: SQLite
- **缓存系统**: Redis/内存缓存
- **API框架**: FastAPI/Flask

### 4.2 文件组织

- **src/**: 源代码目录
  - **api/**: API网关和接口
    - **routes/**: API路由
    - **database.py**: 数据库连接
    - **main.py**: 主应用
    - **models.py**: 数据模型
    - **schemas.py**: 数据模式
  - **mcp/**: MCP协议实现
    - **interpreter.py**: MCP解释器
    - **schemas.py**: MCP模式
  - **data/**: 数据服务
    - **akshare_adapter.py**: AKShare适配器
    - **data_cleaner.py**: 数据清洗
    - **data_validator.py**: 数据验证
  - **services/**: 服务层
    - **stock_data_service.py**: 股票数据服务
    - **database_cache.py**: 数据库缓存接口
    - **models.py**: 数据模型
  - **business/**: 业务服务
    - **data_import.py**: 数据导入服务
    - **query.py**: 数据查询服务
  - **scripts/**: 脚本
    - **init_db.py**: 初始化数据库
    - **import_sample_data.py**: 导入示例数据
  - **config.py**: 配置
  - **database.py**: 数据库操作
  - **downloader.py**: 数据下载
  - **logger.py**: 日志
  - **updater.py**: 数据更新
- **data/**: 数据存储目录
  - **sample/**: 示例数据
- **database/**: 数据库文件和脚本
- **logs/**: 日志文件
- **tests/**: 测试代码
  - **test_api.py**: API测试
  - **test_assets_api.py**: 资产API测试
  - **test_mcp_api.py**: MCP API测试
- **docs/**: 文档
  - **project_management/**: 项目管理文档
  - **00_document_standards.md**: 文档标准
  - **00_vsion_and_roadmap.md**: 愿景和路线图
  - **03_system_architecture.md**: 系统架构

### 4.3 部署架构

系统支持多种部署方式:

1. **单机部署**: 适用于个人用户和小型团队
   - 命令行模式: 通过`main.py`脚本运行特定任务
   - 定时任务: 通过操作系统的定时任务（如cron）调度运行
   - 本地服务: 作为本地API服务运行

2. **分布式部署**: 适用于大型团队和企业用户
   - API服务: 部署为独立的API服务
   - 缓存服务: 部署为独立的缓存服务
   - 数据服务: 部署为独立的数据服务
   - 业务服务: 部署为独立的业务服务

3. **云原生部署**: 适用于需要高可用性和可扩展性的场景
   - 容器化: 使用Docker容器化各组件
   - 编排: 使用Kubernetes进行容器编排
   - 自动扩展: 根据负载自动扩展服务实例

## 5. 接口设计

### 5.1 Agent接口

- **MCP协议接口**: 提供基于MCP协议的自然语言查询接口
  - 端点: `/api/v1/mcp/query`
  - 方法: POST
  - 请求格式: JSON (MCP协议格式)
  - 响应格式: JSON (结构化数据)

- **LangChain工具接口**: 提供与LangChain集成的工具接口
  - 端点: `/api/v1/tools/langchain`
  - 方法: POST
  - 请求格式: JSON (LangChain工具格式)
  - 响应格式: JSON (LangChain工具响应格式)

- **OpenAI Plugin接口**: 提供与OpenAI Plugin集成的接口
  - 端点: `/api/v1/plugins/openai`
  - 方法: POST
  - 请求格式: JSON (OpenAI Plugin格式)
  - 响应格式: JSON (OpenAI Plugin响应格式)

### 5.2 数据服务接口

- **资产API**: 提供资产数据查询接口
  - 端点: `/api/v1/assets`
  - 方法: GET
  - 参数: symbol, name, asset_type, exchange, skip, limit
  - 响应格式: JSON (资产列表)

- **价格API**: 提供价格数据查询接口
  - 端点: `/api/v1/prices`
  - 方法: GET
  - 参数: asset_id, symbol, start_date, end_date, period, skip, limit
  - 响应格式: JSON (价格列表)

- **数据查询接口**: 提供结构化数据查询接口
  - 端点: `/api/v1/data/query`
  - 方法: POST
  - 请求格式: JSON (查询参数)
  - 响应格式: JSON (查询结果)

- **数据更新接口**: 提供数据更新接口
  - 端点: `/api/v1/data/update`
  - 方法: POST
  - 请求格式: JSON (更新参数)
  - 响应格式: JSON (更新结果)

- **数据库缓存状态接口**: 提供数据库缓存状态查询接口
  - 端点: `/api/v1/database/cache/status`
  - 方法: GET
  - 参数: symbol, date_range, data_type
  - 响应格式: JSON (缓存状态)

### 5.3 业务服务接口

- **交易信号接口**: 提供交易信号查询和管理接口
  - 端点: `/api/v1/signals`
  - 方法: GET/POST/PUT/DELETE
  - 请求格式: JSON (信号参数)
  - 响应格式: JSON (信号数据)

- **交易计划接口**: 提供交易计划查询和管理接口
  - 端点: `/api/v1/plans`
  - 方法: GET/POST/PUT/DELETE
  - 请求格式: JSON (计划参数)
  - 响应格式: JSON (计划数据)

### 5.4 内部接口

- **数据库接口**: 通过`database.py`提供统一的数据访问接口
- **数据库缓存接口**: 通过`database_cache.py`提供统一的数据库缓存访问接口
- **AKShare适配器接口**: 通过`akshare_adapter.py`提供统一的AKShare API调用接口
- **股票数据服务接口**: 通过`stock_data_service.py`提供股票数据服务
- **配置接口**: 通过`config.py`提供系统配置
- **日志接口**: 通过`logger.py`提供日志记录功能
- **上下文接口**: 通过`context_manager.py`提供会话上下文管理
