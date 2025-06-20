"""
QuantDB Streamlit Cloud Edition - 主应用入口
适配Streamlit Cloud部署的单体应用架构，保留SQLite数据库和完整功能
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys
import os
from pathlib import Path
import time

# 添加项目根目录到Python路径以访问core模块
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent  # 回到QuantDB根目录
sys.path.insert(0, str(project_root))

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
        
        **版本**: v1.1.0-cloud
        
        高性能股票数据查询平台，专为Streamlit Cloud优化。
        
        ## 核心功能
        - 📈 股票数据查询和图表展示
        - 📊 资产信息和财务指标
        - ⚡ 智能缓存和性能监控
        
        ## 技术特点
        - 🚀 SQLite数据库持久化
        - 🏢 真实公司名称和财务数据
        - 📊 专业的数据可视化
        - ☁️ 云端部署，随时访问
        
        ---
        
        **GitHub**: https://github.com/franksunye/quantdb
        **维护者**: frank
        """
    }
)

# 验证数据库
@st.cache_resource
def verify_database():
    """验证数据库连接和表结构"""
    try:
        from core.database import engine, Base, SessionLocal
        from core.models import Asset, DailyStockData, IntradayStockData, RequestLog, DataCoverage, SystemMetrics
        from sqlalchemy import inspect

        # 检查数据库连接
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()

        expected_tables = ['assets', 'daily_stock_data', 'intraday_stock_data', 'request_logs', 'data_coverage', 'system_metrics']
        missing_tables = [table for table in expected_tables if table not in existing_tables]

        if missing_tables:
            st.warning(f"缺少数据库表: {missing_tables}")
            # 尝试创建缺失的表
            Base.metadata.create_all(bind=engine)
            st.info("已尝试创建缺失的表")

        # 测试基本查询
        db_session = SessionLocal()
        try:
            asset_count = db_session.query(Asset).count()
            st.success(f"数据库验证成功，找到 {asset_count} 个资产")
            return True
        except Exception as query_error:
            st.error(f"数据库查询测试失败: {query_error}")
            # 尝试重新创建所有表
            Base.metadata.drop_all(bind=engine)
            Base.metadata.create_all(bind=engine)
            st.info("已重新创建所有数据库表")
            return False
        finally:
            db_session.close()

    except Exception as e:
        st.error(f"数据库验证失败: {e}")
        return False

# 初始化服务
@st.cache_resource
def init_services():
    """初始化服务实例"""
    try:
        # 首先验证数据库
        if not verify_database():
            st.warning("数据库验证失败，但继续尝试初始化服务")

        # 导入现有服务
        from core.services import StockDataService, AssetInfoService, DatabaseCache
        from core.cache import AKShareAdapter
        from core.database import get_db

        # 创建数据库会话
        db_session = next(get_db())

        # 创建AKShare适配器
        akshare_adapter = AKShareAdapter()

        return {
            'stock_service': StockDataService(db_session, akshare_adapter),
            'asset_service': AssetInfoService(db_session),
            'cache_service': DatabaseCache(db_session),
            'akshare_adapter': akshare_adapter,
            'db_session': db_session
        }
    except Exception as e:
        st.error(f"服务初始化失败: {e}")
        return None

