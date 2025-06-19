"""
自选股管理页面 - 云端版本

用户可以添加、删除、管理自选股票，并进行批量查询和分析。
"""

import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, date, timedelta
import sys
from pathlib import Path

# 添加src目录到Python路径
current_dir = Path(__file__).parent.parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

# 导入工具组件
try:
    from utils.charts import create_price_chart, calculate_basic_metrics
    from utils.config import config
    from utils.stock_validator import validate_stock_code, get_stock_recommendations
    ADVANCED_FEATURES = True
except ImportError:
    ADVANCED_FEATURES = False

# 页面配置
st.set_page_config(
    page_title="自选股管理 - QuantDB Cloud",
    page_icon="🎯",
    layout="wide"
)

# 自选股数据文件路径
WATCHLIST_FILE = current_dir / "data" / "watchlist.json"

@st.cache_data
def load_watchlist():
    """加载自选股列表"""
    try:
        # 确保数据目录存在
        WATCHLIST_FILE.parent.mkdir(exist_ok=True)
        
        if WATCHLIST_FILE.exists():
            with open(WATCHLIST_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # 默认自选股
            default_watchlist = {
                "600000": {"name": "浦发银行", "added_date": "2024-01-01"},
                "000001": {"name": "平安银行", "added_date": "2024-01-01"},
                "600519": {"name": "贵州茅台", "added_date": "2024-01-01"}
            }
            save_watchlist(default_watchlist)
            return default_watchlist
    except Exception as e:
        st.error(f"加载自选股失败: {str(e)}")
        return {}

def save_watchlist(watchlist):
    """保存自选股列表"""
    try:
        WATCHLIST_FILE.parent.mkdir(exist_ok=True)
        with open(WATCHLIST_FILE, 'w', encoding='utf-8') as f:
            json.dump(watchlist, f, ensure_ascii=False, indent=2)
        # 清除缓存以便重新加载
        load_watchlist.clear()
    except Exception as e:
        st.error(f"保存自选股失败: {str(e)}")

@st.cache_resource
def init_services():
    """初始化服务实例"""
    try:
        from services.stock_data_service import StockDataService
        from services.asset_info_service import AssetInfoService
        from cache.akshare_adapter import AKShareAdapter
        from api.database import get_db

        db_session = next(get_db())
        akshare_adapter = AKShareAdapter()
        
        return {
            'stock_service': StockDataService(db_session, akshare_adapter),
            'asset_service': AssetInfoService(db_session),
            'db_session': db_session
        }
    except Exception as e:
        st.error(f"服务初始化失败: {e}")
        return None

def main():
    """主页面函数"""
    
    # 页面标题
    st.title("🎯 自选股管理")
    st.markdown("管理您的自选股票，进行批量分析和监控")
    st.markdown("---")
    
    # 初始化服务
    services = init_services()
    if not services:
        st.error("❌ 服务初始化失败，请刷新页面重试")
        return
    
    # 加载自选股数据
    if 'watchlist' not in st.session_state:
        st.session_state.watchlist = load_watchlist()
    
    # 侧边栏 - 管理操作
    with st.sidebar:
        st.header("📝 自选股管理")
        
        # 添加股票
        st.subheader("➕ 添加股票")
        new_symbol = st.text_input(
            "股票代码",
            placeholder="输入6位股票代码",
            help="例如: 600000, 000001"
        )
        
        if st.button("添加到自选股", use_container_width=True):
            add_to_watchlist(new_symbol, services)
        
        # 推荐股票
        if ADVANCED_FEATURES:
            st.subheader("💡 推荐股票")
            recommendations = get_stock_recommendations()
            for rec in recommendations[:3]:
                if st.button(f"{rec['symbol']} - {rec['name']}", key=f"rec_{rec['symbol']}"):
                    add_to_watchlist(rec['symbol'], services)
        
        st.markdown("---")
        
        # 批量操作
        st.subheader("🔄 批量操作")
        
        if st.button("📊 批量查询数据", use_container_width=True):
            st.session_state.batch_query = True
        
        if st.button("📤 导出自选股", use_container_width=True):
            export_watchlist()
        
        if st.button("🗑️ 清空自选股", use_container_width=True):
            if st.session_state.get('confirm_clear', False):
                st.session_state.watchlist = {}
                save_watchlist({})
                st.success("自选股已清空")
                st.session_state.confirm_clear = False
                st.rerun()
            else:
                st.session_state.confirm_clear = True
                st.warning("再次点击确认清空")
    
    # 主内容区域
    display_watchlist_overview()
    
    # 批量查询结果
    if st.session_state.get('batch_query', False):
        display_batch_query_results(services)
        st.session_state.batch_query = False

def add_to_watchlist(symbol, services):
    """添加股票到自选股"""
    if not symbol:
        st.error("请输入股票代码")
        return
    
    # 验证股票代码
    if ADVANCED_FEATURES:
        validation_result = validate_stock_code(symbol)
        if not validation_result['is_valid']:
            st.error("请输入有效的股票代码（6位数字）")
            return
        symbol = symbol.strip()
    else:
        if not config.validate_symbol(symbol):
            st.error("请输入有效的股票代码（6位数字）")
            return
        symbol = config.normalize_symbol(symbol)
    
    # 检查是否已存在
    if symbol in st.session_state.watchlist:
        st.warning(f"股票 {symbol} 已在自选股中")
        return
    
    # 获取股票信息
    try:
        asset_info, metadata = services['asset_service'].get_or_create_asset(symbol)
        
        if asset_info:
            stock_name = asset_info.name
            st.session_state.watchlist[symbol] = {
                "name": stock_name,
                "added_date": datetime.now().strftime("%Y-%m-%d")
            }
            save_watchlist(st.session_state.watchlist)
            st.success(f"✅ 已添加 {stock_name} ({symbol}) 到自选股")
            st.rerun()
        else:
            st.error(f"未找到股票 {symbol} 的信息")
    
    except Exception as e:
        st.error(f"添加股票失败: {str(e)}")

def remove_from_watchlist(symbol):
    """从自选股中移除股票"""
    if symbol in st.session_state.watchlist:
        stock_name = st.session_state.watchlist[symbol]['name']
        del st.session_state.watchlist[symbol]
        save_watchlist(st.session_state.watchlist)
        st.success(f"✅ 已移除 {stock_name} ({symbol})")
        st.rerun()

def display_watchlist_overview():
    """显示自选股概览"""
    
    st.subheader("📋 我的自选股")
    
    if not st.session_state.watchlist:
        st.info("暂无自选股，请在左侧添加股票")
        return
    
    # 自选股统计
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("自选股数量", len(st.session_state.watchlist))
    
    with col2:
        # 计算平均持有天数
        today = datetime.now()
        total_days = 0
        for stock in st.session_state.watchlist.values():
            added_date = datetime.strptime(stock['added_date'], "%Y-%m-%d")
            days = (today - added_date).days
            total_days += days
        avg_days = total_days // len(st.session_state.watchlist) if st.session_state.watchlist else 0
        st.metric("平均关注天数", f"{avg_days}天")
    
    with col3:
        latest_added = max(st.session_state.watchlist.values(), key=lambda x: x['added_date'])['added_date']
        st.metric("最新添加", latest_added)
    
    # 自选股列表
    st.markdown("### 📊 股票列表")
    
    # 创建表格数据
    table_data = []
    for symbol, info in st.session_state.watchlist.items():
        table_data.append({
            "股票代码": symbol,
            "股票名称": info['name'],
            "添加日期": info['added_date'],
            "操作": symbol
        })
    
    if table_data:
        df = pd.DataFrame(table_data)
        
        # 显示表格
        for idx, row in df.iterrows():
            col1, col2, col3, col4, col5 = st.columns([1, 2, 1, 1, 1])
            
            with col1:
                st.write(row['股票代码'])
            
            with col2:
                st.write(row['股票名称'])
            
            with col3:
                st.write(row['添加日期'])
            
            with col4:
                if st.button("📈 查看", key=f"view_{row['股票代码']}"):
                    st.session_state.selected_stock = row['股票代码']
                    st.session_state.show_stock_detail = True
            
            with col5:
                if st.button("🗑️ 移除", key=f"remove_{row['股票代码']}"):
                    remove_from_watchlist(row['股票代码'])
    
    # 显示选中股票的详细信息
    if st.session_state.get('show_stock_detail', False) and st.session_state.get('selected_stock'):
        display_stock_detail(st.session_state.selected_stock)

def display_stock_detail(symbol):
    """显示股票详细信息"""

    st.markdown("---")
    st.subheader(f"📈 {st.session_state.watchlist[symbol]['name']} ({symbol}) 详细信息")

    try:
        services = init_services()
        if not services:
            st.error("服务初始化失败")
            return

        # 获取最近7天数据
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=7)

        with st.spinner("获取股票数据..."):
            stock_data = services['stock_service'].get_stock_data(
                symbol=symbol,
                start_date=start_date.strftime('%Y%m%d'),
                end_date=end_date.strftime('%Y%m%d')
            )
            asset_info, metadata = services['asset_service'].get_or_create_asset(symbol)

        if stock_data is not None and not stock_data.empty:
            df = stock_data.copy()

            # 确保日期列存在
            if 'date' in df.columns:
                df['trade_date'] = pd.to_datetime(df['date'])
            elif 'trade_date' in df.columns:
                df['trade_date'] = pd.to_datetime(df['trade_date'])

            # 基础指标
            if ADVANCED_FEATURES:
                metrics = calculate_basic_metrics(df)
            else:
                # 简单指标计算
                latest_price = df['close'].iloc[-1] if len(df) > 0 else 0
                first_price = df['close'].iloc[0] if len(df) > 0 else latest_price
                price_change = ((latest_price - first_price) / first_price * 100) if first_price != 0 else 0

                metrics = {
                    'latest_price': latest_price,
                    'high_price': df['close'].max(),
                    'low_price': df['close'].min(),
                    'avg_price': df['close'].mean(),
                    'price_change': price_change
                }

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("最新价格", f"¥{metrics.get('latest_price', 0):.2f}")

            with col2:
                change = metrics.get('price_change', 0)
                st.metric("涨跌幅", f"{change:.2f}%", delta=f"{change:.2f}%")

            with col3:
                st.metric("最高价", f"¥{metrics.get('high_price', 0):.2f}")

            with col4:
                st.metric("最低价", f"¥{metrics.get('low_price', 0):.2f}")

            # 价格图表
            st.markdown("#### 📊 价格趋势")
            if ADVANCED_FEATURES:
                price_chart = create_price_chart(df, f"{symbol} 价格趋势")
            else:
                # 简单图表
                import plotly.express as px
                price_chart = px.line(df, x='trade_date', y='close', title=f"{symbol} 价格趋势")

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
    """显示批量查询结果"""

    st.markdown("---")
    st.subheader("📊 批量查询结果")

    if not st.session_state.watchlist:
        st.info("暂无自选股进行批量查询")
        return

    try:
        symbols = list(st.session_state.watchlist.keys())
        st.info(f"🚀 正在查询 {len(symbols)} 只股票的最新数据...")

        # 批量获取数据
        batch_results = []
        progress_bar = st.progress(0)

        for i, symbol in enumerate(symbols):
            try:
                # 获取资产信息
                asset_info, metadata = services['asset_service'].get_or_create_asset(symbol)

                # 获取最新价格数据（最近1天）
                end_date = datetime.now().date()
                start_date = end_date - timedelta(days=1)

                stock_data = services['stock_service'].get_stock_data(
                    symbol=symbol,
                    start_date=start_date.strftime('%Y%m%d'),
                    end_date=end_date.strftime('%Y%m%d')
                )

                # 处理数据
                latest_price = "N/A"
                price_change = "N/A"

                if stock_data is not None and not stock_data.empty:
                    latest_price = f"¥{stock_data['close'].iloc[-1]:.2f}"
                    if len(stock_data) > 1:
                        first_price = stock_data['close'].iloc[0]
                        last_price = stock_data['close'].iloc[-1]
                        change_pct = ((last_price - first_price) / first_price * 100)
                        price_change = f"{change_pct:.2f}%"

                batch_results.append({
                    "股票代码": symbol,
                    "股票名称": asset_info.name if asset_info else st.session_state.watchlist[symbol]['name'],
                    "行业": asset_info.industry if asset_info else "N/A",
                    "最新价格": latest_price,
                    "涨跌幅": price_change,
                    "数据来源": asset_info.data_source if asset_info else "N/A",
                    "状态": "✅" if stock_data is not None and not stock_data.empty else "❌"
                })

            except Exception as e:
                batch_results.append({
                    "股票代码": symbol,
                    "股票名称": st.session_state.watchlist[symbol]['name'],
                    "行业": "N/A",
                    "最新价格": "错误",
                    "涨跌幅": "N/A",
                    "数据来源": "N/A",
                    "状态": "❌"
                })

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
                success_count = len([r for r in batch_results if r['状态'] == '✅'])
                st.metric("成功查询", success_count)
            with col3:
                error_count = len([r for r in batch_results if r['状态'] == '❌'])
                st.metric("查询失败", error_count)
            with col4:
                st.metric("查询完成", "100%")

            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True
            )

    except Exception as e:
        st.error(f"批量查询失败: {str(e)}")

def export_watchlist():
    """导出自选股列表"""
    try:
        # 创建导出数据
        export_data = []
        for symbol, info in st.session_state.watchlist.items():
            export_data.append({
                "股票代码": symbol,
                "股票名称": info['name'],
                "添加日期": info['added_date']
            })

        if export_data:
            df = pd.DataFrame(export_data)
            csv = df.to_csv(index=False, encoding='utf-8-sig')

            st.download_button(
                label="📥 下载自选股列表 (CSV)",
                data=csv,
                file_name=f"自选股列表_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        else:
            st.info("暂无自选股可导出")

    except Exception as e:
        st.error(f"导出失败: {str(e)}")

if __name__ == "__main__":
    main()
