"""
自选股管理页面

用户可以添加、删除、管理自选股票，并进行批量查询和分析。
"""

import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, date, timedelta
import sys

# 添加项目路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from utils.api_client import get_api_client, QuantDBAPIError, format_date_for_api
from utils.charts import create_price_chart, calculate_basic_metrics
from utils.config import config

# 页面配置
st.set_page_config(
    page_title="自选股管理 - QuantDB",
    page_icon="🎯",
    layout="wide"
)

# 自选股数据文件路径
WATCHLIST_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "watchlist.json")

def load_watchlist():
    """加载自选股列表"""
    try:
        # 确保数据目录存在
        os.makedirs(os.path.dirname(WATCHLIST_FILE), exist_ok=True)
        
        if os.path.exists(WATCHLIST_FILE):
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
        os.makedirs(os.path.dirname(WATCHLIST_FILE), exist_ok=True)
        with open(WATCHLIST_FILE, 'w', encoding='utf-8') as f:
            json.dump(watchlist, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.error(f"保存自选股失败: {str(e)}")

def main():
    """主页面函数"""
    
    # 页面标题
    st.title("🎯 自选股管理")
    st.markdown("---")
    
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
            add_to_watchlist(new_symbol)
        
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
        display_batch_query_results()
        st.session_state.batch_query = False

def add_to_watchlist(symbol):
    """添加股票到自选股"""
    if not symbol:
        st.error("请输入股票代码")
        return
    
    # 验证股票代码
    if not config.validate_symbol(symbol):
        st.error(config.ERROR_MESSAGES["invalid_symbol"])
        return
    
    # 标准化股票代码
    symbol = config.normalize_symbol(symbol)
    
    # 检查是否已存在
    if symbol in st.session_state.watchlist:
        st.warning(f"股票 {symbol} 已在自选股中")
        return
    
    # 获取股票信息
    try:
        client = get_api_client()
        asset_info = client.get_asset_info(symbol)
        
        if asset_info:
            stock_name = asset_info.get('name', f'股票 {symbol}')
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
        st.metric("最新添加", max(st.session_state.watchlist.values(), key=lambda x: x['added_date'])['added_date'])
    
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
        client = get_api_client()
        
        # 获取最近7天数据，提升性能
        end_date = date.today()
        start_date = end_date - timedelta(days=7)
        
        start_date_str = format_date_for_api(start_date)
        end_date_str = format_date_for_api(end_date)
        
        with st.spinner("获取股票数据..."):
            stock_data = client.get_stock_data(symbol, start_date_str, end_date_str)
            asset_info = client.get_asset_info(symbol)
        
        if stock_data and 'data' in stock_data:
            df = pd.DataFrame(stock_data['data'])
            
            # 基础指标
            metrics = calculate_basic_metrics(df)
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("最新价格", f"¥{metrics.get('latest_price', 0):.2f}")
            
            with col2:
                st.metric("涨跌幅", f"{metrics.get('price_change', 0):.2f}%")
            
            with col3:
                st.metric("最高价", f"¥{metrics.get('high_price', 0):.2f}")
            
            with col4:
                st.metric("最低价", f"¥{metrics.get('low_price', 0):.2f}")
            
            # 价格图表
            st.markdown("#### 📊 价格趋势")
            price_chart = create_price_chart(df, f"{symbol} 价格趋势")
            st.plotly_chart(price_chart, use_container_width=True)
            
            # 财务信息
            if asset_info:
                st.markdown("#### 💰 财务信息")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    pe_ratio = asset_info.get('pe_ratio')
                    st.metric("市盈率 (PE)", f"{pe_ratio:.2f}" if pe_ratio else "N/A")
                
                with col2:
                    pb_ratio = asset_info.get('pb_ratio')
                    st.metric("市净率 (PB)", f"{pb_ratio:.2f}" if pb_ratio else "N/A")
                
                with col3:
                    roe = asset_info.get('roe')
                    st.metric("净资产收益率", f"{roe:.2f}%" if roe else "N/A")
        
        # 关闭详情按钮
        if st.button("关闭详情"):
            st.session_state.show_stock_detail = False
            st.rerun()
    
    except Exception as e:
        st.error(f"获取股票详情失败: {str(e)}")

def display_batch_query_results():
    """显示批量查询结果（性能优化版本）"""

    st.markdown("---")
    st.subheader("📊 批量查询结果")

    if not st.session_state.watchlist:
        st.info("暂无自选股进行批量查询")
        return

    try:
        # 使用批量客户端进行高性能查询
        from utils.batch_client import get_batch_client, create_st_batch_progress

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

            batch_results.append({
                "股票代码": symbol,
                "股票名称": summary_info.get("name", watchlist_info.get("name", f"Stock {symbol}")),
                "行业": summary_info.get("industry", "其他"),
                "最新价格": summary_info.get("latest_price", "N/A"),
                "涨跌幅(%)": summary_info.get("price_change_pct", "N/A"),
                "数据来源": summary_info.get("data_source", "unknown"),
                "有价格数据": "✅" if summary_info.get("has_price_data") else "❌"
            })

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
            styled_df['涨跌幅(%)'] = styled_df['涨跌幅(%)'].apply(format_price_change)
            
            st.dataframe(
                styled_df,
                use_container_width=True,
                hide_index=True
            )
            
            # 统计信息
            valid_changes = [x for x in df['涨跌幅(%)'] if isinstance(x, (int, float))]
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
