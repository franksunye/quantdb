# QuantDB 项目文档

**版本**: v1.1.0-cloud-deployment | **更新**: 2025-06-18 | **状态**: Streamlit Cloud部署就绪

## 📚 文档导航

### 🎯 核心项目文档
- [00_BACKLOG.md](./00_BACKLOG.md) - 项目待办事项和开发计划
- [01_CHANGELOG.md](./01_CHANGELOG.md) - 版本更新日志

### 🏗️ 架构和设计文档
- [10_ARCHITECTURE.md](./10_ARCHITECTURE.md) - 系统架构设计
- [11_DATABASE.md](./11_DATABASE.md) - 数据库设计和模型

### 🚀 API和接口文档
- [20_API.md](./20_API.md) - API接口文档

### 🛠️ 开发和测试文档
- [30_DEVELOPMENT.md](./30_DEVELOPMENT.md) - 开发环境和规范
- [31_TESTING.md](./31_TESTING.md) - 测试策略和指南

### 📱 前端文档
- [40_FRONTEND.md](./40_FRONTEND.md) - 前端架构和组件
- [41_FRONTEND_BACKLOG.md](./41_FRONTEND_BACKLOG.md) - 前端开发计划

### ☁️ Streamlit Cloud部署文档
- [50_STREAMLIT_CLOUD_DEPLOYMENT_PLAN.md](./50_STREAMLIT_CLOUD_DEPLOYMENT_PLAN.md) - 部署方案设计
- [51_STREAMLIT_CLOUD_IMPLEMENTATION.md](./51_STREAMLIT_CLOUD_IMPLEMENTATION.md) - 实施指南
- [52_PROJECT_ARCHITECTURE_EVOLUTION.md](./52_PROJECT_ARCHITECTURE_EVOLUTION.md) - 架构演进规划
- [53_MIGRATION_IMPLEMENTATION_PLAN.md](./53_MIGRATION_IMPLEMENTATION_PLAN.md) - 迁移实施方案
- [54_STREAMLIT_CLOUD_DEPLOYMENT_REPORT.md](./54_STREAMLIT_CLOUD_DEPLOYMENT_REPORT.md) - 部署完成报告

### 🌏 港股支持文档（未来功能）
- [HONG_KONG_STOCK_ASSESSMENT.md](./HONG_KONG_STOCK_ASSESSMENT.md) - 港股支持技术评估
- [HONG_KONG_STOCK_IMPLEMENTATION_PLAN.md](./HONG_KONG_STOCK_IMPLEMENTATION_PLAN.md) - 港股实施计划
- [HONG_KONG_STOCK_QUICKSTART.md](./HONG_KONG_STOCK_QUICKSTART.md) - 港股快速开始
- [HONG_KONG_STOCK_COMPLETION_REPORT.md](./HONG_KONG_STOCK_COMPLETION_REPORT.md) - 港股完成报告

## 🎯 当前项目状态

### ✅ 已完成 (2025-06-18)
- **Streamlit Cloud部署第一阶段** - 云端单体应用开发完成
- **100%功能保留** - 股票查询、资产信息、系统监控
- **SQLite数据库支持** - 完整的数据持久化
- **本地测试通过** - 所有功能验证完成

### 🚀 当前任务
- **CLOUD-005**: Streamlit Cloud实际部署
- **部署验证**: 云端功能完整性测试
- **用户反馈收集**: 公开体验版本优化

### 📋 后续规划
1. **第二阶段**: 架构重构和多服务支持
2. **港股支持**: 多市场数据支持
3. **高级功能**: 用户管理、实时数据、高级分析

## 📖 快速开始

### 本地开发
```bash
# 克隆项目
git clone https://github.com/franksunye/quantdb.git
cd quantdb

# 安装依赖
pip install -r requirements.txt

# 启动后端API
python src/api/main.py

# 启动前端（新终端）
cd quantdb_frontend
streamlit run app.py
```

### Streamlit Cloud版本
```bash
# 进入云端版本目录
cd cloud/streamlit_cloud

# 安装依赖
pip install -r requirements.txt

# 运行应用
streamlit run app.py
```

## 🔗 相关链接

- **GitHub仓库**: https://github.com/franksunye/quantdb
- **部署分支**: `streamlit-cloud-deployment`
- **云端应用路径**: `cloud/streamlit_cloud/app.py`

## 📝 文档维护

### 文档更新原则
1. **保持同步**: 文档与代码实现保持同步
2. **版本控制**: 重要变更记录在CHANGELOG中
3. **敏捷精简**: 避免过度文档化，保持核心内容
4. **用户导向**: 文档服务于开发和使用需求

### 文档编号规则
- **00-09**: 项目管理文档
- **10-19**: 架构设计文档
- **20-29**: API和接口文档
- **30-39**: 开发和测试文档
- **40-49**: 前端相关文档
- **50-59**: 部署相关文档
- **其他**: 特定功能或评估文档

---

**维护者**: frank | **最后更新**: 2025-06-18
