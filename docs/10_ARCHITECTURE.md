# QuantDB 系统架构

**版本**: v0.8.0-asset-enhanced | **状态**: 高性能智能缓存 + 增强资产档案 | **测试**: 186/186 通过

## 架构概述

QuantDB 采用简化架构设计，专注于高性能股票数据缓存服务，集成智能交易日历、实时监控系统和增强资产档案。

### 设计原则
- **简化优先**: 避免过度设计，选择简单可靠的解决方案
- **数据库作为缓存**: 使用 SQLite 作为主要数据存储和缓存
- **统一数据源**: 通过 AKShare 适配器获取股票数据
- **API优先**: 以 RESTful API 为核心的服务架构
- **🔥 数据质量第一**: 真实公司名称和财务指标，专业金融数据展示
- **🆕 实时监控**: 每个请求自动记录，核心价值可量化验证

## 核心组件

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   FastAPI   │    │  Services   │    │   SQLite    │
│   Routes    │───▶│   Layer     │───▶│  Database   │
└─────────────┘    └─────────────┘    └─────────────┘
       │                   │                   │
       │                   ▼                   │
       │           ┌─────────────┐             │
       │           │  AKShare    │             │
       └──────────▶│  Adapter    │─────────────┘
                   └─────────────┘

🆕 监控系统 (实时数据收集)
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ Monitoring  │    │ Monitoring  │    │ Monitoring  │
│ Middleware  │───▶│  Service    │───▶│   Tables    │
└─────────────┘    └─────────────┘    └─────────────┘
       ▲                                       │
       │                                       ▼
┌─────────────┐                       ┌─────────────┐
│ Every API   │                       │ Monitoring  │
│  Request    │                       │   Tools     │
└─────────────┘                       └─────────────┘
```

### 1. API层 (FastAPI)
- **路由管理**: 处理HTTP请求和响应
- **数据验证**: 使用Pydantic进行请求/响应验证
- **错误处理**: 统一的错误响应格式
- **文档生成**: 自动生成OpenAPI文档

### 2. 服务层 (Services)
- **StockDataService**: 股票数据获取、存储、查询
- **🔥 AssetInfoService**: 资产信息管理，从AKShare获取真实公司名称和财务指标
- **DatabaseCache**: 数据库缓存管理
- **🆕 MonitoringService**: 监控数据收集和分析

### 3. 数据层
- **SQLite数据库**: 主要数据存储
- **AKShare适配器**: 外部数据源接口
- **🆕 监控数据表**: request_logs, data_coverage, system_metrics

### 4. 🆕 监控系统
- **MonitoringMiddleware**: 自动拦截每个API请求
- **RequestMonitor**: 记录请求详情和性能数据
- **监控工具**: water_pool_monitor.py, system_performance_monitor.py

## 数据流程

### 数据获取流程
```
1. API请求 → 2. 服务层 → 3. 检查数据库缓存
                    ↓
4. 返回数据 ← 5. 合并数据 ← 6. 调用AKShare (如需要)
```

### 智能缓存策略
1. **检查现有数据**: 查询数据库中已有的数据范围
2. **确定缺失数据**: 计算需要从AKShare获取的日期范围
3. **批量获取**: 分组连续日期，减少API调用
4. **存储数据**: 将新数据保存到数据库
5. **返回结果**: 合并缓存和新数据

## 数据模型

### 核心表结构

**Assets (资产表) - 增强版**
```sql
CREATE TABLE assets (
    asset_id INTEGER PRIMARY KEY,
    symbol VARCHAR(10) UNIQUE NOT NULL,
    name VARCHAR(100),                  -- 真实公司名称
    asset_type VARCHAR(20),
    exchange VARCHAR(20),
    currency VARCHAR(10),

    -- 🆕 增强字段
    industry VARCHAR(100),              -- 行业分类
    concept VARCHAR(200),               -- 概念分类
    listing_date DATE,                  -- 上市日期
    total_shares BIGINT,                -- 总股本
    circulating_shares BIGINT,          -- 流通股
    market_cap BIGINT,                  -- 总市值
    pe_ratio REAL,                      -- 市盈率
    pb_ratio REAL,                      -- 市净率
    roe REAL,                           -- 净资产收益率
    last_updated DATETIME,              -- 最后更新时间
    data_source VARCHAR(20)             -- 数据来源
);
```

**Prices (价格表)**
```sql
CREATE TABLE prices (
    id INTEGER PRIMARY KEY,
    asset_id INTEGER REFERENCES assets(asset_id),
    date DATE NOT NULL,
    open DECIMAL(10,4),
    high DECIMAL(10,4),
    low DECIMAL(10,4),
    close DECIMAL(10,4),
    volume BIGINT,
    turnover DECIMAL(15,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 关键特性

### 1. 简化缓存
- **无复杂缓存层**: 直接使用数据库作为缓存
- **智能数据获取**: 只获取缺失的数据范围
- **持久化存储**: 数据永久保存，无过期问题

### 2. 错误处理
- **统一错误格式**: 所有API使用相同的错误响应结构
- **增强日志**: 详细的错误日志和调试信息
- **优雅降级**: 部分数据失败不影响整体服务

### 3. 测试覆盖
- **单元测试**: 77个单元测试覆盖核心逻辑 (含30个监控测试)
- **API测试**: 18个API测试验证接口功能
- **集成测试**: 端到端测试验证完整流程 (含6个监控集成测试)
- **监控测试**: 36个专门测试确保监控系统质量

## 性能特点

- **数据库查询优化**: 使用索引和批量操作
- **智能缓存**: 避免重复获取相同数据
- **同步处理**: 数据获取和缓存同步完成
- **轻量级架构**: 最小化组件依赖

## 扩展性

### 当前支持
- SQLite 开发环境
- AKShare 数据源
- RESTful API 接口

### 未来扩展 (已规划但暂缓)
- MCP 协议支持
- Supabase 云部署
- 多数据源支持
- 实时数据流
