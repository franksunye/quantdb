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

# 尝试添加项目根目录到Python路径以访问core模块
try:
    current_dir = Path(__file__).parent
    project_root = current_dir.parent.parent  # 回到QuantDB根目录
    sys.path.insert(0, str(project_root))

    # 添加本地src目录到路径（云端部署备用）
    src_dir = current_dir / "src"
    if src_dir.exists():
        sys.path.insert(0, str(src_dir))
except Exception as path_error:
    st.warning(f"路径设置警告: {path_error}")

# 设置云端模式标志 - 更智能的检测
CLOUD_MODE = True
try:
    # 检测是否在Streamlit Cloud环境
    import os
    if 'STREAMLIT_SHARING' in os.environ or 'STREAMLIT_CLOUD' in os.environ:
        CLOUD_MODE = True
        st.info("🌐 检测到Streamlit Cloud环境，使用云端模式")
    else:
        # 测试是否可以完整导入和初始化core模块
        from core.services import StockDataService, AssetInfoService, DatabaseCache
        from core.cache import AKShareAdapter
        from core.database import get_db

        # 测试是否可以创建数据库会话
        db_session = next(get_db())
        db_session.close()

        CLOUD_MODE = False
        st.info("🖥️ 检测到本地完整环境，使用完整模式")
except Exception as e:
    CLOUD_MODE = True
    st.info(f"🌐 环境检测失败，使用云端模式: {str(e)[:100]}...")

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

# 简化的数据库验证
@st.cache_resource
def verify_database():
    """验证数据库连接和表结构 - 简化版本"""
    try:
        import sqlite3
        from pathlib import Path

        current_dir = Path(__file__).parent
        db_path = current_dir / "database" / "stock_data.db"

        if not db_path.exists():
            st.warning(f"数据库文件不存在: {db_path}")
            return False

        # 测试SQLite连接
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # 检查表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]

        expected_tables = ['assets', 'daily_stock_data', 'intraday_stock_data', 'request_logs', 'data_coverage', 'system_metrics']
        existing_tables = [table for table in expected_tables if table in tables]
        missing_tables = [table for table in expected_tables if table not in tables]

        if missing_tables:
            st.warning(f"缺少数据库表: {missing_tables}")

        if existing_tables:
            st.success(f"数据库验证成功，找到表: {existing_tables}")

        # 测试基本查询
        if 'assets' in tables:
            cursor.execute("SELECT COUNT(*) FROM assets")
            asset_count = cursor.fetchone()[0]
            st.info(f"资产表中有 {asset_count} 条记录")

        conn.close()
        return len(existing_tables) > 0

    except Exception as e:
        st.error(f"数据库验证失败: {e}")
        return False

# 条件化的服务初始化
@st.cache_resource
def init_services():
    """初始化服务实例 - 支持完整模式和云端模式"""

    try:
        # 强制检查是否在云端环境
        import os
        is_streamlit_cloud = (
            'STREAMLIT_SHARING' in os.environ or
            'STREAMLIT_CLOUD' in os.environ or
            'HOSTNAME' in os.environ and 'streamlit' in os.environ.get('HOSTNAME', '').lower()
        )

        if not CLOUD_MODE and not is_streamlit_cloud:
            # 完整模式：尝试使用core模块（仅在非云端环境）
            try:
                from core.services import StockDataService, AssetInfoService, DatabaseCache
                from core.cache import AKShareAdapter
                from core.database import get_db

                # 创建数据库会话
                db_session = next(get_db())
                akshare_adapter = AKShareAdapter()

                result = {
                    'stock_service': StockDataService(db_session, akshare_adapter),
                    'asset_service': AssetInfoService(db_session),
                    'cache_service': DatabaseCache(db_session),
                    'akshare_adapter': akshare_adapter,
                    'db_session': db_session,
                    'mode': 'full',
                    'status': 'success',
                    'message': '完整服务初始化成功'
                }
                return result

            except Exception as full_error:
                # 完整模式失败，继续尝试云端模式
                pass

        # 云端模式：简化的服务初始化
        # 创建一个简化的服务容器
        services = {
            'stock_service': None,
            'asset_service': None,
            'cache_service': None,
            'akshare_adapter': None,
            'db_session': None,
            'mode': 'cloud',
            'status': 'success',
            'message': '云端服务初始化成功'
        }

        # 尝试基本的数据库连接
        try:
            import sqlite3
            from pathlib import Path

            current_dir = Path(__file__).parent
            db_path = current_dir / "database" / "stock_data.db"

            if not db_path.exists():
                # 尝试其他可能的路径
                alternative_paths = [
                    current_dir / "database" / "stock_data.db.backup",
                    Path("database/stock_data.db"),
                    Path("./database/stock_data.db")
                ]
                for alt_path in alternative_paths:
                    if alt_path.exists():
                        db_path = alt_path
                        break

            # 测试SQLite连接
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            conn.close()

            # 创建简化的服务对象
            services['db_path'] = str(db_path)
            services['table_count'] = len(tables)
            services['tables'] = [table[0] for table in tables]
            services['message'] = f'云端服务初始化成功，数据库连接正常（{len(tables)}个表）'

        except Exception as db_error:
            services['status'] = 'error'
            services['message'] = f'数据库连接失败: {db_error}'
            services['db_error'] = str(db_error)

        return services

    except Exception as e:
        return {
            'mode': 'error',
            'status': 'error',
            'message': f'服务初始化失败: {e}',
            'error': str(e)
        }

