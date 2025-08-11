"""
Performance Monitoring Page - Cloud Version

Display system performance metrics, cache hit rates and response time monitoring.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time
import sys
from pathlib import Path

# 添加项目根目录到Python路径以访问core模块
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent  # 回到QuantDB根目录
sys.path.insert(0, str(project_root))

# 导入工具组件
try:
    import plotly.graph_objects as go
    import plotly.express as px

    ADVANCED_FEATURES = True
except ImportError:
    ADVANCED_FEATURES = False

# Detect running environment
CLOUD_MODE = True
try:
    # Detect if in Streamlit Cloud environment
    import os

    if "STREAMLIT_SHARING" in os.environ or "STREAMLIT_CLOUD" in os.environ:
        CLOUD_MODE = True
    else:
        # Test if core modules can be imported
        from core.services import StockDataService

        CLOUD_MODE = False
except Exception:
    CLOUD_MODE = True

# 页面配置
st.set_page_config(page_title="Performance - QuantDB", page_icon="📊", layout="wide")


@st.cache_resource
def init_services():
    """Initialize service instances - cloud optimized version"""
    try:
        if not CLOUD_MODE:
            # Full mode: use core modules
            from core.services import StockDataService, DatabaseCache
            from core.cache import AKShareAdapter
            from core.database import get_db

            db_session = next(get_db())
            akshare_adapter = AKShareAdapter()

            return {
                "stock_service": StockDataService(db_session, akshare_adapter),
                "cache_service": DatabaseCache(db_session),
                "db_session": db_session,
                "mode": "full",
            }
        else:
            # Cloud mode: simplified service initialization
            import sqlite3
            from pathlib import Path

            current_dir = Path(__file__).parent
            db_path = current_dir / "database" / "stock_data.db"

            # Test SQLite connection
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            # Get basic statistics
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]

            # Get asset count
            asset_count = 0
            data_count = 0
            if "assets" in tables:
                cursor.execute("SELECT COUNT(*) FROM assets")
                asset_count = cursor.fetchone()[0]

            if "daily_stock_data" in tables:
                cursor.execute("SELECT COUNT(*) FROM daily_stock_data")
                data_count = cursor.fetchone()[0]

            conn.close()

            return {
                "db_path": str(db_path),
                "tables": tables,
                "asset_count": asset_count,
                "data_count": data_count,
                "mode": "cloud",
            }

    except Exception as e:
        st.error(f"Service initialization failed: {e}")
        # Return minimal service object to avoid page crash
        return {"mode": "minimal", "error": str(e), "asset_count": 0, "data_count": 0}


def main():
    """主页面函数"""

    # Page title
    st.title("⚡ Performance Monitoring")
    st.markdown("Monitor system performance metrics, cache efficiency and response time")
    st.markdown("---")

    # Initialize services
    services = init_services()
    if not services:
        st.error("❌ Service initialization failed, please refresh the page and try again")
        return

    # Display running mode
    mode = services.get("mode", "unknown")
    if mode == "full":
        st.info("🖥️ Running Mode: Full Mode (using core services)")
    elif mode == "cloud":
        st.info("☁️ Running Mode: Cloud Mode (SQLite direct connection)")
    elif mode == "minimal":
        st.warning("⚠️ Running Mode: Minimal Mode (limited functionality)")
        st.error(f"Initialization error: {services.get('error', 'Unknown error')}")

    # Control panel
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        st.markdown("### 📊 Real-time Performance Monitoring")

    with col2:
        auto_refresh = st.checkbox(
            "Auto Refresh", value=False, help="Auto refresh data every 30 seconds"
        )

    with col3:
        if st.button("🔄 Refresh Now", use_container_width=True):
            st.session_state.force_refresh = True
            # Clear cache to get latest data
            init_services.clear()

    # 自动刷新逻辑
    if auto_refresh:
        time.sleep(30)
        st.rerun()

    # Display performance monitoring data
    display_performance_monitoring(services)


def display_performance_monitoring(services):
    """Display performance monitoring data"""

    try:
        mode = services.get("mode", "unknown")

        # Get cache statistics
        with st.spinner("Getting performance data..."):
            if mode == "full":
                # Full mode: use cache_service
                cache_stats = services["cache_service"].get_stats()
            elif mode == "cloud":
                # Cloud mode: construct statistics data
                cache_stats = {
                    "total_assets": services.get("asset_count", 0),
                    "total_data_points": services.get("data_count", 0),
                    "date_range": {"min_date": "N/A", "max_date": "N/A"},
                    "top_assets": [],
                }

                # Try to get more detailed statistics
                try:
                    import sqlite3

                    conn = sqlite3.connect(services["db_path"])
                    cursor = conn.cursor()

                    # Get date range
                    if "daily_stock_data" in services.get("tables", []):
                        cursor.execute("SELECT MIN(date), MAX(date) FROM daily_stock_data")
                        date_range = cursor.fetchone()
                        if date_range[0] and date_range[1]:
                            cache_stats["date_range"] = {
                                "min_date": str(date_range[0]),
                                "max_date": str(date_range[1]),
                            }

                    conn.close()
                except Exception as e:
                    st.warning(f"Failed to get detailed statistics: {e}")
            else:
                # Minimal mode: use default values
                cache_stats = {
                    "total_assets": 0,
                    "total_data_points": 0,
                    "date_range": {"min_date": "N/A", "max_date": "N/A"},
                    "top_assets": [],
                }

        # Core performance metrics
        st.subheader("🚀 Core Performance Metrics")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            # Test database response time
            start_time = time.time()

            if mode == "full":
                # Full mode: use SQLAlchemy
                from sqlalchemy import text

                test_query = (
                    services["db_session"].execute(text("SELECT COUNT(*) FROM assets")).scalar()
                )
            elif mode == "cloud":
                # Cloud mode: use SQLite direct connection
                import sqlite3

                conn = sqlite3.connect(services["db_path"])
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM assets")
                test_query = cursor.fetchone()[0]
                conn.close()
            else:
                test_query = 0

            cache_response_time = (time.time() - start_time) * 1000

            st.metric(
                label="Database Response Time",
                value=f"{cache_response_time:.1f}ms",
                delta="Excellent" if cache_response_time < 50 else "Fast",
                help="Response time for getting data from SQLite database",
            )

        with col2:
            # Simulate AKShare response time
            akshare_response_time = 1200.0
            st.metric(
                label="AKShare Response Time",
                value=f"{akshare_response_time:.1f}ms",
                help="Estimated response time for getting data directly from AKShare",
            )

        with col3:
            # Calculate performance improvement
            performance_improvement = (
                (akshare_response_time - cache_response_time) / akshare_response_time * 100
            )
            st.metric(
                label="Performance Improvement",
                value=f"{performance_improvement:.1f}%",
                delta="Excellent",
                help="Performance improvement of local cache compared to AKShare direct calls",
            )

        with col4:
            # Data coverage rate
            total_assets = cache_stats.get("total_assets", 0)
            total_data_points = cache_stats.get("total_data_points", 0)
            coverage_rate = (
                min(100, (total_data_points / 1000) * 100) if total_data_points > 0 else 0
            )

            st.metric(
                label="Data Coverage Rate",
                value=f"{coverage_rate:.1f}%",
                delta="Good" if coverage_rate > 50 else "Building",
                help="Coverage level of data in database",
            )

        st.markdown("---")

        # Performance comparison charts
        if ADVANCED_FEATURES:
            st.subheader("📊 Performance Comparison Analysis")

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("#### Response Time Comparison")
                perf_chart = create_performance_comparison_chart(
                    cache_response_time, akshare_response_time
                )
                st.plotly_chart(perf_chart, use_container_width=True)

            with col2:
                st.markdown("#### Data Coverage Distribution")
                # Simulate cache hit rate
                cache_hits = int(coverage_rate)
                cache_misses = 100 - cache_hits
                cache_pie = create_cache_hit_pie_chart(cache_hits, cache_misses)
                st.plotly_chart(cache_pie, use_container_width=True)
        else:
            st.info(
                "📊 Chart functionality requires plotly support, currently using simplified display mode"
            )

        # System resource monitoring
        st.markdown("---")
        st.subheader("💻 System Resource Monitoring")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            # Calculate database size (estimated)
            db_size = total_data_points * 0.1 / 1024  # Estimate ~0.1KB per record
            st.metric(
                label="Database Size",
                value=f"{db_size:.1f} MB",
                help="Estimated SQLite database size",
            )

        with col2:
            st.metric(
                label="Total Records",
                value=f"{total_data_points:,}",
                help="Total historical data records in database",
            )

        with col3:
            st.metric(
                label="Cached Assets",
                value=f"{total_assets:,}",
                help="Number of cached stock assets",
            )

        with col4:
            # Calculate data density
            data_density = total_data_points / total_assets if total_assets > 0 else 0
            st.metric(
                label="Average Data Density",
                value=f"{data_density:.0f} records/stock",
                help="Average historical data records per stock",
            )

        # Real-time performance testing
        st.markdown("---")
        st.subheader("🧪 Real-time Performance Testing")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("Test Database Query", use_container_width=True):
                test_database_performance(services)

        with col2:
            if st.button("Test Data Query Performance", use_container_width=True):
                test_data_query_performance(services)

        with col3:
            if st.button("Test Cache Performance", use_container_width=True):
                test_cache_performance(services)

        # Database detailed information
        st.markdown("---")
        st.subheader("📈 Database Detailed Information")

        if cache_stats:
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("#### 📊 Data Statistics")
                date_range = cache_stats.get("date_range", {})
                st.write(f"**Earliest Data**: {date_range.get('min_date', 'N/A')}")
                st.write(f"**Latest Data**: {date_range.get('max_date', 'N/A')}")
                st.write(f"**Total Assets**: {total_assets:,}")
                st.write(f"**Total Data Points**: {total_data_points:,}")

            with col2:
                st.markdown("#### 🏆 Popular Assets")
                top_assets = cache_stats.get("top_assets", [])
                if top_assets:
                    for i, asset in enumerate(top_assets[:5], 1):
                        st.write(
                            f"{i}. **{asset['symbol']}** - {asset['name']} ({asset['data_points']} records)"
                        )
                else:
                    st.write("No data available")

    except Exception as e:
        st.error(f"Failed to get performance data: {str(e)}")
        st.info("Please check database connection status")


def test_database_performance(services):
    """Test database query performance"""
    with st.spinner("Testing database query performance..."):
        try:
            mode = services.get("mode", "unknown")
            times = []

            # Perform multiple tests to get average
            for i in range(5):
                start_time = time.time()

                if mode == "full":
                    # Full mode: use SQLAlchemy
                    from sqlalchemy import text

                    result = (
                        services["db_session"]
                        .execute(text("SELECT COUNT(*) FROM daily_stock_data"))
                        .scalar()
                    )
                elif mode == "cloud":
                    # Cloud mode: use SQLite direct connection
                    import sqlite3

                    conn = sqlite3.connect(services["db_path"])
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM daily_stock_data")
                    result = cursor.fetchone()[0]
                    conn.close()
                else:
                    result = 0

                end_time = time.time()
                times.append((end_time - start_time) * 1000)

            avg_time = sum(times) / len(times)
            min_time = min(times)
            max_time = max(times)

            st.success("✅ Database query performance test completed")

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Average Response Time", f"{avg_time:.1f}ms")
            with col2:
                st.metric("Fastest Response Time", f"{min_time:.1f}ms")
            with col3:
                st.metric("Slowest Response Time", f"{max_time:.1f}ms")

        except Exception as e:
            st.error(f"Database query test failed: {str(e)}")
            with st.expander("🔍 Error Details"):
                st.code(str(e))


def test_data_query_performance(services):
    """测试数据查询性能"""
    with st.spinner("测试数据查询性能..."):
        try:
            mode = services.get("mode", "unknown")
            start_time = time.time()

            if mode == "full":
                # 完整模式：使用stock_service
                stock_data = services["stock_service"].get_stock_data(
                    "600000", "20240101", "20240105"
                )
                record_count = (
                    len(stock_data) if stock_data is not None and not stock_data.empty else 0
                )
            elif mode == "cloud":
                # 云端模式：直接查询数据库
                import sqlite3

                conn = sqlite3.connect(services["db_path"])
                cursor = conn.cursor()

                # 查询600000的数据
                cursor.execute(
                    """
                    SELECT COUNT(*) FROM daily_stock_data d
                    JOIN assets a ON d.asset_id = a.asset_id
                    WHERE a.symbol = '600000' AND d.date BETWEEN '2024-01-01' AND '2024-01-05'
                """
                )
                record_count = cursor.fetchone()[0]
                conn.close()
            else:
                record_count = 0

            end_time = time.time()
            response_time = (end_time - start_time) * 1000

            st.success("✅ Data query performance test completed")

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Response Time", f"{response_time:.1f}ms")
            with col2:
                st.metric("Data Records", f"{record_count}")
            with col3:
                status = (
                    "Excellent"
                    if response_time < 100
                    else "Good" if response_time < 1000 else "Needs Optimization"
                )
                st.metric("Performance Level", status)

        except Exception as e:
            st.error(f"Data query test failed: {str(e)}")
            with st.expander("🔍 Error Details"):
                st.code(str(e))


def test_cache_performance(services):
    """测试缓存性能"""
    with st.spinner("测试缓存性能..."):
        try:
            mode = services.get("mode", "unknown")
            symbol = "600000"
            times = []

            for i in range(3):
                start_time = time.time()

                if mode == "full":
                    # 完整模式：使用stock_service
                    stock_data = services["stock_service"].get_stock_data(
                        symbol, "20240101", "20240105"
                    )
                elif mode == "cloud":
                    # 云端模式：SQLite查询（本身就是缓存）
                    import sqlite3

                    conn = sqlite3.connect(services["db_path"])
                    cursor = conn.cursor()
                    cursor.execute(
                        """
                        SELECT COUNT(*) FROM daily_stock_data d
                        JOIN assets a ON d.asset_id = a.asset_id
                        WHERE a.symbol = ? AND d.date BETWEEN '2024-01-01' AND '2024-01-05'
                    """,
                        (symbol,),
                    )
                    result = cursor.fetchone()[0]
                    conn.close()
                else:
                    result = 0

                end_time = time.time()
                response_time = (end_time - start_time) * 1000
                times.append(response_time)

            avg_time = sum(times) / len(times)
            improvement = ((times[0] - times[-1]) / times[0] * 100) if times[0] > 0 else 0

            st.success("✅ Cache performance test completed")

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Average Response Time", f"{avg_time:.1f}ms")
            with col2:
                st.metric("First Query", f"{times[0]:.1f}ms")
            with col3:
                st.metric("Subsequent Queries", f"{times[-1]:.1f}ms")

            if improvement > 0:
                st.info(f"🚀 Cache Effect: Performance improvement {improvement:.1f}%")
            elif mode == "cloud":
                st.info("💾 SQLite database itself provides efficient data caching")

        except Exception as e:
            st.error(f"Cache performance test failed: {str(e)}")
            with st.expander("🔍 Error Details"):
                st.code(str(e))


# Simplified chart creation functions
def create_performance_comparison_chart(cache_time, akshare_time):
    """Create performance comparison chart"""
    if not ADVANCED_FEATURES:
        return None

    try:
        import plotly.graph_objects as go

        fig = go.Figure(
            data=[
                go.Bar(
                    name="SQLite Cache",
                    x=["Response Time"],
                    y=[cache_time],
                    marker_color="lightblue",
                ),
                go.Bar(
                    name="AKShare Direct",
                    x=["Response Time"],
                    y=[akshare_time],
                    marker_color="lightcoral",
                ),
            ]
        )

        fig.update_layout(
            title="Response Time Comparison (milliseconds)",
            yaxis_title="Response Time (ms)",
            barmode="group",
            height=400,
        )

        return fig
    except Exception:
        return None


def create_cache_hit_pie_chart(hits, misses):
    """Create cache hit rate pie chart"""
    if not ADVANCED_FEATURES:
        return None

    try:
        import plotly.graph_objects as go

        fig = go.Figure(
            data=[
                go.Pie(
                    labels=["数据覆盖", "待补充"],
                    values=[hits, misses],
                    hole=0.3,
                    marker_colors=["lightgreen", "lightgray"],
                )
            ]
        )

        fig.update_layout(title="数据覆盖分布", height=400)

        return fig
    except Exception:
        return None


if __name__ == "__main__":
    main()
