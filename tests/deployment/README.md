# 部署测试指南

本目录包含用于测试部署环境的脚本，包括 Supabase 和 Vercel 部署测试。

## Supabase 部署测试

Supabase 部署测试用于验证 Supabase 环境的配置是否正确，包括数据库连接、API 功能和数据迁移。

### 前提条件

在运行测试之前，请确保：

1. 已按照 [Supabase 部署指南](../../docs/technical/deployment/supabase_setup_guide.md) 设置了 Supabase 项目
2. 已在 `.env` 文件中配置了以下环境变量：
   - `DATABASE_URL`: Supabase PostgreSQL 数据库的连接字符串
   - `SUPABASE_URL`: Supabase 项目 URL
   - `SUPABASE_KEY`: Supabase API 密钥（anon 密钥）
   - `SUPABASE_SERVICE_KEY`: Supabase 服务角色密钥（可选，用于测试行级安全策略）

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行测试

运行所有 Supabase 测试：

```bash
python -m tests.deployment.run_supabase_tests
```

运行特定测试模块：

```bash
python -m tests.deployment.run_supabase_tests --module test_supabase_connection
```

列出可用的测试模块：

```bash
python -m tests.deployment.run_supabase_tests --list
```

### 测试模块说明

1. **test_supabase_connection.py**
   - 测试与 Supabase PostgreSQL 数据库的连接
   - 验证数据库架构是否正确
   - 测试基本的数据操作（插入、查询、更新、删除）

2. **test_supabase_api.py**
   - 测试 Supabase REST API 连接
   - 测试数据访问功能
   - 测试行级安全策略

3. **test_data_migration.py**
   - 测试从 SQLite 数据库迁移数据到 Supabase PostgreSQL 数据库
   - 创建测试 SQLite 数据库
   - 导出数据到 CSV
   - 导入数据到 PostgreSQL
   - 验证数据完整性

### 测试结果

测试结果将输出到控制台和日志文件。日志文件命名为 `supabase_tests_YYYYMMDD_HHMMSS.log`，保存在当前目录。

测试成功时，将显示：

```
所有测试通过！Supabase 部署测试成功。
```

如果测试失败，将显示失败的测试模块和详细错误信息。

### 故障排除

如果测试失败，请检查以下内容：

1. 环境变量是否正确配置
2. Supabase 项目是否正确设置
3. 数据库架构是否正确创建
4. 网络连接是否正常
5. 行级安全策略是否正确配置

## Vercel 部署测试

Vercel 部署测试将在未来添加，用于验证 Vercel 环境的配置是否正确。

## 注意事项

- 这些测试脚本会创建和删除测试数据，请不要在生产环境中运行
- 如果测试中断，可能会留下测试数据，请手动清理
- 测试需要适当的权限才能运行，请确保使用的 API 密钥具有足够的权限
