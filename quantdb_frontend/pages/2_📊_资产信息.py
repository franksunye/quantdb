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
    layout="wide",
)

def main():
    """主页面函数"""

    # 页面标题
    st.title("📊 资产信息")
    st.markdown("查看股票的详细资产信息，包括基本面数据、财务指标和市场表现。")
    st.markdown("---")

    # 主页面布局：左侧内容区 + 右侧查询面板
    col_main, col_query = st.columns([7, 3])  # 70% + 30% 布局

    # 右侧查询面板
    with col_query:
        with st.container():
            st.markdown("### 🔍 资产查询")

            # 查询方式选择
            query_mode = st.radio(
                "查询方式",
                ["手动输入", "浏览已有资产"],
                help="选择查询方式：手动输入股票代码或从已有资产中选择"
            )

            if query_mode == "手动输入":
                # 股票代码输入
                symbol = st.text_input(
                    "股票代码",
                    value="600000",
                    placeholder="如: 600000",
                    help="支持沪深A股代码"
                )

                # 查询按钮
                query_button = st.button("🔍 查询资产信息", type="primary", use_container_width=True)

                # 刷新按钮
                refresh_button = st.button("🔄 刷新数据", use_container_width=True)

            else:
                # 浏览已有资产
                symbol, query_button, refresh_button = display_asset_browser()

            # 显示最近查询
            display_recent_queries()

    # 检查是否有自动查询请求
    if st.session_state.get('auto_query_asset'):
        symbol = st.session_state.get('symbol', '600000')
        query_button = True
        st.session_state.auto_query_asset = False

    # 检查是否有保存的查询状态（用于保持页面状态）
    if not query_button and not refresh_button and st.session_state.get('current_asset_symbol'):
        symbol = st.session_state.get('current_asset_symbol')
        query_button = True  # 自动重新显示之前查询的资产信息

    # 左侧主内容区域
    with col_main:
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
                    asset_response = client.get_asset_info(symbol)

                    if asset_response:
                        # 新的API响应格式: {asset: {...}, metadata: {...}}
                        asset_data = asset_response.get('asset', asset_response)  # 兼容旧格式
                        asset_metadata = asset_response.get('metadata', {})

                        # 保存当前查询的资产信息到session state（用于保持页面状态）
                        st.session_state.current_asset_symbol = symbol
                        st.session_state.current_asset_data = asset_data
                        st.session_state.current_asset_metadata = asset_metadata

                        # 添加到最近查询列表
                        add_to_recent_queries(symbol, asset_data.get('name', f'Stock {symbol}'))

                        # 显示资产信息
                        display_asset_info(asset_data, symbol)

                        # 显示资产信息的缓存状态
                        display_asset_cache_info(asset_metadata)

                        # 可选的数据覆盖信息（使用expander避免页面重新加载）
                        st.markdown("---")

                        with st.expander("📈 查看数据覆盖情况", expanded=False):
                            st.info("💡 此功能显示系统内该股票的历史数据覆盖情况")

                            # 检查数据覆盖状态的按钮
                            if st.button("🔍 检查数据覆盖情况", help="检查系统内的数据覆盖情况", key=f"check_coverage_{symbol}"):
                                try:
                                    # 先检查系统内是否有数据（查询较长时间范围来了解真实覆盖）
                                    from datetime import timedelta
                                    end_date = date.today()
                                    # 查询更长时间范围来了解系统真实的数据覆盖情况
                                    start_date = end_date - timedelta(days=365)  # 查询一年范围了解覆盖情况

                                    from utils.api_client import format_date_for_api
                                    start_date_str = format_date_for_api(start_date)
                                    end_date_str = format_date_for_api(end_date)

                                    with st.spinner("正在检查系统数据覆盖情况..."):
                                        stock_data = client.get_stock_data(symbol, start_date_str, end_date_str)

                                        if stock_data and 'data' in stock_data and stock_data['data']:
                                            # 系统内有数据，显示真实覆盖情况
                                            coverage_data_key = f"coverage_data_{symbol}"
                                            st.session_state[coverage_data_key] = stock_data

                                            # 分析数据来源
                                            cache_info = stock_data.get('metadata', {}).get('cache_info', {})
                                            data_count = len(stock_data['data'])

                                            if cache_info.get('cache_hit', False):
                                                st.success(f"✅ 系统内已有 {data_count} 条历史数据记录（来自缓存）")
                                            else:
                                                st.info(f"📊 系统内有部分数据，已补齐缺失部分，共 {data_count} 条记录")

                                            st.rerun()
                                        else:
                                            # 系统内没有数据，提示将获取7天数据
                                            st.warning("⚠️ 系统内暂无该股票的历史数据")

                                            if st.button("📥 获取最近7天数据", help="获取并缓存最近7天的数据", key=f"fetch_7days_{symbol}"):
                                                # 获取7天数据
                                                start_date_7d = end_date - timedelta(days=7)
                                                start_date_7d_str = format_date_for_api(start_date_7d)

                                                with st.spinner("正在获取最近7天数据并缓存到系统..."):
                                                    stock_data_7d = client.get_stock_data(symbol, start_date_7d_str, end_date_str)

                                                    if stock_data_7d and 'data' in stock_data_7d and stock_data_7d['data']:
                                                        coverage_data_key = f"coverage_data_{symbol}"
                                                        st.session_state[coverage_data_key] = stock_data_7d

                                                        data_count = len(stock_data_7d['data'])
                                                        st.success(f"✅ 已获取并缓存 {data_count} 条数据（最近7天）")
                                                        st.rerun()
                                                    else:
                                                        st.error("❌ 无法获取该股票的历史数据")

                                except Exception as e:
                                    st.error(f"检查数据覆盖情况时出错: {str(e)}")

                            # 显示数据覆盖信息
                            coverage_data_key = f"coverage_data_{symbol}"
                            if coverage_data_key in st.session_state:
                                stock_data = st.session_state[coverage_data_key]

                                # 显示数据来源信息
                                cache_info = stock_data.get('metadata', {}).get('cache_info', {})
                                data_count = len(stock_data.get('data', []))

                                if cache_info.get('cache_hit', False):
                                    st.info(f"📊 数据来源：系统缓存（{data_count} 条记录）")
                                elif cache_info.get('akshare_called', False):
                                    st.info(f"📊 数据来源：部分来自缓存，部分新获取（{data_count} 条记录）")
                                else:
                                    st.info(f"📊 数据来源：新获取并已缓存（{data_count} 条记录）")

                                display_data_coverage(stock_data, symbol)

                                # 提供刷新按钮
                                if st.button("🔄 刷新覆盖信息", help="重新检查数据覆盖情况", key=f"refresh_coverage_{symbol}"):
                                    del st.session_state[coverage_data_key]
                                    st.rerun()

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
    
    # 第二行财务指标 - 修复字段映射
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        # 修复字段名：total_share -> total_shares
        total_shares = asset_data.get('total_shares')
        if total_shares:
            if total_shares >= 1e8:
                share_display = f"{total_shares/1e8:.2f}亿股"
            elif total_shares >= 1e4:
                share_display = f"{total_shares/1e4:.2f}万股"
            else:
                share_display = f"{total_shares:.2f}股"
        else:
            share_display = "N/A"

        st.metric(
            label="总股本",
            value=share_display
        )

    with col2:
        # 修复字段名：float_share -> circulating_shares
        circulating_shares = asset_data.get('circulating_shares')
        if circulating_shares:
            if circulating_shares >= 1e8:
                float_display = f"{circulating_shares/1e8:.2f}亿股"
            elif circulating_shares >= 1e4:
                float_display = f"{circulating_shares/1e4:.2f}万股"
            else:
                float_display = f"{circulating_shares:.2f}股"
        else:
            float_display = "N/A"

        st.metric(
            label="流通股本",
            value=float_display
        )

    with col3:
        # EPS字段后端暂未提供，显示说明
        st.metric(
            label="每股收益 (EPS)",
            value="待完善",
            help="每股收益数据正在完善中"
        )

    with col4:
        # BPS字段后端暂未提供，显示说明
        st.metric(
            label="每股净资产 (BPS)",
            value="待完善",
            help="每股净资产数据正在完善中"
        )

