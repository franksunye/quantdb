# QuantDB Cloud Edition

**🌟 云端版本** | **📊 股票数据平台** | **⚡ 智能缓存** | **☁️ 随时访问**

## 🎯 项目简介

QuantDB Cloud Edition 是专为 Streamlit Cloud 优化的股票数据查询平台，提供：

- 📈 **股票数据查询**: 支持A股历史数据查询和多维度图表展示
- 📊 **资产信息展示**: 真实公司名称、财务指标、市场数据
- ⚡ **智能缓存**: SQLite数据库持久化缓存，98.1%性能提升
- 🎨 **专业图表**: 基于Plotly的交互式数据可视化

## 🚀 在线体验

**部署地址**: [即将发布]

## 💻 本地运行

```bash
# 克隆仓库
git clone https://github.com/franksunye/quantdb.git
cd quantdb

# 切换到云端分支
git checkout streamlit-cloud-deployment

# 进入云端应用目录
cd cloud/streamlit_cloud

# 安装依赖
pip install -r requirements.txt

# 运行应用
streamlit run app.py
```

## 📋 功能特性

### 核心功能
- ✅ A股股票数据查询（沪深两市）
- ✅ 价格趋势图、成交量图表展示
- ✅ 公司基本信息和财务指标
- ✅ SQLite数据库持久化缓存
- ✅ 系统状态监控和性能测试
- ✅ 数据导出（CSV格式）

### 技术特点
- 🏗️ **单体架构**: 无需独立后端服务
- 💾 **SQLite持久化**: 真正的数据库缓存，非会话级别
- 📊 **实时数据**: 来源于AKShare官方接口
- 🎨 **响应式设计**: 适配不同屏幕尺寸
- ⚡ **性能优化**: 智能缓存和懒加载

## 🔧 技术栈

- **前端框架**: Streamlit
- **数据源**: AKShare
- **数据库**: SQLite
- **图表库**: Plotly
- **数据处理**: Pandas
- **部署平台**: Streamlit Community Cloud

## 📊 使用说明

1. **股票代码格式**: 6位数字（如：600000、000001、300001）
2. **支持市场**: 沪深A股、科创板
3. **数据范围**: 支持任意历史时间段查询
4. **缓存机制**: SQLite数据库持久化，应用重启后数据保留

## 🏗️ 项目结构

```
cloud/streamlit_cloud/
├── app.py                          # 主应用入口
├── pages/                          # 页面文件
│   ├── 1_📈_股票数据查询.py         # 股票数据查询
│   ├── 2_📊_资产信息.py             # 资产信息展示
│   └── 3_⚡_系统状态.py             # 系统状态监控
├── src/                           # 业务逻辑层（复制自主项目）
│   ├── services/                  # 业务服务
│   ├── cache/                     # 缓存层
│   ├── api/                       # 数据模型
│   └── config.py                  # 配置文件
├── database/                      # 数据库文件
│   ├── stock_data.db             # SQLite数据库
│   └── schema.sql                # 数据库结构
├── requirements.txt               # 依赖文件
├── .streamlit/
│   └── config.toml               # Streamlit配置
└── README.md                     # 使用说明
```

## 🎯 版本信息

- **当前版本**: v1.1.0-cloud
- **架构类型**: 单体应用
- **缓存策略**: SQLite数据库持久化
- **数据持久化**: 完全支持（非会话级别）

## 🚀 部署到 Streamlit Cloud

### 1. 准备GitHub仓库
```bash
# 确保代码已推送到GitHub
git add .
git commit -m "feat: Streamlit Cloud deployment ready"
git push origin streamlit-cloud-deployment
```

### 2. 配置Streamlit Cloud
1. 访问 https://share.streamlit.io/
2. 连接GitHub账户
3. 选择仓库: `franksunye/quantdb`
4. 选择分支: `streamlit-cloud-deployment`
5. 设置主文件路径: `cloud/streamlit_cloud/app.py`
6. 点击部署

### 3. 验证部署
- 检查所有页面功能正常
- 验证SQLite数据库读写
- 测试股票数据查询功能
- 确认图表显示正常

## 🧪 测试清单

### 功能测试
- [ ] 股票数据查询功能正常
- [ ] 资产信息展示正确
- [ ] 系统状态监控工作
- [ ] 图表显示无误
- [ ] 数据库读写正常
- [ ] 缓存机制有效

### 性能测试
- [ ] 首次查询响应时间 < 3秒
- [ ] 缓存命中响应时间 < 1秒
- [ ] 页面加载时间 < 5秒
- [ ] 内存使用合理

## 📄 许可证

MIT License - 详见 [LICENSE](../../LICENSE) 文件

## 🔗 相关链接

- **主项目**: [QuantDB](https://github.com/franksunye/quantdb)
- **问题反馈**: [Issues](https://github.com/franksunye/quantdb/issues)
- **架构文档**: [项目架构演进规划](../../project_architecture_evolution.md)
- **维护者**: frank

---

⭐ 如果这个项目对你有帮助，请给个 Star！
