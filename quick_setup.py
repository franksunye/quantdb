#!/usr/bin/env python3
"""
QuantDB Streamlit Cloud 快速设置脚本
自动创建云端部署所需的目录结构和核心文件
"""

import os
import shutil
from pathlib import Path

def create_directory_structure():
    """创建目录结构"""
    print("📁 创建目录结构...")
    
    base_dir = Path("quantdb_streamlit_cloud")
    
    # 创建主目录
    base_dir.mkdir(exist_ok=True)
    
    # 创建子目录
    directories = [
        "pages",
        "services", 
        "utils",
        ".streamlit"
    ]
    
    for dir_name in directories:
        (base_dir / dir_name).mkdir(exist_ok=True)
        
        # 创建__init__.py文件
        if dir_name in ["services", "utils"]:
            (base_dir / dir_name / "__init__.py").touch()
    
    print("✅ 目录结构创建完成")
    return base_dir

def copy_core_files(base_dir):
    """复制核心文件"""
    print("📋 复制核心文件...")
    
    # 从现有项目复制必要的服务文件
    source_files = {
        "src/cache/akshare_adapter.py": "services/akshare_adapter.py",
        "src/services/trading_calendar.py": "services/trading_calendar.py",
        "quantdb_frontend/utils/charts.py": "utils/charts.py"
    }
    
    for source, target in source_files.items():
        source_path = Path(source)
        target_path = base_dir / target
        
        if source_path.exists():
            shutil.copy2(source_path, target_path)
            print(f"  ✅ 复制 {source} -> {target}")
        else:
            print(f"  ⚠️  源文件不存在: {source}")
    
    print("✅ 核心文件复制完成")

def create_requirements_txt(base_dir):
    """创建requirements.txt"""
    print("📦 创建requirements.txt...")
    
    requirements = """# 核心框架
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
"""
    
    with open(base_dir / "requirements.txt", "w", encoding="utf-8") as f:
        f.write(requirements)
    
    print("✅ requirements.txt 创建完成")

def create_streamlit_config(base_dir):
    """创建Streamlit配置文件"""
    print("⚙️ 创建Streamlit配置...")
    
    config_content = """[server]
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
"""
    
    with open(base_dir / ".streamlit" / "config.toml", "w", encoding="utf-8") as f:
        f.write(config_content)
    
    print("✅ Streamlit配置创建完成")

def create_main_app(base_dir):
    """创建主应用文件"""
    print("🎯 创建主应用文件...")
    
    app_content = '''"""
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
    initial_sidebar_state="expanded"
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
        'app_start_time': datetime.now()
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

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
    
    session_duration = datetime.now() - st.session_state.app_start_time
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="缓存股票数",
            value=len(st.session_state.stock_data_cache),
            delta="个股票" if len(st.session_state.stock_data_cache) > 0 else "暂无数据"
        )
    
    with col2:
        st.metric(
            label="资产信息数",
            value=len(st.session_state.asset_info_cache),
            delta="个公司" if len(st.session_state.asset_info_cache) > 0 else "暂无数据"
        )
    
    with col3:
        st.metric(
            label="总查询次数",
            value=st.session_state.performance_metrics['total_queries'],
            delta=f"命中率 {st.session_state.performance_metrics.get('cache_hits', 0) / max(st.session_state.performance_metrics['total_queries'], 1) * 100:.1f}%"
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

if __name__ == "__main__":
    main()
'''
    
    with open(base_dir / "app.py", "w", encoding="utf-8") as f:
        f.write(app_content)
    
    print("✅ 主应用文件创建完成")

def create_readme(base_dir):
    """创建README文件"""
    print("📖 创建README文件...")
    
    readme_content = """# QuantDB Cloud Edition

**🌟 云端版本** | **📊 股票数据平台** | **⚡ 智能缓存** | **☁️ 随时访问**

## 🎯 项目简介

QuantDB Cloud Edition 是专为 Streamlit Cloud 优化的股票数据查询平台。

## 🚀 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 运行应用
streamlit run app.py
```

## 📋 功能特性

- ✅ A股股票数据查询（沪深两市）
- ✅ 价格趋势图、K线图、成交量图
- ✅ 收益率分析和统计指标
- ✅ 会话级智能缓存
- ✅ 数据导出（CSV格式）

## 🔧 技术栈

- **前端框架**: Streamlit
- **数据源**: AKShare
- **图表库**: Plotly
- **数据处理**: Pandas

## 📄 许可证

MIT License

---

⭐ 如果这个项目对你有帮助，请给个 Star！
"""
    
    with open(base_dir / "README.md", "w", encoding="utf-8") as f:
        f.write(readme_content)
    
    print("✅ README文件创建完成")

def main():
    """主函数"""
    print("🚀 QuantDB Streamlit Cloud 快速设置")
    print("=" * 50)
    
    try:
        # 创建目录结构
        base_dir = create_directory_structure()
        
        # 复制核心文件
        copy_core_files(base_dir)
        
        # 创建配置文件
        create_requirements_txt(base_dir)
        create_streamlit_config(base_dir)
        
        # 创建应用文件
        create_main_app(base_dir)
        create_readme(base_dir)
        
        print("\n🎉 设置完成！")
        print(f"📁 项目目录: {base_dir.absolute()}")
        print("\n📋 下一步操作:")
        print(f"1. cd {base_dir}")
        print("2. pip install -r requirements.txt")
        print("3. streamlit run app.py")
        print("\n🌟 本地测试成功后，可以部署到 Streamlit Cloud")
        
    except Exception as e:
        print(f"❌ 设置过程中出现错误: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
