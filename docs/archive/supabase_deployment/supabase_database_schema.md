# Supabase数据库架构设计

## 文档信息
**文档类型**: 技术设计  
**文档编号**: quantdb-TECH-003-DESIGN-001  
**版本**: 1.0.0  
**创建日期**: 2025-05-18  
**状态**: 初稿  
**负责人**: frank  

## 概述

本文档描述了QuantDB项目在Supabase中的数据库架构设计。Supabase使用PostgreSQL作为底层数据库，我们将利用其强大的功能来存储和管理金融数据。

## 设计目标

1. **高效存储**: 优化数据存储，减少冗余
2. **快速查询**: 设计适合常见查询模式的架构
3. **数据完整性**: 确保数据的一致性和完整性
4. **安全性**: 实现适当的行级安全策略
5. **可扩展性**: 支持未来的功能扩展
6. **兼容性**: 与现有SQLite架构兼容，便于迁移

## 数据库架构

### 1. 资产表 (assets)

存储所有金融资产的基本信息。

```sql
CREATE TABLE assets (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    asset_type VARCHAR(20) NOT NULL,
    exchange VARCHAR(20) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 索引
CREATE INDEX idx_assets_symbol ON assets(symbol);
CREATE INDEX idx_assets_asset_type ON assets(asset_type);
CREATE INDEX idx_assets_exchange ON assets(exchange);
```

### 2. 股票历史数据表 (stock_historical_data)

存储股票的历史交易数据。

```sql
CREATE TABLE stock_historical_data (
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
CREATE INDEX idx_stock_hist_symbol ON stock_historical_data(symbol);
CREATE INDEX idx_stock_hist_date ON stock_historical_data(trade_date);
CREATE INDEX idx_stock_hist_symbol_date ON stock_historical_data(symbol, trade_date);
```

### 3. 数据源表 (data_sources)

记录数据来源信息。

```sql
CREATE TABLE data_sources (
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
VALUES ('akshare', 'AKShare金融数据接口', NULL, TRUE);
```

### 4. 数据获取记录表 (data_fetch_records)

记录数据获取的历史记录。

```sql
CREATE TABLE data_fetch_records (
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
CREATE INDEX idx_fetch_records_source ON data_fetch_records(data_source_id);
CREATE INDEX idx_fetch_records_symbol ON data_fetch_records(symbol);
CREATE INDEX idx_fetch_records_dates ON data_fetch_records(start_date, end_date);
```

### 5. 缓存元数据表 (cache_metadata)

存储缓存相关的元数据。

```sql
CREATE TABLE cache_metadata (
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
CREATE INDEX idx_cache_metadata_key ON cache_metadata(cache_key);
CREATE INDEX idx_cache_metadata_type ON cache_metadata(data_type);
CREATE INDEX idx_cache_metadata_symbol ON cache_metadata(symbol);
CREATE INDEX idx_cache_metadata_dates ON cache_metadata(start_date, end_date);
```

### 6. 用户表 (users)

存储用户信息（使用Supabase Auth）。

```sql
-- 注意：Supabase Auth已经创建了auth.users表
-- 这里我们创建一个公共表来存储额外的用户信息

CREATE TABLE user_profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id),
    display_name VARCHAR(100),
    bio TEXT,
    preferences JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 索引
CREATE INDEX idx_user_profiles_display_name ON user_profiles(display_name);
```

### 7. 用户资产表 (user_assets)

存储用户关注的资产。

```sql
CREATE TABLE user_assets (
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
CREATE INDEX idx_user_assets_user ON user_assets(user_id);
CREATE INDEX idx_user_assets_symbol ON user_assets(symbol);
```

## 行级安全策略 (RLS)

为确保数据安全，我们将实现以下行级安全策略：

### 1. 资产表 (assets)

```sql
-- 允许所有用户读取
ALTER TABLE assets ENABLE ROW LEVEL SECURITY;
CREATE POLICY assets_select_policy ON assets
    FOR SELECT USING (true);

-- 只允许管理员修改
CREATE POLICY assets_insert_policy ON assets
    FOR INSERT WITH CHECK (auth.role() = 'service_role');
CREATE POLICY assets_update_policy ON assets
    FOR UPDATE USING (auth.role() = 'service_role');
CREATE POLICY assets_delete_policy ON assets
    FOR DELETE USING (auth.role() = 'service_role');
```

### 2. 股票历史数据表 (stock_historical_data)

```sql
-- 允许所有用户读取
ALTER TABLE stock_historical_data ENABLE ROW LEVEL SECURITY;
CREATE POLICY stock_data_select_policy ON stock_historical_data
    FOR SELECT USING (true);

-- 只允许管理员修改
CREATE POLICY stock_data_insert_policy ON stock_historical_data
    FOR INSERT WITH CHECK (auth.role() = 'service_role');
CREATE POLICY stock_data_update_policy ON stock_historical_data
    FOR UPDATE USING (auth.role() = 'service_role');
CREATE POLICY stock_data_delete_policy ON stock_historical_data
    FOR DELETE USING (auth.role() = 'service_role');
```

### 3. 用户资产表 (user_assets)

```sql
-- 用户只能访问自己的数据
ALTER TABLE user_assets ENABLE ROW LEVEL SECURITY;
CREATE POLICY user_assets_select_policy ON user_assets
    FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY user_assets_insert_policy ON user_assets
    FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY user_assets_update_policy ON user_assets
    FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY user_assets_delete_policy ON user_assets
    FOR DELETE USING (auth.uid() = user_id);
```

## 数据类型映射

从SQLite迁移到PostgreSQL时，我们需要考虑以下数据类型映射：

| SQLite类型 | PostgreSQL类型 | 说明 |
|------------|---------------|------|
| INTEGER    | INTEGER       | 整数 |
| REAL       | DECIMAL(18,4) | 金融数值 |
| TEXT       | VARCHAR/TEXT  | 文本 |
| BLOB       | BYTEA         | 二进制数据 |
| DATETIME   | TIMESTAMPTZ   | 时间戳 |

## 迁移策略

1. **创建架构**: 使用上述SQL创建表和索引
2. **数据迁移**: 使用自动化工具将数据从SQLite迁移到Supabase
3. **验证数据**: 确保数据完整性和一致性
4. **应用RLS策略**: 实现行级安全策略
5. **更新应用程序**: 修改应用程序代码以使用新的数据库

## 性能优化

1. **索引优化**: 为常用查询创建适当的索引
2. **分区表**: 考虑对大表（如股票历史数据）进行分区
3. **缓存策略**: 利用Supabase的缓存功能
4. **查询优化**: 优化常用查询的SQL语句

## 后续工作

1. **创建数据库迁移脚本**: 开发自动化迁移工具
2. **实现数据同步机制**: 确保SQLite和Supabase数据的同步
3. **开发数据验证工具**: 验证迁移后的数据完整性
4. **完善行级安全策略**: 根据实际需求调整RLS策略
5. **性能测试**: 进行全面的性能测试和优化

## 参考资料

1. [Supabase文档](https://supabase.io/docs)
2. [PostgreSQL文档](https://www.postgresql.org/docs/)
3. [SQLite到PostgreSQL迁移指南](https://wiki.postgresql.org/wiki/Converting_from_other_Databases_to_PostgreSQL#SQLite)
4. [Supabase行级安全](https://supabase.io/docs/guides/auth/row-level-security)

## 更新记录

| 版本 | 日期 | 更新者 | 更新内容 |
|------|------|--------|----------|
| 1.0.0 | 2025-05-18 | frank | 初始版本 |
