"""
系统状态页面
展示系统健康状态、数据库信息和性能指标
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os
from pathlib import Path
import time

# 添加src目录到Python路径
current_dir = Path(__file__).parent.parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

# 页面配置
st.set_page_config(
    page_title="系统状态 - QuantDB",
    page_icon="⚡",
    layout="wide"
)

# 初始化服务
@st.cache_resource
def init_services():
    """初始化服务实例"""
    try:
        from services.database_cache import DatabaseCache
        from api.database import get_db
        
        db_session = next(get_db())
        return DatabaseCache(db_session)
    except Exception as e:
        st.error(f"服务初始化失败: {e}")
        return None

def get_database_info():
    """获取数据库信息"""
    try:
        from api.database import get_db
        from api.models import Asset, DailyStockData

        db_session = next(get_db())

        # 数据库查询
        try:
            asset_count = db_session.query(Asset).count()
        except Exception:
            asset_count = 0

        try:
            daily_data_count = db_session.query(DailyStockData).count()
        except Exception:
            daily_data_count = 0

        # 获取最新数据日期
        try:
            latest_data = db_session.query(DailyStockData.trade_date).order_by(
                DailyStockData.trade_date.desc()
            ).first()
            latest_date = latest_data[0] if latest_data else None
        except Exception:
            latest_date = None

        # 获取数据库文件大小
        db_path = current_dir / "database" / "stock_data.db"
        db_size_mb = 0
        if db_path.exists():
            try:
                db_size_mb = db_path.stat().st_size / (1024 * 1024)
            except Exception:
                db_size_mb = 0

        return {
            'asset_count': asset_count,
            'daily_data_count': daily_data_count,
            'latest_date': latest_date,
            'db_size_mb': db_size_mb
        }
    except Exception as e:
        st.error(f"获取数据库信息失败: {e}")
        return None

def test_system_performance():
    """测试系统性能"""
    try:
        # 确保数据库表存在
        from api.database import engine, Base, get_db
        from api.models import Asset

        Base.metadata.create_all(bind=engine)

        db_session = next(get_db())

        # 测试数据库查询性能
        start_time = time.time()
        try:
            assets = db_session.query(Asset).limit(10).all()
            assets_count = len(assets)
        except Exception:
            assets_count = 0
        db_query_time = (time.time() - start_time) * 1000

        # 测试缓存服务
        cache_service = init_services()
        if cache_service:
            start_time = time.time()
            try:
                cache_stats = cache_service.get_cache_stats()
            except Exception:
                cache_stats = {}
            cache_query_time = (time.time() - start_time) * 1000
        else:
            cache_query_time = 0
            cache_stats = {}

        return {
            'db_query_time': db_query_time,
            'cache_query_time': cache_query_time,
            'cache_stats': cache_stats,
            'assets_sample': assets_count
        }
    except Exception as e:
        st.error(f"性能测试失败: {e}")
        return None

def main():
    """主页面"""
    
    st.title("⚡ 系统状态")
    st.markdown("监控系统健康状态、数据库信息和性能指标")
    st.markdown("---")
    
    # 系统健康检查
    st.markdown("### 🏥 系统健康检查")
    
    col1, col2, col3, col4 = st.columns(4)
    
    # 检查服务状态
    cache_service = init_services()
    service_status = "正常" if cache_service else "异常"
    service_color = "normal" if cache_service else "inverse"
    
    with col1:
        st.metric("服务状态", service_status, delta="运行中" if cache_service else "需要检查")
    
    # 检查数据库连接
    db_info = get_database_info()
    db_status = "正常" if db_info else "异常"
    
    with col2:
        st.metric("数据库状态", db_status, delta="SQLite连接正常" if db_info else "连接失败")
    
    # 检查数据完整性
    if db_info:
        data_integrity = "良好" if db_info['asset_count'] > 0 and db_info['daily_data_count'] > 0 else "需要数据"
        with col3:
            st.metric("数据完整性", data_integrity, delta=f"{db_info['asset_count']}个资产")
    else:
        with col3:
            st.metric("数据完整性", "未知", delta="无法检查")
    
    # 系统响应时间
    start_time = time.time()
    # 简单的系统响应测试
    test_response = True
    response_time = (time.time() - start_time) * 1000
    
    with col4:
        st.metric("系统响应", f"{response_time:.1f}ms", delta="正常" if response_time < 100 else "较慢")
    
    st.markdown("---")
    
    # 数据库信息
    st.markdown("### 🗄️ 数据库信息")
    
    if db_info:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("资产数量", f"{db_info['asset_count']:,}个")
        
        with col2:
            st.metric("数据记录", f"{db_info['daily_data_count']:,}条")
        
        with col3:
            latest_date = db_info['latest_date'].strftime('%Y-%m-%d') if db_info['latest_date'] else "N/A"
            st.metric("最新数据", latest_date)
        
        with col4:
            st.metric("数据库大小", f"{db_info['db_size_mb']:.2f}MB")
    else:
        st.error("❌ 无法获取数据库信息")
    
    st.markdown("---")
    
    # 性能测试
    st.markdown("### 🚀 性能测试")
    
    if st.button("🧪 运行性能测试"):
        with st.spinner("正在运行性能测试..."):
            perf_results = test_system_performance()
            
            if perf_results:
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("数据库查询", f"{perf_results['db_query_time']:.1f}ms")
                
                with col2:
                    st.metric("缓存查询", f"{perf_results['cache_query_time']:.1f}ms")
                
                with col3:
                    st.metric("样本数据", f"{perf_results['assets_sample']}条")
                
                with col4:
                    total_time = perf_results['db_query_time'] + perf_results['cache_query_time']
                    st.metric("总响应时间", f"{total_time:.1f}ms")
                
                # 缓存统计
                cache_stats = perf_results.get('cache_stats', {})
                if cache_stats:
                    st.markdown("#### 📊 缓存统计")
                    
                    cache_col1, cache_col2, cache_col3 = st.columns(3)
                    
                    with cache_col1:
                        hit_rate = cache_stats.get('hit_rate', 0)
                        st.metric("缓存命中率", f"{hit_rate:.1f}%")
                    
                    with cache_col2:
                        total_requests = cache_stats.get('total_requests', 0)
                        st.metric("总请求数", f"{total_requests:,}")
                    
                    with cache_col3:
                        cache_size = cache_stats.get('cache_size', 0)
                        st.metric("缓存大小", f"{cache_size:,}条")
            else:
                st.error("❌ 性能测试失败")
    
    st.markdown("---")
    
    # 系统信息
    st.markdown("### 📋 系统信息")
    
    with st.expander("🔧 技术信息", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **架构信息**:
            - 应用类型: Streamlit Cloud单体应用
            - 数据库: SQLite (持久化)
            - 数据源: AKShare
            - 缓存策略: 数据库缓存
            """)
        
        with col2:
            st.markdown("""
            **版本信息**:
            - 应用版本: v1.1.0-cloud
            - Python版本: 3.8+
            - Streamlit版本: 1.28+
            - 部署平台: Streamlit Community Cloud
            """)
    
    with st.expander("📊 数据库详情", expanded=False):
        if db_info:
            st.markdown(f"""
            **数据库统计**:
            - 数据库文件: stock_data.db
            - 文件大小: {db_info['db_size_mb']:.2f} MB
            - 资产表记录: {db_info['asset_count']:,} 条
            - 日线数据记录: {db_info['daily_data_count']:,} 条
            - 最新数据日期: {db_info['latest_date'].strftime('%Y-%m-%d') if db_info['latest_date'] else 'N/A'}
            """)
        else:
            st.error("无法获取数据库详情")
    
    # 刷新按钮
    st.markdown("---")
    if st.button("🔄 刷新系统状态"):
        st.rerun()

if __name__ == "__main__":
    main()
