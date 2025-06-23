# 分支管理规范

## 🌿 分支结构

```
main                    # 稳定发布分支 (生产环境)
├── develop            # 开发集成分支 (默认开发分支)
├── feature/*          # 功能开发分支
├── hotfix/*           # 紧急修复分支
└── release/*          # 发布准备分支
```

## 📋 分支说明

### main 分支
- **用途**: 生产环境稳定版本
- **保护**: 只接受来自 develop 和 hotfix 的合并
- **标签**: 所有版本标签都在此分支创建
- **部署**: 自动部署到生产环境

### develop 分支  
- **用途**: 日常开发集成分支
- **来源**: 从 main 分支创建
- **合并**: 接受 feature 分支的合并请求
- **测试**: 持续集成测试

### feature/* 分支
- **命名**: `feature/功能名称` (如 `feature/hk-stock-support`)
- **来源**: 从 develop 分支创建
- **生命周期**: 功能完成后合并到 develop 并删除
- **示例**: `feature/monitoring-dashboard`

### hotfix/* 分支
- **命名**: `hotfix/问题描述` (如 `hotfix/api-timeout-fix`)
- **来源**: 从 main 分支创建
- **紧急性**: 用于生产环境紧急修复
- **合并**: 同时合并到 main 和 develop

### release/* 分支
- **命名**: `release/版本号` (如 `release/v2.1.0`)
- **来源**: 从 develop 分支创建
- **用途**: 发布前的最后准备和测试
- **合并**: 完成后合并到 main 并标记版本

## 🔄 工作流程

### 日常开发流程
```bash
# 1. 创建功能分支
git checkout develop
git pull origin develop
git checkout -b feature/new-feature

# 2. 开发和提交
git add .
git commit -m "feat: 添加新功能"

# 3. 推送并创建PR
git push origin feature/new-feature
# 在GitHub创建PR: feature/new-feature -> develop
```

### 发布流程
```bash
# 1. 创建发布分支
git checkout develop
git checkout -b release/v2.1.0

# 2. 发布准备 (版本号更新、文档更新)
# 更新版本信息、运行测试

# 3. 合并到main并标记
git checkout main
git merge release/v2.1.0
git tag -a v2.1.0 -m "Release v2.1.0"
git push origin main --tags

# 4. 合并回develop
git checkout develop
git merge release/v2.1.0
git push origin develop

# 5. 删除发布分支
git branch -d release/v2.1.0
```

### 紧急修复流程
```bash
# 1. 创建hotfix分支
git checkout main
git checkout -b hotfix/critical-bug-fix

# 2. 修复和测试
git add .
git commit -m "fix: 修复关键bug"

# 3. 合并到main
git checkout main
git merge hotfix/critical-bug-fix
git tag -a v2.0.1 -m "Hotfix v2.0.1"
git push origin main --tags

# 4. 合并到develop
git checkout develop
git merge hotfix/critical-bug-fix
git push origin develop

# 5. 删除hotfix分支
git branch -d hotfix/critical-bug-fix
```

## 🛡️ 分支保护规则

### main 分支保护
- 禁止直接推送
- 要求PR审查
- 要求状态检查通过
- 要求分支为最新

### develop 分支保护
- 要求PR审查
- 要求CI测试通过
- 允许管理员绕过

## 📝 提交信息规范

```
类型(范围): 简短描述

详细描述 (可选)

关联问题: #123
```

### 提交类型
- `feat`: 新功能
- `fix`: 修复bug
- `docs`: 文档更新
- `style`: 代码格式调整
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建过程或辅助工具变动

### 示例
```
feat(api): 添加港股数据支持

- 扩展AKShare适配器支持5位港股代码
- 添加港股数据验证逻辑
- 更新API文档

关联问题: #45
```

## 🚀 快速命令

```bash
# 查看所有分支
git branch -a

# 切换到开发分支
git checkout develop

# 创建功能分支
git checkout -b feature/功能名称

# 同步远程分支
git fetch origin
git pull origin develop

# 删除已合并的分支
git branch -d feature/已完成功能
```

## 📊 分支状态检查

定期检查分支健康状态：
- 清理已合并的功能分支
- 确保develop与main同步
- 检查长期未合并的分支
- 验证分支保护规则有效性
