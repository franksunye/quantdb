#!/usr/bin/env python3
"""
QuantDB Cloud - Asset Information Page

Provides stock asset information query functionality,
supports manual input and browsing existing assets.
"""

import streamlit as st
import time
import sys
import os
from datetime import datetime
from typing import Dict, List, Any

# Add project root directory to path to access core modules
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(parent_dir)  # 回到QuantDB根目录
if project_root not in sys.path:
    sys.path.append(project_root)

# Import existing backend services (direct call, not through HTTP API)
try:
    from core.services import AssetInfoService, QueryService
    from core.database import get_db
    BACKEND_SERVICES_AVAILABLE = True
except ImportError as e:
    BACKEND_SERVICES_AVAILABLE = False

# Set page configuration
st.set_page_config(
    page_title="Asset Information - QuantDB",
    page_icon="📊",
    layout="wide"
)

def init_services():
    """Initialize backend services"""
    # Check if services are already cached in session state
    if 'asset_services' in st.session_state:
        return st.session_state['asset_services']

    try:
        # Get database session
        db_session = next(get_db())

        # Initialize services
        asset_service = AssetInfoService(db_session)
        query_service = QueryService(db_session)

        services = (asset_service, query_service)

        # Cache in session state instead of @st.cache_resource to avoid stale database sessions
        st.session_state['asset_services'] = services
        return services
    except Exception as e:
        st.error(f"Service initialization failed: {e}")
        return None, None

