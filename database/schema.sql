-- 创建 assets 表
CREATE TABLE assets (
    asset_id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    name TEXT NOT NULL,
    isin TEXT NOT NULL UNIQUE,  -- 添加唯一标识码
    asset_type TEXT NOT NULL,
    exchange TEXT NOT NULL,
    currency TEXT NOT NULL
);

-- 创建 prices 表
CREATE TABLE prices (
    price_id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id INTEGER NOT NULL,
    date DATE NOT NULL,
    open REAL,
    high REAL,
    low REAL,
    close REAL,
    volume REAL,
    adjusted_close REAL,
    FOREIGN KEY (asset_id) REFERENCES assets(asset_id)
);

-- 创建 index_constituents 表
CREATE TABLE index_constituents (
    constituent_id INTEGER PRIMARY KEY AUTOINCREMENT,
    index_name TEXT NOT NULL,         -- 指数名称，如“沪深300”或“科创50”
    asset_id INTEGER NOT NULL,        -- 关联到assets表中的asset_id
    inclusion_date DATE NOT NULL,     -- 股票纳入指数的日期
    exclusion_date DATE,              -- 股票移出指数的日期（如果已移出）
    FOREIGN KEY (asset_id) REFERENCES assets(asset_id)
);

-- 创建 indicators 表
CREATE TABLE indicators (
    indicator_id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id INTEGER NOT NULL,
    date DATE NOT NULL,
    indicator_type TEXT NOT NULL,
    value REAL,
    FOREIGN KEY (asset_id) REFERENCES assets(asset_id)
);

-- 创建 trade_signals 表
CREATE TABLE trade_signals (
    signal_id INTEGER PRIMARY KEY AUTOINCREMENT,
    strategy_id INTEGER NOT NULL,
    asset_id INTEGER NOT NULL,
    signal_date DATE NOT NULL,
    signal_type TEXT NOT NULL,
    signal_strength REAL,
    price_at_signal REAL,  -- 新增字段：发出信号时的价格（一般为收盘价）
    suggested_quantity INTEGER,  -- 新增字段：建议的交易数量
    optimal_result TEXT,  -- 新增字段：与信号对应的最优结果（如回报率、夏普比率等）
    notes TEXT,
    FOREIGN KEY (strategy_id) REFERENCES strategies(strategy_id),
    FOREIGN KEY (asset_id) REFERENCES assets(asset_id)
);

-- 创建交易计划表
CREATE TABLE trade_plans (
    plan_id INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_date DATE NOT NULL,           -- 计划生成日期
    signal_id INTEGER NOT NULL,        -- 关联的信号 ID
    asset_id INTEGER NOT NULL,         -- 冗余存储的股票 ID
    asset_name TEXT NOT NULL,          -- 冗余存储的股票名称
    symbol TEXT NOT NULL,              -- 冗余存储的股票代码（符号）
    status TEXT NOT NULL,              -- 计划状态
    entry_price REAL,                  -- 入场价格
    entry_date DATE,                   -- 入场日期
    order_entry INTEGER,               -- 入场订单量
    slip_entry REAL,                   -- 入场滑点
    comm_entry REAL,                   -- 入场佣金
    exit_price REAL,                   -- 出场价格
    exit_date DATE,                    -- 出场日期
    order_exit INTEGER,                -- 出场订单量
    slip_exit REAL,                    -- 出场滑点
    comm_exit REAL,                    -- 出场佣金
    fee REAL,                          -- 费用
    pnl REAL,                          -- 盈亏
    net REAL,                          -- 净收益
    entry_pct_change REAL,             -- 入场时涨跌幅
    exit_pct_change REAL,              -- 出场时涨跌幅
    trade_p REAL,                      -- 交易表现
    level TEXT,                        -- 计划级别
    upch INTEGER,                      -- 上涨股票数量
    downch INTEGER,                    -- 下跌股票数量
    high REAL,                         -- 计划内的最高价格
    low REAL,                          -- 计划内的最低价格
    notes TEXT,                        -- 备注
    FOREIGN KEY (signal_id) REFERENCES trade_signals(signal_id),
    FOREIGN KEY (asset_id) REFERENCES assets(asset_id)
);

-- PENDING：初始状态，表示计划已经创建但还未执行。
-- ACTIVE：表示计划已被激活或执行，处于进行中状态。
-- COMPLETED：计划已成功完成，通常表示所有预定操作已经执行。
-- CANCELLED：计划被取消，可能是由于市场条件变化或其他原因。
-- FAILED：计划执行失败，可能是由于技术问题、市场波动等。

-- 创建 trades 表
CREATE TABLE trades (
    trade_id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id INTEGER NOT NULL,
    trade_date DATE NOT NULL,
    quantity INTEGER NOT NULL,
    price REAL NOT NULL,
    trade_type TEXT NOT NULL,
    strategy_id INTEGER NOT NULL,
    FOREIGN KEY (asset_id) REFERENCES assets(asset_id),
    FOREIGN KEY (strategy_id) REFERENCES strategies(strategy_id)
);

