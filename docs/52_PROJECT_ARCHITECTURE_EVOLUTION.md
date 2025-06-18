# QuantDB 项目架构演进规划

**版本**: v2.0-architecture | **目标**: 多模式部署架构 | **策略**: 渐进式演进

## 🎯 架构演进目标

### 当前状态 (v1.x)
- ✅ 后端API服务 (FastAPI)
- ✅ 前端展示应用 (Streamlit)
- ✅ 数据库和缓存系统 (SQLite + 智能缓存)

### 目标状态 (v2.x)
1. **🔧 后端API服务** - 独立的API服务，可单独部署和调用
2. **👨‍💼 管理后台** - Admin管理界面，数据管理和系统监控
3. **🌐 前端SaaS应用** - 独立的用户体验应用，可公开访问

## 🏗️ 推荐项目结构

```
quantdb/
├── README.md                           # 项目总览
├── docker-compose.yml                  # 多服务编排
├── .env.example                        # 环境变量模板
├── 
├── core/                              # 🔥 核心业务逻辑层
│   ├── __init__.py
│   ├── models/                        # 数据模型
│   │   ├── __init__.py
│   │   ├── asset.py
│   │   ├── stock_data.py
│   │   └── system_metrics.py
│   ├── services/                      # 业务服务层
│   │   ├── __init__.py
│   │   ├── stock_data_service.py
│   │   ├── asset_info_service.py
│   │   ├── trading_calendar.py
│   │   └── cache_service.py
│   ├── database/                      # 数据库层
│   │   ├── __init__.py
│   │   ├── connection.py
│   │   ├── migrations/
│   │   └── schema.sql
│   ├── cache/                         # 缓存层
│   │   ├── __init__.py
│   │   ├── akshare_adapter.py
│   │   └── cache_manager.py
│   └── utils/                         # 工具函数
│       ├── __init__.py
│       ├── logger.py
│       ├── validators.py
│       └── helpers.py
│
├── api/                               # 🚀 后端API服务
│   ├── __init__.py
│   ├── main.py                        # FastAPI应用入口
│   ├── dependencies.py               # 依赖注入
│   ├── middleware.py                 # 中间件
│   ├── routes/                       # API路由
│   │   ├── __init__.py
│   │   ├── health.py
│   │   ├── stocks.py
│   │   ├── assets.py
│   │   ├── cache.py
│   │   └── admin.py
│   ├── schemas/                      # API数据模型
│   │   ├── __init__.py
│   │   ├── stock.py
│   │   ├── asset.py
│   │   └── response.py
│   ├── auth/                         # 认证授权
│   │   ├── __init__.py
│   │   ├── jwt_handler.py
│   │   └── permissions.py
│   ├── requirements.txt              # API服务依赖
│   ├── Dockerfile                    # API容器化
│   └── README.md                     # API服务文档
│
├── admin/                            # 👨‍💼 管理后台
│   ├── __init__.py
│   ├── app.py                        # Streamlit Admin应用
│   ├── pages/                        # 管理页面
│   │   ├── 1_📊_数据概览.py
│   │   ├── 2_🗄️_数据管理.py
│   │   ├── 3_⚡_系统监控.py
│   │   ├── 4_👥_用户管理.py
│   │   └── 5_⚙️_系统设置.py
│   ├── components/                   # 管理组件
│   │   ├── __init__.py
│   │   ├── data_table.py
│   │   ├── charts.py
│   │   └── forms.py
│   ├── auth/                         # 管理员认证
│   │   ├── __init__.py
│   │   └── admin_auth.py
│   ├── requirements.txt              # Admin依赖
│   ├── Dockerfile                    # Admin容器化
│   └── README.md                     # Admin使用文档
│
├── webapp/                           # 🌐 前端SaaS应用
│   ├── __init__.py
│   ├── app.py                        # 主应用入口
│   ├── pages/                        # 用户页面
│   │   ├── 1_📈_股票查询.py
│   │   ├── 2_📊_资产分析.py
│   │   ├── 3_📋_我的关注.py
│   │   └── 4_⚙️_个人设置.py
│   ├── components/                   # UI组件
│   │   ├── __init__.py
│   │   ├── stock_chart.py
│   │   ├── data_table.py
│   │   └── sidebar.py
│   ├── utils/                        # 前端工具
│   │   ├── __init__.py
│   │   ├── api_client.py
│   │   ├── session_manager.py
│   │   └── formatters.py
│   ├── auth/                         # 用户认证
│   │   ├── __init__.py
│   │   └── user_auth.py
│   ├── requirements.txt              # WebApp依赖
│   ├── Dockerfile                    # WebApp容器化
│   └── README.md                     # WebApp使用文档
│
├── cloud/                            # ☁️ 云端部署版本
│   ├── streamlit_cloud/             # Streamlit Cloud版本
│   │   ├── app.py                    # 单体应用
│   │   ├── pages/
│   │   ├── requirements.txt
│   │   └── README.md
│   ├── vercel/                       # Vercel部署版本
│   │   ├── api/
│   │   ├── package.json
│   │   └── vercel.json
│   └── docker/                       # Docker部署版本
│       ├── docker-compose.yml
│       ├── nginx.conf
│       └── README.md
│
├── database/                         # 🗄️ 数据库文件
│   ├── stock_data.db                # SQLite数据库
│   ├── schema.sql                   # 数据库结构
│   └── migrations/                  # 数据库迁移
│
├── tests/                           # 🧪 测试套件
│   ├── __init__.py
│   ├── conftest.py
│   ├── unit/                        # 单元测试
│   ├── integration/                 # 集成测试
│   ├── api/                         # API测试
│   └── e2e/                         # 端到端测试
│
├── docs/                            # 📚 项目文档
│   ├── api/                         # API文档
│   ├── admin/                       # 管理文档
│   ├── webapp/                      # 应用文档
│   ├── deployment/                  # 部署文档
│   └── architecture/               # 架构文档
│
├── scripts/                         # 🔧 管理脚本
│   ├── setup.py                     # 环境设置
│   ├── deploy.py                    # 部署脚本
│   ├── backup.py                    # 数据备份
│   └── migrate.py                   # 数据迁移
│
└── tools/                           # 🛠️ 开发工具
    ├── monitoring/                  # 监控工具
    ├── performance/                 # 性能测试
    └── data_import/                 # 数据导入工具
```