def main():
    """Main page function"""

    # Page title
    st.title("📊 Asset Information")
    st.markdown("View detailed asset information for stocks, including fundamental data, financial metrics, and market performance.")
    st.markdown("---")

    # Check if backend services are available
    if not BACKEND_SERVICES_AVAILABLE:
        st.warning("⚠️ Backend services unavailable, using API mode")
        use_backend_services = False
        asset_service, query_service = None, None
    else:
        # Initialize backend services
        services = init_services()
        if services and all(services):
            asset_service, query_service = services
            use_backend_services = True
        else:
            st.warning("⚠️ Backend service initialization failed, using API mode")
            use_backend_services = False
            asset_service, query_service = None, None

    # Main page layout: left content area + right query panel
    col_main, col_query = st.columns([7, 3])  # 70% + 30% layout

    # Right query panel
    with col_query:
        with st.container():
            st.markdown("### 🔍 Asset Query")

            # Query method selection
            query_mode = st.radio(
                "Query Method",
                ["Manual Input", "Browse Existing"],
                help="Choose query method: manual input or select from existing assets"
            )

            if query_mode == "Manual Input":
                # Stock code input
                symbol = st.text_input(
                    "Stock Code",
                    value="600000",
                    placeholder="e.g.: 600000 or 00700",
                    help="Supports A-share (6 digits) and HK stock (5 digits) codes"
                )

                # Query button
                query_button = st.button("🔍 Query Asset Info", type="primary", use_container_width=True)

                # Refresh button - add detailed description
                refresh_button = st.button(
                    "🔄 Force Refresh Asset Data",
                    use_container_width=True,
                    help="Force fetch latest asset information from AKShare, including company name, financial metrics, etc."
                )

                # Add refresh explanation
                with st.expander("ℹ️ Data Refresh Instructions", expanded=False):
                    st.markdown("""
                    **🔄 Force Refresh Function:**

                    - **Purpose**: Force re-fetch latest asset information from AKShare
                    - **Update Content**: Company name, industry classification, financial metrics (PE/PB/ROE), market cap data, etc.
                    - **Use Cases**:
                      - When company name displays incorrectly (e.g., "HK Stock 02171")
                      - When latest financial metrics are needed
                      - When data displays abnormally
                    - **Note**: Refresh calls external API, may take a few seconds

                    **Difference from Normal Query:**
                    - 🔍 **Normal Query**: Prioritizes cached data (valid within 1 day)
                    - 🔄 **Force Refresh**: Ignores cache, directly calls AKShare for latest data
                    """)

            else:
                # Browse existing assets
                symbol, query_button, refresh_button = display_asset_browser(query_service)

            # Display recent queries
            display_recent_queries()

    # Check for automatic query requests
    if st.session_state.get('auto_query_asset'):
        symbol = st.session_state.get('symbol', '600000')
        query_button = True
        st.session_state.auto_query_asset = False

    # Check for saved query state (to maintain page state)
    if not query_button and not refresh_button and st.session_state.get('current_asset_symbol'):
        symbol = st.session_state.get('current_asset_symbol')
        query_button = True  # Automatically redisplay previously queried asset information

    # Left main content area
    with col_main:
        if query_button or refresh_button or st.session_state.get('auto_query_asset', False):

            # Validate input
            if not symbol:
                st.error("Please enter a stock code")
                return

            # Validate stock code format - simplified validation logic
            if not symbol or len(symbol) < 5 or len(symbol) > 6 or not symbol.isdigit():
                st.error("Please enter a valid stock code (5-6 digits)")
                return

            # Normalize stock code
            if len(symbol) == 5:
                symbol = symbol  # Keep HK stock as 5 digits
            elif len(symbol) == 6:
                symbol = symbol  # Keep A-share as 6 digits
            else:
                st.error("Incorrect stock code length")
                return

            # Display query information
            st.info(f"Querying asset information for stock {symbol}...")

            # Query data
            with st.spinner("Querying asset information..." if query_button else "Force refreshing asset data..."):
                try:
                    if use_backend_services and asset_service:
                        # Choose different processing methods based on button type
                        if refresh_button:
                            # Refresh button: force update asset information
                            st.info("🔄 Force fetching latest asset information from AKShare...")
                            asset_obj = asset_service.update_asset_info(symbol)
                            metadata = {
                                'cache_info': {
                                    'cache_hit': False,
                                    'akshare_called': True,
                                    'force_refresh': True,
                                    'response_time_ms': 0  # Actual time recorded by service layer
                                }
                            }

                            if not asset_obj:
                                st.error(f"❌ Unable to update asset {symbol}, may be invalid stock code or AKShare service exception")
                                return

                        else:
                            # Query button: normal query (prioritize cache)
                            asset_result = asset_service.get_or_create_asset(symbol)

                            if isinstance(asset_result, tuple):
                                asset_obj, metadata = asset_result
                            else:
                                asset_obj = asset_result
                                metadata = {}

                        # Debug information: display actual Asset object attributes
                        st.info(f"🔍 Asset object attributes: {[attr for attr in dir(asset_obj) if not attr.startswith('_')]}")

                        # Convert to dictionary format using actual Asset model fields
                        asset_data = {
                            'symbol': asset_obj.symbol,
                            'name': asset_obj.name,
                            'asset_type': asset_obj.asset_type,
                            'exchange': asset_obj.exchange,
                            'currency': getattr(asset_obj, 'currency', 'CNY'),
                            'industry': asset_obj.industry,
                            'concept': asset_obj.concept,
                            'area': 'China',  # No area field in Asset model, use default value
                            'market': 'A-Share' if len(asset_obj.symbol) == 6 else 'HK Stock',  # Determine market by code length
                            'list_date': getattr(asset_obj, 'listing_date', None),  # Use correct field name
                            'pe_ratio': asset_obj.pe_ratio,
                            'pb_ratio': asset_obj.pb_ratio,
                            'roe': asset_obj.roe,
                            'market_cap': asset_obj.market_cap,
                            'total_shares': asset_obj.total_shares,
                            'circulating_shares': asset_obj.circulating_shares,
                            'created_at': None,  # No created_at field in Asset model
                            'updated_at': getattr(asset_obj, 'last_updated', None),  # Use correct field name
                            'last_accessed': None  # No last_accessed field in Asset model
                        }

                        asset_metadata = metadata

                    else:
                        # Fallback to API mode (should not be used in cloud version)
                        st.error("❌ Backend services unavailable, cloud version does not support API mode")
                        return

                    # Save current queried asset information to session state (to maintain page state)
                    st.session_state.current_asset_symbol = symbol
                    st.session_state.current_asset_data = asset_data
                    st.session_state.current_asset_metadata = asset_metadata

                    # Add to recent query list
                    add_to_recent_queries(symbol, asset_data.get('name', f'Stock {symbol}'))

                    # Display asset information
                    display_asset_info(asset_data, symbol)

                    # Display asset information cache status
                    display_asset_cache_info(asset_metadata)

                    # Optional data coverage information (use expander to avoid page reload)
                    st.markdown("---")
                    with st.expander("Data Coverage Analysis", expanded=False):
                        display_data_coverage(symbol)

                except Exception as e:
                    error_msg = str(e)

                    # 特殊处理只读数据库错误
                    if "readonly database" in error_msg.lower() or "attempt to write a readonly database" in error_msg.lower():
                        st.error("❌ Database is in read-only mode")
                        st.info("🔍 Cloud environment detected - using read-only database mode")
                        st.markdown("""
                        **💡 In read-only mode:**
                        - Asset information is retrieved from existing database records
                        - New assets cannot be created or updated
                        - If the asset doesn't exist in database, default information will be used
                        - This is normal behavior in cloud deployment
                        """)

                        # 尝试使用默认信息显示
                        try:
                            if asset_service and hasattr(asset_service, '_get_default_hk_name'):
                                default_name = asset_service._get_default_hk_name(symbol)
                                st.info(f"📋 Using default information for {symbol}: {default_name}")

                                # 创建基本的资产信息显示
                                basic_asset_data = {
                                    'symbol': symbol,
                                    'name': default_name,
                                    'asset_type': 'stock',
                                    'exchange': 'HKEX' if len(symbol) == 5 else ('SHSE' if symbol.startswith('6') else 'SZSE'),
                                    'currency': 'HKD' if len(symbol) == 5 else 'CNY',
                                    'industry': 'N/A',
                                    'concept': 'N/A',
                                    'area': 'Hong Kong' if len(symbol) == 5 else 'China',
                                    'market': 'HK Stock' if len(symbol) == 5 else 'A-Share',
                                    'list_date': None,
                                    'pe_ratio': None,
                                    'pb_ratio': None,
                                    'roe': None,
                                    'market_cap': None,
                                    'total_shares': None,
                                    'circulating_shares': None,
                                    'updated_at': None
                                }

                                display_asset_info(basic_asset_data, symbol)

                                # 显示只读模式的缓存信息
                                readonly_metadata = {
                                    'cache_info': {
                                        'cache_hit': False,
                                        'akshare_called': False,
                                        'readonly_mode': True,
                                        'response_time_ms': 0
                                    }
                                }
                                display_asset_cache_info(readonly_metadata)

                        except Exception as fallback_error:
                            st.error(f"❌ Fallback display also failed: {str(fallback_error)}")
                    else:
                        st.error(f"❌ Error occurred during query: {error_msg}")
                        st.info("Please check service status or try again later")

                    # Display detailed error information for debugging
                    with st.expander("🔍 Error Details", expanded=False):
                        st.code(error_msg)
        else:
            # Display usage guide
            show_usage_guide()


