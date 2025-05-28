-- QuantDB Supabase数据库初始化脚本 (第1部分)
-- 为MVP部署设计的精简版表结构
-- 版本: 1.0.0
-- 日期: 2025-05-19

-- 启用UUID扩展（Supabase推荐使用UUID作为主键）
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 创建 assets 表
CREATE TABLE IF NOT EXISTS assets (
    asset_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol TEXT NOT NULL,
    name TEXT NOT NULL,
    isin TEXT NOT NULL UNIQUE,
    asset_type TEXT NOT NULL,
    exchange TEXT NOT NULL,
    currency TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 创建 daily_stock_data 表（MVP核心表）
CREATE TABLE IF NOT EXISTS daily_stock_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    asset_id UUID NOT NULL,
    trade_date DATE NOT NULL,
    open NUMERIC(10, 2),
    high NUMERIC(10, 2),
    low NUMERIC(10, 2),
    close NUMERIC(10, 2),
    volume BIGINT,
    turnover NUMERIC(20, 2),
    amplitude NUMERIC(10, 4),
    pct_change NUMERIC(10, 4),
    change NUMERIC(10, 4),
    turnover_rate NUMERIC(10, 4),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    FOREIGN KEY (asset_id) REFERENCES assets (asset_id),
    UNIQUE (asset_id, trade_date)
);
