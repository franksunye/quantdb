"""
QuantDB Streamlit Cloud Edition - Main Application Entry
Monolithic application architecture adapted for Streamlit Cloud deployment,
retaining SQLite database and complete functionality
"""

import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import streamlit as st

# Try to add project root directory to Python path to access core modules
PATH_ERROR = None
try:
    current_dir = Path(__file__).parent
    project_root = current_dir.parent.parent  # 回到QuantDB根目录
    sys.path.insert(0, str(project_root))

    # Add local src directory to path (cloud deployment backup)
    src_dir = current_dir / "src"
    if src_dir.exists():
        sys.path.insert(0, str(src_dir))
except Exception as path_error:
    PATH_ERROR = str(path_error)

# Set cloud mode flag - smarter detection
CLOUD_MODE = True
ENVIRONMENT_INFO = None
try:
    # Detect if running in Streamlit Cloud environment
    import os

    if "STREAMLIT_SHARING" in os.environ or "STREAMLIT_CLOUD" in os.environ:
        CLOUD_MODE = True
        ENVIRONMENT_INFO = "Streamlit Cloud environment detected, using cloud mode"
    else:
        # Test if core modules can be fully imported and initialized
        from core.cache import AKShareAdapter
        from core.database import get_db
        from core.services import AssetInfoService, DatabaseCache, StockDataService

        # Test if database session can be created
        db_session = next(get_db())
        db_session.close()

        CLOUD_MODE = False
        ENVIRONMENT_INFO = "Local complete environment detected, using full mode"
except Exception as e:
    CLOUD_MODE = True
    ENVIRONMENT_INFO = (
        f"Environment detection failed, using cloud mode: {str(e)[:100]}..."
    )

# Page configuration
st.set_page_config(
    page_title="QuantDB - Professional Data Platform",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://github.com/franksunye/quantdb",
        "Report a bug": "https://github.com/franksunye/quantdb/issues",
        "About": """
        # QuantDB Professional Platform

        **Version**: v2.1.0

        Professional financial data platform with advanced analytics capabilities.

        ## Core Features
        - Stock data query and analysis
        - Asset information and financial metrics
        - Performance monitoring and caching
        - Multi-market support (A-shares and Hong Kong stocks)

        ## Technical Highlights
        - SQLite database persistence
        - Real-time data processing
        - Professional data visualization
        - Cloud deployment ready

        ---

        **GitHub**: https://github.com/franksunye/quantdb
        """,
    },
)


# Simplified database verification
@st.cache_resource
def verify_database():
    """Verify database connection and table structure - simplified version"""
    try:
        import sqlite3
        from pathlib import Path

        current_dir = Path(__file__).parent
        # Use unified database at project root
        project_root = current_dir.parent.parent
        db_path = project_root / "database" / "stock_data.db"

        result = {
            "db_exists": db_path.exists(),
            "db_path": str(db_path),
            "tables": [],
            "asset_count": 0,
            "status": "unknown",
            "message": "",
        }

        if not db_path.exists():
            result["status"] = "error"
            result["message"] = f"Database file does not exist: {db_path}"
            return result

        # Test SQLite connection
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Check if tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        result["tables"] = tables

        expected_tables = [
            "assets",
            "daily_stock_data",
            "intraday_stock_data",
            "request_logs",
            "data_coverage",
            "system_metrics",
        ]
        existing_tables = [table for table in expected_tables if table in tables]
        missing_tables = [table for table in expected_tables if table not in tables]

        # Test basic queries
        if "assets" in tables:
            cursor.execute("SELECT COUNT(*) FROM assets")
            result["asset_count"] = cursor.fetchone()[0]

        conn.close()

        if len(existing_tables) > 0:
            result["status"] = "success"
            result["message"] = (
                f"Database verification successful, found tables: {existing_tables}"
            )
            if missing_tables:
                result["message"] += f", missing tables: {missing_tables}"
        else:
            result["status"] = "error"
            result["message"] = "Expected database tables not found"

        return result

    except Exception as e:
        return {
            "db_exists": False,
            "db_path": "",
            "tables": [],
            "asset_count": 0,
            "status": "error",
            "message": f"Database verification failed: {e}",
        }


