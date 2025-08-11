"""
Watchlist Management Page - Cloud Version

Users can add, remove, manage watchlist stocks, and perform batch queries and analysis.
"""

import json
import os
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd
import streamlit as st

# Add project root directory to Python path to access core modules
current_dir = Path(__file__).parent.parent
project_root = current_dir.parent  # 回到QuantDB根目录
sys.path.insert(0, str(project_root))

# Import utility components
try:
    from utils.charts import calculate_basic_metrics, create_price_chart
    from utils.config import config
    from utils.stock_validator import get_stock_recommendations, validate_stock_code

    ADVANCED_FEATURES = True
except ImportError:
    ADVANCED_FEATURES = False

# Page configuration
st.set_page_config(page_title="Watchlist - QuantDB", page_icon="📊", layout="wide")

# Watchlist data file path
WATCHLIST_FILE = current_dir / "data" / "watchlist.json"


@st.cache_data
def load_watchlist():
    """Load watchlist"""
    try:
        # Ensure data directory exists
        WATCHLIST_FILE.parent.mkdir(exist_ok=True)

        if WATCHLIST_FILE.exists():
            with open(WATCHLIST_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        else:
            # Default watchlist
            default_watchlist = {
                "600000": {"name": "SPDB", "added_date": "2024-01-01"},
                "000001": {"name": "PAB", "added_date": "2024-01-01"},
                "600519": {"name": "Kweichow Moutai", "added_date": "2024-01-01"},
            }
            save_watchlist(default_watchlist)
            return default_watchlist
    except Exception as e:
        st.error(f"Failed to load watchlist: {str(e)}")
        return {}


def save_watchlist(watchlist):
    """Save watchlist"""
    try:
        WATCHLIST_FILE.parent.mkdir(exist_ok=True)
        with open(WATCHLIST_FILE, "w", encoding="utf-8") as f:
            json.dump(watchlist, f, ensure_ascii=False, indent=2)
        # 清除缓存以便重新加载
        load_watchlist.clear()
    except Exception as e:
        st.error(f"Failed to save watchlist: {str(e)}")


@st.cache_resource
def init_services():
    """Initialize service instances"""
    try:
        from core.cache import AKShareAdapter
        from core.database import get_db
        from core.services import AssetInfoService, StockDataService

        db_session = next(get_db())
        akshare_adapter = AKShareAdapter()

        return {
            "stock_service": StockDataService(db_session, akshare_adapter),
            "asset_service": AssetInfoService(db_session),
            "db_session": db_session,
        }
    except Exception as e:
        st.error(f"Service initialization failed: {e}")
        return None


def main():
    """Main page function"""

    # Page title
    st.title("🎯 Watchlist Management")
    st.markdown("Manage your watchlist stocks, perform batch analysis and monitoring")
    st.markdown("---")

    # 初始化服务
    services = init_services()
    if not services:
        st.error("❌ Service initialization failed, please refresh the page and try again")
        return

    # Load watchlist data
    if "watchlist" not in st.session_state:
        st.session_state.watchlist = load_watchlist()

    # Sidebar - Management operations
    with st.sidebar:
        st.header("📝 Watchlist Management")

        # Add stock
        st.subheader("➕ Add Stock")
        new_symbol = st.text_input(
            "Stock Code", placeholder="Enter 6-digit stock code", help="e.g.: 600000, 000001"
        )

        if st.button("Add to Watchlist", use_container_width=True):
            add_to_watchlist(new_symbol, services)

        # Recommended stocks
        if ADVANCED_FEATURES:
            st.subheader("💡 Recommended Stocks")
            recommendations = get_stock_recommendations()
            for rec in recommendations[:3]:
                if st.button(f"{rec['symbol']} - {rec['name']}", key=f"rec_{rec['symbol']}"):
                    add_to_watchlist(rec["symbol"], services)

        st.markdown("---")

        # Batch operations
        st.subheader("🔄 Batch Operations")

        if st.button("📊 Batch Query Data", use_container_width=True):
            st.session_state.batch_query = True

        if st.button("📤 Export Watchlist", use_container_width=True):
            export_watchlist()

        if st.button("🗑️ Clear Watchlist", use_container_width=True):
            if st.session_state.get("confirm_clear", False):
                st.session_state.watchlist = {}
                save_watchlist({})
                st.success("Watchlist cleared")
                st.session_state.confirm_clear = False
                st.rerun()
            else:
                st.session_state.confirm_clear = True
                st.warning("Click again to confirm clearing")

    # Main content area
    display_watchlist_overview()

    # Batch query results
    if st.session_state.get("batch_query", False):
        display_batch_query_results(services)
        st.session_state.batch_query = False


def add_to_watchlist(symbol, services):
    """Add stock to watchlist"""
    if not symbol:
        st.error("Please enter stock code")
        return

    # Validate stock code
    if ADVANCED_FEATURES:
        validation_result = validate_stock_code(symbol)
        if not validation_result["is_valid"]:
            st.error("Please enter valid stock code (6 digits)")
            return
        symbol = symbol.strip()
    else:
        if not config.validate_symbol(symbol):
            st.error("Please enter valid stock code (6 digits)")
            return
        symbol = config.normalize_symbol(symbol)

    # Check if already exists
    if symbol in st.session_state.watchlist:
        st.warning(f"Stock {symbol} is already in watchlist")
        return

    # Get stock information
    try:
        asset_info, metadata = services["asset_service"].get_or_create_asset(symbol)

        if asset_info:
            stock_name = asset_info.name
            st.session_state.watchlist[symbol] = {
                "name": stock_name,
                "added_date": datetime.now().strftime("%Y-%m-%d"),
            }
            save_watchlist(st.session_state.watchlist)
            st.success(f"✅ Added {stock_name} ({symbol}) to watchlist")
            st.rerun()
        else:
            st.error(f"Stock {symbol} information not found")

    except Exception as e:
        st.error(f"Failed to add stock: {str(e)}")


def remove_from_watchlist(symbol):
    """Remove stock from watchlist"""
    if symbol in st.session_state.watchlist:
        stock_name = st.session_state.watchlist[symbol]["name"]
        del st.session_state.watchlist[symbol]
        save_watchlist(st.session_state.watchlist)
        st.success(f"✅ Removed {stock_name} ({symbol})")
        st.rerun()


def display_watchlist_overview():
    """Display watchlist overview"""

    st.subheader("📋 My Watchlist")

    if not st.session_state.watchlist:
        st.info("No stocks in watchlist, please add stocks on the left")
        return

    # Watchlist statistics
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Watchlist Count", len(st.session_state.watchlist))

    with col2:
        # Calculate average holding days
        today = datetime.now()
        total_days = 0
        for stock in st.session_state.watchlist.values():
            added_date = datetime.strptime(stock["added_date"], "%Y-%m-%d")
            days = (today - added_date).days
            total_days += days
        avg_days = (
            total_days // len(st.session_state.watchlist) if st.session_state.watchlist else 0
        )
        st.metric("Average Watch Days", f"{avg_days} days")

    with col3:
        latest_added = max(st.session_state.watchlist.values(), key=lambda x: x["added_date"])[
            "added_date"
        ]
        st.metric("Latest Added", latest_added)

    # Stock list
    st.markdown("### 📊 Stock List")

    # Create table data
    table_data = []
    for symbol, info in st.session_state.watchlist.items():
        table_data.append(
            {
                "Stock Code": symbol,
                "Stock Name": info["name"],
                "Added Date": info["added_date"],
                "Actions": symbol,
            }
        )

    if table_data:
        df = pd.DataFrame(table_data)

        # Display table
        for idx, row in df.iterrows():
            col1, col2, col3, col4, col5 = st.columns([1, 2, 1, 1, 1])

            with col1:
                st.write(row["Stock Code"])

            with col2:
                st.write(row["Stock Name"])

            with col3:
                st.write(row["Added Date"])

            with col4:
                if st.button("📈 View", key=f"view_{row['Stock Code']}"):
                    st.session_state.selected_stock = row["Stock Code"]
                    st.session_state.show_stock_detail = True

            with col5:
                if st.button("🗑️ Remove", key=f"remove_{row['Stock Code']}"):
                    remove_from_watchlist(row["Stock Code"])

    # Display selected stock details
    if st.session_state.get("show_stock_detail", False) and st.session_state.get("selected_stock"):
        display_stock_detail(st.session_state.selected_stock)


def display_stock_detail(symbol):
    """Display stock detailed information"""

    st.markdown("---")
    st.subheader(f"📈 {st.session_state.watchlist[symbol]['name']} ({symbol}) Details")

    try:
        services = init_services()
        if not services:
            st.error("Service initialization failed")
            return

        # Get last 7 days data
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=7)

        with st.spinner("Getting stock data..."):
            stock_data = services["stock_service"].get_stock_data(
                symbol=symbol,
                start_date=start_date.strftime("%Y%m%d"),
                end_date=end_date.strftime("%Y%m%d"),
            )
            asset_info, metadata = services["asset_service"].get_or_create_asset(symbol)

        if stock_data is not None and not stock_data.empty:
            df = stock_data.copy()

            # 确保日期列存在
            if "date" in df.columns:
                df["trade_date"] = pd.to_datetime(df["date"])
            elif "trade_date" in df.columns:
                df["trade_date"] = pd.to_datetime(df["trade_date"])

            # 基础指标
            if ADVANCED_FEATURES:
                metrics = calculate_basic_metrics(df)
            else:
                # 简单指标计算
                latest_price = df["close"].iloc[-1] if len(df) > 0 else 0
                first_price = df["close"].iloc[0] if len(df) > 0 else latest_price
                price_change = (
                    ((latest_price - first_price) / first_price * 100) if first_price != 0 else 0
                )

                metrics = {
                    "latest_price": latest_price,
                    "high_price": df["close"].max(),
                    "low_price": df["close"].min(),
                    "avg_price": df["close"].mean(),
                    "price_change": price_change,
                }

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Latest Price", f"¥{metrics.get('latest_price', 0):.2f}")

            with col2:
                change = metrics.get("price_change", 0)
                st.metric("Price Change", f"{change:.2f}%", delta=f"{change:.2f}%")

            with col3:
                st.metric("High Price", f"¥{metrics.get('high_price', 0):.2f}")

            with col4:
                st.metric("Low Price", f"¥{metrics.get('low_price', 0):.2f}")

            # Price chart
            st.markdown("#### 📊 Price Trend")
            if ADVANCED_FEATURES:
                price_chart = create_price_chart(df, f"{symbol} Price Trend")
            else:
                # Simple chart
                import plotly.express as px

                price_chart = px.line(df, x="trade_date", y="close", title=f"{symbol} Price Trend")

            st.plotly_chart(price_chart, use_container_width=True)

            # 财务信息
            if asset_info:
                st.markdown("#### 💰 基本信息")
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.write(f"**公司名称**: {asset_info.name}")
                    st.write(f"**股票代码**: {asset_info.symbol}")

                with col2:
                    st.write(f"**交易所**: {asset_info.exchange}")
                    st.write(f"**行业**: {asset_info.industry or 'N/A'}")

                with col3:
                    st.write(f"**数据来源**: {asset_info.data_source}")
                    st.write(f"**更新时间**: {asset_info.last_updated or 'N/A'}")

        else:
            st.warning("暂无最近的价格数据")

        # 关闭详情按钮
        if st.button("关闭详情"):
            st.session_state.show_stock_detail = False
            st.rerun()

    except Exception as e:
        st.error(f"获取股票详情失败: {str(e)}")