def display_asset_browser():
    """显示资产浏览器"""

    st.markdown("**📋 浏览已有资产**")

    try:
        client = get_api_client()

        # 获取资产列表
        with st.spinner("加载资产列表..."):
            assets = client.get_assets_list(limit=50)  # 限制50个以提高性能

        if not assets:
            st.warning("暂无已有资产数据")
            return "", False, False

        # 按行业分组
        industry_groups = {}
        for asset in assets:
            industry = asset.get('industry', '其他')
            if industry not in industry_groups:
                industry_groups[industry] = []
            industry_groups[industry].append(asset)

        # 行业筛选
        selected_industry = st.selectbox(
            "按行业筛选",
            ["全部"] + list(industry_groups.keys()),
            help="选择特定行业查看相关股票"
        )

        # 筛选资产
        if selected_industry == "全部":
            filtered_assets = assets
        else:
            filtered_assets = industry_groups[selected_industry]

        # 资产选择
        asset_options = {}
        for asset in filtered_assets:
            display_name = f"{asset['symbol']} - {asset['name']}"
            if asset.get('industry'):
                display_name += f" ({asset['industry']})"
            asset_options[display_name] = asset['symbol']

        if asset_options:
            selected_display = st.selectbox(
                "选择股票",
                list(asset_options.keys()),
                help="从列表中选择要查看的股票"
            )

            selected_symbol = asset_options[selected_display]

            # 操作按钮
            col1, col2 = st.columns(2)
            with col1:
                query_button = st.button("🔍 查看详情", type="primary", use_container_width=True)
            with col2:
                refresh_button = st.button("🔄 刷新数据", use_container_width=True)

            return selected_symbol, query_button, refresh_button
        else:
            st.info("该行业暂无资产数据")
            return "", False, False

    except Exception as e:
        st.error(f"加载资产列表失败: {str(e)}")
        return "", False, False

