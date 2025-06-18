# QuantDB Streamlit Cloud 实施指南

**实施时间**: 2-3天 | **难度**: 中等 | **改动范围**: 最小化

## 🚀 第一步：创建云端版本目录结构

### 1.1 创建项目结构
```bash
# 在项目根目录执行
mkdir quantdb_streamlit_cloud
cd quantdb_streamlit_cloud

# 创建目录结构
mkdir -p {pages,services,utils,.streamlit}
touch app.py requirements.txt README.md
```

### 1.2 目录结构说明
```
quantdb_streamlit_cloud/
├── app.py                          # 主应用入口
├── pages/
│   ├── 1_📈_股票数据查询.py         # 股票数据查询页面
│   ├── 2_📊_资产信息.py             # 资产信息展示页面
│   └── 3_⚡_系统状态.py             # 系统状态监控页面
├── services/
│   ├── __init__.py
│   ├── integrated_service.py       # 集成服务层
│   ├── akshare_adapter.py          # AKShare适配器
│   └── trading_calendar.py         # 交易日历服务
├── utils/
│   ├── __init__.py
│   ├── session_manager.py          # 会话状态管理
│   ├── charts.py                   # 图表工具
│   └── helpers.py                  # 辅助函数
├── .streamlit/
│   ├── config.toml                 # Streamlit配置
│   └── secrets.toml                # 密钥配置（本地开发用）
├── requirements.txt                # 依赖文件
└── README.md                       # 部署说明
```

## 📝 第二步：核心文件实现

### 2.1 requirements.txt
```txt
# 核心框架
streamlit>=1.28.0

# 数据处理
pandas>=2.0.0
numpy>=1.24.0

# 数据源
akshare>=1.0.0

# 图表和可视化
plotly>=5.15.0

# HTTP请求
requests>=2.31.0

# 日期处理
python-dateutil>=2.8.0

# 可选：增强功能
streamlit-option-menu>=0.3.6
```

### 2.2 .streamlit/config.toml
```toml
[server]
maxUploadSize = 200
maxMessageSize = 200
enableCORS = false
enableXsrfProtection = false

[theme]
primaryColor = "#1f77b4"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
font = "sans serif"

[browser]
gatherUsageStats = false
```

