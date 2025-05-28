# Supabase 部署指南

## 文档信息
**文档类型**: 部署指南
**文档编号**: quantdb-DEPLOY-001
**版本**: 1.1.0
**创建日期**: 2025-05-15
**最后更新**: 2025-07-01
**状态**: 已发布
**负责人**: frank

## 1. 概述

本文档提供了在 Supabase 上部署 QuantDB 数据库的详细指南。Supabase 是一个开源的 Firebase 替代品，提供了 PostgreSQL 数据库、身份验证、实时订阅等功能。

## 2. 前提条件

- Supabase 账户（可在 [https://supabase.com](https://supabase.com) 注册）
- 基本的 SQL 知识
- QuantDB 代码库的访问权限

## 3. 创建 Supabase 项目

### 3.1 登录 Supabase

1. 访问 [https://app.supabase.com](https://app.supabase.com)
2. 使用您的账户登录

### 3.2 创建新项目

1. 点击 "New Project"
2. 输入项目详情：
   - **Name**: QuantDB
   - **Database Password**: 创建一个强密码（请记住此密码）
   - **Region**: 选择离您用户最近的区域
   - **Pricing Plan**: 免费计划（开发环境）或付费计划（生产环境）
3. 点击 "Create New Project"

### 3.3 获取项目凭证

项目创建后，您需要获取以下凭证：

1. 在项目仪表板中，点击左侧菜单的 "Settings"
2. 点击 "API" 选项
3. 记录以下值：
   - **Project URL**: `https://[YOUR_PROJECT_ID].supabase.co`
   - **API Key**: `anon` 公钥（用于客户端请求）
   - **Service Role Key**: `service_role` 密钥（用于服务器端请求，请保密）

## 4. 设置数据库架构

### 4.1 使用 SQL 编辑器

1. 在 Supabase 仪表板中，点击左侧菜单的 "SQL Editor"
2. 点击 "New Query"
3. 复制并粘贴以下 SQL 脚本：

```sql
-- 创建资产表
CREATE TABLE IF NOT EXISTS assets (
    asset_id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    name VARCHAR(100),
    isin VARCHAR(12),
    asset_type VARCHAR(20),
    exchange VARCHAR(20),
    currency VARCHAR(3),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 创建价格表
CREATE TABLE IF NOT EXISTS prices (
    price_id SERIAL PRIMARY KEY,
    asset_id INTEGER REFERENCES assets(asset_id),
    date DATE NOT NULL,
    open NUMERIC(15, 5),
    high NUMERIC(15, 5),
    low NUMERIC(15, 5),
    close NUMERIC(15, 5),
    volume BIGINT,
    adjusted_close NUMERIC(15, 5),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(asset_id, date)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_assets_symbol ON assets(symbol);
CREATE INDEX IF NOT EXISTS idx_prices_asset_id ON prices(asset_id);
CREATE INDEX IF NOT EXISTS idx_prices_date ON prices(date);
CREATE INDEX IF NOT EXISTS idx_prices_asset_date ON prices(asset_id, date);

-- 创建更新触发器函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 为资产表添加触发器
CREATE TRIGGER update_assets_updated_at
BEFORE UPDATE ON assets
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- 为价格表添加触发器
CREATE TRIGGER update_prices_updated_at
BEFORE UPDATE ON prices
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
```

4. 点击 "Run" 执行脚本

### 4.2 使用数据库迁移（可选）

对于更可控的方法，您可以使用 Alembic 进行数据库迁移：

1. 更新 `.env` 文件，添加 Supabase 连接详情：
   ```
   DATABASE_URL=postgresql://postgres:[YOUR_PASSWORD]@db.[YOUR_PROJECT_ID].supabase.co:5432/postgres
   ```
2. 运行迁移脚本（将在未来的 Sprint 中实现）

### 4.3 设置行级安全策略 (RLS)

为了确保数据安全，我们需要设置行级安全策略：

1. 在 SQL 编辑器中创建新查询
2. 复制并粘贴以下 SQL 脚本：

```sql
-- 启用 RLS
ALTER TABLE assets ENABLE ROW LEVEL SECURITY;
ALTER TABLE prices ENABLE ROW LEVEL SECURITY;

-- 创建公共读取策略
CREATE POLICY "Public assets are viewable by everyone"
ON assets
FOR SELECT
USING (true);

CREATE POLICY "Public prices are viewable by everyone"
ON prices
FOR SELECT
USING (true);

-- 创建仅管理员可写入的策略
CREATE POLICY "Only admins can insert assets"
ON assets
FOR INSERT
USING (auth.role() = 'authenticated' AND auth.email() IN ('admin@example.com'));

CREATE POLICY "Only admins can update assets"
ON assets
FOR UPDATE
USING (auth.role() = 'authenticated' AND auth.email() IN ('admin@example.com'));

CREATE POLICY "Only admins can delete assets"
ON assets
FOR DELETE
USING (auth.role() = 'authenticated' AND auth.email() IN ('admin@example.com'));

CREATE POLICY "Only admins can insert prices"
ON prices
FOR INSERT
USING (auth.role() = 'authenticated' AND auth.email() IN ('admin@example.com'));

CREATE POLICY "Only admins can update prices"
ON prices
FOR UPDATE
USING (auth.role() = 'authenticated' AND auth.email() IN ('admin@example.com'));

CREATE POLICY "Only admins can delete prices"
ON prices
FOR DELETE
USING (auth.role() = 'authenticated' AND auth.email() IN ('admin@example.com'));
```

3. 将 `'admin@example.com'` 替换为您的管理员邮箱
4. 点击 "Run" 执行脚本

## 5. 配置身份验证

### 5.1 启用电子邮件身份验证

1. 在 Supabase 仪表板中，点击左侧菜单的 "Authentication"
2. 点击 "Providers" 选项卡
3. 确保 "Email" 提供商已启用
4. 配置电子邮件模板（可选）

### 5.2 创建管理员用户

1. 点击 "Users" 选项卡
2. 点击 "Invite User"
3. 输入管理员电子邮件地址
4. 设置管理员角色

## 6. 配置环境变量

在 QuantDB 项目中，您需要更新 `.env` 文件以使用 Supabase 凭证：

```
# Supabase 配置
DATABASE_URL=postgresql://postgres:[YOUR_PASSWORD]@db.[YOUR_PROJECT_ID].supabase.co:5432/postgres
SUPABASE_URL=https://[YOUR_PROJECT_ID].supabase.co
SUPABASE_KEY=[YOUR_SUPABASE_API_KEY]
SUPABASE_JWT_SECRET=[YOUR_SUPABASE_JWT_SECRET]
```

请替换以下值：
- `[YOUR_PASSWORD]`: 您在创建项目时设置的数据库密码
- `[YOUR_PROJECT_ID]`: 您的 Supabase 项目 ID
- `[YOUR_SUPABASE_API_KEY]`: 您的 Supabase API 密钥（service_role 密钥）
- `[YOUR_SUPABASE_JWT_SECRET]`: 您的 Supabase JWT 密钥（在 Settings > API > JWT Settings 中找到）

## 7. 数据迁移

如果您已经有本地 SQLite 数据库，可以将数据迁移到 Supabase：

### 7.1 导出 SQLite 数据

使用以下脚本导出数据：

```python
# export_data.py
import sqlite3
import csv
import os

# 连接到 SQLite 数据库
conn = sqlite3.connect('database/stock_data.db')
cursor = conn.cursor()

# 确保导出目录存在
os.makedirs('data/export', exist_ok=True)

# 导出资产表
cursor.execute('SELECT * FROM assets')
with open('data/export/assets.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow([i[0] for i in cursor.description])  # 写入列名
    writer.writerows(cursor.fetchall())  # 写入数据

# 导出价格表
cursor.execute('SELECT * FROM prices')
with open('data/export/prices.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow([i[0] for i in cursor.description])  # 写入列名
    writer.writerows(cursor.fetchall())  # 写入数据

conn.close()
print("数据导出完成")
```

### 7.2 导入数据到 PostgreSQL

1. 在 Supabase 仪表板中，点击左侧菜单的 "Storage"
2. 创建一个名为 "import" 的新存储桶
3. 上传导出的 CSV 文件
4. 使用 SQL 编辑器导入数据：

```sql
-- 导入资产数据
COPY assets(asset_id, symbol, name, isin, asset_type, exchange, currency, created_at, updated_at)
FROM 'assets.csv'
DELIMITER ','
CSV HEADER;

-- 导入价格数据
COPY prices(price_id, asset_id, date, open, high, low, close, volume, adjusted_close, created_at, updated_at)
FROM 'prices.csv'
DELIMITER ','
CSV HEADER;

-- 重置序列
SELECT setval('assets_asset_id_seq', (SELECT MAX(asset_id) FROM assets));
SELECT setval('prices_price_id_seq', (SELECT MAX(price_id) FROM prices));
```

## 8. 测试连接

使用以下脚本测试与 Supabase 的连接：

```python
# test_connection.py
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 获取数据库 URL
database_url = os.getenv('DATABASE_URL')

# 创建引擎
engine = create_engine(database_url)

# 测试连接
with engine.connect() as conn:
    result = conn.execute(text("SELECT COUNT(*) FROM assets"))
    count = result.scalar()
    print(f"资产表中有 {count} 条记录")

    result = conn.execute(text("SELECT COUNT(*) FROM prices"))
    count = result.scalar()
    print(f"价格表中有 {count} 条记录")

print("连接测试成功")
```

## 9. 故障排除

### 9.1 连接问题

如果遇到连接问题：

1. 检查数据库密码是否正确
2. 确保您的 IP 地址在 Supabase 仪表板中被允许
3. 验证数据库 URL 格式是否正确

### 9.2 权限问题

如果遇到权限问题：

1. 检查 RLS 策略是否正确设置
2. 确保您使用的是正确的 API 密钥
3. 验证用户角色和权限

### 9.3 架构问题

如果遇到架构问题：

1. 检查 SQLite 和 PostgreSQL 语法的差异
2. 确保所有表都已正确创建
3. 验证外键约束是否正确定义

## 10. 下一步

完成 Supabase 设置后：

1. 配置 Vercel 部署（参见 [Vercel 部署指南](./vercel_setup_guide.md)）
2. 设置 CI/CD 流程（参见 [CI/CD 设置指南](./ci_cd_setup_guide.md)）
3. 配置监控和警报
4. 设置定期备份
