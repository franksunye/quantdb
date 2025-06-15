# QuantDB 前端开发规划

**版本**: v1.0.0-frontend-mvp | **技术栈**: Streamlit | **目标**: 个人量化研究工具界面

## 🎯 项目目标

构建一个直观、易用、展现系统核心价值的本地前端，用于支持个人量化研究与数据管理。

### 核心价值展示
- **数据查询便利性**: 简单输入股票代码即可获取历史数据
- **性能优势可视化**: 展示缓存命中率和响应时间优势
- **数据质量展示**: 真实公司名称和完整财务指标
- **智能缓存效果**: 可视化展示系统的智能缓存机制

## 📋 版本规划

| 版本 | 目标 | 主要功能 | 预计工期 |
|------|------|----------|----------|
| V1.0 | MVP基础功能 | 数据查询 + 资产信息展示 | 1周 |
| V1.1 | 性能可视化 | 缓存监控 + 性能指标 | 1周 |
| V1.2 | 分析工具 | 基础图表 + 数据分析 | 1周 |
| V1.3 | 个性化功能 | 自选股 + 数据导出 | 1周 |

## 🚀 V1.0 - 最小可用产品 (MVP)

### 页面结构
```
quantdb_frontend/
├── app.py                          # 主页面/导航
├── pages/
│   ├── 1_📈_股票数据查询.py         # 股票日线数据查询
│   ├── 2_📊_资产信息.py             # 资产档案和数据覆盖
│   └── 3_⚡_系统状态.py             # 系统健康状态
├── utils/
│   ├── api_client.py               # FastAPI请求封装
│   ├── charts.py                   # 图表构建工具
│   └── config.py                   # 配置管理
├── assets/
│   └── logo.png                    # 项目Logo
├── requirements.txt
└── README.md
```

### 功能详细设计

#### 页面1: 📈 股票数据查询
**目标**: 提供直观的股票数据查询和展示

**功能组件**:
- 股票代码输入框 (支持6位数字代码)
- 日期范围选择器 (默认最近30天)
- 数据类型选择 (当前仅支持日线，预留分时选项)
- 查询按钮
- 数据表格展示 (`st.dataframe`)
- 收盘价趋势图 (`st.line_chart`)
- 基础统计信息 (最高价、最低价、平均价等)

**技术实现**:
```python
import streamlit as st
import pandas as pd
from utils.api_client import QuantDBClient

def show_stock_query_page():
    st.title("📈 股票数据查询")
    
    # 输入组件
    col1, col2, col3 = st.columns(3)
    with col1:
        symbol = st.text_input("股票代码", placeholder="例如: 600000")
    with col2:
        start_date = st.date_input("开始日期")
    with col3:
        end_date = st.date_input("结束日期")
    
    if st.button("查询数据"):
        # 调用API获取数据
        # 展示结果
```

#### 页面2: 📊 资产信息
**目标**: 展示资产档案和数据覆盖情况

**功能组件**:
- 股票代码输入框
- 资产基本信息卡片 (公司名称、行业、交易所)
- 财务指标展示 (`st.metric` 组件)
- 数据覆盖信息 (起止日期、记录数、最后更新)
- 数据覆盖时间轴图表

**展示指标**:
- 基本信息: 公司名称、股票代码、交易所、行业
- 财务指标: PE、PB、ROE、总股本、流通股本、市值
- 数据覆盖: 数据起始日期、结束日期、总记录数、最后访问时间

#### 页面3: ⚡ 系统状态
**目标**: 展示系统健康状态和基础性能信息

**功能组件**:
- API健康状态检查
- 数据库基本信息 (大小、记录数)
- 系统版本信息
- 基础性能指标

## 🔧 技术实现

### API客户端封装
```python
# utils/api_client.py
import requests
from typing import Optional, Dict, Any

class QuantDBClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.api_prefix = "/api/v1"
    
    def get_health(self) -> Dict[str, Any]:
        """获取系统健康状态"""
        response = requests.get(f"{self.base_url}{self.api_prefix}/health")
        return response.json()
    
    def get_stock_data(self, symbol: str, start_date: str, end_date: str) -> Dict[str, Any]:
        """获取股票历史数据"""
        params = {
            "start_date": start_date,
            "end_date": end_date
        }
        response = requests.get(
            f"{self.base_url}{self.api_prefix}/historical/stock/{symbol}",
            params=params
        )
        return response.json()
    
    def get_asset_info(self, symbol: str) -> Dict[str, Any]:
        """获取资产信息"""
        response = requests.get(f"{self.base_url}{self.api_prefix}/assets/symbol/{symbol}")
        return response.json()
```