### 2.3 主应用文件 app.py
```python
"""
QuantDB Streamlit Cloud版本 - 主应用入口
适配Streamlit Cloud部署的单体应用架构
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# 页面配置
st.set_page_config(
    page_title="QuantDB - 量化数据平台",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/franksunye/quantdb',
        'Report a bug': 'https://github.com/franksunye/quantdb/issues',
        'About': """
        # QuantDB Cloud Edition
        
        **版本**: v1.0.0-cloud
        
        高性能股票数据查询平台，专为Streamlit Cloud优化。
        
        ## 核心功能
        - 📈 股票数据查询和图表展示
        - 📊 资产信息和财务指标
        - ⚡ 智能缓存和性能监控
        
        ## 技术特点
        - 🚀 会话级智能缓存
        - 🏢 真实公司名称和财务数据
        - 📊 专业的数据可视化
        - ☁️ 云端部署，随时访问
        
        ---
        
        **GitHub**: https://github.com/franksunye/quantdb
        **维护者**: frank
        """
    }
)

def init_session_state():
    """初始化会话状态"""
    defaults = {
        'stock_data_cache': {},
        'asset_info_cache': {},
        'performance_metrics': {
            'total_queries': 0,
            'cache_hits': 0,
            'avg_response_time': 0
        },
        'user_preferences': {
            'default_days': 30,
            'chart_theme': 'plotly_white'
        },
        'app_start_time': datetime.now()
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def get_cache_stats():
    """获取缓存统计信息"""
    return {
        'stock_data_count': len(st.session_state.stock_data_cache),
        'asset_info_count': len(st.session_state.asset_info_cache),
        'total_queries': st.session_state.performance_metrics['total_queries'],
        'cache_hits': st.session_state.performance_metrics['cache_hits'],
        'cache_hit_rate': (
            st.session_state.performance_metrics['cache_hits'] / 
            max(st.session_state.performance_metrics['total_queries'], 1) * 100
        )
    }

def main():
    """主页面"""
    
    # 初始化会话状态
    init_session_state()
    
    # 页面标题
    st.title("📊 QuantDB - 量化数据平台")
    st.markdown("### 🌟 云端版本 - 随时随地访问股票数据")
    st.markdown("---")
    
    # 欢迎信息
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ### 🎯 欢迎使用 QuantDB Cloud
        
        这是QuantDB的云端版本，专为Streamlit Cloud优化，提供：
        
        **🚀 核心优势**:
        - ⚡ **智能缓存**: 会话级数据缓存，避免重复请求
        - 🏢 **真实数据**: 显示真实公司名称和财务指标
        - 📊 **专业图表**: 基于Plotly的交互式数据可视化
        - ☁️ **云端访问**: 无需安装，浏览器直接使用
        - 🔍 **简单易用**: 输入股票代码即可获取完整分析
        """)
    
    with col2:
        st.markdown("### 📈")
        st.markdown("### 数据")
        st.markdown("### 驱动")
        st.markdown("### 决策")
    
    st.markdown("---")
    
    # 系统状态概览
    st.markdown("### 📊 会话状态概览")
    
    cache_stats = get_cache_stats()
    session_duration = datetime.now() - st.session_state.app_start_time
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="缓存股票数",
            value=cache_stats['stock_data_count'],
            delta="个股票" if cache_stats['stock_data_count'] > 0 else "暂无数据"
        )
    
    with col2:
        st.metric(
            label="资产信息数",
            value=cache_stats['asset_info_count'],
            delta="个公司" if cache_stats['asset_info_count'] > 0 else "暂无数据"
        )
    
    with col3:
        st.metric(
            label="总查询次数",
            value=cache_stats['total_queries'],
            delta=f"命中率 {cache_stats['cache_hit_rate']:.1f}%"
        )
    
    with col4:
        st.metric(
            label="会话时长",
            value=f"{int(session_duration.total_seconds() // 60)}分钟",
            delta="活跃中"
        )
    
    # 功能导航
    st.markdown("---")
    st.markdown("### 🧭 功能导航")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        #### 📈 股票数据查询
        - 历史价格数据查询
        - 价格趋势图表展示
        - 基础统计信息分析
        - 成交量和涨跌幅分析
        
        👉 **使用左侧导航栏进入**
        """)
    
    with col2:
        st.markdown("""
        #### 📊 资产信息
        - 公司基本信息展示
        - 财务指标详细分析
        - 数据覆盖情况统计
        - 市场数据实时更新
        
        👉 **使用左侧导航栏进入**
        """)
    
    with col3:
        st.markdown("""
        #### ⚡ 系统状态
        - 会话缓存状态监控
        - 系统性能指标展示
        - 数据获取统计信息
        - 用户使用情况分析
        
        👉 **使用左侧导航栏进入**
        """)
    
    # 快速开始
    st.markdown("---")
    st.markdown("### 🚀 快速开始")
    
    with st.expander("📖 使用指南", expanded=False):
        st.markdown("""
        #### 如何使用 QuantDB Cloud
        
        1. **股票代码格式**
           - A股代码：6位数字（如：600000 浦发银行，000001 平安银行）
           - 支持沪深两市主要股票
        
        2. **数据查询**
           - 点击左侧"📈 股票数据查询"
           - 输入股票代码和日期范围
           - 系统自动获取并缓存数据
        
        3. **缓存机制**
           - 首次查询：从AKShare获取数据（1-3秒）
           - 缓存命中：从会话缓存获取（<1秒）
           - 会话结束后缓存清空
        
        4. **注意事项**
           - 数据来源：AKShare官方接口
           - 缓存范围：当前浏览器会话
           - 建议使用：Chrome、Firefox、Edge浏览器
        """)
    
    # 技术信息
    with st.expander("🔧 技术信息", expanded=False):
        st.markdown("""
        ### 技术架构
        - **前端框架**: Streamlit Cloud
        - **数据源**: AKShare
        - **图表库**: Plotly Express
        - **缓存策略**: 会话状态 + Streamlit缓存
        - **部署平台**: Streamlit Community Cloud
        
        ### 版本信息
        - **版本**: v1.0.0-cloud
        - **架构**: 单体应用
        - **缓存**: 会话级别
        - **持久化**: 无（会话结束清空）
        
        ### 性能特点
        - **首次查询**: 1-3秒（取决于网络）
        - **缓存命中**: <1秒
        - **并发支持**: Streamlit Cloud限制
        - **数据更新**: 实时从AKShare获取
        """)

if __name__ == "__main__":
    main()
```

