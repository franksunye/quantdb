# QuantDB Supabase 部署计划

## 文档信息
**文档类型**: 部署计划
**版本**: 1.0.0
**创建日期**: 2025-07-02
**状态**: 进行中
**负责人**: frank

## 1. 前提条件

在开始部署之前，请确保满足以下条件：

- [x] Supabase 账户已创建并设置好项目
- [x] 已安装 PostgreSQL 客户端工具（psql）
- [x] 已安装必要的 Python 依赖（psycopg2-binary 等）
- [x] 已配置 SSL 证书（prod-ca-2021.crt）
- [x] 已准备好 `.env` 文件，包含必要的 Supabase 连接信息

### 1.1 环境变量检查清单

确保 `.env` 文件中包含以下变量：

```
# Supabase 连接信息
SUPABASE_DB_HOST=aws-0-us-west-1.pooler.supabase.com
SUPABASE_DB_PORT=6543
SUPABASE_DB_NAME=postgres
SUPABASE_DB_USER=postgres.dvusiqfijdmjcsubyapw
SUPABASE_DB_PASSWORD=your_password_here
SUPABASE_SSL_CERT=prod-ca-2021.crt

# 数据库 URL（用于 SQLAlchemy）
DATABASE_URL=postgresql://postgres:your_password_here@aws-0-us-west-1.pooler.supabase.com:6543/postgres?sslmode=verify-full&sslrootcert=prod-ca-2021.crt

# Supabase API 信息
SUPABASE_URL=https://your_project_id.supabase.co
SUPABASE_KEY=your_anon_key_here
SUPABASE_SERVICE_KEY=your_service_role_key_here
```

## 2. 部署步骤

### 2.1 数据库初始化

使用 `deploy_to_supabase.py` 脚本初始化 Supabase 数据库：

```bash
# 初始化数据库（创建表和索引）
python scripts/deploy_to_supabase.py --init-db
```

这将执行以下操作：
1. 连接到 Supabase PostgreSQL 数据库
2. 执行 `database/supabase_schema.sql` 脚本创建表和索引
3. 设置行级安全策略（RLS）
4. 创建触发器和函数

### 2.2 数据迁移

使用 `deploy_to_supabase.py` 脚本迁移数据：

```bash
# 迁移数据（从 SQLite 到 Supabase）
python scripts/deploy_to_supabase.py --migrate-data
```

这将执行以下操作：
1. 从本地 SQLite 数据库读取数据
2. 将数据转换为 PostgreSQL 兼容格式
3. 批量插入数据到 Supabase
4. 创建资产 ID 映射（SQLite ID -> Supabase UUID）

### 2.3 测试 Supabase 适配器

运行 Supabase 适配器测试，确保适配器能够正常工作：

```bash
# 运行 Supabase 适配器测试
python -m unittest tests.test_supabase_adapter
```

测试将验证以下功能：
1. 数据库连接
2. 资产查询
3. 股票数据查询
4. 股票数据保存

### 2.4 更新 API 配置

修改 `.env` 文件，将 API 配置为使用 Supabase：

```bash
# 编辑 .env 文件
# 注释掉 SQLite 配置
# DATABASE_URL=sqlite:///./database/stock_data.db

# 启用 Supabase 配置
DATABASE_URL=postgresql://postgres:your_password_here@aws-0-us-west-1.pooler.supabase.com:6543/postgres?sslmode=verify-full&sslrootcert=prod-ca-2021.crt
```

### 2.5 部署 API 服务

启动 API 服务，使用 Supabase 作为后端数据库：

```bash
# 启动 API 服务
uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

### 2.6 端到端测试

运行端到端测试，验证 API 与 Supabase 的集成：

```bash
# 启动测试服务器
python start_test_server.py --port 8766

# 在另一个终端运行测试
python -m unittest tests.e2e.test_stock_data_http_api
```

## 3. 验证清单

部署完成后，使用以下清单验证部署是否成功：

- [ ] 数据库表已成功创建
- [ ] 数据已成功迁移
- [ ] Supabase 适配器测试通过
- [ ] API 能够连接到 Supabase
- [ ] API 能够查询和保存数据
- [ ] 端到端测试通过

## 4. 回滚计划

如果部署失败，使用以下步骤回滚：

1. 恢复 `.env` 文件中的 SQLite 配置
2. 重启 API 服务
3. 记录失败原因，以便后续修复

## 5. 后续步骤

成功部署后，考虑以下后续步骤：

1. 设置定期备份
2. 监控数据库性能
3. 优化查询性能
4. 实现更完善的错误处理
5. 添加更多的安全措施

## 附录：常见问题与解决方案

### 连接问题

**问题**: 无法连接到 Supabase 数据库
**解决方案**: 
- 检查 `.env` 文件中的连接信息
- 确保使用 Transaction Pooler 端口 (6543)
- 验证 SSL 证书路径是否正确

### 编码问题

**问题**: 中文字符导致连接重置
**解决方案**:
- 使用参数化查询而不是字符串拼接
- 确保所有字符串都使用 UTF-8 编码

### 权限问题

**问题**: 无法执行某些操作，如创建表
**解决方案**:
- 确保使用具有足够权限的账户
- 检查 RLS 策略是否正确设置
