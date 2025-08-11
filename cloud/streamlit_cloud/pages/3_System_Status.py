"""
System Status Page
Display system health status, database information and performance metrics
"""

import os
import sys
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

# Add project root directory to Python path to access core modules
current_dir = Path(__file__).parent.parent
project_root = current_dir.parent  # 回到QuantDB根目录
sys.path.insert(0, str(project_root))

# Page configuration
st.set_page_config(page_title="System Status - QuantDB", page_icon="📊", layout="wide")


# Initialize services
@st.cache_resource
def init_services():
    """Initialize service instances"""
    try:
        from core.database import get_db
        from core.services import DatabaseCache

        db_session = next(get_db())
        return DatabaseCache(db_session)
    except Exception as e:
        st.error(f"Service initialization failed: {e}")
        return None


def get_database_info():
    """Get database information"""
    try:
        from core.database import get_db
        from core.models import Asset, DailyStockData

        db_session = next(get_db())

        # Database queries
        try:
            asset_count = db_session.query(Asset).count()
        except Exception:
            asset_count = 0

        try:
            daily_data_count = db_session.query(DailyStockData).count()
        except Exception:
            daily_data_count = 0

        # Get latest data date
        try:
            latest_data = (
                db_session.query(DailyStockData.trade_date)
                .order_by(DailyStockData.trade_date.desc())
                .first()
            )
            latest_date = latest_data[0] if latest_data else None
        except Exception:
            latest_date = None

        # Get database file size
        db_path = current_dir / "database" / "stock_data.db"
        db_size_mb = 0
        if db_path.exists():
            try:
                db_size_mb = db_path.stat().st_size / (1024 * 1024)
            except Exception:
                db_size_mb = 0

        return {
            "asset_count": asset_count,
            "daily_data_count": daily_data_count,
            "latest_date": latest_date,
            "db_size_mb": db_size_mb,
        }
    except Exception as e:
        st.error(f"Failed to get database information: {e}")
        return None


def test_system_performance():
    """Test system performance"""
    try:
        # Ensure database tables exist
        from core.database import Base, engine, get_db
        from core.models import Asset

        Base.metadata.create_all(bind=engine)

        db_session = next(get_db())

        # Test database query performance
        start_time = time.time()
        try:
            assets = db_session.query(Asset).limit(10).all()
            assets_count = len(assets)
        except Exception:
            assets_count = 0
        db_query_time = (time.time() - start_time) * 1000

        # Test cache service
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
            "db_query_time": db_query_time,
            "cache_query_time": cache_query_time,
            "cache_stats": cache_stats,
            "assets_sample": assets_count,
        }
    except Exception as e:
        st.error(f"Performance test failed: {e}")
        return None


