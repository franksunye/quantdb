# Supabase Management API 使用指南

本文档提供了关于如何使用 Supabase Management API 进行自动化操作的指南。

## 概述

Supabase Management API 是一个强大的工具，允许您以编程方式管理 Supabase 项目、数据库、API 密钥和其他资源。这使您能够自动化许多通常需要通过 Supabase 仪表板手动执行的操作。

## 个人访问令牌 (Personal Access Token)

要使用 Supabase Management API，您需要一个个人访问令牌 (Personal Access Token, PAT)。这与项目的 API 密钥或服务角色密钥不同。

### 获取个人访问令牌

1. 登录到 [Supabase 仪表板](https://app.supabase.com)
2. 点击右上角的个人资料图标，然后选择 "Account"
3. 在左侧菜单中，选择 "Access Tokens"
4. 点击 "Generate New Token"
5. 输入令牌名称（例如 "QuantDB Management"）
6. 选择适当的权限（通常需要所有权限）
7. 点击 "Generate"
8. 复制生成的令牌（这是唯一一次显示完整令牌的机会）

### 配置个人访问令牌

将令牌添加到您的 `.env` 文件中：

```
SUPABASE_ACCESS_TOKEN=your_personal_access_token
```

## 使用 Supabase Management API

一旦您配置了个人访问令牌，您就可以使用我们的 Supabase 自动化工具来管理您的项目。

### 测试连接

首先，测试您的连接是否正常工作：

```bash
python -m scripts.test_supabase_management_api
```

如果一切正常，您应该看到所有测试都通过了。

### 使用自动化工具

现在您可以使用我们的自动化工具来管理您的 Supabase 项目：

```bash
# 列出所有项目
python -m scripts.supabase_cli project list

# 获取项目详情
python -m scripts.supabase_cli project get your_project_ref

# 重置数据库密码
python -m scripts.supabase_cli db reset-password your_project_ref --update-env

# 执行 SQL 查询
python -m scripts.supabase_cli db sql your_project_ref "SELECT NOW();"
```

## 常见问题

### 无效签名错误

如果您收到 "invalid signature" 错误，这通常意味着您正在使用项目的 API 密钥或服务角色密钥，而不是个人访问令牌。确保您使用的是从 Supabase 仪表板的 "Access Tokens" 页面生成的个人访问令牌。

### 权限错误

如果您收到权限错误，确保您的个人访问令牌具有执行所请求操作的适当权限。您可能需要生成一个具有更多权限的新令牌。

### 令牌过期

个人访问令牌可能会过期。如果您的令牌过期，您需要生成一个新的令牌并更新您的 `.env` 文件。

## 部署注意事项

在部署环境中使用 Supabase Management API 时，请确保：

1. 个人访问令牌安全存储，不要在代码中硬编码
2. 在 CI/CD 环境中，将令牌设置为环境变量
3. 定期轮换令牌以提高安全性

## 限制

Supabase Management API 有一些限制：

1. 某些操作可能受到速率限制
2. 某些高级功能可能仅适用于付费计划
3. API 可能会随着时间的推移而变化，请关注 Supabase 的更新

## 结论

使用 Supabase Management API 和我们的自动化工具，您可以以编程方式管理您的 Supabase 基础设施，而不是通过手动仪表板交互。这使您能够自动化部署、配置和管理过程，提高效率和一致性。

请记住，要使用这些工具，您需要一个个人访问令牌，而不是项目的 API 密钥或服务角色密钥。