def display_asset_info(asset_data: dict, symbol: str):
    """Display asset information"""

    st.success(f"✅ Successfully retrieved asset information for stock {symbol}")

    # Basic information cards
    st.subheader("🏢 Basic Information")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### 📋 Company Information")
        st.write(f"**Stock Code**: {asset_data.get('symbol', 'N/A')}")
        st.write(f"**Company Name**: {asset_data.get('name', 'N/A')}")
        st.write(f"**Asset Type**: {asset_data.get('asset_type', 'N/A')}")
        st.write(f"**Exchange**: {asset_data.get('exchange', 'N/A')}")

    with col2:
        st.markdown("### 🏭 Classification Information")
        st.write(f"**Industry**: {asset_data.get('industry') or 'N/A'}")
        st.write(f"**Concept**: {asset_data.get('concept') or 'N/A'}")
        st.write(f"**Region**: {asset_data.get('area') or 'N/A'}")
        st.write(f"**Market**: {asset_data.get('market') or 'N/A'}")
        st.write(f"**Currency**: {asset_data.get('currency') or 'N/A'}")

    with col3:
        st.markdown("### 📅 Time Information")
        list_date = asset_data.get('list_date')
        if list_date:
            list_date_str = list_date.strftime('%Y-%m-%d') if hasattr(list_date, 'strftime') else str(list_date)
        else:
            list_date_str = 'N/A'
        st.write(f"**Listing Date**: {list_date_str}")
        st.write(f"**Data Source**: AKShare")
        st.write(f"**Update Time**: {format_datetime(asset_data.get('updated_at'))}")
        st.write(f"**Data Status**: Cached")
    
    st.markdown("---")

    # Financial metrics
    st.subheader("💰 Financial Metrics")

    # Use st.metric to display key financial metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        pe_ratio = asset_data.get('pe_ratio')
        if pe_ratio is not None and pe_ratio > 0:
            pe_value = f"{pe_ratio:.2f}"
            pe_delta = "Reasonable" if 10 <= pe_ratio <= 30 else ("Low" if pe_ratio < 10 else "High")
        else:
            pe_value = "N/A"
            pe_delta = None
        st.metric(
            label="P/E Ratio",
            value=pe_value,
            delta=pe_delta,
            help="P/E Ratio = Stock Price / Earnings Per Share"
        )

    with col2:
        pb_ratio = asset_data.get('pb_ratio')
        if pb_ratio is not None and pb_ratio > 0:
            pb_value = f"{pb_ratio:.2f}"
            pb_delta = "Reasonable" if 1 <= pb_ratio <= 3 else ("Low" if pb_ratio < 1 else "High")
        else:
            pb_value = "N/A"
            pb_delta = None
        st.metric(
            label="P/B Ratio",
            value=pb_value,
            delta=pb_delta,
            help="P/B Ratio = Stock Price / Book Value Per Share"
        )

    with col3:
        roe = asset_data.get('roe')
        if roe is not None and roe > 0:
            roe_value = f"{roe:.2f}%"
            roe_delta = "Excellent" if roe >= 15 else ("Good" if roe >= 10 else "Average")
        else:
            roe_value = "N/A"
            roe_delta = None
        st.metric(
            label="Return on Equity (ROE)",
            value=roe_value,
            delta=roe_delta,
            help="ROE = Net Income / Shareholders' Equity"
        )

    with col4:
        market_cap = asset_data.get('market_cap')
        if market_cap and market_cap > 0:
            market_cap_display = format_large_number(market_cap)
            if market_cap >= 1000e8:  # Above 100 billion
                cap_delta = "Large Cap"
            elif market_cap >= 100e8:  # 10-100 billion
                cap_delta = "Mid Cap"
            else:  # Below 10 billion
                cap_delta = "Small Cap"
        else:
            market_cap_display = "N/A"
            cap_delta = None
        st.metric(
            label="Market Cap",
            value=market_cap_display,
            delta=cap_delta,
            help="Market Cap = Stock Price × Total Shares"
        )

    # Second row financial metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_shares = asset_data.get('total_shares')
        if total_shares and total_shares > 0:
            total_shares_display = format_large_number(total_shares)
            shares_delta = "Shares"
        else:
            total_shares_display = "N/A"
            shares_delta = None
        st.metric(
            label="Total Shares",
            value=total_shares_display,
            delta=shares_delta
        )

    with col2:
        circulating_shares = asset_data.get('circulating_shares')
        if circulating_shares and circulating_shares > 0:
            circulating_shares_display = format_large_number(circulating_shares)
            # Calculate circulation ratio
            total_shares = asset_data.get('total_shares')
            if total_shares and total_shares > 0:
                ratio = (circulating_shares / total_shares) * 100
                circ_delta = f"{ratio:.1f}% Float"
            else:
                circ_delta = "Shares"
        else:
            circulating_shares_display = "N/A"
            circ_delta = None

        st.metric(
            label="Circulating Shares",
            value=circulating_shares_display,
            delta=circ_delta
        )

    with col3:
        # Calculate earnings per share (if P/E ratio and market cap data available)
        pe_ratio = asset_data.get('pe_ratio')
        market_cap = asset_data.get('market_cap')
        total_shares = asset_data.get('total_shares')

        if pe_ratio and market_cap and total_shares and pe_ratio > 0 and total_shares > 0:
            # Stock price = Market cap / Total shares
            stock_price = market_cap / total_shares
            # EPS = Stock price / PE
            eps = stock_price / pe_ratio
            eps_value = f"{eps:.2f}"
            eps_delta = "Calculated"
        else:
            eps_value = "N/A"
            eps_delta = "Insufficient Data"

        st.metric(
            label="Earnings Per Share (EPS)",
            value=eps_value,
            delta=eps_delta,
            help="EPS = Stock Price / P/E Ratio (Calculated)"
        )

    with col4:
        # Calculate book value per share (if P/B ratio and market cap data available)
        pb_ratio = asset_data.get('pb_ratio')

        if pb_ratio and market_cap and total_shares and pb_ratio > 0 and total_shares > 0:
            # Stock price = Market cap / Total shares
            stock_price = market_cap / total_shares
            # BPS = Stock price / PB
            bps = stock_price / pb_ratio
            bps_value = f"{bps:.2f}"
            bps_delta = "Calculated"
        else:
            bps_value = "N/A"
            bps_delta = "Insufficient Data"

        st.metric(
            label="Book Value Per Share (BPS)",
            value=bps_value,
            delta=bps_delta,
            help="BPS = Stock Price / P/B Ratio (Calculated)"
        )


