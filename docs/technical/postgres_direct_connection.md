# PostgreSQL 直连指南

本文档提供了直接连接 PostgreSQL 数据库的详细指南，特别是针对 Supabase PostgreSQL 数据库。

## 目录

1. [概述](#概述)
2. [环境配置](#环境配置)
3. [连接方式](#连接方式)
4. [基本操作](#基本操作)
5. [中文编码处理](#中文编码处理)
6. [性能考虑](#性能考虑)
7. [故障排除](#故障排除)
8. [工具脚本](#工具脚本)
9. [最佳实践](#最佳实践)

## 概述

直接连接 PostgreSQL 数据库可以提供更高的性能和更多的功能，特别是在以下情况：

- 需要执行复杂的 SQL 查询
- 需要批量处理数据
- 需要使用 PostgreSQL 特有的功能
- 需要更高的性能

本项目提供了 `PostgresClient` 类，封装了直接连接 PostgreSQL 数据库的功能，解决了中文 Windows 环境下的编码问题。

## 环境配置

### 环境变量

在 `.env` 文件中配置以下环境变量：

```
SUPABASE_DB_HOST=db.dvusiqfijdmjcsubyapw.supabase.co
SUPABASE_DB_PORT=5432
SUPABASE_DB_NAME=postgres
SUPABASE_DB_USER=postgres
SUPABASE_DB_PASSWORD=your_password_here
```

### 依赖安装

安装必要的依赖：

```bash
pip install psycopg2-binary python-dotenv
```

或者使用 pg8000（纯 Python 实现，可能对编码问题更友好）：

```bash
pip install pg8000 python-dotenv
```

## 连接方式

### 使用 PostgresClient 类

```python
from services.postgres_client import get_postgres_client

# 获取客户端
client = get_postgres_client()

# 执行查询
result = client.execute_query_dict("SELECT * FROM assets LIMIT 10")
print(result)
```

### 自定义连接参数

```python
from services.postgres_client import PostgresClient

# 创建客户端
client = PostgresClient(
    host="db.dvusiqfijdmjcsubyapw.supabase.co",
    port=5432,
    dbname="postgres",
    user="postgres",
    password="your_password_here"
)

# 执行查询
result = client.execute_query_dict("SELECT * FROM assets LIMIT 10")
print(result)
```

## 基本操作

### 查询操作

```python
# 执行查询并返回元组列表
result = client.execute_query("SELECT * FROM assets LIMIT 10")

# 执行查询并返回字典列表
result = client.execute_query_dict("SELECT * FROM assets LIMIT 10")

# 执行查询并返回一条结果
result = client.execute_query_one("SELECT * FROM assets WHERE symbol = %s", ("AAPL",))

# 执行查询并返回一个字典
result = client.execute_query_dict_one("SELECT * FROM assets WHERE symbol = %s", ("AAPL",))

# 执行查询并返回单个值
result = client.execute_query_scalar("SELECT COUNT(*) FROM assets")
```

### 非查询操作

```python
# 执行非查询操作
rows_affected = client.execute_non_query("UPDATE assets SET name = %s WHERE symbol = %s", ("Apple Inc.", "AAPL"))

# 插入数据
asset_id = client.execute_query_scalar(
    "INSERT INTO assets (symbol, name) VALUES (%s, %s) RETURNING id",
    ("AAPL", "Apple Inc.")
)

# 更新数据
rows_affected = client.execute_non_query(
    "UPDATE assets SET name = %s WHERE symbol = %s",
    ("Apple Inc.", "AAPL")
)

# 删除数据
rows_affected = client.execute_non_query(
    "DELETE FROM assets WHERE symbol = %s",
    ("AAPL",)
)
```

### 事务操作

```python
# 使用上下文管理器进行事务操作
with client.get_connection() as conn:
    # 开始事务
    with conn.cursor() as cursor:
        # 执行多个操作
        cursor.execute("INSERT INTO assets (symbol, name) VALUES (%s, %s) RETURNING id", ("AAPL", "Apple Inc."))
        asset_id = cursor.fetchone()[0]
        
        cursor.execute("INSERT INTO prices (asset_id, date, close) VALUES (%s, %s, %s)", (asset_id, "2023-01-01", 100.0))
        
        # 事务会自动提交或回滚
```

## 中文编码处理

`PostgresClient` 类已经处理了中文编码问题，主要通过以下方式：

1. 使用显式参数连接，避免使用 DSN 字符串
2. 设置客户端编码为 UTF-8
3. 支持 pg8000 驱动程序，它是纯 Python 实现的，可能对编码问题更友好

示例：

```python
# 插入中文数据
client.execute_non_query(
    "INSERT INTO assets (symbol, name, exchange) VALUES (%s, %s, %s)",
    ("600000", "浦发银行", "上海证券交易所")
)

# 查询中文数据
result = client.execute_query_dict_one(
    "SELECT * FROM assets WHERE symbol = %s",
    ("600000",)
)
print(result)
```

## 性能考虑

### 批量操作

对于批量操作，可以使用 `executemany` 方法：

```python
# 批量插入数据
data = [
    ("AAPL", "Apple Inc."),
    ("MSFT", "Microsoft Corporation"),
    ("GOOG", "Alphabet Inc.")
]

with client.get_connection() as conn:
    with conn.cursor() as cursor:
        cursor.executemany(
            "INSERT INTO assets (symbol, name) VALUES (%s, %s)",
            data
        )
        conn.commit()
```

### 连接池

`PostgresClient` 类使用单例模式，但没有实现连接池。如果需要连接池，可以使用 `psycopg2.pool` 模块：

```python
from psycopg2 import pool

# 创建连接池
connection_pool = pool.SimpleConnectionPool(
    minconn=1,
    maxconn=10,
    host="db.dvusiqfijdmjcsubyapw.supabase.co",
    port=5432,
    dbname="postgres",
    user="postgres",
    password="your_password_here"
)

# 获取连接
conn = connection_pool.getconn()

# 使用连接
# ...

# 归还连接
connection_pool.putconn(conn)

# 关闭连接池
connection_pool.closeall()
```

## 故障排除

### 编码问题

如果遇到编码问题，可以尝试以下方法：

1. 确保使用显式参数连接，不要使用 DSN 字符串
2. 设置客户端编码为 UTF-8
3. 使用 pg8000 驱动程序
4. 对密码进行 URL 编码

### 连接问题

如果遇到连接问题，可以尝试以下方法：

1. 检查网络连接
2. 验证连接参数是否正确
3. 确认 IP 地址是否在允许列表中
4. 检查防火墙设置

## 工具脚本

本项目提供了以下工具脚本：

### 测试连接

```bash
python scripts/test_postgres_direct.py
```

### 初始化数据库

```bash
python scripts/init_postgres_db.py
```

### 执行 SQL 命令

```bash
# 执行单个 SQL 命令
python scripts/postgres_execute_sql.py -c "SELECT * FROM assets LIMIT 10"

# 执行 SQL 文件
python scripts/postgres_execute_sql.py -f database/postgres_init.sql

# 交互式模式
python scripts/postgres_execute_sql.py -i
```

## 最佳实践

1. **使用参数化查询**：避免 SQL 注入
2. **使用事务**：确保数据一致性
3. **处理异常**：捕获并处理异常
4. **关闭连接**：使用完连接后关闭
5. **使用连接池**：提高性能
6. **使用 UTF-8 编码**：避免编码问题
7. **使用 pg8000**：如果遇到编码问题
8. **使用 URL 编码**：对密码进行 URL 编码
