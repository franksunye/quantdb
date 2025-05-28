# Supabase连接方案总结

## 文档信息
**文档类型**: 技术总结  
**版本**: 1.0.0  
**创建日期**: 2025-05-19  
**状态**: 已完成  
**负责人**: frank  

## 概述

本文档总结了QuantDB项目与Supabase PostgreSQL数据库的连接方案，特别是在中文Windows环境下的解决方案。经过多次尝试和测试，我们找到了一种可靠的连接方法，可以在IPv4网络环境下成功连接和管理Supabase数据库。

## 关键发现

1. **IPv4/IPv6兼容性问题**:
   - Supabase直接数据库连接（端口5432）仅支持IPv6
   - 在IPv4网络环境下，直接连接会超时
   - 使用Supabase提供的Connection Pooler可以解决此问题

2. **连接方式比较**:

   | 连接方式 | 端口 | IPv4兼容 | 适用场景 | 限制 |
   |----------|------|-----------|----------|------|
   | 直接连接 | 5432 | ❌ | 需要完整数据库功能 | 仅IPv6网络 |
   | Transaction Pooler | 6543 | ✅ | 短暂连接，基本操作 | 部分高级功能受限 |
   | Session Pooler | 5432 | ✅ | 长连接，复杂操作 | 连接数有限 |
   | REST API | 443 | ✅ | 数据操作，应用集成 | 需要额外编码 |

3. **中文编码问题**:
   - 在某些操作中，中文字符可能导致连接重置
   - 使用英文字符或REST API可以避免此问题

## 推荐的连接方案

### 1. 使用Transaction Pooler (推荐用于IPv4网络)

```powershell
$env:PGPASSWORD="your_password_here"; psql "sslmode=verify-full sslrootcert=prod-ca-2021.crt host=aws-0-us-west-1.pooler.supabase.com port=6543 dbname=postgres user=postgres.dvusiqfijdmjcsubyapw"
```

或使用简化脚本:

```powershell
.\scripts\connect_supabase_pooler_simple.ps1
```

### 2. 使用REST API (推荐用于应用集成和数据操作)

REST API是与Supabase交互的另一种方式，特别适合:
- 数据插入、更新和查询操作
- 应用程序集成
- 处理中文等非ASCII字符

示例代码:
```python
import requests

# 设置请求头
headers = {
    "apikey": "your_supabase_key",
    "Authorization": f"Bearer your_supabase_key",
    "Content-Type": "application/json"
}

# 查询数据
response = requests.get(
    "https://your_project_id.supabase.co/rest/v1/your_table?select=*",
    headers=headers
)

# 插入数据
data = {"name": "测试", "value": 100}
response = requests.post(
    "https://your_project_id.supabase.co/rest/v1/your_table",
    headers=headers,
    json=data
)
```

## 功能验证

我们已经验证了以下操作可以成功执行:

1. **基本SQL操作**:
   - ✅ 创建表 (CREATE TABLE)
   - ✅ 插入数据 (INSERT)
   - ✅ 查询数据 (SELECT)
   - ✅ 更新数据 (UPDATE)
   - ✅ 删除数据 (DELETE)
   - ✅ 删除表 (DROP TABLE)

2. **限制和注意事项**:
   - ⚠️ 中文字符可能导致连接重置
   - ⚠️ 某些高级操作可能受限
   - ⚠️ 需要使用SSL证书进行安全连接

## 最佳实践

1. **连接管理**:
   - 使用环境变量存储密码，避免硬编码
   - 使用SSL证书验证连接安全性
   - 使用脚本简化连接过程

2. **操作建议**:
   - 使用Transaction Pooler进行查询和基本操作
   - 使用REST API进行数据写入和复杂操作
   - 避免在直接SQL操作中使用中文字符

3. **安全考虑**:
   - 不要在代码中硬编码密码
   - 使用最小权限原则
   - 实施行级安全策略

## 结论

通过使用Supabase的Transaction Pooler，我们成功解决了IPv4网络环境下连接Supabase PostgreSQL数据库的问题。这为QuantDB项目使用Supabase作为云数据库解决方案提供了可行的路径。

虽然仍有一些限制（如中文字符处理和某些高级操作），但通过结合使用psql和REST API，我们可以满足项目的所有需求。

## 参考文档

- [psql_supabase_guide.md](./psql_supabase_guide.md) - 详细的psql连接指南
- [Supabase官方文档](https://supabase.com/docs) - Supabase官方文档
- [PostgreSQL官方文档](https://www.postgresql.org/docs/) - PostgreSQL官方文档