## 🔧 第三步：核心服务实现

### 3.1 会话管理器 utils/session_manager.py
```python
"""
会话状态管理器
负责管理Streamlit会话状态和数据缓存
"""

import streamlit as st
from datetime import datetime
from typing import Dict, Any, Optional

class SessionDataManager:
    """会话数据管理器"""
    
    @staticmethod
    def init_session():
        """初始化会话状态"""
        defaults = {
            'stock_data_cache': {},
            'asset_info_cache': {},
            'performance_metrics': {
                'total_queries': 0,
                'cache_hits': 0,
                'akshare_calls': 0,
                'avg_response_time': 0,
                'query_history': []
            },
            'user_preferences': {
                'default_days': 30,
                'chart_theme': 'plotly_white',
                'auto_refresh': False
            },
            'app_start_time': datetime.now(),
            'last_activity': datetime.now()
        }
        
        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value
    
    @staticmethod
    def get_stock_data_from_cache(cache_key: str) -> Optional[Dict[str, Any]]:
        """从缓存获取股票数据"""
        return st.session_state.stock_data_cache.get(cache_key)
    
    @staticmethod
    def set_stock_data_to_cache(cache_key: str, data: Dict[str, Any]):
        """设置股票数据到缓存"""
        st.session_state.stock_data_cache[cache_key] = data
        st.session_state.last_activity = datetime.now()
    
    @staticmethod
    def get_asset_info_from_cache(symbol: str) -> Optional[Dict[str, Any]]:
        """从缓存获取资产信息"""
        return st.session_state.asset_info_cache.get(symbol)
    
    @staticmethod
    def set_asset_info_to_cache(symbol: str, data: Dict[str, Any]):
        """设置资产信息到缓存"""
        st.session_state.asset_info_cache[symbol] = data
        st.session_state.last_activity = datetime.now()
    
    @staticmethod
    def update_performance_metrics(query_type: str, response_time: float, cache_hit: bool = False):
        """更新性能指标"""
        metrics = st.session_state.performance_metrics
        
        metrics['total_queries'] += 1
        if cache_hit:
            metrics['cache_hits'] += 1
        else:
            metrics['akshare_calls'] += 1
        
        # 更新平均响应时间
        current_avg = metrics['avg_response_time']
        total_queries = metrics['total_queries']
        metrics['avg_response_time'] = (current_avg * (total_queries - 1) + response_time) / total_queries
        
        # 记录查询历史（保持最近50条）
        metrics['query_history'].append({
            'timestamp': datetime.now(),
            'query_type': query_type,
            'response_time': response_time,
            'cache_hit': cache_hit
        })
        
        if len(metrics['query_history']) > 50:
            metrics['query_history'] = metrics['query_history'][-50:]
    
    @staticmethod
    def get_cache_stats() -> Dict[str, Any]:
        """获取缓存统计信息"""
        metrics = st.session_state.performance_metrics
        
        return {
            'stock_data_count': len(st.session_state.stock_data_cache),
            'asset_info_count': len(st.session_state.asset_info_cache),
            'total_queries': metrics['total_queries'],
            'cache_hits': metrics['cache_hits'],
            'akshare_calls': metrics['akshare_calls'],
            'cache_hit_rate': (
                metrics['cache_hits'] / max(metrics['total_queries'], 1) * 100
            ),
            'avg_response_time': metrics['avg_response_time'],
            'session_duration': datetime.now() - st.session_state.app_start_time,
            'last_activity': st.session_state.last_activity
        }
    
    @staticmethod
    def clear_cache():
        """清空缓存"""
        st.session_state.stock_data_cache = {}
        st.session_state.asset_info_cache = {}
        st.session_state.performance_metrics = {
            'total_queries': 0,
            'cache_hits': 0,
            'akshare_calls': 0,
            'avg_response_time': 0,
            'query_history': []
        }
        st.success("缓存已清空")
```

## 📊 第四步：图表工具实现