def display_asset_browser(query_service):
    """Display asset browser - query real asset data from database"""

    st.markdown("**📋 Browse Existing Assets**")

    # Add refresh button to force reload
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🔄 Refresh List", help="Refresh asset list from database"):
            # Clear any cached data by reinitializing the service
            if 'asset_services' in st.session_state:
                del st.session_state['asset_services']
            st.rerun()

    try:
        if query_service:
            # Use backend service to query real asset data from database
            with st.spinner("Loading asset list..."):
                assets, total_count = query_service.query_assets(
                    sort_by="symbol",
                    sort_order="asc",
                    limit=100  # Limit return quantity to avoid loading too much data
                )

            if not assets:
                # If no asset data in database, show tips
                st.info("📊 No asset data in database")
                st.markdown("""
                **💡 Tips:**
                - Asset data in database will be automatically created when you first query stocks
                - You can first use "Manual Input" to query some stocks, system will automatically save asset information
                - Recommended to query first: 600000(SPDB), 000001(PAB), 600519(Kweichow Moutai)
                """)
                return "", False, False

            # 转换为字典格式，便于处理
            asset_list = []
            for asset in assets:
                asset_dict = {
                    'symbol': asset.symbol,
                    'name': asset.name or f'Stock {asset.symbol}',
                    'industry': asset.industry or 'Other'
                }
                asset_list.append(asset_dict)

            # Display statistics
            st.caption(f"📊 Total {total_count} stocks in database")

        else:
            # Backend service unavailable, display error message
            st.error("❌ Backend service unavailable, unable to load asset list")
            st.info("Cloud version requires backend service support, please check service initialization status")
            return "", False, False

        # Group by industry
        industry_groups = {}
        for asset in asset_list:
            industry = asset.get('industry', 'Other')
            if industry not in industry_groups:
                industry_groups[industry] = []
            industry_groups[industry].append(asset)

        # Industry filter
        selected_industry = st.selectbox(
            "Filter by Industry",
            ["All"] + sorted(list(industry_groups.keys())),
            help="Select specific industry to view related stocks"
        )

        # Filter assets
        if selected_industry == "All":
            filtered_assets = asset_list
        else:
            filtered_assets = industry_groups[selected_industry]

        # Asset selection
        asset_options = {}
        for asset in filtered_assets:
            display_name = f"{asset['symbol']} - {asset['name']}"
            if asset.get('industry') and asset['industry'] != 'Other':
                display_name += f" ({asset['industry']})"
            asset_options[display_name] = asset['symbol']

        if asset_options:
            selected_display = st.selectbox(
                "Select Stock",
                list(asset_options.keys()),
                help="Select stock to view from the list"
            )

            selected_symbol = asset_options[selected_display]

            # Action buttons
            col1, col2 = st.columns(2)
            with col1:
                query_button = st.button("🔍 View Details", type="primary", use_container_width=True)
            with col2:
                refresh_button = st.button("🔄 Refresh Data", use_container_width=True)

            return selected_symbol, query_button, refresh_button
        else:
            st.info("No asset data available for this industry")
            return "", False, False

    except Exception as e:
        st.error(f"Failed to load asset list: {str(e)}")
        # Provide default options when error occurs
        st.markdown("**🔄 Use Default Asset List:**")
        default_options = {
            "600000 - SPDB": "600000",
            "000001 - PAB": "000001",
            "600519 - Kweichow Moutai": "600519"
        }

        selected_display = st.selectbox(
            "Select Stock",
            list(default_options.keys()),
            help="Select stock from default list"
        )

        selected_symbol = default_options[selected_display]

        # Action buttons
        col1, col2 = st.columns(2)
        with col1:
            query_button = st.button("🔍 View Details", type="primary", use_container_width=True)
        with col2:
            refresh_button = st.button("🔄 Refresh Data", use_container_width=True)

        return selected_symbol, query_button, refresh_button