def display_batch_query_results(services):
    """显示批量查询结果（性能优化版本）"""

    st.markdown("---")
    st.subheader("📊 批量查询结果")

    if not st.session_state.watchlist:
        st.info("暂无自选股进行批量查询")
        return

    try:
        # 尝试使用高性能批量客户端
        try:
            from utils.batch_client import create_st_batch_progress, get_batch_client

            batch_client = get_batch_client()
            symbols = list(st.session_state.watchlist.keys())

            st.info(f"🚀 使用高性能批量查询获取 {len(symbols)} 只股票数据...")

            # 创建进度显示
            progress_callback = create_st_batch_progress()

            # 批量获取自选股汇总信息
            with st.spinner("正在批量获取数据..."):
                summary_result = batch_client.get_watchlist_summary(symbols)

            # 处理结果
            batch_results = []
            summary_data = summary_result.get("summary", {})

            for symbol in symbols:
                watchlist_info = st.session_state.watchlist[symbol]
                summary_info = summary_data.get(symbol, {})

                batch_results.append(
                    {
                        "股票代码": symbol,
                        "股票名称": summary_info.get(
                            "name", watchlist_info.get("name", f"Stock {symbol}")
                        ),
                        "行业": summary_info.get("industry", "其他"),
                        "最新价格": summary_info.get("latest_price", "N/A"),
                        "涨跌幅(%)": summary_info.get("price_change_pct", "N/A"),
                        "数据来源": summary_info.get("data_source", "unknown"),
                        "有价格数据": "✅" if summary_info.get("has_price_data") else "❌",
                    }
                )

            # 显示性能统计
            metadata = summary_result.get("metadata", {})
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("总股票数", metadata.get("total_symbols", 0))
            with col2:
                st.metric("资产信息", metadata.get("assets_found", 0))
            with col3:
                st.metric("价格数据", metadata.get("price_data_found", 0))
            with col4:
                st.success("⚡ 高性能批量查询")

            st.text("查询完成！")

            # 显示结果
            if batch_results:
                df = pd.DataFrame(batch_results)

                # 格式化显示
                def format_price_change(val):
                    if isinstance(val, (int, float)):
                        if val > 0:
                            return f"+{val:.2f}%"
                        else:
                            return f"{val:.2f}%"
                    return str(val)

                # 应用样式
                styled_df = df.copy()
                styled_df["涨跌幅(%)"] = styled_df["涨跌幅(%)"].apply(format_price_change)

                st.dataframe(styled_df, use_container_width=True, hide_index=True)

                # 统计信息
                valid_changes = [x for x in df["涨跌幅(%)"] if isinstance(x, (int, float))]
                if valid_changes:
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        up_count = len([x for x in valid_changes if x > 0])
                        st.metric("上涨股票", f"{up_count}只")

                    with col2:
                        down_count = len([x for x in valid_changes if x < 0])
                        st.metric("下跌股票", f"{down_count}只")

                    with col3:
                        avg_change = sum(valid_changes) / len(valid_changes)
                        st.metric("平均涨跌幅", f"{avg_change:.2f}%")

        except ImportError:
            # 回退到基础批量查询
            st.warning("⚠️ 高性能批量查询不可用，使用基础查询模式")
            display_basic_batch_query(services)

    except Exception as e:
        st.error(f"批量查询失败: {str(e)}")