### 4.1 图表工具 utils/charts.py
```python
"""
图表工具模块
提供各种股票数据可视化图表
"""

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from typing import Dict, Any

class StockChartBuilder:
    """股票图表构建器"""
    
    @staticmethod
    def create_price_trend_chart(df: pd.DataFrame, symbol: str, name: str = None) -> go.Figure:
        """创建价格趋势图"""
        fig = px.line(
            df, 
            x='date', 
            y='close', 
            title=f'{name or symbol} - 收盘价趋势',
            labels={'close': '收盘价 (元)', 'date': '日期'}
        )
        
        fig.update_layout(
            hovermode='x unified',
            showlegend=False,
            height=400
        )
        
        fig.update_traces(
            line=dict(width=2, color='#1f77b4'),
            hovertemplate='日期: %{x}<br>收盘价: ¥%{y:.2f}<extra></extra>'
        )
        
        return fig
    
    @staticmethod
    def create_volume_chart(df: pd.DataFrame, symbol: str, name: str = None) -> go.Figure:
        """创建成交量图表"""
        fig = px.bar(
            df, 
            x='date', 
            y='volume', 
            title=f'{name or symbol} - 成交量',
            labels={'volume': '成交量', 'date': '日期'}
        )
        
        fig.update_layout(
            showlegend=False,
            height=300
        )
        
        fig.update_traces(
            marker_color='lightblue',
            hovertemplate='日期: %{x}<br>成交量: %{y:,.0f}<extra></extra>'
        )
        
        return fig
    
    @staticmethod
    def create_candlestick_chart(df: pd.DataFrame, symbol: str, name: str = None) -> go.Figure:
        """创建K线图"""
        fig = go.Figure(data=go.Candlestick(
            x=df['date'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name=name or symbol
        ))
        
        fig.update_layout(
            title=f'{name or symbol} - K线图',
            yaxis_title='价格 (元)',
            xaxis_title='日期',
            height=500,
            showlegend=False
        )
        
        return fig
    
    @staticmethod
    def create_returns_chart(df: pd.DataFrame, symbol: str, name: str = None) -> go.Figure:
        """创建收益率图表"""
        # 计算日收益率
        df_copy = df.copy()
        df_copy['returns'] = df_copy['close'].pct_change() * 100
        
        fig = px.line(
            df_copy, 
            x='date', 
            y='returns', 
            title=f'{name or symbol} - 日收益率',
            labels={'returns': '收益率 (%)', 'date': '日期'}
        )
        
        # 添加零线
        fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
        
        fig.update_layout(
            hovermode='x unified',
            showlegend=False,
            height=350
        )
        
        fig.update_traces(
            line=dict(width=1.5),
            hovertemplate='日期: %{x}<br>收益率: %{y:.2f}%<extra></extra>'
        )
        
        return fig
    
    @staticmethod
    def create_performance_comparison_chart(cache_stats: Dict[str, Any]) -> go.Figure:
        """创建性能对比图表"""
        categories = ['缓存命中', 'AKShare调用']
        values = [cache_stats['cache_hits'], cache_stats['akshare_calls']]
        colors = ['#2ca02c', '#ff7f0e']
        
        fig = px.pie(
            values=values,
            names=categories,
            title='查询来源分布',
            color_discrete_sequence=colors
        )
        
        fig.update_traces(
            textposition='inside',
            textinfo='percent+label',
            hovertemplate='%{label}<br>次数: %{value}<br>占比: %{percent}<extra></extra>'
        )
        
        fig.update_layout(height=300)
        
        return fig
```

## 🔧 第五步：集成服务层实现

