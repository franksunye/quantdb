# QuantDB Frontend

**版本**: v1.0.0-mvp | **技术栈**: Streamlit | **状态**: 开发中

QuantDB 的前端界面，提供直观的股票数据查询、资产信息展示和性能监控功能。

## 🎯 项目目标

构建一个简洁、高效、专业的个人量化研究工具界面，展现 QuantDB 的核心价值：
- **数据查询便利性**: 简单输入即可获取股票历史数据
- **性能优势可视化**: 展示智能缓存的性能提升效果
- **数据质量展示**: 真实公司名称和完整财务指标
- **专业分析工具**: 基础的数据分析和图表功能

## 🚀 快速开始

### 1. 环境准备

```bash
# 确保后端API正在运行
cd ../  # 回到QuantDB根目录
uvicorn src.api.main:app --reload

# 安装前端依赖
cd quantdb_frontend
pip install -r requirements.txt
```

### 2. 启动前端

```bash
# 启动Streamlit应用
streamlit run app.py

# 访问地址: http://localhost:8501
```

### 3. 功能概览

- **📈 股票数据查询**: 输入股票代码，查看历史价格数据和趋势图
- **📊 资产信息**: 查看公司基本信息、财务指标和数据覆盖情况
- **⚡ 系统状态**: 监控API健康状态和基础性能指标

## 📁 项目结构

```
quantdb_frontend/
├── app.py                          # 主应用入口
├── pages/                          # 页面模块
│   ├── 1_📈_股票数据查询.py         # 股票数据查询页面
│   ├── 2_📊_资产信息.py             # 资产信息展示页面
│   └── 3_⚡_系统状态.py             # 系统状态监控页面
├── utils/                          # 工具模块
│   ├── api_client.py               # API客户端封装
│   ├── charts.py                   # 图表工具
│   └── config.py                   # 配置管理
├── assets/                         # 静态资源
│   └── logo.png                    # 项目Logo
├── requirements.txt                # 依赖列表
└── README.md                       # 项目说明
```

## 🔧 技术栈

- **前端框架**: Streamlit 1.28+
- **图表库**: Plotly Express / Streamlit原生图表
- **HTTP客户端**: Requests
- **数据处理**: Pandas
- **日期处理**: Python-dateutil

## 📊 功能特性

### V1.0 MVP功能
- ✅ 股票代码输入和验证
- ✅ 日期范围选择 (默认30天)
- ✅ 历史数据表格展示
- ✅ 收盘价趋势图
- ✅ 资产基本信息展示
- ✅ 财务指标展示 (PE、PB、ROE等)
- ✅ 系统健康状态检查

### V1.1 性能监控 (规划中)
- [ ] 缓存命中率展示
- [ ] API响应时间监控
- [ ] 性能对比图表
- [ ] 系统性能仪表板

### V1.2 分析工具 (规划中)
- [ ] 涨跌幅分析
- [ ] 价格统计摘要
- [ ] 成交量分析
- [ ] 交互式图表

### V1.3 个性化功能 (规划中)
- [ ] 自选股管理
- [ ] 数据导出 (CSV/Excel)
- [ ] 用户偏好设置
- [ ] 批量数据查询

## 🛠️ 开发指南

### 添加新页面

1. 在 `pages/` 目录下创建新的 Python 文件
2. 文件名格式: `序号_图标_页面名称.py`
3. 实现页面逻辑和UI组件
4. Streamlit会自动识别并添加到侧边栏

### API调用示例

```python
from utils.api_client import QuantDBClient

# 创建客户端
client = QuantDBClient()

# 获取股票数据
data = client.get_stock_data("600000", "20240101", "20240131")

# 获取资产信息
asset = client.get_asset_info("600000")

# 检查系统健康状态
health = client.get_health()
```

### 图表创建示例

```python
from utils.charts import create_price_chart
import pandas as pd

# 创建价格趋势图
df = pd.DataFrame(data['data'])
fig = create_price_chart(df)
st.plotly_chart(fig, use_container_width=True)
```

## 🎨 设计规范

### 色彩方案
- **主色调**: 深蓝色 (#1f77b4) - 专业、稳重
- **辅助色**: 绿色 (#2ca02c) - 上涨、正面
- **警告色**: 红色 (#d62728) - 下跌、警告
- **背景色**: 浅灰色 (#f8f9fa) - 清洁、现代

### UI原则
- **简洁明了**: 避免复杂的界面设计
- **数据驱动**: 突出数据展示和分析功能
- **响应迅速**: 快速加载和响应用户操作
- **专业感**: 体现金融数据工具的专业性

### 组件规范
- 使用Streamlit原生组件保持一致性
- 合理使用列布局 (`st.columns`)
- 统一的标题层级 (`st.title`, `st.header`, `st.subheader`)
- 清晰的错误提示和加载状态

## 🧪 测试

### 手动测试清单
- [ ] 所有页面正常加载
- [ ] API调用成功返回数据
- [ ] 图表正确渲染
- [ ] 错误处理友好
- [ ] 响应时间合理 (<3秒)

### 测试数据
推荐使用以下股票代码进行测试：
- `600000` - 浦发银行 (大盘蓝筹)
- `000001` - 平安银行 (深市股票)
- `600519` - 贵州茅台 (高价股)

## 📈 性能优化

### 前端优化
- 使用 `@st.cache_data` 缓存API响应
- 懒加载大数据集
- 优化图表渲染性能
- 合理使用 `st.spinner` 显示加载状态

### 用户体验优化
- 提供清晰的错误提示
- 合理的默认值设置
- 快速的页面响应
- 直观的操作流程

## 🔗 相关链接

- **后端API**: http://localhost:8000/docs
- **项目仓库**: https://github.com/franksunye/quantdb
- **技术文档**: ../docs/40_FRONTEND.md
- **任务清单**: ../docs/41_FRONTEND_BACKLOG.md

## 📄 许可证

本项目采用 MIT 许可证 - 详情请参阅 [LICENSE](../LICENSE) 文件

---

⭐ 如果这个项目对你有帮助，请给个 Star！