def show_initialization_status():
    """显示初始化状态"""
    services = init_services()
    if services:
        status = services.get('status', 'unknown')
        message = services.get('message', '初始化完成')
        mode = services.get('mode', 'unknown')

        if status == 'success':
            if mode == 'full':
                st.success(f"✅ {message}")
                # 测试DatabaseCache方法
                if services.get('cache_service'):
                    if hasattr(services['cache_service'], 'get_stats'):
                        st.success("✅ DatabaseCache.get_stats方法可用")
                    else:
                        st.error("❌ DatabaseCache.get_stats方法不可用")
            elif mode == 'cloud':
                st.info(f"☁️ {message}")
            else:
                st.success(f"✅ {message}")
        elif status == 'error':
            st.error(f"❌ {message}")
        else:
            st.warning(f"⚠️ {message}")
    else:
        st.error("❌ 服务初始化失败")

def get_system_status():
    """获取系统状态"""
    try:
        # 使用简化的配置，避免复杂的模块导入
        import os
        from pathlib import Path

        current_dir = Path(__file__).parent

        # 简化的数据库路径配置
        possible_db_paths = [
            current_dir / "database" / "stock_data.db",
            current_dir / "database" / "stock_data.db.backup",
            "database/stock_data.db",
            "./database/stock_data.db"
        ]

        DATABASE_PATH = None
        db_exists = False

        for path in possible_db_paths:
            if os.path.exists(path):
                DATABASE_PATH = str(path)
                db_exists = True
                break

        if not DATABASE_PATH:
            DATABASE_PATH = str(current_dir / "database" / "stock_data.db")

        DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

        # 尝试简化的服务初始化
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
                    'current_dir': str(current_dir),
                    'checked_paths': [str(p) for p in possible_db_paths]
                }
            }

        # 测试API响应时间
        start_time = time.time()

        # 改进的数据库查询测试
        asset_count = 0
        cache_stats = {}

        if services:
            if services.get('mode') == 'full':
                # 完整模式：使用服务查询
                try:
                    if services.get('db_session'):
                        from core.models import Asset
                        asset_count = services['db_session'].query(Asset).count()
                    if services.get('cache_service'):
                        # 检查cache_service是否有get_stats方法
                        if hasattr(services['cache_service'], 'get_stats'):
                            cache_stats = services['cache_service'].get_stats()
                        else:
                            st.warning("DatabaseCache对象缺少get_stats方法")
                            cache_stats = {'error': 'get_stats method not found'}
                except Exception as full_query_error:
                    st.error(f"完整模式查询错误: {full_query_error}")
                    st.error(f"错误类型: {type(full_query_error).__name__}")
                    # 强制切换到云端模式查询
                    asset_count = 0
                    cache_stats = {'error': str(full_query_error)}

            elif services.get('mode') == 'cloud':
                # 云端模式：使用SQLite直连查询
                try:
                    if 'db_path' in services and os.path.exists(services['db_path']):
                        import sqlite3
                        conn = sqlite3.connect(services['db_path'])
                        cursor = conn.cursor()

                        # 检查assets表是否存在
                        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='assets';")
                        if cursor.fetchone():
                            cursor.execute("SELECT COUNT(*) FROM assets")
                            asset_count = cursor.fetchone()[0]

                        # 获取简化的缓存统计
                        tables = services.get('tables', [])
                        cache_stats = {
                            'database_type': 'SQLite',
                            'status': 'active',
                            'tables': len(tables),
                            'table_names': tables
                        }

                        conn.close()

                except Exception as cloud_query_error:
                    st.warning(f"云端模式查询错误: {cloud_query_error}")
                    asset_count = 0
                    cache_stats = {
                        'database_type': 'SQLite',
                        'status': 'error',
                        'error': str(cloud_query_error)
                    }

        api_response_time = (time.time() - start_time) * 1000

        return {
            'api_status': 'running',
            'api_response_time': api_response_time,
            'asset_count': asset_count,
            'cache_stats': cache_stats,
            'service_mode': services.get('mode', 'unknown') if services else 'none',
            'debug_info': {
                'database_url': DATABASE_URL,
                'database_path': DATABASE_PATH,
                'db_exists': db_exists,
                'current_dir': str(current_dir),
                'services_available': bool(services),
                'cloud_mode': CLOUD_MODE
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

    # 显示初始化状态
    show_initialization_status()

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
            service_mode = system_status.get('service_mode', 'unknown')

            # 根据服务模式和缓存状态确定显示内容
            if cache_stats.get('status') == 'active':
                if service_mode == 'full':
                    cache_efficiency = "完整模式"
                    cache_delta = "核心服务"
                elif service_mode == 'cloud':
                    cache_efficiency = "云端模式"
                    cache_delta = f"SQLite({cache_stats.get('tables', 0)}表)"
                else:
                    cache_efficiency = "运行中"
                    cache_delta = "SQLite持久化"
            else:
                cache_efficiency = "初始化中"
                cache_delta = "请稍候"

            st.metric(
                label="缓存状态",
                value=cache_efficiency,
                delta=cache_delta
            )

        # 显示服务模式信息
        service_mode = system_status.get('service_mode', 'unknown')
        if service_mode != 'unknown':
            st.info(f"🔧 当前运行模式: **{service_mode.upper()}** {'(完整功能)' if service_mode == 'full' else '(云端优化)'}")

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