### 5.1 集成服务 services/integrated_service.py
```python
"""
集成服务层 - 适配Streamlit Cloud的单体架构
整合AKShare数据获取、缓存管理和性能监控
"""

import streamlit as st
import pandas as pd
import akshare as ak
from datetime import datetime, timedelta
import time
from typing import Dict, Any, Optional, List
from utils.session_manager import SessionDataManager

class IntegratedQuantDBService:
    """集成的QuantDB服务"""

    def __init__(self):
        self.session_manager = SessionDataManager()
        self.session_manager.init_session()

    def get_stock_data(self, symbol: str, start_date: str, end_date: str) -> Optional[Dict[str, Any]]:
        """获取股票历史数据"""
        cache_key = f"{symbol}_{start_date}_{end_date}"

        # 检查缓存
        cached_data = self.session_manager.get_stock_data_from_cache(cache_key)
        if cached_data:
            self.session_manager.update_performance_metrics('stock_data', 0.01, cache_hit=True)
            return cached_data

        # 从AKShare获取数据
        try:
            start_time = time.time()

            # 获取股票历史数据
            df = ak.stock_zh_a_hist(
                symbol=symbol,
                period="daily",
                start_date=start_date.replace('-', ''),
                end_date=end_date.replace('-', ''),
                adjust=""
            )

            if df.empty:
                return None

            # 数据处理
            df.columns = ['date', 'open', 'close', 'high', 'low', 'volume', 'turnover', 'amplitude', 'pct_change', 'change', 'turnover_rate']
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')

            # 获取股票基本信息
            stock_info = self._get_stock_basic_info(symbol)

            response_time = time.time() - start_time

            result = {
                'symbol': symbol,
                'name': stock_info.get('name', f'股票{symbol}'),
                'start_date': start_date,
                'end_date': end_date,
                'data': df.to_dict('records'),
                'metadata': {
                    'total_records': len(df),
                    'data_source': 'AKShare',
                    'fetch_time': datetime.now().isoformat(),
                    'response_time': response_time
                }
            }

            # 缓存结果
            self.session_manager.set_stock_data_to_cache(cache_key, result)
            self.session_manager.update_performance_metrics('stock_data', response_time, cache_hit=False)

            return result

        except Exception as e:
            st.error(f"获取股票数据失败: {str(e)}")
            return None

    def get_asset_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """获取资产信息"""
        # 检查缓存
        cached_info = self.session_manager.get_asset_info_from_cache(symbol)
        if cached_info:
            self.session_manager.update_performance_metrics('asset_info', 0.01, cache_hit=True)
            return cached_info

        try:
            start_time = time.time()

            # 获取股票基本信息
            basic_info = self._get_stock_basic_info(symbol)

            # 获取实时数据
            realtime_data = self._get_realtime_data(symbol)

            response_time = time.time() - start_time

            result = {
                'symbol': symbol,
                'name': basic_info.get('name', f'股票{symbol}'),
                'basic_info': basic_info,
                'realtime_data': realtime_data,
                'metadata': {
                    'data_source': 'AKShare',
                    'fetch_time': datetime.now().isoformat(),
                    'response_time': response_time
                }
            }

            # 缓存结果
            self.session_manager.set_asset_info_to_cache(symbol, result)
            self.session_manager.update_performance_metrics('asset_info', response_time, cache_hit=False)

            return result

        except Exception as e:
            st.error(f"获取资产信息失败: {str(e)}")
            return None

    def _get_stock_basic_info(self, symbol: str) -> Dict[str, Any]:
        """获取股票基本信息"""
        try:
            # 获取股票基本信息
            info_df = ak.stock_individual_info_em(symbol=symbol)
            if not info_df.empty:
                info_dict = dict(zip(info_df['item'], info_df['value']))
                return {
                    'name': info_dict.get('股票简称', f'股票{symbol}'),
                    'industry': info_dict.get('所属行业', '未知'),
                    'exchange': '上交所' if symbol.startswith('6') else '深交所',
                    'listing_date': info_dict.get('上市时间', '未知'),
                    'total_shares': info_dict.get('总股本', 0),
                    'circulating_shares': info_dict.get('流通股', 0)
                }
        except:
            pass

        return {
            'name': f'股票{symbol}',
            'industry': '未知',
            'exchange': '上交所' if symbol.startswith('6') else '深交所',
            'listing_date': '未知',
            'total_shares': 0,
            'circulating_shares': 0
        }

    def _get_realtime_data(self, symbol: str) -> Dict[str, Any]:
        """获取实时数据"""
        try:
            # 获取实时数据
            realtime_df = ak.stock_zh_a_spot_em()
            stock_data = realtime_df[realtime_df['代码'] == symbol]

            if not stock_data.empty:
                row = stock_data.iloc[0]
                return {
                    'current_price': row.get('最新价', 0),
                    'change': row.get('涨跌额', 0),
                    'pct_change': row.get('涨跌幅', 0),
                    'volume': row.get('成交量', 0),
                    'turnover': row.get('成交额', 0),
                    'pe_ratio': row.get('市盈率-动态', 0),
                    'pb_ratio': row.get('市净率', 0),
                    'market_cap': row.get('总市值', 0)
                }
        except:
            pass

        return {
            'current_price': 0,
            'change': 0,
            'pct_change': 0,
            'volume': 0,
            'turnover': 0,
            'pe_ratio': 0,
            'pb_ratio': 0,
            'market_cap': 0
        }

    def get_cache_status(self) -> Dict[str, Any]:
        """获取缓存状态"""
        return self.session_manager.get_cache_stats()

    def clear_cache(self):
        """清空缓存"""
        self.session_manager.clear_cache()
```

