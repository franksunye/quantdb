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
    notes TEXT,
    FOREIGN KEY (strategy_id) REFERENCES strategies(strategy_id),
    FOREIGN KEY (asset_id) REFERENCES assets(asset_id)
);

-- 创建 trade_plans 表
CREATE TABLE trade_plans (
    plan_id INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_date DATE NOT NULL,
    signal_id INTEGER NOT NULL,
    status TEXT NOT NULL,
    decision TEXT,
    notes TEXT,
    FOREIGN KEY (signal_id) REFERENCES trade_signals(signal_id)
);

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
