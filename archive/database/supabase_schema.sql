-- QuantDB Supabase数据库架构
-- 版本: 1.1.0
-- 日期: 2025-05-18

-- 启用UUID扩展（如果尚未启用）
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. 资产表 (assets)
CREATE TABLE IF NOT EXISTS assets (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    asset_type VARCHAR(20) NOT NULL,
    exchange VARCHAR(20) NOT NULL,
    currency VARCHAR(3),
    isin VARCHAR(12),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_assets_symbol ON assets(symbol);
CREATE INDEX IF NOT EXISTS idx_assets_asset_type ON assets(asset_type);
CREATE INDEX IF NOT EXISTS idx_assets_exchange ON assets(exchange);

-- 2. 股票历史数据表 (stock_historical_data)
CREATE TABLE IF NOT EXISTS stock_historical_data (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    trade_date DATE NOT NULL,
    open DECIMAL(18, 4) NOT NULL,
    high DECIMAL(18, 4) NOT NULL,
    low DECIMAL(18, 4) NOT NULL,
    close DECIMAL(18, 4) NOT NULL,
    volume BIGINT NOT NULL,
    amount DECIMAL(18, 4),
    turnover DECIMAL(10, 4),
    pe_ratio DECIMAL(10, 4),
    pb_ratio DECIMAL(10, 4),
    ps_ratio DECIMAL(10, 4),
    pcf_ratio DECIMAL(10, 4),
    market_cap DECIMAL(18, 4),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT fk_stock_symbol FOREIGN KEY (symbol) REFERENCES assets(symbol),
    CONSTRAINT uk_stock_date UNIQUE (symbol, trade_date)
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_stock_hist_symbol ON stock_historical_data(symbol);
CREATE INDEX IF NOT EXISTS idx_stock_hist_date ON stock_historical_data(trade_date);
CREATE INDEX IF NOT EXISTS idx_stock_hist_symbol_date ON stock_historical_data(symbol, trade_date);

-- 3. 数据源表 (data_sources)
CREATE TABLE IF NOT EXISTS data_sources (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    api_base_url VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 初始数据
INSERT INTO data_sources (name, description, api_base_url, is_active)
VALUES ('akshare', 'AKShare金融数据接口', NULL, TRUE)
ON CONFLICT (name) DO NOTHING;

-- 4. 数据获取记录表 (data_fetch_records)
CREATE TABLE IF NOT EXISTS data_fetch_records (
    id SERIAL PRIMARY KEY,
    data_source_id INTEGER NOT NULL,
    asset_type VARCHAR(20) NOT NULL,
    symbol VARCHAR(20),
    start_date DATE,
    end_date DATE,
    status VARCHAR(20) NOT NULL,
    record_count INTEGER,
    error_message TEXT,
    execution_time DECIMAL(10, 2),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT fk_data_source FOREIGN KEY (data_source_id) REFERENCES data_sources(id)
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_fetch_records_source ON data_fetch_records(data_source_id);
CREATE INDEX IF NOT EXISTS idx_fetch_records_symbol ON data_fetch_records(symbol);
CREATE INDEX IF NOT EXISTS idx_fetch_records_dates ON data_fetch_records(start_date, end_date);

-- 5. 缓存元数据表 (cache_metadata)
CREATE TABLE IF NOT EXISTS cache_metadata (
    id SERIAL PRIMARY KEY,
    cache_key VARCHAR(255) NOT NULL UNIQUE,
    data_type VARCHAR(50) NOT NULL,
    symbol VARCHAR(20),
    start_date DATE,
    end_date DATE,
    record_count INTEGER,
    last_accessed TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_cache_metadata_key ON cache_metadata(cache_key);
CREATE INDEX IF NOT EXISTS idx_cache_metadata_type ON cache_metadata(data_type);
CREATE INDEX IF NOT EXISTS idx_cache_metadata_symbol ON cache_metadata(symbol);
CREATE INDEX IF NOT EXISTS idx_cache_metadata_dates ON cache_metadata(start_date, end_date);

-- 6. 用户资料表 (user_profiles)
CREATE TABLE IF NOT EXISTS user_profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id),
    display_name VARCHAR(100),
    bio TEXT,
    preferences JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_user_profiles_display_name ON user_profiles(display_name);

-- 7. 用户资产表 (user_assets)
CREATE TABLE IF NOT EXISTS user_assets (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    is_favorite BOOLEAN DEFAULT FALSE,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT fk_user_asset_user FOREIGN KEY (user_id) REFERENCES user_profiles(id),
    CONSTRAINT fk_user_asset_symbol FOREIGN KEY (symbol) REFERENCES assets(symbol),
    CONSTRAINT uk_user_asset UNIQUE (user_id, symbol)
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_user_assets_user ON user_assets(user_id);
CREATE INDEX IF NOT EXISTS idx_user_assets_symbol ON user_assets(symbol);

-- 行级安全策略 (RLS)

-- 1. 资产表 (assets)
ALTER TABLE assets ENABLE ROW LEVEL SECURITY;

-- 允许所有用户读取
CREATE POLICY assets_select_policy ON assets
    FOR SELECT USING (true);

-- 只允许管理员修改
CREATE POLICY assets_insert_policy ON assets
    FOR INSERT WITH CHECK (auth.role() = 'service_role');
CREATE POLICY assets_update_policy ON assets
    FOR UPDATE USING (auth.role() = 'service_role');
CREATE POLICY assets_delete_policy ON assets
    FOR DELETE USING (auth.role() = 'service_role');

-- 2. 股票历史数据表 (stock_historical_data)
ALTER TABLE stock_historical_data ENABLE ROW LEVEL SECURITY;

-- 允许所有用户读取
CREATE POLICY stock_data_select_policy ON stock_historical_data
    FOR SELECT USING (true);

-- 只允许管理员修改
CREATE POLICY stock_data_insert_policy ON stock_historical_data
    FOR INSERT WITH CHECK (auth.role() = 'service_role');
CREATE POLICY stock_data_update_policy ON stock_historical_data
    FOR UPDATE USING (auth.role() = 'service_role');
CREATE POLICY stock_data_delete_policy ON stock_historical_data
    FOR DELETE USING (auth.role() = 'service_role');

-- 3. 数据源表 (data_sources)
ALTER TABLE data_sources ENABLE ROW LEVEL SECURITY;

-- 允许所有用户读取
CREATE POLICY data_sources_select_policy ON data_sources
    FOR SELECT USING (true);

-- 只允许管理员修改
CREATE POLICY data_sources_insert_policy ON data_sources
    FOR INSERT WITH CHECK (auth.role() = 'service_role');
CREATE POLICY data_sources_update_policy ON data_sources
    FOR UPDATE USING (auth.role() = 'service_role');
CREATE POLICY data_sources_delete_policy ON data_sources
    FOR DELETE USING (auth.role() = 'service_role');

-- 4. 数据获取记录表 (data_fetch_records)
ALTER TABLE data_fetch_records ENABLE ROW LEVEL SECURITY;

-- 允许所有用户读取
CREATE POLICY data_fetch_records_select_policy ON data_fetch_records
    FOR SELECT USING (true);

-- 只允许管理员修改
CREATE POLICY data_fetch_records_insert_policy ON data_fetch_records
    FOR INSERT WITH CHECK (auth.role() = 'service_role');
CREATE POLICY data_fetch_records_update_policy ON data_fetch_records
    FOR UPDATE USING (auth.role() = 'service_role');
CREATE POLICY data_fetch_records_delete_policy ON data_fetch_records
    FOR DELETE USING (auth.role() = 'service_role');

-- 5. 缓存元数据表 (cache_metadata)
ALTER TABLE cache_metadata ENABLE ROW LEVEL SECURITY;

-- 允许所有用户读取
CREATE POLICY cache_metadata_select_policy ON cache_metadata
    FOR SELECT USING (true);

-- 只允许管理员修改
CREATE POLICY cache_metadata_insert_policy ON cache_metadata
    FOR INSERT WITH CHECK (auth.role() = 'service_role');
CREATE POLICY cache_metadata_update_policy ON cache_metadata
    FOR UPDATE USING (auth.role() = 'service_role');
CREATE POLICY cache_metadata_delete_policy ON cache_metadata
    FOR DELETE USING (auth.role() = 'service_role');

-- 6. 用户资料表 (user_profiles)
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;

-- 用户只能访问自己的资料
CREATE POLICY user_profiles_select_policy ON user_profiles
    FOR SELECT USING (auth.uid() = id);
CREATE POLICY user_profiles_insert_policy ON user_profiles
    FOR INSERT WITH CHECK (auth.uid() = id);
CREATE POLICY user_profiles_update_policy ON user_profiles
    FOR UPDATE USING (auth.uid() = id);
CREATE POLICY user_profiles_delete_policy ON user_profiles
    FOR DELETE USING (auth.uid() = id);

-- 7. 用户资产表 (user_assets)
ALTER TABLE user_assets ENABLE ROW LEVEL SECURITY;

-- 用户只能访问自己的数据
CREATE POLICY user_assets_select_policy ON user_assets
    FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY user_assets_insert_policy ON user_assets
    FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY user_assets_update_policy ON user_assets
    FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY user_assets_delete_policy ON user_assets
    FOR DELETE USING (auth.uid() = user_id);

-- 创建更新时间触发器函数
CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 为所有表添加更新时间触发器
CREATE TRIGGER update_assets_modtime
    BEFORE UPDATE ON assets
    FOR EACH ROW
    EXECUTE FUNCTION update_modified_column();

CREATE TRIGGER update_stock_historical_data_modtime
    BEFORE UPDATE ON stock_historical_data
    FOR EACH ROW
    EXECUTE FUNCTION update_modified_column();

CREATE TRIGGER update_data_sources_modtime
    BEFORE UPDATE ON data_sources
    FOR EACH ROW
    EXECUTE FUNCTION update_modified_column();

CREATE TRIGGER update_cache_metadata_modtime
    BEFORE UPDATE ON cache_metadata
    FOR EACH ROW
    EXECUTE FUNCTION update_modified_column();

CREATE TRIGGER update_user_profiles_modtime
    BEFORE UPDATE ON user_profiles
    FOR EACH ROW
    EXECUTE FUNCTION update_modified_column();

CREATE TRIGGER update_user_assets_modtime
    BEFORE UPDATE ON user_assets
    FOR EACH ROW
    EXECUTE FUNCTION update_modified_column();

-- 授予必要的权限
GRANT SELECT ON assets TO anon, authenticated;
GRANT SELECT ON stock_historical_data TO anon, authenticated;
GRANT SELECT ON data_sources TO anon, authenticated;
GRANT SELECT ON data_fetch_records TO anon, authenticated;
GRANT SELECT ON cache_metadata TO anon, authenticated;

-- 为服务角色授予所有权限
GRANT ALL ON assets TO service_role;
GRANT ALL ON stock_historical_data TO service_role;
GRANT ALL ON data_sources TO service_role;
GRANT ALL ON data_fetch_records TO service_role;
GRANT ALL ON cache_metadata TO service_role;
GRANT ALL ON user_profiles TO service_role;
GRANT ALL ON user_assets TO service_role;

-- 授予序列使用权限
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO service_role;
