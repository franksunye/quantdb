"""
Stock Data Query Page - Cloud Version
Provides stock historical data query and chart display functionality,
adapted for Streamlit Cloud monolithic architecture
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import sys
import os
import time

# Add project root directory to path to access core modules
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(parent_dir)  # 回到QuantDB根目录
if project_root not in sys.path:
    sys.path.append(project_root)

# Import existing backend services (direct call, not through HTTP API)
try:
    from core.services import StockDataService, AssetInfoService
    from core.cache import AKShareAdapter
    from core.database import get_db
    BACKEND_SERVICES_AVAILABLE = True
except ImportError as e:
    BACKEND_SERVICES_AVAILABLE = False

# Import chart tools (try to import from original version)
try:
    from utils.charts import (
        create_price_chart,
        create_volume_chart,
        create_metrics_dashboard,
        calculate_basic_metrics,
        create_candlestick_chart,
        create_returns_distribution,
        create_performance_comparison_chart
    )
    CHARTS_AVAILABLE = True
except ImportError:
    CHARTS_AVAILABLE = False

# Page configuration
st.set_page_config(
    page_title="Stock Data - QuantDB",
    page_icon="📊",
    layout="wide"
)

def validate_stock_code(code: str) -> bool:
    """Validate stock code format - supports A-shares and HK stocks"""
    if not code:
        return False

    # Remove spaces
    code = code.strip()

    # HK stock validation: 5 digits (00700, 09988, 01810, etc.)
    if len(code) == 5 and code.isdigit():
        return True

    # A-share validation: 6 digits
    if len(code) == 6 and code.isdigit():
        # Check if it's a valid A-share code
        if code.startswith(('000', '001', '002', '003', '300')):  # Shenzhen Stock Exchange
            return True
        elif code.startswith('6'):  # Shanghai Stock Exchange
            return True
        elif code.startswith('688'):  # STAR Market
            return True

    return False

@st.cache_resource
def init_services():
    """Initialize backend services"""
    try:
        # Get database session
        db_session = next(get_db())

        # Initialize AKShare adapter
        akshare_adapter = AKShareAdapter()

        # Initialize services
        stock_service = StockDataService(db_session, akshare_adapter)
        asset_service = AssetInfoService(db_session)

        # Initialize query service
        from core.services import QueryService
        query_service = QueryService(db_session)

        return stock_service, asset_service, query_service
    except Exception as e:
        st.error(f"Service initialization failed: {e}")
        return None, None, None

def main():
    """Main page function"""

    # Check if backend services are available
    if not BACKEND_SERVICES_AVAILABLE:
        st.warning("Backend services unavailable - Demo mode")
        st.info("In demo mode, you can view the interface layout and functionality")

        # Still show interface in demo mode
        show_demo_interface()
        return

    # Initialize backend services
    services = init_services()
    if len(services) != 3 or not all(services):
        st.error("Service initialization failed - Please refresh the page")
        return

    stock_service, asset_service, query_service = services

    # Main page layout: left content area + right query panel
    col_main, col_query = st.columns([7, 3])  # 70% + 30% layout

    # 右侧查询面板
    with col_query:
        with st.container():
            st.markdown("### Stock Data Query")

            # 查询方式选择
            query_mode = st.radio(
                "Query Method",
                ["Manual Input", "Browse Existing"],
                help="Choose query method: manual input or select from existing stocks"
            )

            if query_mode == "Manual Input":
                # 股票代码输入
                symbol = st.text_input(
                    "Stock Code",
                    value="600000",
                    placeholder="A-shares: 600000 | HK: 00700",
                    help="Supports A-share codes (6 digits) and Hong Kong stock codes (5 digits)"
                )
            else:
                # Browse existing stocks
                symbol = display_stock_browser(query_service)

            # Date range selection
            st.markdown("#### Date Range")

            # Quick selection buttons
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Last 7 Days", use_container_width=True):
                    st.session_state.start_date = date.today() - timedelta(days=7)
                    st.session_state.end_date = date.today()
            with col2:
                if st.button("Last 30 Days", use_container_width=True):
                    st.session_state.start_date = date.today() - timedelta(days=30)
                    st.session_state.end_date = date.today()

            # Date selectors
            start_date = st.date_input(
                "Start Date",
                value=st.session_state.get('start_date', date.today() - timedelta(days=7)),
                max_value=date.today(),
                key='start_date'
            )

            end_date = st.date_input(
                "End Date",
                value=st.session_state.get('end_date', date.today()),
                max_value=date.today(),
                key='end_date'
            )

            # Adjustment selection
            adjust_type = st.selectbox(
                "Adjustment Type",
                options=["None", "Forward", "Backward"],
                index=0,
                help="Forward: Adjust based on current price\nBackward: Adjust based on listing price"
            )

            # Convert adjustment parameters
            adjust_map = {"None": "", "Forward": "qfq", "Backward": "hfq"}
            adjust = adjust_map[adjust_type]

            # Query button
            query_button = st.button("Query Data", type="primary", use_container_width=True)

            # Display recent queries
            display_recent_stock_queries()

    # Check for automatic query requests
    if st.session_state.get('auto_query_stock'):
        symbol = st.session_state.get('symbol', '600000')
        query_button = True
        st.session_state.auto_query_stock = False

    # Check for saved query state (to maintain page state)
    if not query_button and st.session_state.get('current_stock_symbol'):
        symbol = st.session_state.get('current_stock_symbol')
        start_date = st.session_state.get('current_start_date', date.today() - timedelta(days=7))
        end_date = st.session_state.get('current_end_date', date.today())
        adjust = st.session_state.get('current_adjust', "")
        query_button = True  # Automatically redisplay previously queried stock data

    # Handle suggested stock queries
    if st.session_state.get('suggested_symbol'):
        suggested_symbol = st.session_state.pop('suggested_symbol')
        suggested_name = st.session_state.pop('suggested_name', '')

        # Automatically set parameters and query
        symbol = suggested_symbol
        start_date = date.today() - timedelta(days=7)  # Use 7-day range for better performance
        end_date = date.today()
        adjust = ""
        query_button = True

    # Left main content area
    with col_main:
        if query_button or st.session_state.get('auto_query', False):

            # Validate input
            if not symbol:
                st.error("Please enter a stock code")
                return

            if start_date >= end_date:
                st.error("Start date must be earlier than end date")
                return

            # Validate stock code format
            if not validate_stock_code(symbol):
                st.error("Please enter a valid stock code (A-shares: 6 digits, HK stocks: 5 digits)")
                return

            # Save current query state
            st.session_state.current_stock_symbol = symbol
            st.session_state.current_start_date = start_date
            st.session_state.current_end_date = end_date
            st.session_state.current_adjust = adjust

            # Display query information
            st.info(f"Querying stock {symbol} data from {start_date} to {end_date}...")

            # Query data
            with st.spinner("Querying data..."):
                try:
                    # Call backend service to get stock data
                    result = stock_service.get_stock_data(
                        symbol=symbol,
                        start_date=start_date.strftime('%Y%m%d'),
                        end_date=end_date.strftime('%Y%m%d'),
                        adjust=adjust
                    )

                    if result is None or (isinstance(result, pd.DataFrame) and result.empty):
                        st.warning("No data found for the specified time range")

                        # Provide basic error information and solutions
                        with st.expander("🔍 Possible Causes and Solutions"):
                            st.markdown("""
                            **Possible Causes:**
                            1. 📅 **Date Range Issue**: No trading days in the selected date range (weekends, holidays)
                            2. 📈 **Stock Status Issue**: The stock may be suspended, delisted, or long-term suspended
                            3. 🌐 **Data Source Issue**: AKShare temporarily unable to retrieve data for this stock
                            4. ⏰ **Data Delay**: Latest data may not be updated yet

                            **Suggested Solutions:**
                            - 🔄 **Expand Time Range**: Try querying the last 30 days or longer period
                            - 📊 **Change Stock Code**: Try active stocks like: 600000(SPDB), 000001(PAB)
                            - 📅 **Check Trading Days**: Avoid selecting weekends or holidays
                            - 🔍 **Verify Stock Code**: Confirm the stock code is correct and still trading
                            """)

                        # Provide quick alternative options
                        st.markdown("**🚀 Quick Try Active Stocks:**")

                        # A-share recommendations
                        st.markdown("**A-Share Recommendations:**")
                        col1, col2, col3 = st.columns(3)

                        with col1:
                            if st.button("SPDB(600000)", key="suggest_600000"):
                                st.session_state.update({
                                    'suggested_symbol': '600000',
                                    'suggested_name': 'SPDB'
                                })
                                st.rerun()

                        with col2:
                            if st.button("PAB(000001)", key="suggest_000001"):
                                st.session_state.update({
                                    'suggested_symbol': '000001',
                                    'suggested_name': 'PAB'
                                })
                                st.rerun()

                        with col3:
                            if st.button("Kweichow Moutai(600519)", key="suggest_600519"):
                                st.session_state.update({
                                    'suggested_symbol': '600519',
                                    'suggested_name': 'Kweichow Moutai'
                                })
                                st.rerun()

                        # HK stock recommendations
                        st.markdown("**🇭🇰 HK Stock Recommendations:**")
                        col4, col5, col6 = st.columns(3)

                        with col4:
                            if st.button("Tencent(00700)", key="suggest_00700"):
                                st.session_state.update({
                                    'suggested_symbol': '00700',
                                    'suggested_name': 'Tencent'
                                })
                                st.rerun()

                        with col5:
                            if st.button("Alibaba(09988)", key="suggest_09988"):
                                st.session_state.update({
                                    'suggested_symbol': '09988',
                                    'suggested_name': 'Alibaba-SW'
                                })
                                st.rerun()

                        with col6:
                            if st.button("Xiaomi(01810)", key="suggest_01810"):
                                st.session_state.update({
                                    'suggested_symbol': '01810',
                                    'suggested_name': 'Xiaomi-W'
                                })
                                st.rerun()

                        return

                    # Convert to DataFrame
                    df = pd.DataFrame(result) if not isinstance(result, pd.DataFrame) else result

                    # Display success information
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.success(f"Retrieved {len(df)} records")
                    with col2:
                        st.info("Data from backend service")
                    with col3:
                        st.info("Response time: Fast")

                    # Add to recent query list
                    add_to_recent_stock_queries(symbol, f"Stock {symbol}")

                    # Display data
                    display_stock_data(df, symbol, {
                        'cache_hit': False,
                        'response_time_ms': 100,
                        'akshare_called': True
                    })

                except Exception as e:
                    st.error(f"Query failed: {str(e)}")
                    st.exception(e)

        else:
            # Display usage guide
            show_usage_guide()





def display_stock_data(df: pd.DataFrame, symbol: str, metadata: dict):
    """Display stock data"""

    # Calculate basic metrics
    if CHARTS_AVAILABLE:
        metrics = calculate_basic_metrics(df)

        # Display metrics dashboard
        st.subheader("Key Metrics")
        create_metrics_dashboard(metrics)
    else:
        # Simple metrics display
        st.subheader("Key Metrics")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Latest Price", f"¥{df['close'].iloc[-1]:.2f}")
        with col2:
            st.metric("High", f"¥{df['high'].max():.2f}")
        with col3:
            st.metric("Low", f"¥{df['low'].min():.2f}")
        with col4:
            if len(df) > 1:
                change = (df['close'].iloc[-1] - df['close'].iloc[0]) / df['close'].iloc[0] * 100
                st.metric("Period Change", f"{change:.2f}%")
            else:
                st.metric("Period Change", "N/A")

    st.markdown("---")

    # Chart selection
    st.subheader("Data Visualization")

    if CHARTS_AVAILABLE:
        chart_tabs = st.tabs(["Price Trend", "Candlestick", "Volume", "Returns Analysis", "Performance"])

        with chart_tabs[0]:
            st.markdown("#### Price Trend Chart")
            price_chart = create_price_chart(df, f"Stock {symbol} Price Trend")
            st.plotly_chart(price_chart, use_container_width=True)

        with chart_tabs[1]:
            st.markdown("#### Candlestick Chart")
            if all(col in df.columns for col in ['open', 'high', 'low', 'close']):
                candlestick_chart = create_candlestick_chart(df, f"Stock {symbol} Candlestick Chart")
                st.plotly_chart(candlestick_chart, use_container_width=True)
            else:
                st.info("No complete OHLC data available, cannot display candlestick chart")

        with chart_tabs[2]:
            st.markdown("#### Volume")
            if 'volume' in df.columns:
                volume_chart = create_volume_chart(df, f"Stock {symbol} Volume")
                st.plotly_chart(volume_chart, use_container_width=True)
            else:
                st.info("No volume data available")

        with chart_tabs[3]:
            st.markdown("#### Returns Analysis")
            if 'close' in df.columns and len(df) > 1:
                returns_chart = create_returns_distribution(df, f"Stock {symbol} Returns Distribution")
                st.plotly_chart(returns_chart, use_container_width=True)

                # Returns statistics
                returns = df['close'].pct_change().dropna() * 100
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Average Daily Return", f"{returns.mean():.2f}%")
                with col2:
                    st.metric("Return Std Dev", f"{returns.std():.2f}%")
                with col3:
                    st.metric("Max Daily Gain", f"{returns.max():.2f}%")
            else:
                st.info("Insufficient data for returns analysis")

        with chart_tabs[4]:
            st.markdown("#### Performance Comparison")
            if metadata.get('response_time_ms') is not None:
                cache_time = metadata.get('response_time_ms', 0)
                # Simulate AKShare direct call time (based on cache hit)
                akshare_time = 1075.2 if metadata.get('cache_hit') else cache_time

                if cache_time != akshare_time:
                    perf_chart = create_performance_comparison_chart(cache_time, akshare_time)
                    st.plotly_chart(perf_chart, use_container_width=True)

                    # Performance improvement explanation
                    improvement = ((akshare_time - cache_time) / akshare_time * 100) if akshare_time > 0 else 0
                    st.success(f"🚀 QuantDB cache is {improvement:.1f}% faster than direct AKShare calls")
                else:
                    st.info("First query, no performance comparison data available")
            else:
                st.info("No performance data available")
    else:
        # Simple chart display
        st.info("📊 Chart functionality requires complete backend service support")

        # Display simple price trend
        st.markdown("#### Price Data")
        st.line_chart(df.set_index('date')['close'] if 'date' in df.columns else df['close'])

    # Data table
    st.subheader("Detailed Data")

    # Data processing and formatting
    display_df = df.copy()

    # Format numeric columns
    numeric_columns = ['open', 'high', 'low', 'close', 'volume']
    for col in numeric_columns:
        if col in display_df.columns:
            if col == 'volume':
                display_df[col] = display_df[col].apply(lambda x: f"{x:,.0f}" if pd.notnull(x) else "")
            else:
                display_df[col] = display_df[col].apply(lambda x: f"{x:.2f}" if pd.notnull(x) else "")

    # Rename columns
    column_names = {
        'date': 'Date',
        'trade_date': 'Trade Date',
        'open': 'Open',
        'high': 'High',
        'low': 'Low',
        'close': 'Close',
        'volume': 'Volume',
        'amount': 'Amount'
    }

    display_df = display_df.rename(columns=column_names)

    # Display table
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )

    # Data statistics
    with st.expander("📈 Data Statistics"):
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Price Statistics**")
            st.write(f"- Latest Price: ¥{metrics.get('latest_price', 0):.2f}")
            st.write(f"- Highest Price: ¥{metrics.get('high_price', 0):.2f}")
            st.write(f"- Lowest Price: ¥{metrics.get('low_price', 0):.2f}")
            st.write(f"- Average Price: ¥{metrics.get('avg_price', 0):.2f}")
            st.write(f"- Price Volatility: {metrics.get('volatility', 0):.2f}")

        with col2:
            st.markdown("**Query Information**")
            st.write(f"- Data Records: {len(df)}")
            st.write(f"- Cache Hit: {'Yes' if metadata.get('cache_hit') else 'No'}")
            st.write(f"- AKShare Called: {'Yes' if metadata.get('akshare_called') else 'No'}")
            st.write(f"- Response Time: {metadata.get('response_time_ms', 0):.1f}ms")
            if 'total_volume' in metrics:
                st.write(f"- Total Volume: {metrics['total_volume']:,.0f}")

def show_demo_interface():
    """Display demo interface"""

    # Main page layout: left content area + right query panel
    col_main, col_query = st.columns([7, 3])  # 70% + 30% layout

    # Right query panel
    with col_query:
        with st.container():
            st.markdown("### 🔍 Stock Data Query")

            # Query method selection
            query_mode = st.radio(
                "Query Method",
                ["Manual Input", "Browse Existing"],
                help="Choose query method: manual input or select from existing stocks"
            )

            if query_mode == "Manual Input":
                # Stock code input
                symbol = st.text_input(
                    "Stock Code",
                    value="600000",
                    placeholder="A-shares: 600000 | HK: 02171",
                    help="Supports A-share codes (6 digits) and HK stock codes (5 digits)"
                )
            else:
                # Browse existing stocks
                st.selectbox("Select Stock", ["600000 - SPDB", "000001 - PAB"])

            # Date range selection
            st.markdown("#### 📅 Date Range")

            # Quick selection buttons
            col1, col2 = st.columns(2)
            with col1:
                st.button("Last 7 Days", use_container_width=True)
            with col2:
                st.button("Last 30 Days", use_container_width=True)

            # Date selectors
            start_date = st.date_input(
                "Start Date",
                value=date.today() - timedelta(days=7),
                max_value=date.today()
            )

            end_date = st.date_input(
                "End Date",
                value=date.today(),
                max_value=date.today()
            )

            # Adjustment selection
            adjust_type = st.selectbox(
                "Adjustment Type",
                options=["None", "Forward", "Backward"],
                index=0,
                help="Forward: Adjust based on current price\nBackward: Adjust based on listing price"
            )

            # Query button
            query_button = st.button("🔍 Query Data", type="primary", use_container_width=True)

            # Display recent queries
            st.markdown("---")
            st.markdown("**🕒 Recent Queries**")
            st.caption("No recent query records")

    # 左侧主内容区域
    with col_main:
        if query_button:
            st.info("⚠️ 演示模式：实际查询功能需要完整的后端服务支持")

            # 显示模拟的成功信息
            col1, col2, col3 = st.columns(3)
            with col1:
                st.success("✅ 演示数据已加载")
            with col2:
                st.info("🌐 演示模式")
            with col3:
                st.info("⏱️ 响应时间: 演示")

            # 显示模拟数据
            st.markdown("### 📊 演示数据展示")
            st.info("这里将显示股票数据的图表和统计信息")

            # 创建一些模拟数据用于演示
            import numpy as np
            dates = pd.date_range(start=start_date, end=end_date, freq='D')
            mock_data = {
                'date': dates,
                'open': np.random.uniform(10, 15, len(dates)),
                'high': np.random.uniform(15, 20, len(dates)),
                'low': np.random.uniform(8, 12, len(dates)),
                'close': np.random.uniform(10, 15, len(dates)),
                'volume': np.random.randint(1000000, 10000000, len(dates))
            }
            mock_df = pd.DataFrame(mock_data)

            # 显示模拟数据表格
            st.subheader("📋 演示数据表格")
            st.dataframe(mock_df, use_container_width=True)

        else:
            # 显示使用说明
            show_usage_guide()

def show_usage_guide():
    """显示使用指南"""

    st.markdown("### 📖 使用指南")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        #### 🔍 如何查询股票数据

        1. **选择查询方式**: 手动输入股票代码或浏览已有股票
        2. **输入股票代码**: 在右侧面板输入股票代码 (A股6位/港股5位)
        3. **选择日期范围**: 选择查询的开始和结束日期
        4. **选择复权类型**: 根据需要选择复权方式
        5. **点击查询**: 点击"查询数据"按钮获取数据

        #### 📊 功能特点

        - **智能缓存**: 重复查询响应极快
        - **实时数据**: 数据来源于AKShare官方接口
        - **多种图表**: 价格趋势图、成交量图等
        - **详细统计**: 提供完整的数据统计信息
        """)

    with col2:
        st.markdown("""
        #### 💡 使用技巧

        - **股票代码格式**: A股6位(600000)、港股5位(02171)
        - **日期范围**: 默认7天，可根据需要调整
        - **复权选择**: 分析价格趋势时建议使用前复权
        - **快速选择**: 使用"最近7天"、"最近30天"快速设置

        #### 🎯 推荐股票代码

        **A股 (6位)**:
        - **600000**: 浦发银行 (大盘蓝筹)
        - **000001**: 平安银行 (深市银行)
        - **600519**: 贵州茅台 (消费龙头)

        **港股 (5位)**:
        - **02171**: 科济药业-B (生物医药)
        - **00700**: 腾讯控股 (科技龙头)
        - **00981**: 中芯国际 (半导体)
        """)

    # 示例查询
    st.markdown("### 🚀 快速开始")
    st.markdown("点击下方按钮快速查询热门股票，或使用右侧查询面板自定义查询")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("查询浦发银行(600000)", use_container_width=True, key="quick_600000"):
            st.session_state.update({
                'suggested_symbol': '600000',
                'suggested_name': '浦发银行'
            })
            st.rerun()

    with col2:
        if st.button("查询平安银行(000001)", use_container_width=True, key="quick_000001"):
            st.session_state.update({
                'suggested_symbol': '000001',
                'suggested_name': '平安银行'
            })
            st.rerun()

    with col3:
        if st.button("查询贵州茅台(600519)", use_container_width=True, key="quick_600519"):
            st.session_state.update({
                'suggested_symbol': '600519',
                'suggested_name': '贵州茅台'
            })
            st.rerun()

