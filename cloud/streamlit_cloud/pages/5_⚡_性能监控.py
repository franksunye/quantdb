"""
性能监控页面 - 云端版本

展示系统性能指标、缓存命中率和响应时间监控。
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time
import sys
from pathlib import Path

# 添加src目录到Python路径
current_dir = Path(__file__).parent.parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

# 导入工具组件
try:
    from utils.charts import (
        create_performance_comparison_chart,
        create_cache_hit_pie_chart,
        create_data_coverage_timeline
    )
    from utils.config import config
    ADVANCED_FEATURES = True
except ImportError:
    ADVANCED_FEATURES = False

# 页面配置
st.set_page_config(
    page_title="性能监控 - QuantDB Cloud",
    page_icon="⚡",
    layout="wide"
)

@st.cache_resource
def init_services():
    """初始化服务实例"""
    try:
        from services.stock_data_service import StockDataService
        from services.database_cache import DatabaseCache
        from cache.akshare_adapter import AKShareAdapter
        from api.database import get_db

        db_session = next(get_db())
        akshare_adapter = AKShareAdapter()
        
        return {
            'stock_service': StockDataService(db_session, akshare_adapter),
            'cache_service': DatabaseCache(db_session),
            'db_session': db_session
        }
    except Exception as e:
        st.error(f"服务初始化失败: {e}")
        return None

def main():
    """主页面函数"""
    
    # 页面标题
    st.title("⚡ 性能监控")
    st.markdown("监控系统性能指标、缓存效率和响应时间")
    st.markdown("---")
    
    # 初始化服务
    services = init_services()
    if not services:
        st.error("❌ 服务初始化失败，请刷新页面重试")
        return
    
    # 控制面板
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.markdown("### 📊 实时性能监控")
    
    with col2:
        auto_refresh = st.checkbox("自动刷新", value=False, help="每30秒自动刷新数据")
    
    with col3:
        if st.button("🔄 立即刷新", use_container_width=True):
            st.session_state.force_refresh = True
            # 清除缓存以获取最新数据
            init_services.clear()
    
    # 自动刷新逻辑
    if auto_refresh:
        time.sleep(30)
        st.rerun()
    
    # 显示性能监控数据
    display_performance_monitoring(services)

def display_performance_monitoring(services):
    """显示性能监控数据"""
    
    try:
        # 获取缓存统计
        with st.spinner("获取性能数据..."):
            cache_stats = services['cache_service'].get_stats()
        
        # 核心性能指标
        st.subheader("🚀 核心性能指标")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # 模拟缓存响应时间（基于实际数据库查询）
            from sqlalchemy import text
            start_time = time.time()
            test_query = services['db_session'].execute(text("SELECT COUNT(*) FROM assets")).scalar()
            cache_response_time = (time.time() - start_time) * 1000
            
            st.metric(
                label="数据库响应时间",
                value=f"{cache_response_time:.1f}ms",
                delta="极快",
                help="从SQLite数据库获取数据的响应时间"
            )
        
        with col2:
            # 模拟AKShare响应时间
            akshare_response_time = 1200.0
            st.metric(
                label="AKShare响应时间",
                value=f"{akshare_response_time:.1f}ms",
                help="直接从AKShare获取数据的估计响应时间"
            )
        
        with col3:
            # 计算性能提升
            performance_improvement = ((akshare_response_time - cache_response_time) / akshare_response_time * 100)
            st.metric(
                label="性能提升",
                value=f"{performance_improvement:.1f}%",
                delta="优秀",
                help="本地缓存相比AKShare直接调用的性能提升"
            )
        
        with col4:
            # 数据覆盖率
            total_assets = cache_stats.get('total_assets', 0)
            total_data_points = cache_stats.get('total_data_points', 0)
            coverage_rate = min(100, (total_data_points / 1000) * 100) if total_data_points > 0 else 0
            
            st.metric(
                label="数据覆盖率",
                value=f"{coverage_rate:.1f}%",
                delta="良好" if coverage_rate > 50 else "建设中",
                help="数据库中数据的覆盖程度"
            )
        
        st.markdown("---")
        
        # 性能对比图表
        if ADVANCED_FEATURES:
            st.subheader("📊 性能对比分析")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 响应时间对比")
                perf_chart = create_performance_comparison_chart(cache_response_time, akshare_response_time)
                st.plotly_chart(perf_chart, use_container_width=True)
            
            with col2:
                st.markdown("#### 数据覆盖分布")
                # 模拟缓存命中率
                cache_hits = int(coverage_rate)
                cache_misses = 100 - cache_hits
                cache_pie = create_cache_hit_pie_chart(cache_hits, cache_misses)
                st.plotly_chart(cache_pie, use_container_width=True)
        
        # 系统资源监控
        st.markdown("---")
        st.subheader("💻 系统资源监控")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # 计算数据库大小（估算）
            db_size = total_data_points * 0.1 / 1024  # 估算每条记录约0.1KB
            st.metric(
                label="数据库大小",
                value=f"{db_size:.1f} MB",
                help="SQLite数据库估算大小"
            )
        
        with col2:
            st.metric(
                label="总记录数",
                value=f"{total_data_points:,}",
                help="数据库中的历史数据记录总数"
            )
        
        with col3:
            st.metric(
                label="缓存资产数",
                value=f"{total_assets:,}",
                help="已缓存的股票资产数量"
            )
        
        with col4:
            # 计算数据密度
            data_density = total_data_points / total_assets if total_assets > 0 else 0
            st.metric(
                label="平均数据密度",
                value=f"{data_density:.0f}条/股",
                help="每只股票的平均历史数据记录数"
            )
        
        # 实时性能测试
        st.markdown("---")
        st.subheader("🧪 实时性能测试")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("测试数据库查询", use_container_width=True):
                test_database_performance(services)
        
        with col2:
            if st.button("测试数据查询性能", use_container_width=True):
                test_data_query_performance(services)
        
        with col3:
            if st.button("测试缓存性能", use_container_width=True):
                test_cache_performance(services)
        
        # 数据库详细信息
        st.markdown("---")
        st.subheader("📈 数据库详细信息")
        
        if cache_stats:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 📊 数据统计")
                date_range = cache_stats.get('date_range', {})
                st.write(f"**最早数据**: {date_range.get('min_date', 'N/A')}")
                st.write(f"**最新数据**: {date_range.get('max_date', 'N/A')}")
                st.write(f"**总资产数**: {total_assets:,}")
                st.write(f"**总数据点**: {total_data_points:,}")
            
            with col2:
                st.markdown("#### 🏆 热门资产")
                top_assets = cache_stats.get('top_assets', [])
                if top_assets:
                    for i, asset in enumerate(top_assets[:5], 1):
                        st.write(f"{i}. **{asset['symbol']}** - {asset['name']} ({asset['data_points']}条)")
                else:
                    st.write("暂无数据")
        
    except Exception as e:
        st.error(f"获取性能数据失败: {str(e)}")
        st.info("请检查数据库连接状态")

def test_database_performance(services):
    """测试数据库查询性能"""
    with st.spinner("测试数据库查询性能..."):
        try:
            # 进行多次测试取平均值
            from sqlalchemy import text
            times = []
            for i in range(5):
                start_time = time.time()
                result = services['db_session'].execute(text("SELECT COUNT(*) FROM daily_stock_data")).scalar()
                end_time = time.time()
                times.append((end_time - start_time) * 1000)
            
            avg_time = sum(times) / len(times)
            min_time = min(times)
            max_time = max(times)
            
            st.success("✅ 数据库查询性能测试完成")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("平均响应时间", f"{avg_time:.1f}ms")
            with col2:
                st.metric("最快响应时间", f"{min_time:.1f}ms")
            with col3:
                st.metric("最慢响应时间", f"{max_time:.1f}ms")
            
        except Exception as e:
            st.error(f"数据库查询测试失败: {str(e)}")

def test_data_query_performance(services):
    """测试数据查询性能"""
    with st.spinner("测试数据查询性能..."):
        try:
            # 测试股票数据查询
            start_time = time.time()
            stock_data = services['stock_service'].get_stock_data("600000", "20240101", "20240105")
            end_time = time.time()
            
            response_time = (end_time - start_time) * 1000
            
            if stock_data is not None and not stock_data.empty:
                record_count = len(stock_data)
                
                st.success("✅ 数据查询性能测试完成")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("响应时间", f"{response_time:.1f}ms")
                with col2:
                    st.metric("数据记录数", f"{record_count}")
                with col3:
                    status = "优秀" if response_time < 100 else "良好" if response_time < 1000 else "需优化"
                    st.metric("性能等级", status)
            
        except Exception as e:
            st.error(f"数据查询测试失败: {str(e)}")

def test_cache_performance(services):
    """测试缓存性能"""
    with st.spinner("测试缓存性能..."):
        try:
            # 连续查询同一数据，测试缓存效果
            symbol = "600000"
            start_date = "20240101"
            end_date = "20240105"
            
            times = []
            
            for i in range(3):
                start_time = time.time()
                stock_data = services['stock_service'].get_stock_data(symbol, start_date, end_date)
                end_time = time.time()
                
                response_time = (end_time - start_time) * 1000
                times.append(response_time)
            
            avg_time = sum(times) / len(times)
            improvement = ((times[0] - times[-1]) / times[0] * 100) if times[0] > 0 else 0
            
            st.success("✅ 缓存性能测试完成")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("平均响应时间", f"{avg_time:.1f}ms")
            with col2:
                st.metric("首次查询", f"{times[0]:.1f}ms")
            with col3:
                st.metric("后续查询", f"{times[-1]:.1f}ms")
            
            if improvement > 0:
                st.info(f"🚀 缓存效果: 性能提升 {improvement:.1f}%")
            
        except Exception as e:
            st.error(f"缓存性能测试失败: {str(e)}")

if __name__ == "__main__":
    main()
