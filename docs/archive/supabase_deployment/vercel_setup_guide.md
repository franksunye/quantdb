# Vercel 部署指南

## 文档信息
**文档类型**: 部署指南
**文档编号**: quantdb-DEPLOY-002
**版本**: 1.1.0
**创建日期**: 2025-05-15
**最后更新**: 2025-07-01
**状态**: 已发布
**负责人**: frank

## 1. 概述

本文档提供了在 Vercel 上部署 QuantDB API 的详细指南。Vercel 是一个面向前端开发者的云平台，提供了静态站点托管和无服务器函数的功能，非常适合部署 FastAPI 应用。

## 2. 前提条件

- Vercel 账户（可在 [https://vercel.com](https://vercel.com) 注册）
- GitHub 账户，并已将 QuantDB 代码推送到 GitHub 仓库
- 已完成 Supabase 设置（参见 [Supabase 部署指南](./supabase_setup_guide.md)）

## 3. 准备部署配置文件

在部署到 Vercel 之前，我们需要创建一些配置文件：

### 3.1 创建 vercel.json

在项目根目录创建 `vercel.json` 文件：

```json
{
  "version": 2,
  "builds": [
    {
      "src": "src/api/main.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "src/api/main.py"
    }
  ]
}
```

这个配置告诉 Vercel 使用 Python 运行时来构建我们的应用，并将所有请求路由到 `src/api/main.py`。

### 3.2 创建 requirements.txt

确保项目根目录有一个 `requirements.txt` 文件，包含所有必要的依赖：

```
fastapi==0.95.1
uvicorn==0.22.0
sqlalchemy==2.0.12
psycopg2-binary==2.9.6
python-dotenv==1.0.0
pydantic==2.0.3
pandas==2.0.1
numpy==1.24.3
requests==2.30.0
httpx==0.24.1
python-jose==3.3.0
passlib==1.7.4
bcrypt==4.0.1
```

### 3.3 创建 .env.example

创建一个 `.env.example` 文件，作为环境变量的模板：

```
# Database Configuration
DATABASE_URL=postgresql://postgres:[YOUR_PASSWORD]@db.[YOUR_PROJECT_ID].supabase.co:5432/postgres

# Supabase Configuration
SUPABASE_URL=https://[YOUR_PROJECT_ID].supabase.co
SUPABASE_KEY=[YOUR_SUPABASE_API_KEY]
SUPABASE_JWT_SECRET=[YOUR_SUPABASE_JWT_SECRET]

# API Configuration
API_PREFIX=/api/v1
DEBUG=False
ENVIRONMENT=production

# Security
SECRET_KEY=[GENERATE_A_SECURE_SECRET_KEY]
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Logging
LOG_LEVEL=INFO
```

## 4. 连接 GitHub 仓库

### 4.1 登录 Vercel

1. 访问 [https://vercel.com/dashboard](https://vercel.com/dashboard)
2. 使用您的账户登录

### 4.2 导入项目

1. 点击 "Add New" > "Project"
2. 从列表中选择您的 GitHub 仓库
   - 如果没有看到您的仓库，点击 "Adjust GitHub App Permissions" 并添加仓库
3. 点击 "Import"

## 5. 配置项目设置

### 5.1 基本设置

1. 项目导入后，配置以下设置：
   - **Project Name**: QuantDB（或您喜欢的名称）
   - **Framework Preset**: Other
   - **Root Directory**: ./
   - **Build Command**: `pip install -r requirements.txt`
   - **Output Directory**: 留空
   - **Install Command**: 留空

### 5.2 环境变量

1. 点击 "Environment Variables"
2. 添加以下变量（从 `.env.example` 复制，并填入实际值）：
   - `DATABASE_URL`: 您的 Supabase PostgreSQL 连接字符串
   - `SUPABASE_URL`: 您的 Supabase 项目 URL
   - `SUPABASE_KEY`: 您的 Supabase API 密钥
   - `SUPABASE_JWT_SECRET`: 您的 Supabase JWT 密钥
   - `SECRET_KEY`: 一个安全的随机字符串，用于 JWT 编码
   - `ENVIRONMENT`: `production`
   - `DEBUG`: `False`
   - `API_PREFIX`: `/api/v1`
   - `LOG_LEVEL`: `INFO`

3. 点击 "Save"

### 5.3 部署

1. 点击 "Deploy"
2. 等待部署完成

## 6. 验证部署

### 6.1 测试 API 端点

部署完成后：

1. 访问您的 Vercel 部署 URL（例如 `https://quantdb.vercel.app`）
2. 测试以下 API 端点：
   - 根端点：`https://quantdb.vercel.app/`
   - 健康检查：`https://quantdb.vercel.app/api/v1/health`
   - API 文档：`https://quantdb.vercel.app/api/v1/docs`

### 6.2 测试 MCP 端点

使用 curl 或 Postman 测试 MCP 端点：

```bash
curl -X POST https://quantdb.vercel.app/api/v1/mcp/query \
  -H "Content-Type: application/json" \
  -d '{"query": "查询平安银行的股价"}'
```

## 7. 配置自定义域名（可选）

### 7.1 添加域名

1. 在项目设置中，点击 "Domains" 选项卡
2. 点击 "Add" 并输入您的域名
3. 按照说明验证域名所有权
4. 配置 DNS 设置

### 7.2 配置 SSL

Vercel 会自动为您的域名配置 SSL 证书。

## 8. 设置持续部署

Vercel 会自动在您推送到主分支时部署。要自定义此行为：

1. 在项目设置中，点击 "Git" 选项卡
2. 配置生产分支和预览分支
3. 设置构建缓存（如需要）

## 9. 监控和日志

### 9.1 查看部署日志

1. 在项目仪表板中，点击最新的部署
2. 点击 "View Logs" 查看构建和部署日志

### 9.2 查看函数日志

1. 在项目仪表板中，点击 "Functions" 选项卡
2. 选择一个函数查看其日志和性能指标

### 9.3 设置警报（付费计划）

如果您使用付费计划，可以设置性能和错误警报：

1. 在项目设置中，点击 "Monitoring" 选项卡
2. 配置警报规则

## 10. 限制和注意事项

使用 Vercel 部署 FastAPI 应用时，需要注意以下限制：

- **冷启动**：无服务器函数可能会经历冷启动
- **执行时间**：Vercel 对无服务器函数有 10 秒的执行时间限制
- **内存**：每个函数限制为 1GB RAM
- **无状态**：函数是无状态的，不要依赖本地文件存储

## 11. 故障排除

### 11.1 部署失败

如果部署失败：

1. 检查 Vercel 仪表板中的构建日志
2. 确保所有依赖都正确指定
3. 验证环境变量是否正确设置
4. 检查是否有任何 Python 版本兼容性问题

### 11.2 API 问题

如果 API 不能按预期工作：

1. 检查 Vercel 仪表板中的函数日志
2. 确保数据库连接正常工作
3. 验证 API 路由是否正确配置
4. 检查是否有任何 CORS 问题（如果从前端访问）

## 12. 下一步

完成 Vercel 部署后：

1. 设置监控和警报
2. 配置自定义错误页面
3. 使用 GitHub Actions 实现 CI/CD 流程（参见 [CI/CD 设置指南](./ci_cd_setup_guide.md)）
4. 设置测试环境进行测试
