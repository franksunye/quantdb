# Supabase PostgreSQL 直接连接指南

本文档提供了直接连接 Supabase PostgreSQL 数据库的最佳实践和指南。

## 目录

1. [概述](#概述)
2. [连接方式](#连接方式)
   - [SQLAlchemy](#sqlalchemy)
   - [psycopg2](#psycopg2)
   - [pg8000](#pg8000)
3. [中文编码处理](#中文编码处理)
4. [性能考虑](#性能考虑)
5. [安全最佳实践](#安全最佳实践)
6. [故障排除](#故障排除)
7. [参考代码](#参考代码)

## 概述

Supabase 提供了基于 PostgreSQL 的数据库服务，我们可以通过多种方式直接连接到这个数据库：

1. 使用 Supabase 客户端库（REST API）
2. 直接连接 PostgreSQL 数据库

直接连接 PostgreSQL 数据库的优势：

- 完整访问 PostgreSQL 的所有功能
- 更高的性能（避免 HTTP 请求的开销）
- 支持复杂的 SQL 查询和事务
- 与现有的 SQLAlchemy 模型兼容

## 连接方式

### SQLAlchemy

SQLAlchemy 是 Python 中最流行的 ORM 库，可以用于连接 Supabase PostgreSQL 数据库。

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 从环境变量获取数据库 URL
database_url = os.getenv('DATABASE_URL')

# 创建数据库引擎
engine = create_engine(database_url)

# 创建会话
Session = sessionmaker(bind=engine)
session = Session()

# 使用会话进行数据库操作
try:
    # 查询操作
    result = session.execute("SELECT version()")
    version = result.scalar()
    print(f"PostgreSQL 版本: {version}")
    
    # 提交事务
    session.commit()
except Exception as e:
    # 回滚事务
    session.rollback()
    raise e
finally:
    # 关闭会话
    session.close()
```

### psycopg2

psycopg2 是 PostgreSQL 的 Python 驱动程序，提供了直接连接 PostgreSQL 数据库的能力。

```python
import psycopg2

# 解析数据库 URL
def parse_db_url(database_url):
    if database_url.startswith('postgresql://'):
        parts = database_url.replace('postgresql://', '').split('@')
        user_pass = parts[0].split(':')
        host_db = parts[1].split('/')
        
        user = user_pass[0]
        password = user_pass[1]
        host_port = host_db[0].split(':')
        host = host_port[0]
        port = int(host_port[1]) if len(host_port) > 1 else 5432
        dbname = host_db[1]
        
        return {
            'dbname': dbname,
            'user': user,
            'password': password,
            'host': host,
            'port': port
        }
    else:
        raise ValueError(f"不支持的数据库 URL 格式: {database_url}")

# 从环境变量获取数据库 URL
database_url = os.getenv('DATABASE_URL')

# 解析数据库 URL
db_params = parse_db_url(database_url)

# 连接到数据库
conn = psycopg2.connect(
    dbname=db_params['dbname'],
    user=db_params['user'],
    password=db_params['password'],
    host=db_params['host'],
    port=db_params['port']
)

# 使用连接进行数据库操作
try:
    # 创建游标
    cur = conn.cursor()
    
    # 执行查询
    cur.execute("SELECT version()")
    version = cur.fetchone()
    print(f"PostgreSQL 版本: {version[0]}")
    
    # 提交事务
    conn.commit()
except Exception as e:
    # 回滚事务
    conn.rollback()
    raise e
finally:
    # 关闭游标和连接
    if 'cur' in locals():
        cur.close()
    conn.close()
```

### pg8000

pg8000 是一个纯 Python 实现的 PostgreSQL 驱动程序，可能对于中文编码问题有更好的支持。

```python
import pg8000

# 从环境变量获取数据库 URL
database_url = os.getenv('DATABASE_URL')

# 解析数据库 URL
db_params = parse_db_url(database_url)

# 连接到数据库
conn = pg8000.connect(
    database=db_params['dbname'],
    user=db_params['user'],
    password=db_params['password'],
    host=db_params['host'],
    port=db_params['port']
)

# 使用连接进行数据库操作
try:
    # 创建游标
    cursor = conn.cursor()
    
    # 执行查询
    cursor.execute("SELECT version()")
    version = cursor.fetchone()
    print(f"PostgreSQL 版本: {version[0]}")
    
    # 提交事务
    conn.commit()
except Exception as e:
    # 回滚事务
    conn.rollback()
    raise e
finally:
    # 关闭游标和连接
    if 'cursor' in locals():
        cursor.close()
    conn.close()
```

## 中文编码处理

在处理中文数据时，可能会遇到编码问题。以下是一些解决方案：

### 使用 pg8000

pg8000 是一个纯 Python 实现的 PostgreSQL 驱动程序，可能对于中文编码问题有更好的支持。

### 设置客户端编码

使用 psycopg2 时，可以设置客户端编码：

```python
# 连接到数据库
conn = psycopg2.connect(
    dbname=db_params['dbname'],
    user=db_params['user'],
    password=db_params['password'],
    host=db_params['host'],
    port=db_params['port']
)

# 设置客户端编码
conn.set_client_encoding('UTF8')
```

### 使用 URL 编码的密码

如果密码中包含特殊字符，可以使用 URL 编码：

```python
import urllib.parse

# URL 编码密码
encoded_password = urllib.parse.quote_plus(db_params['password'])

# 构建数据库 URL
database_url = f"postgresql://{db_params['user']}:{encoded_password}@{db_params['host']}:{db_params['port']}/{db_params['dbname']}"
```

## 性能考虑

直接连接 PostgreSQL 数据库通常比使用 REST API 有更好的性能，特别是在以下情况：

1. 批量插入数据
2. 复杂查询
3. 需要事务支持

### 批量插入优化

使用 SQLAlchemy 的 `bulk_save_objects` 或 `bulk_insert_mappings` 方法可以提高批量插入的性能：

```python
# 批量插入
session.bulk_save_objects(objects)
session.commit()
```

### 连接池

使用连接池可以提高性能：

```python
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    database_url,
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800
)
```

## 安全最佳实践

### 使用环境变量

将数据库连接信息存储在环境变量中，而不是硬编码在代码中：

```python
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 获取数据库 URL
database_url = os.getenv('DATABASE_URL')
```

### 使用最小权限原则

为应用程序创建具有最小所需权限的数据库用户。

### 使用 SSL 连接

确保使用 SSL 连接到数据库：

```python
# 使用 psycopg2 连接
conn = psycopg2.connect(
    dbname=db_params['dbname'],
    user=db_params['user'],
    password=db_params['password'],
    host=db_params['host'],
    port=db_params['port'],
    sslmode='require'
)

# 使用 SQLAlchemy 连接
engine = create_engine(
    database_url,
    connect_args={"sslmode": "require"}
)
```

## 故障排除

### 连接问题

1. 检查网络连接
2. 验证数据库 URL 是否正确
3. 确认 IP 地址是否在允许列表中
4. 检查防火墙设置

### 编码问题

1. 确保使用 UTF-8 编码
2. 尝试使用 pg8000 代替 psycopg2
3. 设置客户端编码为 UTF8

## 参考代码

项目中包含了多个测试脚本，可以用于测试直接连接 Supabase PostgreSQL 数据库：

1. `scripts/test_direct_postgres_connection.py` - 测试直接连接
2. `scripts/test_postgres_performance.py` - 测试性能
3. `scripts/test_pg8000_connection.py` - 测试 pg8000 连接

运行测试脚本：

```bash
python scripts/test_direct_postgres_connection.py
python scripts/test_postgres_performance.py
python scripts/test_pg8000_connection.py
```
