# QuantDB 技术指南

本目录包含 QuantDB 项目的技术指南和设置说明文档。这些文档提供了有关如何设置、配置和使用 QuantDB 系统各个组件的详细信息。

## 文档目录

### 开发指南

- [开发者指南](developer_guide.md) - QuantDB 开发者指南，包含项目结构和核心组件
- [测试指南](testing_guide.md) - 测试流程、测试类型和最佳实践（参见 `/docs/05_testing_approach.md` 了解高级测试策略）

### 数据源集成

- [AKShare 使用指南](akshare_usage_guide.md) - 如何使用 AKShare 获取金融数据

### 开发环境

- [开发环境设置](development_environment.md) - 设置 QuantDB 开发环境的指南

### 基础设施

- [Supabase 设置](supabase_setup.md) - 如何设置和配置 Supabase 数据库
- [Vercel 设置](vercel_setup.md) - 如何在 Vercel 上部署 QuantDB
- [CI/CD 设置](ci_cd_setup.md) - 持续集成和部署流程设置

## 使用指南

### 开发入门

1. 首先阅读 [开发者指南](developer_guide.md) 文档，了解项目结构和核心组件
2. 参考 [测试指南](testing_guide.md) 了解如何编写和运行测试
3. 按照 [开发环境设置](development_environment.md) 文档设置基本的开发环境

### 数据源和数据库

1. 根据需要设置 [Supabase](supabase_setup.md) 数据库
2. 如果需要使用 AKShare 获取数据，请参考 [AKShare 使用指南](akshare_usage_guide.md)

### 部署流程

1. 了解 [CI/CD 设置](ci_cd_setup.md) 文档中的持续集成和部署流程
2. 按照 [Vercel 设置](vercel_setup.md) 文档中的说明部署应用

## 文档维护

这些技术文档应定期更新，以反映系统的最新状态和最佳实践。如果您发现任何文档过时或不准确，请更新文档或通知团队。