def display_basic_batch_query(services):
    """基础批量查询（回退方案）"""

    symbols = list(st.session_state.watchlist.keys())
    st.info(f"🔄 正在查询 {len(symbols)} 只股票的最新数据...")

    # 批量获取数据
    batch_results = []
    progress_bar = st.progress(0)

    for i, symbol in enumerate(symbols):
        try:
            # 获取资产信息
            asset_info, metadata = services["asset_service"].get_or_create_asset(symbol)

            # 获取最新价格数据（最近1天）
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=1)

            stock_data = services["stock_service"].get_stock_data(
                symbol=symbol,
                start_date=start_date.strftime("%Y%m%d"),
                end_date=end_date.strftime("%Y%m%d"),
            )

            # 处理数据
            latest_price = "N/A"
            price_change = "N/A"

            if stock_data is not None and not stock_data.empty:
                latest_price = f"¥{stock_data['close'].iloc[-1]:.2f}"
                if len(stock_data) > 1:
                    first_price = stock_data["close"].iloc[0]
                    last_price = stock_data["close"].iloc[-1]
                    change_pct = (last_price - first_price) / first_price * 100
                    price_change = f"{change_pct:.2f}%"

            batch_results.append(
                {
                    "股票代码": symbol,
                    "股票名称": (
                        asset_info.name
                        if asset_info
                        else st.session_state.watchlist[symbol]["name"]
                    ),
                    "行业": asset_info.industry if asset_info else "N/A",
                    "最新价格": latest_price,
                    "涨跌幅": price_change,
                    "数据来源": asset_info.data_source if asset_info else "N/A",
                    "状态": "✅" if stock_data is not None and not stock_data.empty else "❌",
                }
            )

        except Exception as e:
            batch_results.append(
                {
                    "股票代码": symbol,
                    "股票名称": st.session_state.watchlist[symbol]["name"],
                    "行业": "N/A",
                    "最新价格": "错误",
                    "涨跌幅": "N/A",
                    "数据来源": "N/A",
                    "状态": "❌",
                }
            )

        # 更新进度
        progress_bar.progress((i + 1) / len(symbols))

    progress_bar.empty()

    # 显示结果
    if batch_results:
        df = pd.DataFrame(batch_results)

        # 统计信息
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("总股票数", len(batch_results))
        with col2:
            success_count = len([r for r in batch_results if r["状态"] == "✅"])
            st.metric("成功查询", success_count)
        with col3:
            error_count = len([r for r in batch_results if r["状态"] == "❌"])
            st.metric("查询失败", error_count)
        with col4:
            st.metric("查询完成", "100%")

        st.dataframe(df, use_container_width=True, hide_index=True)


def export_watchlist():
    """导出自选股列表"""
    try:
        # 创建导出数据
        export_data = []
        for symbol, info in st.session_state.watchlist.items():
            export_data.append(
                {"股票代码": symbol, "股票名称": info["name"], "添加日期": info["added_date"]}
            )

        if export_data:
            df = pd.DataFrame(export_data)
            csv = df.to_csv(index=False, encoding="utf-8-sig")

            st.download_button(
                label="📥 下载自选股列表 (CSV)",
                data=csv,
                file_name=f"自选股列表_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
            )
        else:
            st.info("暂无自选股可导出")

    except Exception as e:
        st.error(f"导出失败: {str(e)}")


if __name__ == "__main__":
    main()
