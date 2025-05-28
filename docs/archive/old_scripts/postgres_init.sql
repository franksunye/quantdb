-- PostgreSQL 数据库初始化脚本
-- 此脚本用于创建 QuantDB 所需的表和索引

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

-- 创建获取资产价格的函数
CREATE OR REPLACE FUNCTION get_asset_prices(
    asset_symbol VARCHAR,
    start_date DATE,
    end_date DATE
)
RETURNS TABLE (
    symbol VARCHAR,
    date DATE,
    open NUMERIC,
    high NUMERIC,
    low NUMERIC,
    close NUMERIC,
    volume BIGINT,
    adjusted_close NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        a.symbol,
        p.date,
        p.open,
        p.high,
        p.low,
        p.close,
        p.volume,
        p.adjusted_close
    FROM
        assets a
    JOIN
        prices p ON a.id = p.asset_id
    WHERE
        a.symbol = asset_symbol
        AND p.date BETWEEN start_date AND end_date
    ORDER BY
        p.date;
END;
$$ LANGUAGE plpgsql;
