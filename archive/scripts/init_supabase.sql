-- Supabase PostgreSQL 数据库初始化脚本

-- 创建 assets 表
CREATE TABLE IF NOT EXISTS assets (
    id SERIAL PRIMARY KEY,
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

-- 创建 prices 表
CREATE TABLE IF NOT EXISTS prices (
    id SERIAL PRIMARY KEY,
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
    FOREIGN KEY (asset_id) REFERENCES assets (id),
    UNIQUE (asset_id, date)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_prices_asset_id ON prices (asset_id);
CREATE INDEX IF NOT EXISTS idx_prices_date ON prices (date);
CREATE INDEX IF NOT EXISTS idx_assets_symbol ON assets (symbol);

-- 创建更新 updated_at 的触发器函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 为 assets 表创建触发器
DROP TRIGGER IF EXISTS update_assets_updated_at ON assets;
CREATE TRIGGER update_assets_updated_at
BEFORE UPDATE ON assets
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- 为 prices 表创建触发器
DROP TRIGGER IF EXISTS update_prices_updated_at ON prices;
CREATE TRIGGER update_prices_updated_at
BEFORE UPDATE ON prices
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- 插入测试数据
INSERT INTO assets (symbol, name, asset_type, exchange, currency)
VALUES ('AAPL', 'Apple Inc.', 'STOCK', 'NASDAQ', 'USD')
ON CONFLICT (symbol) DO NOTHING;

INSERT INTO assets (symbol, name, asset_type, exchange, currency)
VALUES ('600000', '浦发银行', 'STOCK', '上海证券交易所', 'CNY')
ON CONFLICT (symbol) DO NOTHING;

-- 查询表信息
\echo '数据库表信息：'
\dt

-- 查询 assets 表结构
\echo 'assets 表结构：'
\d assets

-- 查询 prices 表结构
\echo 'prices 表结构：'
\d prices

-- 查询 assets 表数据
\echo 'assets 表数据：'
SELECT * FROM assets;
