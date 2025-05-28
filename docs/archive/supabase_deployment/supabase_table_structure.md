# Supabase表结构定义

## 文档信息
**文档类型**: 技术规范  
**文档编号**: quantdb-TECH-SPEC-001  
**版本**: 1.0.0  
**创建日期**: 2025-05-17  
**状态**: 初稿  
**负责人**: frank  

## 概述

本文档定义了QuantDB项目在Supabase中使用的表结构。由于在中文Windows环境下无法通过API自动创建表，需要手动在Supabase控制台中创建这些表。

## 表结构

### 1. assets表

assets表用于存储资产信息，如股票、指数等。

#### 表定义

```sql
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

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_assets_symbol ON assets (symbol);

-- 创建更新时间戳触发器
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_assets_updated_at
BEFORE UPDATE ON assets
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
```

#### 字段说明

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| asset_id | SERIAL | 资产ID | 主键 |
| symbol | VARCHAR(20) | 资产代码 | 非空，唯一 |
| name | VARCHAR(100) | 资产名称 | 可空 |
| isin | VARCHAR(12) | 国际证券识别码 | 可空 |
| asset_type | VARCHAR(20) | 资产类型 | 可空 |
| exchange | VARCHAR(20) | 交易所 | 可空 |
| currency | VARCHAR(3) | 货币 | 可空 |
| created_at | TIMESTAMP WITH TIME ZONE | 创建时间 | 默认当前时间 |
| updated_at | TIMESTAMP WITH TIME ZONE | 更新时间 | 默认当前时间 |

#### 行级安全策略

```sql
-- 启用行级安全
ALTER TABLE assets ENABLE ROW LEVEL SECURITY;

-- 允许任何人读取assets
CREATE POLICY "Allow public read access to assets" ON assets
    FOR SELECT
    USING (true);

-- 允许只有具有admin角色的认证用户插入/更新/删除assets
CREATE POLICY "Allow admin insert access to assets" ON assets
    FOR INSERT
    TO authenticated
    WITH CHECK (auth.jwt() ? 'role' AND auth.jwt()->>'role' = 'admin');

CREATE POLICY "Allow admin update access to assets" ON assets
    FOR UPDATE
    TO authenticated
    USING (auth.jwt() ? 'role' AND auth.jwt()->>'role' = 'admin')
    WITH CHECK (auth.jwt() ? 'role' AND auth.jwt()->>'role' = 'admin');

CREATE POLICY "Allow admin delete access to assets" ON assets
    FOR DELETE
    TO authenticated
    USING (auth.jwt() ? 'role' AND auth.jwt()->>'role' = 'admin');
```

### 2. prices表

prices表用于存储资产价格信息，如股票的每日价格数据。

#### 表定义

```sql
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

-- 创建更新时间戳触发器
CREATE TRIGGER update_prices_updated_at
BEFORE UPDATE ON prices
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
```

#### 字段说明

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| price_id | SERIAL | 价格ID | 主键 |
| asset_id | INTEGER | 资产ID | 非空，外键 |
| date | DATE | 日期 | 非空 |
| open | NUMERIC(10, 2) | 开盘价 | 可空 |
| high | NUMERIC(10, 2) | 最高价 | 可空 |
| low | NUMERIC(10, 2) | 最低价 | 可空 |
| close | NUMERIC(10, 2) | 收盘价 | 可空 |
| volume | BIGINT | 成交量 | 可空 |
| adjusted_close | NUMERIC(10, 2) | 调整后收盘价 | 可空 |
| created_at | TIMESTAMP WITH TIME ZONE | 创建时间 | 默认当前时间 |
| updated_at | TIMESTAMP WITH TIME ZONE | 更新时间 | 默认当前时间 |

#### 行级安全策略

```sql
-- 启用行级安全
ALTER TABLE prices ENABLE ROW LEVEL SECURITY;

-- 允许任何人读取prices
CREATE POLICY "Allow public read access to prices" ON prices
    FOR SELECT
    USING (true);

-- 允许只有具有admin角色的认证用户插入/更新/删除prices
CREATE POLICY "Allow admin insert access to prices" ON prices
    FOR INSERT
    TO authenticated
    WITH CHECK (auth.jwt() ? 'role' AND auth.jwt()->>'role' = 'admin');

CREATE POLICY "Allow admin update access to prices" ON prices
    FOR UPDATE
    TO authenticated
    USING (auth.jwt() ? 'role' AND auth.jwt()->>'role' = 'admin')
    WITH CHECK (auth.jwt() ? 'role' AND auth.jwt()->>'role' = 'admin');

CREATE POLICY "Allow admin delete access to prices" ON prices
    FOR DELETE
    TO authenticated
    USING (auth.jwt() ? 'role' AND auth.jwt()->>'role' = 'admin');
```

## 手动创建表步骤

1. 登录 [Supabase 控制台](https://app.supabase.com)
2. 选择您的项目 "franksunye's Project"
3. 点击左侧菜单中的 "SQL 编辑器"
4. 点击 "新查询"
5. 复制上面的表定义SQL脚本并粘贴到查询编辑器中
6. 点击 "运行" 按钮执行查询

## 验证表创建

创建表后，可以通过以下方式验证表是否创建成功：

1. 在Supabase控制台中，点击左侧菜单中的 "表编辑器"
2. 查看是否有assets和prices表
3. 点击表名，查看表结构是否正确
4. 点击 "行级安全" 选项卡，查看RLS策略是否正确设置

或者，可以使用以下SQL查询验证表结构：

```sql
-- 查看表列表
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public';

-- 查看assets表结构
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'assets' 
ORDER BY ordinal_position;

-- 查看prices表结构
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'prices' 
ORDER BY ordinal_position;

-- 查看索引
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename IN ('assets', 'prices');

-- 查看RLS策略
SELECT * 
FROM pg_policies 
WHERE tablename IN ('assets', 'prices');
```

## 注意事项

1. 确保在创建prices表之前已经创建了assets表，因为prices表有一个引用assets表的外键
2. 确保在创建触发器之前已经创建了update_updated_at_column函数
3. 如果表已经存在，可以使用ALTER TABLE语句修改表结构
4. 如果需要删除表，可以使用DROP TABLE语句，但要注意先删除引用表的外键约束

## 数据迁移

如果需要从SQLite迁移数据到Supabase，可以使用以下步骤：

1. 从SQLite导出数据为CSV格式
2. 在Supabase控制台中，点击左侧菜单中的 "表编辑器"
3. 选择要导入数据的表
4. 点击 "插入" 按钮，选择 "上传CSV"
5. 选择CSV文件并上传

或者，可以使用QuantDB项目中的数据迁移工具：

```bash
python scripts/migrate_to_supabase.py
```

## 参考资料

1. [Supabase 表编辑器文档](https://supabase.io/docs/guides/database)
2. [PostgreSQL 数据类型](https://www.postgresql.org/docs/current/datatype.html)
3. [Supabase 行级安全](https://supabase.io/docs/guides/auth/row-level-security)