-- 创建 strategies 表
CREATE TABLE strategies (
    strategy_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    parameters TEXT
);

-- 创建 orders 表
CREATE TABLE orders (
    order_id INTEGER PRIMARY KEY AUTOINCREMENT,
    trade_id INTEGER NOT NULL,
    order_date DATE NOT NULL,
    status TEXT NOT NULL,
    order_type TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    price REAL NOT NULL,
    FOREIGN KEY (trade_id) REFERENCES trades(trade_id)
);

-- 创建 portfolios 表
CREATE TABLE portfolios (
    portfolio_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    creation_date DATE NOT NULL,
    strategy_id INTEGER NOT NULL,
    FOREIGN KEY (strategy_id) REFERENCES strategies(strategy_id)
);

-- 创建 portfolio_holdings 表
CREATE TABLE portfolio_holdings (
    holding_id INTEGER PRIMARY KEY AUTOINCREMENT,
    portfolio_id INTEGER NOT NULL,
    asset_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    average_price REAL NOT NULL,
    last_update DATE NOT NULL,
    FOREIGN KEY (portfolio_id) REFERENCES portfolios(portfolio_id),
    FOREIGN KEY (asset_id) REFERENCES assets(asset_id)
);

-- 创建 logs 表
CREATE TABLE logs (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL,
    message TEXT NOT NULL,
    level TEXT NOT NULL,
    strategy_id INTEGER NOT NULL,
    FOREIGN KEY (strategy_id) REFERENCES strategies(strategy_id)
);

-- 创建 backtests 表
CREATE TABLE backtests (
    backtest_id INTEGER PRIMARY KEY AUTOINCREMENT,
    strategy_id INTEGER NOT NULL,
    asset_id INTEGER NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    parameters TEXT,
    performance REAL,
    created_at DATETIME NOT NULL,
    FOREIGN KEY (strategy_id) REFERENCES strategies(strategy_id),
    FOREIGN KEY (asset_id) REFERENCES assets(asset_id)
);

-- 创建 optimization_results 表
CREATE TABLE optimization_results (
    optimization_id INTEGER PRIMARY KEY AUTOINCREMENT,
    backtest_id INTEGER NOT NULL,
    asset_id INTEGER NOT NULL,
    indicator_type TEXT NOT NULL,
    optimal_value REAL,
    performance REAL,
    created_at DATETIME NOT NULL,
    FOREIGN KEY (backtest_id) REFERENCES backtests(backtest_id),
    FOREIGN KEY (asset_id) REFERENCES assets(asset_id)
);

-- 创建股票日数据表
CREATE TABLE IF NOT EXISTS daily_stock_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id INTEGER,
    trade_date DATE,
    open REAL,
    high REAL,
    low REAL,
    close REAL,
    volume INTEGER,
    turnover REAL,
    amplitude REAL,        -- 振幅
    pct_change REAL,      -- 涨跌幅
    change REAL,          -- 涨跌额
    turnover_rate REAL,   -- 换手率
    FOREIGN KEY (asset_id) REFERENCES assets (asset_id),
    UNIQUE (asset_id, trade_date)  -- 确保每天的数据唯一
);

CREATE TABLE intraday_stock_data (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id            INTEGER,
    capture_time        DATETIME,   -- 数据抓取的时间戳
    trade_date          DATE,       -- 对应的交易日期
    latest_price        REAL,       -- 最新价
    pct_change          REAL,       -- 涨跌幅百分比
    change              REAL,       -- 涨跌额
    volume              INTEGER,    -- 成交量
    turnover            REAL,       -- 成交额
    amplitude           REAL,       -- 振幅
    high                REAL,       -- 当天到当前时刻的最高价
    low                 REAL,       -- 当天到当前时刻的最低价
    open                REAL,       -- 当日开盘价
    prev_close          REAL,       -- 昨日收盘价
    volume_ratio        REAL,       -- 量比
    turnover_rate       REAL,       -- 换手率
    pe_ratio_dynamic    REAL,       -- 市盈率-动态
    pb_ratio            REAL,       -- 市净率
    total_market_cap    REAL,       -- 总市值
    circulating_market_cap REAL,    -- 流通市值
    speed_of_increase   REAL,       -- 涨速
    five_min_pct_change REAL,       -- 5分钟涨跌
    sixty_day_pct_change REAL,      -- 60日涨跌幅
    ytd_pct_change      REAL,       -- 年初至今涨跌幅
    is_final            BOOLEAN,    -- 是否为闭市后的最终数据
    FOREIGN KEY (asset_id) 
        REFERENCES assets(asset_id),
    UNIQUE (asset_id, capture_time)  -- 确保同一时刻的同一股票数据唯一
);
