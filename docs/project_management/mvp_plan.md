# QuantDB MVP 计划

> **版本**: v1.0.0  
> **创建日期**: 2025-05-13  
> **负责人**: frank  
> **状态**: 规划中

## 1. MVP 概述

### 1.1 目标

开发并部署 QuantDB 的最小可行产品(MVP)，实现从本地开发到公网部署的端到端流程，验证核心功能和技术架构。

### 1.2 MVP 范围

本 MVP 将聚焦于以下核心功能:

1. **基础数据服务**: 提供股票日线数据的获取、存储和查询功能
2. **简单 MCP 协议实现**: 支持基本的自然语言到结构化查询的转换
3. **REST API 接口**: 提供基本的数据查询 API
4. **简单 Web 界面**: 提供基本的数据可视化和查询界面
5. **云端部署**: 将服务部署到公网，可供远程访问

### 1.3 技术选型

| 组件 | 本地开发 | 云端部署 | 说明 |
|-----|---------|---------|-----|
| 后端框架 | FastAPI | FastAPI | 高性能异步 API 框架 |
| 数据库 | SQLite | Supabase (PostgreSQL) | 本地开发使用 SQLite，云端使用 Supabase |
| 前端框架 | React | React | 流行的前端框架 |
| 部署平台 | 本地 | Vercel | 前端部署到 Vercel |
| API 托管 | 本地 | Vercel Serverless Functions | 后端 API 部署到 Vercel |
| 数据存储 | 本地文件 | Supabase Storage | 大文件存储 |
| 认证服务 | 无 | Supabase Auth | 用户认证 |

## 2. 用户故事

### 2.1 数据查询场景

**故事 1**: 作为一个投资者，我想通过自然语言查询股票数据，以便快速获取我需要的信息。
- 验收标准:
  - 能够理解"显示上证指数最近30天的走势"这样的查询
  - 返回正确的数据结果
  - 以图表形式展示结果

**故事 2**: 作为一个分析师，我想通过 API 获取股票历史数据，以便进行进一步分析。
- 验收标准:
  - 提供 REST API 接口获取股票历史数据
  - 支持日期范围、股票代码等参数
  - 返回标准格式的 JSON 数据

**故事 3**: 作为一个用户，我想在网页上浏览和搜索股票数据，以便了解市场情况。
- 验收标准:
  - 提供简洁的 Web 界面
  - 支持股票搜索功能
  - 显示基本的股票信息和价格图表

## 3. 技术架构

### 3.1 系统组件

```
                  ┌─────────────┐
                  │   Web 界面   │
                  │   (React)   │
                  └──────┬──────┘
                         │
                         ▼
┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│  MCP 解析器  │◄──┤  REST API   │◄──┤ 认证服务    │
│  (FastAPI)  │   │  (FastAPI)  │   │ (Supabase) │
└──────┬──────┘   └──────┬──────┘   └─────────────┘
       │                 │
       ▼                 ▼
┌─────────────┐   ┌─────────────┐
│ 数据服务层   │   │   数据库     │
│ (Python)    │◄──┤ (PostgreSQL)│
└─────────────┘   └─────────────┘
```

### 3.2 数据流

1. 用户通过 Web 界面或 API 发送请求
2. 请求经过认证服务验证
3. 对于自然语言请求，MCP 解析器将其转换为结构化查询
4. 数据服务层处理查询，从数据库获取数据
5. 结果返回给用户

## 4. 开发计划

### 4.1 Sprint 1: 基础设施搭建 (1周)

| ID | 任务 | 估计(天) | 负责人 | 优先级 |
|----|-----|---------|-------|-------|
| 1.1 | 设置 Supabase 项目 | 0.5 | TBD | 高 |
| 1.2 | 设置 Vercel 项目 | 0.5 | TBD | 高 |
| 1.3 | 创建数据库模式 | 1 | TBD | 高 |
| 1.4 | 设置本地开发环境 | 1 | TBD | 高 |
| 1.5 | 创建 CI/CD 流程 | 2 | TBD | 中 |

**交付物**:
- 可用的 Supabase 项目
- 可用的 Vercel 项目
- 初始数据库结构
- 本地开发环境配置文档
- 基本的 CI/CD 流程

### 4.2 Sprint 2: 后端开发 (2周)

