-- 基本Supabase架构，只创建表，不包含RLS策略

-- 创建assets表
CREATE TABLE IF NOT EXISTS assets (
    asset_id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    name VARCHAR(100),
    isin VARCHAR(12),
    asset_type VARCHAR(20),
    exchange VARCHAR(20),
    currency VARCHAR(3),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol)
);

-- 创建prices表
CREATE TABLE IF NOT EXISTS prices (
    price_id SERIAL PRIMARY KEY,
    asset_id INTEGER NOT NULL,
    date DATE NOT NULL,
    open NUMERIC(10, 2),
    high NUMERIC(10, 2),
    low NUMERIC(10, 2),
    close NUMERIC(10, 2),
    volume BIGINT,
    adjusted_close NUMERIC(10, 2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (asset_id) REFERENCES assets (asset_id),
    UNIQUE (asset_id, date)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_prices_asset_id ON prices (asset_id);
CREATE INDEX IF NOT EXISTS idx_prices_date ON prices (date);
CREATE INDEX IF NOT EXISTS idx_assets_symbol ON assets (symbol);