# Conditional service initialization
@st.cache_resource
def init_services():
    """Initialize service instances - supports full mode and cloud mode"""

    try:
        # Force check if running in cloud environment
        import os

        is_streamlit_cloud = (
            "STREAMLIT_SHARING" in os.environ
            or "STREAMLIT_CLOUD" in os.environ
            or "HOSTNAME" in os.environ
            and "streamlit" in os.environ.get("HOSTNAME", "").lower()
        )

        if not CLOUD_MODE and not is_streamlit_cloud:
            # Full mode: use ServiceManager for consistent service initialization
            try:
                from core.services import get_service_manager

                # Use ServiceManager for consistent service initialization
                service_manager = get_service_manager()

                result = {
                    "stock_service": service_manager.get_stock_data_service(),
                    "asset_service": service_manager.get_asset_info_service(),
                    "cache_service": service_manager.get_database_cache(),
                    "realtime_service": service_manager.get_realtime_data_service(),
                    "index_service": service_manager.get_index_data_service(),
                    "financial_service": service_manager.get_financial_data_service(),
                    "service_manager": service_manager,
                    "mode": "full",
                    "status": "success",
                    "message": "Full service initialization successful via ServiceManager",
                }
                return result

            except Exception as full_error:
                # Full mode failed, continue trying cloud mode
                pass

        # Cloud mode: simplified service initialization
        # Create a simplified service container
        services = {
            "stock_service": None,
            "asset_service": None,
            "cache_service": None,
            "akshare_adapter": None,
            "db_session": None,
            "mode": "cloud",
            "status": "success",
            "message": "Cloud service initialization successful",
        }

        # Try basic database connection
        try:
            import sqlite3
            from pathlib import Path

            current_dir = Path(__file__).parent
            # Use unified database at project root
            project_root = current_dir.parent.parent
            db_path = project_root / "database" / "stock_data.db"

            if not db_path.exists():
                # 尝试其他可能的路径
                alternative_paths = [
                    current_dir / "database" / "stock_data.db",  # Old cloud path
                    current_dir / "database" / "stock_data.db.backup",
                    Path("database/stock_data.db"),
                    Path("./database/stock_data.db"),
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
            services["db_path"] = str(db_path)
            services["table_count"] = len(tables)
            services["tables"] = [table[0] for table in tables]
            services["message"] = (
                f"云端服务初始化成功，数据库连接正常（{len(tables)}个表）"
            )

        except Exception as db_error:
            services["status"] = "error"
            services["message"] = f"数据库连接失败: {db_error}"
            services["db_error"] = str(db_error)

        return services

    except Exception as e:
        return {
            "mode": "error",
            "status": "error",
            "message": f"服务初始化失败: {e}",
            "error": str(e),
        }


def show_initialization_status():
    """Display initialization status"""
    services = init_services()
    if services:
        status = services.get("status", "unknown")
        message = services.get("message", "Initialization completed")
        mode = services.get("mode", "unknown")

        if status == "success":
            if mode == "full":
                st.success(f"✅ {message}")
                # Test DatabaseCache methods
                if services.get("cache_service"):
                    if hasattr(services["cache_service"], "get_stats"):
                        st.success("✅ DatabaseCache.get_stats method available")
                    else:
                        st.error("❌ DatabaseCache.get_stats method not available")
            elif mode == "cloud":
                st.info(f"☁️ {message}")
            else:
                st.success(f"✅ {message}")
        elif status == "error":
            st.error(f"❌ {message}")
        else:
            st.warning(f"⚠️ {message}")
    else:
        st.error("❌ Service initialization failed")

    # Display database verification results
    db_result = verify_database()
    if db_result["status"] == "success":
        st.success(f"✅ {db_result['message']}")
        if db_result["asset_count"] > 0:
            st.info(f"📊 Asset table contains {db_result['asset_count']} records")
    elif db_result["status"] == "error":
        st.error(f"❌ {db_result['message']}")
    else:
        st.warning(f"⚠️ {db_result['message']}")


def get_system_status():
    """Get system status"""
    try:
        # Use simplified configuration to avoid complex module imports
        import os
        from pathlib import Path

        current_dir = Path(__file__).parent
        # Use unified database at project root
        project_root = current_dir.parent.parent

        # Simplified database path configuration - prioritize unified database
        possible_db_paths = [
            project_root / "database" / "stock_data.db",  # Unified database (priority)
            current_dir / "database" / "stock_data.db",  # Old cloud path (fallback)
            current_dir / "database" / "stock_data.db.backup",
            "database/stock_data.db",
            "./database/stock_data.db",
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

        # Try simplified service initialization
        services = init_services()
        if not services:
            return {
                "api_status": "service_error",
                "api_response_time": 0,
                "asset_count": 0,
                "cache_stats": {},
                "debug_info": {
                    "database_url": DATABASE_URL,
                    "database_path": DATABASE_PATH,
                    "db_exists": db_exists,
                    "current_dir": str(current_dir),
                    "checked_paths": [str(p) for p in possible_db_paths],
                },
            }

        # Test API response time
        start_time = time.time()

        # Improved database query testing
        asset_count = 0
        cache_stats = {}

        if services:
            if services.get("mode") == "full":
                # Full mode: use service queries
                try:
                    if services.get("db_session"):
                        from core.models import Asset

                        asset_count = services["db_session"].query(Asset).count()
                    if services.get("cache_service"):
                        # Check if cache_service has get_stats method
                        if hasattr(services["cache_service"], "get_stats"):
                            cache_stats = services["cache_service"].get_stats()
                        else:
                            # Log error but don't display to avoid calling streamlit before page config
                            cache_stats = {"error": "get_stats method not found"}
                except Exception as full_query_error:
                    # Log error but don't display to avoid calling streamlit before page config
                    # Force switch to cloud mode query
                    asset_count = 0
                    cache_stats = {
                        "error": str(full_query_error),
                        "error_type": type(full_query_error).__name__,
                    }

            elif services.get("mode") == "cloud":
                # Cloud mode: use SQLite direct connection queries
                try:
                    if "db_path" in services and os.path.exists(services["db_path"]):
                        import sqlite3

                        conn = sqlite3.connect(services["db_path"])
                        cursor = conn.cursor()

                        # Check if assets table exists
                        cursor.execute(
                            "SELECT name FROM sqlite_master WHERE type='table' AND name='assets';"
                        )
                        if cursor.fetchone():
                            cursor.execute("SELECT COUNT(*) FROM assets")
                            asset_count = cursor.fetchone()[0]

                        # Get simplified cache statistics
                        tables = services.get("tables", [])
                        cache_stats = {
                            "database_type": "SQLite",
                            "status": "active",
                            "tables": len(tables),
                            "table_names": tables,
                        }

                        conn.close()

                except Exception as cloud_query_error:
                    # Log error but don't display to avoid calling streamlit before page config
                    asset_count = 0
                    cache_stats = {
                        "database_type": "SQLite",
                        "status": "error",
                        "error": str(cloud_query_error),
                    }

        api_response_time = (time.time() - start_time) * 1000

        return {
            "api_status": "running",
            "api_response_time": api_response_time,
            "asset_count": asset_count,
            "cache_stats": cache_stats,
            "service_mode": services.get("mode", "unknown") if services else "none",
            "debug_info": {
                "database_url": DATABASE_URL,
                "database_path": DATABASE_PATH,
                "db_exists": db_exists,
                "current_dir": str(current_dir),
                "services_available": bool(services),
                "cloud_mode": CLOUD_MODE,
            },
        }
    except Exception as e:
        # Log error but don't display to avoid calling streamlit before page config
        return {
            "api_status": "error",
            "api_response_time": 0,
            "asset_count": 0,
            "cache_stats": {},
            "debug_info": {"error": str(e), "function": "get_system_status"},
        }


def main():
    """Main page"""
    # Display environment information (if available)
    if PATH_ERROR:
        st.warning(f"Path setup warning: {PATH_ERROR}")

    if ENVIRONMENT_INFO:
        if "cloud mode" in ENVIRONMENT_INFO.lower():
            st.info(f"🌐 {ENVIRONMENT_INFO}")
        else:
            st.info(f"🖥️ {ENVIRONMENT_INFO}")

    st.markdown("# QuantDB Professional Platform")
    st.markdown("### Financial Data Analytics & Market Intelligence")
    st.markdown("---")

    st.markdown(
        """
    **Professional financial data platform** designed for institutional-grade analysis and research.

    **Core Capabilities**:
    - **High-Performance Data Access**: SQLite caching with 98.1% performance improvement
    - **Real-Time Market Data**: Live company information and financial metrics
    - **Advanced Analytics**: Interactive data visualization and technical analysis
    - **Multi-Market Coverage**: A-shares and Hong Kong stock markets
    - **Enterprise Ready**: Cloud deployment with professional-grade reliability
    """
    )

    st.markdown("---")

    # Display initialization status
    show_initialization_status()

    # System status overview
    st.markdown("### System Status Overview")

    system_status = get_system_status()

    if system_status:
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                label="API Status",
                value=(
                    "Running" if system_status["api_status"] == "running" else "Error"
                ),
                delta=(
                    "Normal"
                    if system_status["api_status"] == "running"
                    else "Check Required"
                ),
            )

        with col2:
            st.metric(
                label="Response Time",
                value=f"{system_status['api_response_time']:.1f}ms",
                delta=(
                    "Excellent"
                    if system_status["api_response_time"] < 100
                    else "Normal"
                ),
            )

        with col3:
            asset_count = system_status["asset_count"]
            st.metric(
                label="Assets",
                value=f"{asset_count}",
                delta="Database OK" if asset_count > 0 else "No Data",
            )

        with col4:
            cache_stats = system_status.get("cache_stats", {})
            service_mode = system_status.get("service_mode", "unknown")

            # Determine display content based on service mode and cache status
            if cache_stats.get("status") == "active":
                if service_mode == "full":
                    cache_efficiency = "Full Mode"
                    cache_delta = "Core Services"
                elif service_mode == "cloud":
                    cache_efficiency = "Cloud Mode"
                    cache_delta = f"SQLite({cache_stats.get('tables', 0)} tables)"
                else:
                    cache_efficiency = "Running"
                    cache_delta = "SQLite Persistent"
            else:
                cache_efficiency = "Initializing"
                cache_delta = "Please wait"

            st.metric(label="Cache Status", value=cache_efficiency, delta=cache_delta)

        # Display service mode information
        service_mode = system_status.get("service_mode", "unknown")
        if service_mode != "unknown":
            st.info(
                f"🔧 Current Mode: **{service_mode.upper()}** {'(Full Features)' if service_mode == 'full' else '(Cloud Optimized)'}"
            )

        # Debug information (only show if there are issues)
        if asset_count == 0 and "debug_info" in system_status:
            with st.expander(
                "🔍 Debug Information (shown when asset count is 0)", expanded=True
            ):
                debug_info = system_status["debug_info"]
                st.write("**Database Configuration:**")
                st.json(debug_info)

                # Additional file check
                import os

                st.write("**File System Check:**")
                current_files = []
                try:
                    for root, dirs, files in os.walk("."):
                        for file in files:
                            if file.endswith(".db"):
                                current_files.append(os.path.join(root, file))
                    st.write(f"Database files found: {current_files}")
                except Exception as e:
                    st.write(f"File check error: {e}")
    else:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(label="API Status", value="Initializing", delta="Please wait")
        with col2:
            st.metric(label="Response Time", value="N/A", delta="Measuring")
        with col3:
            st.metric(label="Assets", value="N/A", delta="Loading")
        with col4:
            st.metric(label="Cache Status", value="N/A", delta="Preparing")

    # Feature navigation
    st.markdown("---")
    st.markdown("### 🧭 Feature Navigation")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            """
        #### 📈 Stock Data Query
        - Historical price data query
        - Price trend chart display
        - Basic statistical analysis
        - Volume and price change analysis

        👉 **Use left sidebar to access**
        """
        )

    with col2:
        st.markdown(
            """
        #### 📊 Asset Information
        - Company basic information display
        - Detailed financial metrics analysis
        - Data coverage statistics
        - Real-time market data updates

        👉 **Use left sidebar to access**
        """
        )

    with col3:
        st.markdown(
            """
        #### ⚡ System Status
        - Database status monitoring
        - System performance metrics display
        - Cache efficiency statistics
        - Service health checks

        👉 **Use left sidebar to access**
        """
        )

    # Quick start
    st.markdown("---")
    st.markdown("### 🚀 Quick Start")

    with st.expander("📖 User Guide", expanded=False):
        st.markdown(
            """
        #### How to Use QuantDB Cloud

        1. **Stock Code Format**
           - A-Share codes: 6-digit numbers (e.g., 600000 SPDB, 000001 PAB)
           - Supports major stocks from Shanghai and Shenzhen markets

        2. **Data Query**
           - Click "📈 Stock Data" in the left sidebar
           - Enter stock code and date range
           - System automatically fetches and caches data to SQLite database

        3. **Data Persistence**
           - Uses SQLite database for persistent storage
           - Data remains after application restart
           - Smart caching avoids duplicate API calls

        4. **Important Notes**
           - Data source: AKShare official API
           - Cache mechanism: SQLite database persistence
           - Recommended browsers: Chrome, Firefox, Edge
        """
        )


if __name__ == "__main__":
    main()
