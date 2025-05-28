-- QuantDB Supabase数据库初始化脚本
-- 为MVP部署设计的精简版表结构
-- 版本: 1.0.0
-- 日期: 2025-05-19

-- 启用UUID扩展（Supabase推荐使用UUID作为主键）
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 创建 assets 表
CREATE TABLE assets (
    asset_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol TEXT NOT NULL,
    name TEXT NOT NULL,
    isin TEXT NOT NULL UNIQUE,  -- 添加唯一标识码
    asset_type TEXT NOT NULL,
    exchange TEXT NOT NULL,
    currency TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 创建 daily_stock_data 表（MVP核心表）
CREATE TABLE daily_stock_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    asset_id UUID NOT NULL,
    trade_date DATE NOT NULL,
    open NUMERIC(10, 2),
    high NUMERIC(10, 2),
    low NUMERIC(10, 2),
    close NUMERIC(10, 2),
    volume BIGINT,
    turnover NUMERIC(20, 2),
    amplitude NUMERIC(10, 4),        -- 振幅
    pct_change NUMERIC(10, 4),      -- 涨跌幅
    change NUMERIC(10, 4),          -- 涨跌额
    turnover_rate NUMERIC(10, 4),   -- 换手率
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    FOREIGN KEY (asset_id) REFERENCES assets (asset_id),
    UNIQUE (asset_id, trade_date)  -- 确保每天的数据唯一
);

-- 创建 strategies 表
CREATE TABLE strategies (
    strategy_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    description TEXT,
    parameters JSONB,  -- 使用JSONB存储参数，更灵活
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 创建 trade_signals 表
CREATE TABLE trade_signals (
    signal_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    strategy_id UUID NOT NULL,
    asset_id UUID NOT NULL,
    signal_date DATE NOT NULL,
    signal_type TEXT NOT NULL,
    signal_strength NUMERIC(10, 4),
    price_at_signal NUMERIC(10, 2),  -- 发出信号时的价格（一般为收盘价）
    suggested_quantity INTEGER,  -- 建议的交易数量
    optimal_result JSONB,  -- 与信号对应的最优结果（如回报率、夏普比率等）
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    FOREIGN KEY (strategy_id) REFERENCES strategies(strategy_id),
    FOREIGN KEY (asset_id) REFERENCES assets(asset_id)
);

-- 创建 trade_plans 表
CREATE TABLE trade_plans (
    plan_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    plan_date DATE NOT NULL,           -- 计划生成日期
    signal_id UUID NOT NULL,           -- 关联的信号 ID
    asset_id UUID NOT NULL,            -- 冗余存储的股票 ID
    asset_name TEXT NOT NULL,          -- 冗余存储的股票名称
    symbol TEXT NOT NULL,              -- 冗余存储的股票代码（符号）
    status TEXT NOT NULL,              -- 计划状态
    entry_price NUMERIC(10, 2),        -- 入场价格
    entry_date DATE,                   -- 入场日期
    order_entry INTEGER,               -- 入场订单量
    slip_entry NUMERIC(10, 4),         -- 入场滑点
    comm_entry NUMERIC(10, 4),         -- 入场佣金
    exit_price NUMERIC(10, 2),         -- 出场价格
    exit_date DATE,                    -- 出场日期
    order_exit INTEGER,                -- 出场订单量
    slip_exit NUMERIC(10, 4),          -- 出场滑点
    comm_exit NUMERIC(10, 4),          -- 出场佣金
    fee NUMERIC(10, 4),                -- 费用
    pnl NUMERIC(10, 4),                -- 盈亏
    net NUMERIC(10, 4),                -- 净收益
    entry_pct_change NUMERIC(10, 4),   -- 入场时涨跌幅
    exit_pct_change NUMERIC(10, 4),    -- 出场时涨跌幅
    trade_p NUMERIC(10, 4),            -- 交易表现
    level TEXT,                        -- 计划级别
    upch INTEGER,                      -- 上涨股票数量
    downch INTEGER,                    -- 下跌股票数量
    high NUMERIC(10, 2),               -- 计划内的最高价格
    low NUMERIC(10, 2),                -- 计划内的最低价格
    notes TEXT,                        -- 备注
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    FOREIGN KEY (signal_id) REFERENCES trade_signals(signal_id),
    FOREIGN KEY (asset_id) REFERENCES assets(asset_id)
);

-- 创建 logs 表
CREATE TABLE logs (
    log_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    message TEXT NOT NULL,
    level TEXT NOT NULL,
    strategy_id UUID,  -- 可以为NULL，因为不是所有日志都与策略相关
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    FOREIGN KEY (strategy_id) REFERENCES strategies(strategy_id)
);

-- 创建索引以提高查询性能
CREATE INDEX idx_daily_stock_data_asset_id ON daily_stock_data(asset_id);
CREATE INDEX idx_daily_stock_data_trade_date ON daily_stock_data(trade_date);
CREATE INDEX idx_trade_signals_asset_id ON trade_signals(asset_id);
CREATE INDEX idx_trade_signals_signal_date ON trade_signals(signal_date);
CREATE INDEX idx_trade_plans_asset_id ON trade_plans(asset_id);
CREATE INDEX idx_trade_plans_plan_date ON trade_plans(plan_date);
CREATE INDEX idx_logs_timestamp ON logs(timestamp);

-- 创建更新时间戳触发器函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 为所有表添加更新时间戳触发器
CREATE TRIGGER update_assets_updated_at
BEFORE UPDATE ON assets
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_daily_stock_data_updated_at
BEFORE UPDATE ON daily_stock_data
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_strategies_updated_at
BEFORE UPDATE ON strategies
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_trade_signals_updated_at
BEFORE UPDATE ON trade_signals
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_trade_plans_updated_at
BEFORE UPDATE ON trade_plans
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 添加行级安全策略（RLS）
ALTER TABLE assets ENABLE ROW LEVEL SECURITY;
ALTER TABLE daily_stock_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE strategies ENABLE ROW LEVEL SECURITY;
ALTER TABLE trade_signals ENABLE ROW LEVEL SECURITY;
ALTER TABLE trade_plans ENABLE ROW LEVEL SECURITY;
ALTER TABLE logs ENABLE ROW LEVEL SECURITY;

-- 创建基本的RLS策略（MVP阶段简化为所有已认证用户可访问）
CREATE POLICY "允许所有已认证用户查看资产" ON assets
    FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "允许所有已认证用户查看股票数据" ON daily_stock_data
    FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "允许所有已认证用户查看策略" ON strategies
    FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "允许所有已认证用户查看交易信号" ON trade_signals
    FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "允许所有已认证用户查看交易计划" ON trade_plans
    FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "允许所有已认证用户查看日志" ON logs
    FOR SELECT USING (auth.role() = 'authenticated');

-- 注释
COMMENT ON TABLE assets IS 'QuantDB资产表，存储股票、指数等资产信息';
COMMENT ON TABLE daily_stock_data IS 'QuantDB股票日线数据表，存储股票的每日交易数据';
COMMENT ON TABLE strategies IS 'QuantDB策略表，存储交易策略信息';
COMMENT ON TABLE trade_signals IS 'QuantDB交易信号表，存储策略生成的交易信号';
COMMENT ON TABLE trade_plans IS 'QuantDB交易计划表，存储基于信号生成的交易计划';
COMMENT ON TABLE logs IS 'QuantDB日志表，存储系统日志信息';
