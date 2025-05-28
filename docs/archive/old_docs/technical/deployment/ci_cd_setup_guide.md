# CI/CD 设置指南

## 文档信息
**文档类型**: 部署指南
**文档编号**: quantdb-DEPLOY-003
**版本**: 1.1.0
**创建日期**: 2025-05-15
**最后更新**: 2025-07-01
**状态**: 已发布
**负责人**: frank

## 1. 概述

本文档提供了为 QuantDB 项目设置持续集成和持续部署 (CI/CD) 流程的详细指南。CI/CD 流程可以自动化测试、构建和部署过程，提高开发效率和代码质量。

## 2. 前提条件

- GitHub 账户，并已将 QuantDB 代码推送到 GitHub 仓库
- 已完成 Supabase 设置（参见 [Supabase 部署指南](./supabase_setup_guide.md)）
- 已完成 Vercel 设置（参见 [Vercel 部署指南](./vercel_setup_guide.md)）

## 3. GitHub Actions 设置

GitHub Actions 是 GitHub 提供的 CI/CD 工具，可以直接在 GitHub 仓库中配置和运行工作流。

### 3.1 创建工作流目录

在项目根目录创建 `.github/workflows` 目录：

```bash
mkdir -p .github/workflows
```

### 3.2 创建 CI 工作流

创建 `.github/workflows/ci.yml` 文件：

```yaml
name: CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:13
        env:
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_db
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Create test directories
      run: |
        mkdir -p data/raw
        mkdir -p data/processed
        mkdir -p logs
        mkdir -p database
    
    - name: Run tests
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test_db
        API_PREFIX: /api/v1
        DEBUG: 'True'
        ENVIRONMENT: testing
        SECRET_KEY: testsecretkey123456789
      run: |
        pytest --cov=src tests/
    
    - name: Upload coverage report
      uses: codecov/codecov-action@v3
      with:
        token: ${{ secrets.CODECOV_TOKEN }}
        file: ./coverage.xml
        flags: unittests
        name: codecov-umbrella
        fail_ci_if_error: false

  lint:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install flake8 black isort
    
    - name: Lint with flake8
      run: |
        flake8 src tests --count --select=E9,F63,F7,F82 --show-source --statistics
    
    - name: Check formatting with black
      run: |
        black --check src tests
    
    - name: Check imports with isort
      run: |
        isort --check-only --profile black src tests
```

### 3.3 创建 CD 工作流

创建 `.github/workflows/cd.yml` 文件：

```yaml
name: CD

on:
  push:
    branches: [ main ]
    tags:
      - 'v*'

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: Run tests
      env:
        DATABASE_URL: ${{ secrets.TEST_DATABASE_URL }}
        API_PREFIX: /api/v1
        DEBUG: 'False'
        ENVIRONMENT: production
        SECRET_KEY: ${{ secrets.SECRET_KEY }}
      run: |
        pytest tests/
    
    - name: Deploy to Vercel
      uses: amondnet/vercel-action@v20
      with:
        vercel-token: ${{ secrets.VERCEL_TOKEN }}
        vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
        vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
        vercel-args: '--prod'
```

## 4. 配置 GitHub Secrets

为了安全地使用敏感信息，我们需要在 GitHub 仓库中设置 Secrets：

1. 在 GitHub 仓库页面，点击 "Settings" > "Secrets" > "Actions"
2. 点击 "New repository secret"
3. 添加以下 Secrets：
   - `TEST_DATABASE_URL`: 测试数据库的连接字符串
   - `SECRET_KEY`: 用于 JWT 编码的密钥
   - `CODECOV_TOKEN`: Codecov 的访问令牌（可选）
   - `VERCEL_TOKEN`: Vercel 的 API 令牌
   - `VERCEL_ORG_ID`: Vercel 组织 ID
   - `VERCEL_PROJECT_ID`: Vercel 项目 ID

## 5. 获取 Vercel 部署凭证

### 5.1 获取 Vercel API 令牌

