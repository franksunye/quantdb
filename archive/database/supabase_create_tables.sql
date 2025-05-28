-- 创建 assets 表
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

-- 创建 prices 表
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

-- 启用行级安全
ALTER TABLE assets ENABLE ROW LEVEL SECURITY;
ALTER TABLE prices ENABLE ROW LEVEL SECURITY;

-- 创建策略
CREATE POLICY "允许所有用户查看资产" ON assets
    FOR SELECT USING (true);

CREATE POLICY "允许所有用户查看价格" ON prices
    FOR SELECT USING (true);

CREATE POLICY "只允许管理员插入资产" ON assets
    FOR INSERT WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY "只允许管理员更新资产" ON assets
    FOR UPDATE USING (auth.role() = 'authenticated');

CREATE POLICY "只允许管理员删除资产" ON assets
    FOR DELETE USING (auth.role() = 'authenticated');

CREATE POLICY "只允许管理员插入价格" ON prices
    FOR INSERT WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY "只允许管理员更新价格" ON prices
    FOR UPDATE USING (auth.role() = 'authenticated');

CREATE POLICY "只允许管理员删除价格" ON prices
    FOR DELETE USING (auth.role() = 'authenticated');