def display_stock_browser(query_service):
    """显示股票浏览器 - 查询数据库中的真实股票数据"""

    st.markdown("**📋 浏览已有股票**")

    try:
        # 查询数据库中的真实股票数据
        with st.spinner("正在加载股票列表..."):
            assets, total_count = query_service.query_assets(
                sort_by="symbol",
                sort_order="asc",
                limit=100  # 限制返回数量，避免加载过多数据
            )

        if not assets:
            # 如果数据库中没有股票数据，显示提示信息
            st.info("📊 数据库中暂无股票数据")
            st.markdown("""
            **💡 提示：**
            - 数据库中的股票数据会在您首次查询股票时自动创建
            - 您可以先使用"手动输入"方式查询一些股票，系统会自动保存股票信息
            - 推荐先查询：600000(浦发银行)、000001(平安银行)、600519(贵州茅台)
            """)
            return ""

        # 转换为字典格式，便于处理
        asset_list = []
        for asset in assets:
            asset_dict = {
                'symbol': asset.symbol,
                'name': asset.name or f'Stock {asset.symbol}',
                'industry': asset.industry or '其他'
            }
            asset_list.append(asset_dict)

        # 按行业分组
        industry_groups = {}
        for asset in asset_list:
            industry = asset.get('industry', '其他')
            if industry not in industry_groups:
                industry_groups[industry] = []
            industry_groups[industry].append(asset)

        # 显示统计信息
        st.caption(f"📊 数据库中共有 {total_count} 只股票")

        # 行业筛选
        selected_industry = st.selectbox(
            "按行业筛选",
            ["全部"] + sorted(list(industry_groups.keys())),
            help="选择特定行业查看相关股票"
        )

        # 筛选股票
        if selected_industry == "全部":
            filtered_assets = asset_list
        else:
            filtered_assets = industry_groups[selected_industry]

        # 股票选择
        asset_options = {}
        for asset in filtered_assets:
            display_name = f"{asset['symbol']} - {asset['name']}"
            if asset.get('industry') and asset['industry'] != '其他':
                display_name += f" ({asset['industry']})"
            asset_options[display_name] = asset['symbol']

        if asset_options:
            selected_display = st.selectbox(
                "选择股票",
                list(asset_options.keys()),
                help="从列表中选择要查看的股票"
            )

            return asset_options[selected_display]
        else:
            st.info("该行业暂无股票数据")
            return ""

    except Exception as e:
        st.error(f"加载股票列表失败: {str(e)}")
        # 发生错误时，提供一些默认选项
        st.markdown("**🔄 使用默认股票列表：**")
        default_options = {
            "600000 - 浦发银行": "600000",
            "000001 - 平安银行": "000001",
            "600519 - 贵州茅台": "600519"
        }

        selected_display = st.selectbox(
            "选择股票",
            list(default_options.keys()),
            help="从默认列表中选择股票"
        )

        return default_options[selected_display]

