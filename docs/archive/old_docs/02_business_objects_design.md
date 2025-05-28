# 业务对象设计

## 1. 核心业务对象

### 1.1 资产 (Asset)
资产是系统中最基础的业务对象，代表可交易的金融工具。

**属性**:
- `asset_id`: 资产唯一标识符
- `symbol`: 交易代码
- `name`: 资产名称
- `isin`: 国际证券识别码
- `asset_type`: 资产类型 (如股票、指数、ETF等)
- `exchange`: 交易所
- `currency`: 交易货币

**关系**:
- 一个资产可以有多个价格记录
- 一个资产可以属于多个指数
- 一个资产可以有多个交易信号
- 一个资产可以有多个交易计划

### 1.2 价格 (Price)
价格对象存储资产的历史价格数据。

**属性**:
- `price_id`: 价格记录唯一标识符
- `asset_id`: 关联的资产ID
- `date`: 日期
- `open`: 开盘价
- `high`: 最高价
- `low`: 最低价
- `close`: 收盘价
- `volume`: 成交量
- `adjusted_close`: 调整后收盘价

**关系**:
- 每个价格记录属于一个资产

### 1.3 指数成分股 (IndexConstituent)
指数成分股对象记录资产与指数的关系。

**属性**:
- `constituent_id`: 成分股记录唯一标识符
- `index_name`: 指数名称
- `asset_id`: 关联的资产ID
- `inclusion_date`: 纳入日期
- `exclusion_date`: 移出日期

**关系**:
- 每个成分股记录关联一个资产

### 1.4 指标 (Indicator)
指标对象存储资产的技术指标数据。

**属性**:
- `indicator_id`: 指标记录唯一标识符
- `asset_id`: 关联的资产ID
- `date`: 日期
- `indicator_type`: 指标类型
- `value`: 指标值

**关系**:
- 每个指标记录关联一个资产

### 1.5 交易信号 (TradeSignal)
交易信号对象代表策略生成的买入或卖出信号。

**属性**:
- `signal_id`: 信号唯一标识符
- `strategy_id`: 关联的策略ID
- `asset_id`: 关联的资产ID
- `signal_date`: 信号日期
- `signal_type`: 信号类型 (BUY/SELL)
- `signal_strength`: 信号强度
- `price_at_signal`: 信号价格
- `suggested_quantity`: 建议交易数量
- `optimal_result`: 最优结果
- `notes`: 备注

**关系**:
- 每个信号关联一个资产
- 每个信号关联一个策略
- 一个信号可以生成一个交易计划

### 1.6 交易计划 (TradePlan)
交易计划对象代表基于信号生成的交易执行计划。

**属性**:
- `plan_id`: 计划唯一标识符
- `plan_date`: 计划生成日期
- `signal_id`: 关联的信号ID
- `asset_id`: 关联的资产ID
- `asset_name`: 资产名称
- `symbol`: 资产代码
- `status`: 计划状态
- `entry_price`: 入场价格
- `entry_date`: 入场日期
- `order_entry`: 入场订单量
- `slip_entry`: 入场滑点
- `comm_entry`: 入场佣金
- `exit_price`: 出场价格
- `exit_date`: 出场日期
- `order_exit`: 出场订单量
- `slip_exit`: 出场滑点
- `comm_exit`: 出场佣金
- `fee`: 费用
- `pnl`: 盈亏
- `net`: 净收益
- `entry_pct_change`: 入场涨跌幅
- `exit_pct_change`: 出场涨跌幅
- `trade_p`: 交易表现
- `level`: 计划级别
- `upch`: 上涨股票数量
- `downch`: 下跌股票数量
- `high`: 最高价
- `low`: 最低价
- `notes`: 备注

**关系**:
- 每个计划关联一个信号
- 每个计划关联一个资产

### 1.7 交易 (Trade)
交易对象代表实际执行的交易。

**属性**:
- `trade_id`: 交易唯一标识符
- `asset_id`: 关联的资产ID
- `trade_date`: 交易日期
- `quantity`: 交易数量
- `price`: 交易价格
- `trade_type`: 交易类型
- `strategy_id`: 关联的策略ID

**关系**:
- 每个交易关联一个资产
- 每个交易关联一个策略
- 一个交易可以有多个订单

### 1.8 策略 (Strategy)
策略对象代表交易策略。

**属性**:
- `strategy_id`: 策略唯一标识符
- `name`: 策略名称
- `description`: 策略描述
- `parameters`: 策略参数

**关系**:
- 一个策略可以生成多个信号
- 一个策略可以关联多个交易
- 一个策略可以关联多个投资组合

## 2. 辅助业务对象

### 2.1 订单 (Order)
订单对象代表交易的执行指令。

**属性**:
- `order_id`: 订单唯一标识符
- `trade_id`: 关联的交易ID
- `order_date`: 订单日期
- `status`: 订单状态
- `order_type`: 订单类型
- `quantity`: 订单数量
- `price`: 订单价格

**关系**:
- 每个订单关联一个交易

### 2.2 投资组合 (Portfolio)
投资组合对象代表资产的集合。

**属性**:
- `portfolio_id`: 投资组合唯一标识符
- `name`: 投资组合名称
- `description`: 投资组合描述
- `creation_date`: 创建日期
- `strategy_id`: 关联的策略ID

**关系**:
- 每个投资组合关联一个策略
- 一个投资组合可以有多个持仓

### 2.3 持仓 (PortfolioHolding)
持仓对象代表投资组合中的资产持有情况。

**属性**:
- `holding_id`: 持仓唯一标识符
- `portfolio_id`: 关联的投资组合ID
- `asset_id`: 关联的资产ID
- `quantity`: 持有数量
- `average_price`: 平均价格
- `last_update`: 最后更新日期

**关系**:
- 每个持仓关联一个投资组合
- 每个持仓关联一个资产