## 📱 第六步：页面实现

### 6.1 股票数据查询页面 pages/1_📈_股票数据查询.py
```python
"""
股票数据查询页面
提供股票历史数据查询和图表展示功能
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

# 添加父目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from services.integrated_service import IntegratedQuantDBService
from utils.charts import StockChartBuilder

# 页面配置
st.set_page_config(
    page_title="股票数据查询 - QuantDB",
    page_icon="📈",
    layout="wide"
)

def validate_stock_code(code: str) -> bool:
    """验证股票代码格式"""
    if not code:
        return False

    # 去除空格
    code = code.strip()

    # 检查是否为6位数字
    if len(code) != 6 or not code.isdigit():
        return False

    # 检查是否为有效的A股代码
    if code.startswith(('000', '001', '002', '003', '300')):  # 深交所
        return True
    elif code.startswith('6'):  # 上交所
        return True
    elif code.startswith('688'):  # 科创板
        return True

    return False

def main():
    """主页面"""

    st.title("📈 股票数据查询")
    st.markdown("查询股票历史数据，支持多种图表展示和数据分析")
    st.markdown("---")

    # 初始化服务
    service = IntegratedQuantDBService()
    chart_builder = StockChartBuilder()

    # 输入区域
    col1, col2, col3, col4 = st.columns([2, 2, 2, 1])

    with col1:
        symbol = st.text_input(
            "股票代码",
            placeholder="例如: 600000",
            help="请输入6位A股代码"
        )

    with col2:
        # 默认查询最近30天
        default_start = datetime.now() - timedelta(days=30)
        start_date = st.date_input(
            "开始日期",
            value=default_start,
            max_value=datetime.now().date()
        )

    with col3:
        end_date = st.date_input(
            "结束日期",
            value=datetime.now().date(),
            max_value=datetime.now().date()
        )

    with col4:
        st.markdown("<br>", unsafe_allow_html=True)  # 空行对齐
        query_button = st.button("🔍 查询数据", type="primary")

    # 验证输入
    if query_button:
        if not validate_stock_code(symbol):
            st.error("❌ 请输入有效的6位股票代码（如：600000、000001、300001）")
            return

        if start_date >= end_date:
            st.error("❌ 开始日期必须早于结束日期")
            return

        # 查询数据
        with st.spinner("正在获取股票数据..."):
            result = service.get_stock_data(
                symbol=symbol,
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d')
            )

        if result is None:
            st.error("❌ 获取数据失败，请检查股票代码或稍后重试")
            return

        # 显示结果
        st.success(f"✅ 成功获取 {result['name']} ({symbol}) 的数据")

        # 数据概览
        df = pd.DataFrame(result['data'])
        df['date'] = pd.to_datetime(df['date'])

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("数据记录数", len(df))

        with col2:
            latest_price = df.iloc[-1]['close']
            first_price = df.iloc[0]['close']
            total_return = (latest_price - first_price) / first_price * 100
            st.metric("期间涨跌幅", f"{total_return:.2f}%")

        with col3:
            st.metric("最高价", f"¥{df['high'].max():.2f}")

        with col4:
            st.metric("最低价", f"¥{df['low'].min():.2f}")

        st.markdown("---")

        # 图表展示
        tab1, tab2, tab3, tab4 = st.tabs(["📈 价格趋势", "📊 成交量", "🕯️ K线图", "📉 收益率"])

        with tab1:
            fig_price = chart_builder.create_price_trend_chart(df, symbol, result['name'])
            st.plotly_chart(fig_price, use_container_width=True)

        with tab2:
            fig_volume = chart_builder.create_volume_chart(df, symbol, result['name'])
            st.plotly_chart(fig_volume, use_container_width=True)

        with tab3:
            fig_candlestick = chart_builder.create_candlestick_chart(df, symbol, result['name'])
            st.plotly_chart(fig_candlestick, use_container_width=True)

        with tab4:
            fig_returns = chart_builder.create_returns_chart(df, symbol, result['name'])
            st.plotly_chart(fig_returns, use_container_width=True)

        # 数据表格
        st.markdown("### 📋 详细数据")

        # 格式化显示
        display_df = df.copy()
        display_df['date'] = display_df['date'].dt.strftime('%Y-%m-%d')
        display_df = display_df.round(2)

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )

        # 数据导出
        csv = display_df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="📥 下载CSV数据",
            data=csv,
            file_name=f"{symbol}_{result['name']}_股票数据.csv",
            mime="text/csv"
        )

        # 显示元数据
        with st.expander("📊 数据信息"):
            col1, col2 = st.columns(2)

            with col1:
                st.write("**数据来源**:", result['metadata']['data_source'])
                st.write("**获取时间**:", result['metadata']['fetch_time'][:19])
                st.write("**响应时间**:", f"{result['metadata']['response_time']:.3f}秒")

            with col2:
                st.write("**股票名称**:", result['name'])
                st.write("**股票代码**:", symbol)
                st.write("**数据记录**:", f"{result['metadata']['total_records']}条")

if __name__ == "__main__":
    main()
```

