# QuantDB 待办事项

**状态**: SQLite开发版本稳定运行 | **测试**: 80/80 通过 | **更新**: 2025-05-28

## 🎯 当前优先级

✅ **所有主要任务已完成**

1. ✅ 代码整理和精简 - 架构简化完成
2. ✅ 文档整理和更新 - 精简文档完成
3. ✅ SQLite版本稳定化 - 所有功能正常

## 📊 项目状态

- **版本**: v0.6.0-sqlite
- **架构**: 简化架构完成
- **测试**: 80/80 核心功能测试通过
- **文档**: 70+ 文档精简到8个核心文档
- **代码**: 减少30%，移除15+冗余文件

## 📊 MVP功能评估 (2025-05-28)

**当前MVP评分**: 7/10分
**核心价值**: AKShare + 数据库缓存 ✅
**架构状态**: 简化架构完成，易于维护 ✅

### ✅ 已实现核心功能
- 历史股票数据获取 (对应 AKShare `stock_zh_a_hist`)
- 智能数据库缓存层 (AKShare没有的增值功能)
- RESTful API接口 (AKShare没有的增值功能)
- 数据导入和后台任务管理

### ⚠️ 当前限制
- 数据范围：仅A股历史数据
- 实时性：缺少实时行情数据
- 分析能力：缺少财务和基本面数据

## 🔴 高优先级扩展 (MVP增强)

### 1. 实时行情数据
- [ ] 添加实时行情API端点 `GET /api/v1/realtime/stock/{symbol}`
- [ ] 集成AKShare的 `stock_zh_a_spot_em()` 功能
- [ ] 实现实时数据缓存策略 (短期缓存)
- [ ] 添加实时数据的API测试

### 2. 多周期历史数据
- [ ] 支持分钟线数据 `GET /api/v1/historical/stock/{symbol}?period=1m`
- [ ] 支持周线、月线数据
- [ ] 扩展数据库模型支持多周期
- [ ] 优化不同周期的缓存策略

### 3. 基础财务数据
- [ ] 资产负债表 `GET /api/v1/financial/stock/{symbol}?report=balance_sheet`
- [ ] 利润表 `GET /api/v1/financial/stock/{symbol}?report=income`
- [ ] 现金流量表 `GET /api/v1/financial/stock/{symbol}?report=cashflow`
- [ ] 设计财务数据表结构

## 🟡 中优先级扩展 (功能完善)

### 4. 股票基础信息
- [ ] 股票列表API `GET /api/v1/stocks/list`
- [ ] 股票基本信息 `GET /api/v1/stocks/{symbol}/info`
- [ ] 行业分类和板块信息
- [ ] 股票搜索功能

### 5. 分红配股数据
- [ ] 分红历史 `GET /api/v1/dividend/stock/{symbol}`
- [ ] 配股信息
- [ ] 股本变动历史

### 6. 技术指标计算
- [ ] 移动平均线 `GET /api/v1/indicators/stock/{symbol}?indicator=ma`
- [ ] MACD、RSI等常用指标
- [ ] 自定义指标计算

## 🟢 中期优化 (可选)

- 性能优化 (数据库查询、API响应)
- 代码质量提升 (pylint, mypy, pre-commit)
- 监控和日志优化
- API响应缓存和压缩

## 🔵 低优先级扩展 (未来考虑)

### 7. 多市场支持
- [ ] 港股数据 `GET /api/v1/historical/hk/{symbol}`
- [ ] 美股数据 `GET /api/v1/historical/us/{symbol}`
- [ ] 多市场数据统一管理

### 8. 宏观经济数据
- [ ] GDP、CPI等宏观指标 `GET /api/v1/macro/gdp`
- [ ] 行业数据和指数数据

### 9. 高级功能
- [ ] MCP协议支持
- [ ] Supabase云部署
- [ ] 实时数据流推送
- [ ] 数据可视化接口