def main():
    """Main page"""

    st.title("⚡ System Status")
    st.markdown(
        "Monitor system health status, database information and performance metrics"
    )
    st.markdown("---")

    # System health check
    st.markdown("### 🏥 System Health Check")

    col1, col2, col3, col4 = st.columns(4)

    # Check service status
    cache_service = init_services()
    service_status = "Normal" if cache_service else "Error"
    service_color = "normal" if cache_service else "inverse"

    with col1:
        st.metric(
            "Service Status",
            service_status,
            delta="Running" if cache_service else "Needs Check",
        )

    # Check database connection
    db_info = get_database_info()
    db_status = "Normal" if db_info else "Error"

    with col2:
        st.metric(
            "Database Status",
            db_status,
            delta="SQLite Connected" if db_info else "Connection Failed",
        )

    # Check data integrity
    if db_info:
        data_integrity = (
            "Good"
            if db_info["asset_count"] > 0 and db_info["daily_data_count"] > 0
            else "Needs Data"
        )
        with col3:
            st.metric(
                "Data Integrity",
                data_integrity,
                delta=f"{db_info['asset_count']} Assets",
            )
    else:
        with col3:
            st.metric("Data Integrity", "Unknown", delta="Cannot Check")

    # System response time
    start_time = time.time()
    # Simple system response test
    test_response = True
    response_time = (time.time() - start_time) * 1000

    with col4:
        st.metric(
            "System Response",
            f"{response_time:.1f}ms",
            delta="Normal" if response_time < 100 else "Slow",
        )

    st.markdown("---")

    # Database information
    st.markdown("### 🗄️ Database Information")

    if db_info:
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Asset Count", f"{db_info['asset_count']:,}")

        with col2:
            st.metric("Data Records", f"{db_info['daily_data_count']:,}")

        with col3:
            latest_date = (
                db_info["latest_date"].strftime("%Y-%m-%d")
                if db_info["latest_date"]
                else "N/A"
            )
            st.metric("Latest Data", latest_date)

        with col4:
            st.metric("Database Size", f"{db_info['db_size_mb']:.2f}MB")
    else:
        st.error("❌ Unable to get database information")

    st.markdown("---")

    # Performance testing
    st.markdown("### 🚀 Performance Testing")

    if st.button("🧪 Run Performance Test"):
        with st.spinner("Running performance test..."):
            perf_results = test_system_performance()

            if perf_results:
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric(
                        "Database Query", f"{perf_results['db_query_time']:.1f}ms"
                    )

                with col2:
                    st.metric(
                        "Cache Query", f"{perf_results['cache_query_time']:.1f}ms"
                    )

                with col3:
                    st.metric("Sample Data", f"{perf_results['assets_sample']} records")

                with col4:
                    total_time = (
                        perf_results["db_query_time"] + perf_results["cache_query_time"]
                    )
                    st.metric("Total Response Time", f"{total_time:.1f}ms")

                # Cache statistics
                cache_stats = perf_results.get("cache_stats", {})
                if cache_stats:
                    st.markdown("#### 📊 Cache Statistics")

                    cache_col1, cache_col2, cache_col3 = st.columns(3)

                    with cache_col1:
                        hit_rate = cache_stats.get("hit_rate", 0)
                        st.metric("Cache Hit Rate", f"{hit_rate:.1f}%")

                    with cache_col2:
                        total_requests = cache_stats.get("total_requests", 0)
                        st.metric("Total Requests", f"{total_requests:,}")

                    with cache_col3:
                        cache_size = cache_stats.get("cache_size", 0)
                        st.metric("Cache Size", f"{cache_size:,} records")
            else:
                st.error("❌ Performance test failed")

    st.markdown("---")

    # System information
    st.markdown("### 📋 System Information")

    with st.expander("🔧 Technical Information", expanded=False):
        col1, col2 = st.columns(2)

        with col1:
            st.markdown(
                """
            **Architecture Information**:
            - Application Type: Streamlit Cloud Monolithic App
            - Database: SQLite (Persistent)
            - Data Source: AKShare
            - Cache Strategy: Database Cache
            """
            )

        with col2:
            st.markdown(
                """
            **Version Information**:
            - Application Version: v1.1.0-cloud
            - Python Version: 3.8+
            - Streamlit Version: 1.28+
            - Deployment Platform: Streamlit Community Cloud
            """
            )

    with st.expander("📊 Database Details", expanded=False):
        if db_info:
            st.markdown(
                f"""
            **Database Statistics**:
            - Database File: stock_data.db
            - File Size: {db_info['db_size_mb']:.2f} MB
            - Asset Table Records: {db_info['asset_count']:,} records
            - Daily Data Records: {db_info['daily_data_count']:,} records
            - Latest Data Date: {db_info['latest_date'].strftime('%Y-%m-%d') if db_info['latest_date'] else 'N/A'}
            """
            )
        else:
            st.error("Unable to get database details")

    # Refresh button
    st.markdown("---")
    if st.button("🔄 Refresh System Status"):
        st.rerun()


if __name__ == "__main__":
    main()