def display_recent_queries():
    """显示最近查询的股票"""

    st.markdown("---")
    st.markdown("**🕒 最近查询**")

    # 从session state获取最近查询
    recent_queries = st.session_state.get('recent_asset_queries', [])

    if recent_queries:
        # 显示最近3个查询
        for i, query in enumerate(recent_queries[:3]):
            symbol = query['symbol']
            name = query.get('name', f'Stock {symbol}')
            query_time = query.get('time', '')

            if st.button(
                f"{symbol} - {name}",
                key=f"recent_{i}_{symbol}",
                help=f"查询时间: {query_time}",
                use_container_width=True
            ):
                st.session_state.update({
                    'symbol': symbol,
                    'auto_query_asset': True
                })
                st.rerun()
    else:
        st.caption("暂无最近查询记录")

def add_to_recent_queries(symbol: str, name: str):
    """添加到最近查询列表"""

    if 'recent_asset_queries' not in st.session_state:
        st.session_state.recent_asset_queries = []

    # 创建查询记录
    query_record = {
        'symbol': symbol,
        'name': name,
        'time': datetime.now().strftime('%Y-%m-%d %H:%M')
    }

    # 移除重复项
    recent_queries = st.session_state.recent_asset_queries
    recent_queries = [q for q in recent_queries if q['symbol'] != symbol]

    # 添加到开头
    recent_queries.insert(0, query_record)

    # 保持最多10个记录
    st.session_state.recent_asset_queries = recent_queries[:10]

def display_asset_cache_info(metadata: dict):
    """显示资产信息的缓存状态"""

    st.markdown("---")
    st.subheader("⚡ 资产信息缓存状态")

    cache_info = metadata.get('cache_info', {})

    col1, col2, col3 = st.columns(3)

    with col1:
        cache_hit = cache_info.get('cache_hit', False)
        st.metric(
            label="缓存命中",
            value="是" if cache_hit else "否",
            help="资产信息是否来自缓存"
        )

    with col2:
        akshare_called = cache_info.get('akshare_called', False)
        st.metric(
            label="AKShare调用",
            value="是" if akshare_called else "否",
            help="是否调用了AKShare获取最新数据"
        )

    with col3:
        response_time = cache_info.get('response_time_ms', 0)
        st.metric(
            label="响应时间",
            value=f"{response_time:.1f}ms",
            help="API响应时间"
        )

    # 显示详细信息
    if cache_info:
        with st.expander("📊 详细缓存信息"):
            st.json(cache_info)

def display_data_coverage(stock_data: dict, symbol: str):
    """显示数据覆盖信息"""

    st.markdown("---")
    st.subheader("📈 数据覆盖情况")

    data = stock_data.get('data', [])
    
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

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**数据完整性**")
        # 数据完整性检查
        missing_data = df.isnull().sum().sum()
        completeness = (1 - missing_data / (len(df) * len(df.columns))) * 100
        st.metric(
            label="数据完整性",
            value=f"{completeness:.1f}%",
            help="数据的完整性百分比，越高表示缺失数据越少"
        )

        # 数据质量评级
        if completeness >= 95:
            quality_grade = "优秀"
            quality_color = "🟢"
        elif completeness >= 85:
            quality_grade = "良好"
            quality_color = "🟡"
        else:
            quality_grade = "需改善"
            quality_color = "🔴"

        st.write(f"{quality_color} 质量评级: **{quality_grade}**")

    with col2:
        st.markdown("**价格统计**")
        if 'close' in df.columns:
            st.metric(
                label="最高收盘价",
                value=f"¥{df['close'].max():.2f}",
                help="查询期间的最高收盘价"
            )
            st.metric(
                label="最低收盘价",
                value=f"¥{df['close'].min():.2f}",
                help="查询期间的最低收盘价"
            )

    with col3:
        st.markdown("**价格分析**")
        if 'close' in df.columns:
            st.metric(
                label="平均收盘价",
                value=f"¥{df['close'].mean():.2f}",
                help="查询期间的平均收盘价"
            )
            st.metric(
                label="价格波动率",
                value=f"{df['close'].std():.2f}",
                help="价格标准差，反映价格波动程度"
            )

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