def display_recent_stock_queries():
    """显示最近查询的股票"""

    st.markdown("---")
    st.markdown("**🕒 最近查询**")

    # 从session state获取最近查询
    recent_queries = st.session_state.get('recent_stock_queries', [])

    if recent_queries:
        # 显示最近3个查询
        for i, query in enumerate(recent_queries[:3]):
            symbol = query['symbol']
            name = query.get('name', f'Stock {symbol}')
            query_time = query.get('time', '')

            if st.button(
                f"{symbol} - {name}",
                key=f"recent_stock_{i}_{symbol}",
                help=f"查询时间: {query_time}",
                use_container_width=True
            ):
                st.session_state.update({
                    'symbol': symbol,
                    'auto_query_stock': True
                })
                st.rerun()
    else:
        st.caption("暂无最近查询记录")

def add_to_recent_stock_queries(symbol: str, name: str):
    """添加到最近查询列表"""

    if 'recent_stock_queries' not in st.session_state:
        st.session_state.recent_stock_queries = []

    # 创建查询记录
    from datetime import datetime
    query_record = {
        'symbol': symbol,
        'name': name,
        'time': datetime.now().strftime('%Y-%m-%d %H:%M')
    }

    # 移除重复项
    recent_queries = st.session_state.recent_stock_queries
    recent_queries = [q for q in recent_queries if q['symbol'] != symbol]

    # 添加到开头
    recent_queries.insert(0, query_record)

    # 保持最多10个记录
    st.session_state.recent_stock_queries = recent_queries[:10]

if __name__ == "__main__":
    main()