## 🚀 第七步：部署准备

### 7.1 创建部署脚本 deploy.sh
```bash
#!/bin/bash
# QuantDB Streamlit Cloud 部署脚本

echo "🚀 准备部署 QuantDB 到 Streamlit Cloud"

# 检查必要文件
echo "📋 检查必要文件..."
required_files=("app.py" "requirements.txt" "README.md")

for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ 缺少必要文件: $file"
        exit 1
    fi
done

echo "✅ 所有必要文件检查完成"

# 创建GitHub仓库分支
echo "📦 准备Git提交..."
git checkout -b streamlit-cloud-deployment
git add .
git commit -m "feat: Streamlit Cloud deployment ready

- 集成前后端为单体应用
- 实现会话级数据缓存
- 优化云端部署架构
- 保留核心功能完整性"

echo "🎯 准备推送到GitHub..."
echo "请手动执行: git push origin streamlit-cloud-deployment"
echo "然后在 Streamlit Cloud 中部署此分支"

echo "🌟 部署准备完成！"
```

### 7.2 README.md 更新
```markdown
# QuantDB Cloud Edition

**🌟 云端版本** | **📊 股票数据平台** | **⚡ 智能缓存** | **☁️ 随时访问**

## 🎯 项目简介

QuantDB Cloud Edition 是专为 Streamlit Cloud 优化的股票数据查询平台，提供：

- 📈 **股票数据查询**: 支持A股历史数据查询和多维度图表展示
- 📊 **资产信息展示**: 真实公司名称、财务指标、市场数据
- ⚡ **智能缓存**: 会话级数据缓存，避免重复请求
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

# 安装依赖
pip install -r requirements.txt

# 运行应用
streamlit run app.py
```

## 📋 功能特性

### 核心功能
- ✅ A股股票数据查询（沪深两市）
- ✅ 价格趋势图、K线图、成交量图
- ✅ 收益率分析和统计指标
- ✅ 公司基本信息和财务数据
- ✅ 会话级智能缓存
- ✅ 数据导出（CSV格式）

### 技术特点
- 🏗️ **单体架构**: 无需独立后端服务
- 💾 **会话缓存**: 基于Streamlit会话状态
- 📊 **实时数据**: 来源于AKShare官方接口
- 🎨 **响应式设计**: 适配不同屏幕尺寸
- ⚡ **性能优化**: 智能缓存和懒加载

## 🔧 技术栈

- **前端框架**: Streamlit
- **数据源**: AKShare
- **图表库**: Plotly
- **数据处理**: Pandas
- **部署平台**: Streamlit Community Cloud

## 📊 使用说明

1. **股票代码格式**: 6位数字（如：600000、000001、300001）
2. **支持市场**: 沪深A股、科创板
3. **数据范围**: 支持任意历史时间段查询
4. **缓存机制**: 会话期间自动缓存，提升查询速度

## 🎯 版本信息

- **当前版本**: v1.0.0-cloud
- **架构类型**: 单体应用
- **缓存策略**: 会话级别
- **数据持久化**: 无（会话结束清空）

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 🔗 相关链接

- **原项目**: [QuantDB](https://github.com/franksunye/quantdb)
- **问题反馈**: [Issues](https://github.com/franksunye/quantdb/issues)
- **维护者**: frank

---

⭐ 如果这个项目对你有帮助，请给个 Star！
```

这个完整的实施方案提供了从架构设计到具体代码实现的详细指导。你觉得这个方案如何？需要我继续完善其他页面的实现吗？
