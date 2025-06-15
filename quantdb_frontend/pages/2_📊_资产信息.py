"""
资产信息页面

展示股票的基本信息、财务指标和数据覆盖情况。
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date
import sys
import os

# 添加项目路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from utils.api_client import get_api_client, QuantDBAPIError
from utils.config import config

# 页面配置
st.set_page_config(
    page_title="资产信息 - QuantDB",
    page_icon="📊",
    layout="wide"
)

def main():
    """主页面函数"""
    
    # 页面标题
    st.title("📊 资产信息")
    st.markdown("---")
    
    # 侧边栏 - 查询参数
    with st.sidebar:
        st.header("🔍 查询参数")
        
        # 股票代码输入
        symbol = st.text_input(
            "股票代码",
            value="600000",
            placeholder="请输入6位股票代码，如: 600000",
            help="支持沪深A股代码，如600000(浦发银行)、000001(平安银行)"
        )
        
        # 查询按钮
        query_button = st.button("🔍 查询资产信息", type="primary", use_container_width=True)
        
        # 刷新按钮
        refresh_button = st.button("🔄 刷新数据", use_container_width=True)
    
    # 主内容区域
    if query_button or refresh_button or st.session_state.get('auto_query_asset', False):
        
        # 验证输入
        if not symbol:
            st.error("请输入股票代码")
            return
        
        # 验证股票代码格式
        if not config.validate_symbol(symbol):
            st.error(config.ERROR_MESSAGES["invalid_symbol"])
            return
        
        # 标准化股票代码
        symbol = config.normalize_symbol(symbol)
        
        # 显示查询信息
        st.info(f"正在查询股票 {symbol} 的资产信息...")
        
        # 查询数据
        with st.spinner("资产信息查询中..."):
            try:
                client = get_api_client()
                
                # 调用API获取资产信息
                asset_data = client.get_asset_info(symbol)
                
                if asset_data:
                    # 显示资产信息
                    display_asset_info(asset_data, symbol)
                    
                    # 获取数据覆盖信息
                    try:
                        # 查询最近30天的数据来展示覆盖情况
                        from datetime import timedelta
                        end_date = date.today()
                        start_date = end_date - timedelta(days=365)  # 查询一年的数据覆盖
                        
                        from utils.api_client import format_date_for_api
                        start_date_str = format_date_for_api(start_date)
                        end_date_str = format_date_for_api(end_date)
                        
                        stock_data = client.get_stock_data(symbol, start_date_str, end_date_str)
                        if stock_data and 'data' in stock_data:
                            display_data_coverage(stock_data, symbol)
                    except Exception as e:
                        st.warning(f"无法获取数据覆盖信息: {str(e)}")
                    
                else:
                    st.error("未找到资产信息")
                    
            except QuantDBAPIError as e:
                st.error(f"查询失败: {str(e)}")
            except Exception as e:
                st.error(f"未知错误: {str(e)}")
                st.exception(e)
    
    else:
        # 显示使用说明
        show_usage_guide()

def display_asset_info(asset_data: dict, symbol: str):
    """显示资产信息"""
    
    st.success(f"✅ 成功获取股票 {symbol} 的资产信息")
    
    # 基本信息卡片
    st.subheader("🏢 基本信息")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 📋 公司信息")
        st.write(f"**股票代码**: {asset_data.get('symbol', 'N/A')}")
        st.write(f"**公司名称**: {asset_data.get('name', 'N/A')}")
        st.write(f"**资产类型**: {asset_data.get('asset_type', 'N/A')}")
        st.write(f"**交易所**: {asset_data.get('exchange', 'N/A')}")
    
    with col2:
        st.markdown("### 🏭 分类信息")
        st.write(f"**行业**: {asset_data.get('industry', 'N/A')}")
        st.write(f"**概念**: {asset_data.get('concept', 'N/A')}")
        st.write(f"**地区**: {asset_data.get('area', 'N/A')}")
        st.write(f"**市场**: {asset_data.get('market', 'N/A')}")
    
    with col3:
        st.markdown("### 📅 时间信息")
        st.write(f"**上市日期**: {asset_data.get('list_date', 'N/A')}")
        st.write(f"**创建时间**: {format_datetime(asset_data.get('created_at'))}")
        st.write(f"**更新时间**: {format_datetime(asset_data.get('updated_at'))}")
        st.write(f"**最后访问**: {format_datetime(asset_data.get('last_accessed'))}")
    
    st.markdown("---")
    
    # 财务指标
    st.subheader("💰 财务指标")
    
    # 使用st.metric展示关键财务指标
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        pe_ratio = asset_data.get('pe_ratio')
        st.metric(
            label="市盈率 (PE)",
            value=f"{pe_ratio:.2f}" if pe_ratio else "N/A",
            help="市盈率 = 股价 / 每股收益"
        )
    
    with col2:
        pb_ratio = asset_data.get('pb_ratio')
        st.metric(
            label="市净率 (PB)",
            value=f"{pb_ratio:.2f}" if pb_ratio else "N/A",
            help="市净率 = 股价 / 每股净资产"
        )
    
    with col3:
        roe = asset_data.get('roe')
        st.metric(
            label="净资产收益率 (ROE)",
            value=f"{roe:.2f}%" if roe else "N/A",
            help="净资产收益率 = 净利润 / 净资产"
        )
    
    with col4:
        market_cap = asset_data.get('market_cap')
        if market_cap:
            if market_cap >= 1e8:
                cap_display = f"{market_cap/1e8:.2f}亿"
            elif market_cap >= 1e4:
                cap_display = f"{market_cap/1e4:.2f}万"
            else:
                cap_display = f"{market_cap:.2f}"
        else:
            cap_display = "N/A"
        
        st.metric(
            label="总市值",
            value=cap_display,
            help="总市值 = 股价 × 总股本"
        )
    
    # 第二行财务指标
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_share = asset_data.get('total_share')
        if total_share:
            if total_share >= 1e8:
                share_display = f"{total_share/1e8:.2f}亿股"
            elif total_share >= 1e4:
                share_display = f"{total_share/1e4:.2f}万股"
            else:
                share_display = f"{total_share:.2f}股"
        else:
            share_display = "N/A"
        
        st.metric(
            label="总股本",
            value=share_display
        )
    
    with col2:
        float_share = asset_data.get('float_share')
        if float_share:
            if float_share >= 1e8:
                float_display = f"{float_share/1e8:.2f}亿股"
            elif float_share >= 1e4:
                float_display = f"{float_share/1e4:.2f}万股"
            else:
                float_display = f"{float_share:.2f}股"
        else:
            float_display = "N/A"
        
        st.metric(
            label="流通股本",
            value=float_display
        )
    
    with col3:
        eps = asset_data.get('eps')
        st.metric(
            label="每股收益 (EPS)",
            value=f"¥{eps:.2f}" if eps else "N/A",
            help="每股收益 = 净利润 / 总股本"
        )
    
    with col4:
        bps = asset_data.get('bps')
        st.metric(
            label="每股净资产 (BPS)",
            value=f"¥{bps:.2f}" if bps else "N/A",
            help="每股净资产 = 净资产 / 总股本"
        )

def display_data_coverage(stock_data: dict, symbol: str):
    """显示数据覆盖信息"""
    
    st.markdown("---")
    st.subheader("📈 数据覆盖情况")
    
    data = stock_data.get('data', [])
    metadata = stock_data.get('metadata', {})
    
    if not data:
        st.warning("暂无历史数据")
        return
    
    # 转换为DataFrame进行分析
    df = pd.DataFrame(data)
    df['date'] = pd.to_datetime(df['date'])
    
    # 数据覆盖统计
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="数据记录数",
            value=f"{len(df):,}",
            help="历史数据的总记录数"
        )
    
    with col2:
        start_date = df['date'].min().strftime('%Y-%m-%d')
        st.metric(
            label="数据起始日期",
            value=start_date,
            help="最早的数据日期"
        )
    
    with col3:
        end_date = df['date'].max().strftime('%Y-%m-%d')
        st.metric(
            label="数据结束日期",
            value=end_date,
            help="最新的数据日期"
        )
    
    with col4:
        data_span = (df['date'].max() - df['date'].min()).days
        st.metric(
            label="数据跨度",
            value=f"{data_span}天",
            help="数据覆盖的时间跨度"
        )
    
    # 数据质量信息
    st.markdown("### 📊 数据质量")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**缓存信息**")
        st.write(f"- 缓存命中: {'是' if metadata.get('cache_hit') else '否'}")
        st.write(f"- AKShare调用: {'是' if metadata.get('akshare_called') else '否'}")
        st.write(f"- 响应时间: {metadata.get('response_time_ms', 0):.1f}ms")
        
        # 数据完整性检查
        missing_data = df.isnull().sum().sum()
        completeness = (1 - missing_data / (len(df) * len(df.columns))) * 100
        st.write(f"- 数据完整性: {completeness:.1f}%")
    
    with col2:
        st.markdown("**价格范围**")
        if 'close' in df.columns:
            st.write(f"- 最高收盘价: ¥{df['close'].max():.2f}")
            st.write(f"- 最低收盘价: ¥{df['close'].min():.2f}")
            st.write(f"- 平均收盘价: ¥{df['close'].mean():.2f}")
            st.write(f"- 价格波动率: {df['close'].std():.2f}")

def format_datetime(dt_str):
    """格式化日期时间字符串"""
    if not dt_str:
        return "N/A"
    
    try:
        # 尝试解析ISO格式
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M')
    except:
        return str(dt_str)

def show_usage_guide():
    """显示使用指南"""
    
    st.markdown("### 📖 使用指南")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        #### 🔍 如何查询资产信息
        
        1. **输入股票代码**: 在左侧输入6位股票代码
        2. **点击查询**: 点击"查询资产信息"按钮
        3. **查看详情**: 浏览基本信息、财务指标和数据覆盖
        4. **刷新数据**: 使用"刷新数据"获取最新信息
        
        #### 📊 信息内容
        
        - **基本信息**: 公司名称、行业、交易所等
        - **财务指标**: PE、PB、ROE、市值等关键指标
        - **数据覆盖**: 历史数据的完整性和质量信息
        """)
    
    with col2:
        st.markdown("""
        #### 💡 使用技巧
        
        - **真实名称**: 显示真实公司名称，如"浦发银行"
        - **财务指标**: 来自AKShare的实时财务数据
        - **数据质量**: 展示缓存命中率和响应时间
        - **自动刷新**: 系统会智能更新过期数据
        
        #### 🎯 推荐查询
        
        - **600000**: 浦发银行 (银行业龙头)
        - **000001**: 平安银行 (股份制银行)
        - **600519**: 贵州茅台 (消费行业)
        - **000002**: 万科A (房地产行业)
        """)
    
    # 快速查询按钮
    st.markdown("### 🚀 快速查询")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("浦发银行(600000)", use_container_width=True):
            st.session_state.update({
                'symbol': '600000',
                'auto_query_asset': True
            })
            st.rerun()
    
    with col2:
        if st.button("平安银行(000001)", use_container_width=True):
            st.session_state.update({
                'symbol': '000001',
                'auto_query_asset': True
            })
            st.rerun()
    
    with col3:
        if st.button("贵州茅台(600519)", use_container_width=True):
            st.session_state.update({
                'symbol': '600519',
                'auto_query_asset': True
            })
            st.rerun()
    
    with col4:
        if st.button("万科A(000002)", use_container_width=True):
            st.session_state.update({
                'symbol': '000002',
                'auto_query_asset': True
            })
            st.rerun()

if __name__ == "__main__":
    main()