1. 访问 [https://vercel.com/account/tokens](https://vercel.com/account/tokens)
2. 点击 "Create" 创建新令牌
3. 输入令牌名称（例如 "GitHub Actions"）
4. 复制生成的令牌并保存为 GitHub Secret `VERCEL_TOKEN`

### 5.2 获取 Vercel 组织 ID 和项目 ID

1. 安装 Vercel CLI：`npm i -g vercel`
2. 登录 Vercel：`vercel login`
3. 链接项目：`vercel link`
4. 查看 `.vercel/project.json` 文件，获取 `orgId` 和 `projectId`
5. 将这些值保存为 GitHub Secrets `VERCEL_ORG_ID` 和 `VERCEL_PROJECT_ID`

## 6. 配置代码覆盖率报告（可选）

### 6.1 设置 Codecov

1. 访问 [https://codecov.io](https://codecov.io) 并使用 GitHub 账户登录
2. 添加您的仓库
3. 获取 Codecov 令牌并保存为 GitHub Secret `CODECOV_TOKEN`

### 6.2 配置 pytest

创建 `pytest.ini` 文件：

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_functions = test_*
python_classes = Test*
addopts = --cov=src --cov-report=xml
```

## 7. 配置代码质量检查

### 7.1 配置 Flake8

创建 `.flake8` 文件：

```ini
[flake8]
max-line-length = 100
exclude = .git,__pycache__,build,dist
```

### 7.2 配置 Black

创建 `pyproject.toml` 文件：

```toml
[tool.black]
line-length = 100
target-version = ['py39']
include = '\.pyi?$'
exclude = '''
/(
    \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | _build
  | buck-out
  | build
  | dist
)/
'''
```

### 7.3 配置 isort

在 `pyproject.toml` 文件中添加：

```toml
[tool.isort]
profile = "black"
line_length = 100
```

## 8. 分支策略

为了有效地使用 CI/CD 流程，我们建议采用以下分支策略：

### 8.1 主要分支

- `main`: 生产环境代码，只接受来自 `develop` 的合并和热修复
- `develop`: 开发环境代码，接受功能分支的合并

### 8.2 辅助分支

- `feature/*`: 新功能开发，从 `develop` 分支出，完成后合并回 `develop`
- `bugfix/*`: 错误修复，从 `develop` 分支出，完成后合并回 `develop`
- `hotfix/*`: 紧急修复，从 `main` 分支出，完成后同时合并到 `main` 和 `develop`
- `release/*`: 发布准备，从 `develop` 分支出，完成后合并到 `main` 和 `develop`

## 9. 工作流程

### 9.1 开发新功能

1. 从 `develop` 创建新的功能分支：`git checkout -b feature/new-feature develop`
2. 开发功能并提交更改
3. 推送分支到 GitHub：`git push origin feature/new-feature`
4. 创建 Pull Request 到 `develop` 分支
5. CI 工作流会自动运行测试和代码质量检查
6. 代码审查通过后，合并 Pull Request
7. 删除功能分支

### 9.2 发布新版本

1. 从 `develop` 创建发布分支：`git checkout -b release/v1.0.0 develop`
2. 进行最终测试和修复
3. 更新版本号和文档
4. 推送分支到 GitHub：`git push origin release/v1.0.0`
5. 创建 Pull Request 到 `main` 分支
6. CI 工作流会自动运行测试
7. 代码审查通过后，合并 Pull Request
8. 在 `main` 分支上创建标签：`git tag -a v1.0.0 -m "Version 1.0.0"`
9. 推送标签：`git push origin v1.0.0`
10. CD 工作流会自动部署到生产环境
11. 将发布分支合并回 `develop`：`git checkout develop && git merge release/v1.0.0`
12. 删除发布分支

## 10. 监控和通知

### 10.1 设置 GitHub 通知

1. 在 GitHub 仓库页面，点击 "Settings" > "Notifications"
2. 配置工作流程运行结果的通知设置

### 10.2 设置 Slack 通知（可选）

1. 在 Slack 中创建一个新的应用和 Webhook
2. 在 `.github/workflows/ci.yml` 和 `.github/workflows/cd.yml` 中添加 Slack 通知步骤

## 11. 故障排除

### 11.1 CI 工作流失败

如果 CI 工作流失败：

1. 检查 GitHub Actions 日志以了解失败原因
2. 修复问题并推送更改
3. 重新运行工作流

### 11.2 CD 工作流失败

如果 CD 工作流失败：

1. 检查 GitHub Actions 日志以了解失败原因
2. 验证 Vercel 凭证是否正确
3. 检查测试是否通过
4. 修复问题并推送更改
5. 重新运行工作流

## 12. 下一步

完成 CI/CD 设置后：

1. 定期更新依赖
2. 监控代码覆盖率和代码质量
3. 优化工作流程以减少构建时间
4. 考虑添加更多自动化测试
