"""
股票数据查询页面
提供股票历史数据查询和图表展示功能
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys
import os
from pathlib import Path
import time
import plotly.express as px
import plotly.graph_objects as go

# 添加src目录到Python路径
current_dir = Path(__file__).parent.parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

# 页面配置
st.set_page_config(
    page_title="股票数据查询 - QuantDB",
    page_icon="📈",
    layout="wide"
)

# 初始化服务
@st.cache_resource
def init_services():
    """初始化服务实例"""
    try:
        from services.stock_data_service import StockDataService
        from cache.akshare_adapter import AKShareAdapter
        from api.database import get_db

        db_session = next(get_db())
        akshare_adapter = AKShareAdapter()
        return StockDataService(db_session, akshare_adapter)
    except Exception as e:
        st.error(f"服务初始化失败: {e}")
        return None

def validate_stock_code(code: str) -> bool:
    """验证股票代码格式"""
    if not code:
        return False
    
    code = code.strip()
    
    # 检查是否为6位数字
    if len(code) != 6 or not code.isdigit():
        return False
    
    # 检查是否为有效的A股代码
    if code.startswith(('000', '001', '002', '003', '300')):  # 深交所
        return True
    elif code.startswith('6'):  # 上交所
        return True
    elif code.startswith('688'):  # 科创板
        return True
    
    return False

def create_price_chart(df: pd.DataFrame, symbol: str, name: str = None):
    """创建价格趋势图"""
    fig = px.line(
        df, 
        x='trade_date', 
        y='close', 
        title=f'{name or symbol} - 收盘价趋势',
        labels={'close': '收盘价 (元)', 'trade_date': '日期'}
    )
    
    fig.update_layout(
        hovermode='x unified',
        showlegend=False,
        height=400
    )
    
    fig.update_traces(
        line=dict(width=2, color='#1f77b4'),
        hovertemplate='日期: %{x}<br>收盘价: ¥%{y:.2f}<extra></extra>'
    )
    
    return fig

def create_volume_chart(df: pd.DataFrame, symbol: str, name: str = None):
    """创建成交量图表"""
    fig = px.bar(
        df, 
        x='trade_date', 
        y='volume', 
        title=f'{name or symbol} - 成交量',
        labels={'volume': '成交量', 'trade_date': '日期'}
    )
    
    fig.update_layout(
        showlegend=False,
        height=300
    )
    
    fig.update_traces(
        marker_color='lightblue',
        hovertemplate='日期: %{x}<br>成交量: %{y:,.0f}<extra></extra>'
    )
    
    return fig

def main():
    """主页面"""
    
    st.title("📈 股票数据查询")
    st.markdown("查询股票历史数据，支持多种图表展示和数据分析")
    st.markdown("---")
    
    # 初始化服务
    stock_service = init_services()
    if not stock_service:
        st.error("❌ 服务初始化失败，请刷新页面重试")
        return
    
    # 输入区域
    col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
    
    with col1:
        symbol = st.text_input(
            "股票代码",
            placeholder="例如: 600000",
            help="请输入6位A股代码"
        )
    
    with col2:
        # 默认查询最近30天
        default_start = datetime.now() - timedelta(days=30)
        start_date = st.date_input(
            "开始日期",
            value=default_start,
            max_value=datetime.now().date()
        )
    
    with col3:
        end_date = st.date_input(
            "结束日期",
            value=datetime.now().date(),
            max_value=datetime.now().date()
        )
    
    with col4:
        st.markdown("<br>", unsafe_allow_html=True)  # 空行对齐
        query_button = st.button("🔍 查询数据", type="primary")
    
    # 验证输入
    if query_button:
        if not validate_stock_code(symbol):
            st.error("❌ 请输入有效的6位股票代码（如：600000、000001、300001）")
            return
        
        if start_date >= end_date:
            st.error("❌ 开始日期必须早于结束日期")
            return
        
        # 查询数据
        with st.spinner("正在获取股票数据..."):
            start_time = time.time()
            
            try:
                # 调用现有服务
                result = stock_service.get_stock_data(
                    symbol=symbol,
                    start_date=start_date.strftime('%Y%m%d'),
                    end_date=end_date.strftime('%Y%m%d')
                )
                
                response_time = time.time() - start_time
                
                if result is None or (isinstance(result, pd.DataFrame) and result.empty):
                    st.error("❌ 获取数据失败，请检查股票代码或稍后重试")
                    return
                
                # 获取资产信息
                try:
                    from services.asset_info_service import AssetInfoService
                    from api.database import get_db

                    db_session = next(get_db())
                    asset_service = AssetInfoService(db_session)
                    asset_info, metadata = asset_service.get_or_create_asset(symbol)
                    company_name = asset_info.name if asset_info else f"股票{symbol}"
                except:
                    company_name = f"股票{symbol}"
                
                # 显示结果
                st.success(f"✅ 成功获取 {company_name} ({symbol}) 的数据 - 响应时间: {response_time:.2f}秒")
                
                # 数据概览
                df = result.copy()
                # 确保日期列存在并转换为datetime
                if 'date' in df.columns:
                    df['trade_date'] = pd.to_datetime(df['date'])
                elif 'trade_date' in df.columns:
                    df['trade_date'] = pd.to_datetime(df['trade_date'])
                else:
                    st.error("❌ 数据格式错误：缺少日期列")
                    return
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("数据记录数", len(df))
                
                with col2:
                    if len(df) > 1:
                        latest_price = df.iloc[-1]['close']
                        first_price = df.iloc[0]['close']
                        total_return = (latest_price - first_price) / first_price * 100
                        st.metric("期间涨跌幅", f"{total_return:.2f}%")
                    else:
                        st.metric("期间涨跌幅", "N/A")
                
                with col3:
                    st.metric("最高价", f"¥{df['high'].max():.2f}")
                
                with col4:
                    st.metric("最低价", f"¥{df['low'].min():.2f}")
                
                st.markdown("---")
                
                # 图表展示
                if len(df) > 0:
                    tab1, tab2, tab3 = st.tabs(["📈 价格趋势", "📊 成交量", "📋 数据表格"])
                    
                    with tab1:
                        fig_price = create_price_chart(df, symbol, company_name)
                        st.plotly_chart(fig_price, use_container_width=True)
                    
                    with tab2:
                        fig_volume = create_volume_chart(df, symbol, company_name)
                        st.plotly_chart(fig_volume, use_container_width=True)
                    
                    with tab3:
                        # 数据表格
                        display_df = df.copy()
                        display_df['trade_date'] = display_df['trade_date'].dt.strftime('%Y-%m-%d')
                        display_df = display_df.round(2)
                        
                        st.dataframe(
                            display_df,
                            use_container_width=True,
                            hide_index=True
                        )
                        
                        # 数据导出
                        csv = display_df.to_csv(index=False, encoding='utf-8-sig')
                        st.download_button(
                            label="📥 下载CSV数据",
                            data=csv,
                            file_name=f"{symbol}_{company_name}_股票数据.csv",
                            mime="text/csv"
                        )
                
                # 显示元数据
                with st.expander("📊 数据信息"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("**数据来源**:", "AKShare")
                        st.write("**获取时间**:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                        st.write("**响应时间**:", f"{response_time:.3f}秒")
                    
                    with col2:
                        st.write("**股票名称**:", company_name)
                        st.write("**股票代码**:", symbol)
                        st.write("**数据记录**:", f"{len(df)}条")
                
            except Exception as e:
                error_msg = str(e)
                st.error(f"❌ 查询过程中出现错误: {error_msg}")

                # 提供更具体的错误提示
                if "Invalid symbol format" in error_msg:
                    st.info("💡 请输入正确的股票代码格式：\n- A股：6位数字（如：600000）\n- 港股：5位数字（如：00700）")
                elif "trade_date" in error_msg:
                    st.info("💡 数据格式问题，请联系技术支持")
                elif "connection" in error_msg.lower() or "timeout" in error_msg.lower():
                    st.info("💡 网络连接问题，请检查网络或稍后重试")
                else:
                    st.info("💡 请检查股票代码是否正确，或稍后重试")

                # 调试信息（仅在开发环境显示）
                with st.expander("🔍 详细错误信息（调试用）"):
                    st.code(error_msg)
                    import traceback
                    st.code(traceback.format_exc())

if __name__ == "__main__":
    main()