def get_system_status():
    """获取系统状态"""
    try:
        # Debug information
        from core.utils.config import DATABASE_URL, DATABASE_PATH
        import os
        from pathlib import Path

        # Check database file existence
        db_exists = os.path.exists(DATABASE_PATH)
        current_dir = Path(__file__).parent

        services = init_services()
        if not services:
            return {
                'api_status': 'service_error',
                'api_response_time': 0,
                'asset_count': 0,
                'cache_stats': {},
                'debug_info': {
                    'database_url': DATABASE_URL,
                    'database_path': DATABASE_PATH,
                    'db_exists': db_exists,
                    'current_dir': str(current_dir)
                }
            }

        # 测试API响应时间
        start_time = time.time()

        # 数据库查询测试
        try:
            from core.models import Asset
            asset_count = services['db_session'].query(Asset).count()
        except Exception as db_error:
            asset_count = 0
            # Add debug info for database errors
            st.error(f"数据库查询错误: {db_error}")
            st.info(f"数据库路径: {DATABASE_PATH}")
            st.info(f"数据库存在: {db_exists}")

        api_response_time = (time.time() - start_time) * 1000

        # 获取缓存状态
        try:
            cache_stats = services['cache_service'].get_cache_stats()
        except Exception:
            cache_stats = {}

        return {
            'api_status': 'running',
            'api_response_time': api_response_time,
            'asset_count': asset_count,
            'cache_stats': cache_stats,
            'debug_info': {
                'database_url': DATABASE_URL,
                'database_path': DATABASE_PATH,
                'db_exists': db_exists,
                'current_dir': str(current_dir)
            }
        }
    except Exception as e:
        st.error(f"获取系统状态失败: {e}")
        return {
            'api_status': 'error',
            'api_response_time': 0,
            'asset_count': 0,
            'cache_stats': {},
            'debug_info': {'error': str(e)}
        }

def main():
    """主页面"""
    
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
        - ⚡ **智能缓存**: SQLite数据库缓存，98.1%性能提升
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
    st.markdown("### 📊 系统状态概览")
    
    system_status = get_system_status()
    
    if system_status:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="API状态",
                value="运行中" if system_status['api_status'] == 'running' else "异常",
                delta="正常" if system_status['api_status'] == 'running' else "需要检查"
            )
        
        with col2:
            st.metric(
                label="响应时间",
                value=f"{system_status['api_response_time']:.1f}ms",
                delta="极快" if system_status['api_response_time'] < 100 else "正常"
            )
        
        with col3:
            asset_count = system_status['asset_count']
            st.metric(
                label="资产数量",
                value=f"{asset_count}个",
                delta="数据库正常" if asset_count > 0 else "需要数据"
            )
        
        with col4:
            cache_stats = system_status.get('cache_stats', {})
            cache_efficiency = "优秀" if asset_count > 5 else "建设中"
            st.metric(
                label="缓存状态",
                value=cache_efficiency,
                delta="SQLite持久化"
            )

        # Debug information (only show if there are issues)
        if asset_count == 0 and 'debug_info' in system_status:
            with st.expander("🔍 调试信息 (资产数量为0时显示)", expanded=True):
                debug_info = system_status['debug_info']
                st.write("**数据库配置信息:**")
                st.json(debug_info)

                # Additional file check
                import os
                st.write("**文件系统检查:**")
                current_files = []
                try:
                    for root, dirs, files in os.walk('.'):
                        for file in files:
                            if file.endswith('.db'):
                                current_files.append(os.path.join(root, file))
                    st.write(f"找到的数据库文件: {current_files}")
                except Exception as e:
                    st.write(f"文件检查错误: {e}")
    else:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(label="API状态", value="初始化中", delta="请稍候")
        with col2:
            st.metric(label="响应时间", value="N/A", delta="测量中")
        with col3:
            st.metric(label="资产数量", value="N/A", delta="加载中")
        with col4:
            st.metric(label="缓存状态", value="N/A", delta="准备中")
    
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
        - 数据库状态监控
        - 系统性能指标展示
        - 缓存效率统计
        - 服务健康检查
        
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
           - 系统自动获取并缓存数据到SQLite数据库
        
        3. **数据持久化**
           - 使用SQLite数据库持久化存储
           - 应用重启后数据仍然保留
           - 智能缓存避免重复API调用
        
        4. **注意事项**
           - 数据来源：AKShare官方接口
           - 缓存机制：SQLite数据库持久化
           - 建议使用：Chrome、Firefox、Edge浏览器
        """)

if __name__ == "__main__":
    main()