def display_recent_queries():
    """Display recent stock queries"""

    st.markdown("---")
    st.markdown("**🕒 Recent Queries**")

    # Get recent queries from session state
    recent_queries = st.session_state.get('recent_asset_queries', [])

    if recent_queries:
        # Display last 3 queries
        for i, query in enumerate(recent_queries[:3]):
            symbol = query['symbol']
            name = query.get('name', f'Stock {symbol}')
            query_time = query.get('time', '')

            if st.button(
                f"{symbol} - {name}",
                key=f"recent_{i}_{symbol}",
                help=f"Query time: {query_time}",
                use_container_width=True
            ):
                st.session_state.update({
                    'symbol': symbol,
                    'auto_query_asset': True
                })
                st.rerun()
    else:
        st.caption("No recent query records")


def add_to_recent_queries(symbol: str, name: str):
    """Add to recent query list"""

    if 'recent_asset_queries' not in st.session_state:
        st.session_state.recent_asset_queries = []

    # Create query record
    query_record = {
        'symbol': symbol,
        'name': name,
        'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    # Remove duplicates
    st.session_state.recent_asset_queries = [
        q for q in st.session_state.recent_asset_queries
        if q['symbol'] != symbol
    ]

    # Add to beginning
    st.session_state.recent_asset_queries.insert(0, query_record)

    # Keep maximum 10 records
    st.session_state.recent_asset_queries = st.session_state.recent_asset_queries[:10]


def display_asset_cache_info(metadata: dict):
    """Display asset information cache status"""

    st.markdown("---")
    st.subheader("⚡ Asset Information Cache Status")

    cache_info = metadata.get('cache_info', {})

    col1, col2, col3 = st.columns(3)

    with col1:
        cache_hit = cache_info.get('cache_hit', False)
        st.metric(
            label="Cache Hit",
            value="Yes" if cache_hit else "No",
            help="Whether asset information comes from cache"
        )

    with col2:
        akshare_called = cache_info.get('akshare_called', False)
        st.metric(
            label="AKShare Called",
            value="Yes" if akshare_called else "No",
            help="Whether AKShare was called to get latest data"
        )

    with col3:
        readonly_mode = cache_info.get('readonly_mode', False)
        if readonly_mode:
            st.metric(
                label="Database Mode",
                value="Read-Only",
                help="Database is in read-only mode (cloud environment)"
            )
        else:
            response_time = cache_info.get('response_time_ms', 0)
            st.metric(
                label="Response Time",
                value=f"{response_time:.1f}ms",
                help="API response time"
            )

    # 如果是只读模式，显示特殊说明
    if cache_info.get('readonly_mode'):
        st.info("🔒 **Read-Only Mode**: Database is in read-only mode, suitable for cloud deployment")
        st.markdown("""
        **Features in read-only mode:**
        - ✅ Query existing asset information from database
        - ✅ Display cached stock data
        - ❌ Cannot create new assets
        - ❌ Cannot update existing asset information
        """)

    # Display detailed information
    if cache_info:
        with st.expander("📊 Detailed Cache Information"):
            st.json(cache_info)





def display_data_coverage(symbol: str):
    """Display data coverage information"""

    try:
        # Use backend service to directly query database
        from core.database import get_db
        from core.models import DailyStockData, Asset
        from datetime import date, timedelta
        from sqlalchemy import func

        # Get database session
        db_session = next(get_db())

        try:
            # Find asset
            asset = db_session.query(Asset).filter(Asset.symbol == symbol).first()
            if not asset:
                st.info("📝 No asset information available, please query this stock first")
                return

            # Query data coverage for last 30 days
            end_date = date.today()
            start_date = end_date - timedelta(days=30)

            data_count = db_session.query(func.count(DailyStockData.id)).filter(
                DailyStockData.asset_id == asset.asset_id,
                DailyStockData.trade_date >= start_date,
                DailyStockData.trade_date <= end_date
            ).scalar()

            # Get data range
            first_record = db_session.query(DailyStockData).filter(
                DailyStockData.asset_id == asset.asset_id
            ).order_by(DailyStockData.trade_date.asc()).first()

            last_record = db_session.query(DailyStockData).filter(
                DailyStockData.asset_id == asset.asset_id
            ).order_by(DailyStockData.trade_date.desc()).first()

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("最近30天数据", f"{data_count:,}条")

            with col2:
                if first_record:
                    st.metric("数据起始", first_record.trade_date.strftime('%Y-%m-%d'))
                else:
                    st.metric("数据起始", "N/A")

            with col3:
                if last_record:
                    st.metric("数据截止", last_record.trade_date.strftime('%Y-%m-%d'))
                else:
                    st.metric("数据截止", "N/A")

            with col4:
                if first_record and last_record:
                    days_span = (last_record.trade_date - first_record.trade_date).days
                    st.metric("数据跨度", f"{days_span}天")
                else:
                    st.metric("数据跨度", "N/A")

            if data_count == 0:
                st.info("📝 No historical data available, please get data from Stock Data Query page first")

        finally:
            db_session.close()

    except Exception as e:
        st.warning(f"⚠️ Failed to get data coverage information: {str(e)}")
        # Display detailed error information for debugging
        with st.expander("🔍 Error Details", expanded=False):
            st.code(str(e))


def format_datetime(dt_obj):
    """格式化日期时间对象"""
    if not dt_obj:
        return "N/A"

    try:
        # 处理datetime对象
        if hasattr(dt_obj, 'strftime'):
            return dt_obj.strftime('%Y-%m-%d %H:%M:%S')

        # 处理字符串
        if isinstance(dt_obj, str):
            # 尝试解析不同的日期格式
            for fmt in ['%Y-%m-%dT%H:%M:%S.%f', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d']:
                try:
                    dt = datetime.strptime(dt_obj, fmt)
                    return dt.strftime('%Y-%m-%d %H:%M:%S')
                except ValueError:
                    continue

        # Other cases: convert directly to string
        return str(dt_obj)
    except Exception:
        return "N/A"


def format_large_number(num):
    """Format large number display"""
    if not num or num == 0:
        return "N/A"

    try:
        num = float(num)
        if num >= 1e8:
            return f"{num/1e8:.2f}B"  # Billion
        elif num >= 1e4:
            return f"{num/1e4:.2f}W"  # Wan (10,000)
        else:
            return f"{num:.2f}"
    except:
        return "N/A"


def show_usage_guide():
    """Display usage guide"""

    st.markdown("### 📖 Usage Guide")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        #### 🔍 How to Query Asset Information

        1. **Choose Query Method**: Manual input or browse existing assets
        2. **Enter Stock Code**: Supports A-share (6 digits) and HK stock (5 digits) codes
        3. **Click Query**: Click "Query Asset Info" button
        4. **View Details**: Browse basic information, financial metrics and data coverage
        5. **Refresh Data**: Use "Force Refresh" to get latest information

        #### 📊 Information Content

        - **Basic Information**: Company name, industry, exchange, etc.
        - **Financial Metrics**: PE, PB, ROE, market cap and other key indicators
        - **Data Coverage**: Historical data completeness and quality information
        """)

    with col2:
        st.markdown("""
        #### 💡 Usage Tips

        - **Browse Function**: Use "Browse Existing Assets" to quickly select stocks
        - **Industry Filter**: View related stocks by industry classification
        - **HK Stock Support**: Supports HK stock code queries (e.g. 00700)
        - **Recent Queries**: Quickly re-view previously queried stocks

        #### 🎯 Recommended Queries

        **A-Share Recommendations**:
        - **600000**: SPDB (Banking leader)
        - **000001**: PAB (Joint-stock bank)
        - **600519**: Kweichow Moutai (Consumer industry)

        **HK Stock Recommendations**:
        - **00700**: Tencent Holdings (Tech leader)
        - **09988**: Alibaba-SW (E-commerce giant)
        """)

    # Quick query buttons
    st.markdown("### 🚀 Quick Query")
    st.markdown("Click buttons below to quickly query popular stock asset information")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("SPDB(600000)", use_container_width=True, key="quick_asset_600000"):
            st.session_state.update({
                'symbol': '600000',
                'auto_query_asset': True
            })
            st.rerun()

    with col2:
        if st.button("PAB(000001)", use_container_width=True, key="quick_asset_000001"):
            st.session_state.update({
                'symbol': '000001',
                'auto_query_asset': True
            })
            st.rerun()

    with col3:
        if st.button("Kweichow Moutai(600519)", use_container_width=True, key="quick_asset_600519"):
            st.session_state.update({
                'symbol': '600519',
                'auto_query_asset': True
            })
            st.rerun()

    with col4:
        if st.button("Vanke A(000002)", use_container_width=True, key="quick_asset_000002"):
            st.session_state.update({
                'symbol': '000002',
                'auto_query_asset': True
            })
            st.rerun()


if __name__ == "__main__":
    main()