### 图表工具
```python
# utils/charts.py
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

def create_price_chart(df: pd.DataFrame) -> go.Figure:
    """创建价格趋势图"""
    fig = px.line(df, x='date', y='close', title='收盘价趋势')
    fig.update_layout(
        xaxis_title="日期",
        yaxis_title="收盘价 (元)",
        hovermode='x unified'
    )
    return fig

def create_volume_chart(df: pd.DataFrame) -> go.Figure:
    """创建成交量图表"""
    fig = px.bar(df, x='date', y='volume', title='成交量')
    fig.update_layout(
        xaxis_title="日期",
        yaxis_title="成交量",
        showlegend=False
    )
    return fig
```

## 📊 V1.1 - 性能可视化增强

### 新增功能
- **缓存命中状态展示**: 显示每次查询的缓存命中情况
- **响应时间监控**: 展示API响应时间和性能对比
- **AKShare调用状态**: 显示是否调用了外部API
- **系统性能仪表板**: 数据库大小、总记录量、命中率统计

### 实现要点
- 集成监控API端点
- 实时性能数据展示
- 历史性能趋势图表
- 缓存效率可视化

## 📈 V1.2 - 分析工具

### 新增功能
- **涨跌幅分析**: 显示股票涨跌幅分布
- **价格统计**: 最大涨幅、跌幅、均值等摘要
- **成交量分析**: 成交量趋势和异常检测
- **财务指标趋势**: PE、PB等指标的历史变化

### 技术特点
- 使用Plotly创建交互式图表
- 支持多种图表类型 (线图、柱图、散点图)
- 数据统计和分析功能
- 图表导出功能

## 🎯 V1.3 - 个性化功能

### 新增功能
- **自选股管理**: 添加/删除自选股票
- **批量数据查询**: 一键查询自选股数据
- **数据导出**: CSV/Excel格式导出
- **用户偏好设置**: 默认日期范围、图表样式等

### 数据持久化
- 使用本地JSON文件存储用户配置
- 支持导入/导出用户配置
- 自选股列表管理

## 🛠️ 开发环境设置

### 依赖安装
```bash
# 创建前端目录
mkdir quantdb_frontend
cd quantdb_frontend

# 安装依赖
pip install streamlit plotly pandas requests python-dateutil
```

### 项目启动
```bash
# 启动后端API (在QuantDB根目录)
uvicorn src.api.main:app --reload

# 启动前端 (在quantdb_frontend目录)
streamlit run app.py
```

## 📋 开发任务清单

### V1.0 MVP任务
- [ ] 创建项目结构和基础文件
- [ ] 实现API客户端封装
- [ ] 开发股票数据查询页面
- [ ] 开发资产信息展示页面
- [ ] 开发系统状态页面
- [ ] 集成基础图表功能
- [ ] 编写用户使用文档

### 质量保证
- [ ] 错误处理和用户友好提示
- [ ] 响应式设计适配
- [ ] 性能优化 (缓存、懒加载)
- [ ] 用户体验测试
- [ ] 文档完善

## 🎨 UI/UX设计原则

### 设计理念
- **简洁明了**: 避免复杂的界面设计
- **数据驱动**: 突出数据展示和分析功能
- **响应迅速**: 快速加载和响应用户操作
- **专业感**: 体现金融数据工具的专业性

### 色彩方案
- 主色调: 深蓝色 (#1f77b4) - 专业、稳重
- 辅助色: 绿色 (#2ca02c) - 上涨、正面
- 警告色: 红色 (#d62728) - 下跌、警告
- 背景色: 浅灰色 (#f8f9fa) - 清洁、现代

### 组件规范
- 使用Streamlit原生组件保持一致性
- 合理使用列布局和容器
- 统一的字体大小和间距
- 清晰的标题层级结构

## 📈 成功指标

### 功能指标
- [ ] 支持主要股票代码查询 (沪深A股)
- [ ] 数据查询响应时间 < 2秒
- [ ] 图表加载时间 < 1秒
- [ ] 支持至少30天历史数据展示

### 用户体验指标
- [ ] 界面加载时间 < 3秒
- [ ] 操作流程不超过3步
- [ ] 错误提示清晰易懂
- [ ] 支持常见浏览器 (Chrome, Firefox, Edge)

### 技术指标
- [ ] 代码结构清晰，易于维护
- [ ] API调用错误处理完善
- [ ] 前端组件可复用性 > 80%
- [ ] 文档覆盖率 100%