## 🚀 部署模式支持

### 1. 开发模式 (Development)
```bash
# 启动完整开发环境
docker-compose -f docker-compose.dev.yml up

# 或分别启动
cd api && uvicorn main:app --reload
cd admin && streamlit run app.py --server.port 8501
cd webapp && streamlit run app.py --server.port 8502
```

### 2. API服务模式 (API Only)
```bash
# 仅启动API服务
cd api && uvicorn main:app --host 0.0.0.0 --port 8000

# 或使用Docker
docker build -t quantdb-api ./api
docker run -p 8000:8000 quantdb-api
```

### 3. 管理后台模式 (Admin Only)
```bash
# 启动管理后台
cd admin && streamlit run app.py

# 或使用Docker
docker build -t quantdb-admin ./admin
docker run -p 8501:8501 quantdb-admin
```

### 4. SaaS应用模式 (WebApp Only)
```bash
# 启动前端应用
cd webapp && streamlit run app.py

# 或使用Docker
docker build -t quantdb-webapp ./webapp
docker run -p 8502:8502 quantdb-webapp
```

### 5. 云端单体模式 (Cloud Monolith)
```bash
# Streamlit Cloud部署
cd cloud/streamlit_cloud && streamlit run app.py
```

### 6. 完整生产模式 (Full Production)
```bash
# 使用docker-compose启动所有服务
docker-compose up -d

# 服务访问地址:
# API: http://localhost:8000
# Admin: http://localhost:8501  
# WebApp: http://localhost:8502
# Nginx: http://localhost:80
```

## 📋 演进实施计划

### 阶段1: 结构重组 (1周)
- [ ] 创建新的项目结构
- [ ] 将现有代码重新组织到core/目录
- [ ] 更新import路径和依赖关系
- [ ] 确保现有功能正常工作

### 阶段2: API服务独立化 (1周)
- [ ] 将FastAPI代码移动到api/目录
- [ ] 创建独立的API服务配置
- [ ] 添加API认证和权限控制
- [ ] 完善API文档和测试

### 阶段3: 管理后台开发 (2周)
- [ ] 创建admin/目录结构
- [ ] 开发数据管理界面
- [ ] 实现系统监控功能
- [ ] 添加用户管理功能

### 阶段4: SaaS应用开发 (2周)
- [ ] 创建webapp/目录结构
- [ ] 开发用户友好的前端界面
- [ ] 实现用户认证和个人设置
- [ ] 优化用户体验和性能

### 阶段5: 云端部署优化 (1周)
- [ ] 完善cloud/目录下的部署版本
- [ ] 优化Streamlit Cloud部署
- [ ] 添加Docker和Vercel部署支持
- [ ] 完善部署文档

### 阶段6: 生产环境准备 (1周)
- [ ] 配置nginx反向代理
- [ ] 添加SSL证书支持
- [ ] 实现日志和监控
- [ ] 性能优化和安全加固

## 🎯 架构优势

### 1. 模块化设计
- **核心业务逻辑复用**: core/目录可被所有应用共享
- **独立部署**: 每个服务可以独立部署和扩展
- **清晰职责**: API、Admin、WebApp各司其职

### 2. 灵活部署
- **按需部署**: 可以只部署需要的服务
- **多环境支持**: 开发、测试、生产环境配置分离
- **容器化**: 支持Docker容器化部署

### 3. 可扩展性
- **水平扩展**: API服务可以多实例部署
- **功能扩展**: 新功能可以独立开发和部署
- **技术栈灵活**: 不同服务可以使用不同技术栈

### 4. 维护性
- **代码复用**: 核心逻辑统一维护
- **独立测试**: 每个服务可以独立测试
- **版本管理**: 服务可以独立版本控制

这个架构设计既满足了你当前的Streamlit Cloud部署需求，又为未来的扩展提供了良好的基础。你觉得这个规划如何？需要我详细说明某个部分吗？