| ID | 任务 | 估计(天) | 负责人 | 优先级 |
|----|-----|---------|-------|-------|
| 2.1 | 开发数据库适配层 | 2 | TBD | 高 |
| 2.2 | 实现基本的 MCP 解析器 | 3 | TBD | 高 |
| 2.3 | 开发 REST API 端点 | 2 | TBD | 高 |
| 2.4 | 实现数据获取服务 | 2 | TBD | 高 |
| 2.5 | 编写单元测试 | 1 | TBD | 中 |

**交付物**:
- 可用的数据库适配层
- 基本的 MCP 解析器
- REST API 端点
- 数据获取服务
- 单元测试

### 4.3 Sprint 3: 前端开发 (2周)

| ID | 任务 | 估计(天) | 负责人 | 优先级 |
|----|-----|---------|-------|-------|
| 3.1 | 创建基本 UI 组件 | 2 | TBD | 高 |
| 3.2 | 实现股票搜索功能 | 1 | TBD | 高 |
| 3.3 | 开发数据可视化组件 | 3 | TBD | 高 |
| 3.4 | 实现自然语言查询界面 | 2 | TBD | 中 |
| 3.5 | 前端单元测试 | 1 | TBD | 中 |
| 3.6 | 响应式设计适配 | 1 | TBD | 低 |

**交付物**:
- 基本 UI 组件库
- 股票搜索功能
- 数据可视化组件
- 自然语言查询界面
- 前端单元测试

### 4.4 Sprint 4: 集成与部署 (1周)

| ID | 任务 | 估计(天) | 负责人 | 优先级 |
|----|-----|---------|-------|-------|
| 4.1 | 前后端集成 | 1 | TBD | 高 |
| 4.2 | 部署到 Vercel | 1 | TBD | 高 |
| 4.3 | 配置 Supabase 数据库 | 1 | TBD | 高 |
| 4.4 | 端到端测试 | 1 | TBD | 高 |
| 4.5 | 性能优化 | 1 | TBD | 中 |

**交付物**:
- 完整的集成系统
- 公网可访问的应用
- 端到端测试报告
- 性能测试报告

## 5. 技术债务与风险

### 5.1 技术债务

1. **数据库适配**: MVP 阶段从 SQLite 迁移到 PostgreSQL 可能需要特殊处理
2. **安全性**: 初始版本可能缺乏完整的安全措施
3. **错误处理**: 可能需要更完善的错误处理机制
4. **文档**: 初始文档可能不完整

### 5.2 风险

| 风险 | 影响 | 可能性 | 缓解策略 |
|-----|-----|-------|---------|
| 数据库迁移问题 | 高 | 中 | 使用 ORM 框架，提前测试兼容性 |
| API 限流 | 中 | 高 | 实现本地缓存，错峰请求 |
| 部署环境问题 | 高 | 低 | 提前熟悉 Vercel 和 Supabase 部署流程 |
| 性能问题 | 中 | 中 | 进行性能测试，实现分页和缓存 |

## 6. 成功指标

1. **功能完成度**: 所有核心功能按计划完成
2. **部署成功**: 应用成功部署到公网并可访问
3. **性能指标**: API 响应时间 < 500ms
4. **用户体验**: 基本功能可用，界面友好

## 7. 后续计划

MVP 成功后，计划在以下方向继续迭代:

1. **增强 MCP 协议**: 支持更复杂的自然语言查询
2. **扩展数据源**: 增加更多金融数据源
3. **高级分析功能**: 添加技术指标和分析工具
4. **用户管理**: 完善用户注册、登录和权限管理
5. **移动端适配**: 优化移动设备体验

## 8. 资源需求

1. **开发资源**: 1-2 名全栈开发者
2. **云服务账户**: Vercel 和 Supabase 账户
3. **数据源**: 股票数据 API 访问权限
4. **开发工具**: 代码编辑器、Git、测试工具等

---

## 附录: 技术栈详情

### 后端技术栈

- **语言**: Python 3.9+
- **Web 框架**: FastAPI
- **ORM**: SQLAlchemy
- **数据处理**: Pandas, NumPy
- **测试**: Pytest

### 前端技术栈

- **框架**: React
- **UI 库**: Material-UI 或 Ant Design
- **状态管理**: Redux 或 Context API
- **图表库**: Chart.js 或 Echarts
- **测试**: Jest, React Testing Library

### 云服务

- **Vercel**: 前端和 Serverless Functions 部署
- **Supabase**: 
  - PostgreSQL 数据库
  - 认证服务
  - 存储服务
