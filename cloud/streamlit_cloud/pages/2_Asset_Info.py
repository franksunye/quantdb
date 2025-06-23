#!/usr/bin/env python3
"""
QuantDB Cloud - 资产信息页面

提供股票资产信息查询功能，支持手动输入和浏览已有资产。
"""

import streamlit as st
import time
import sys
import os
from datetime import datetime
from typing import Dict, List, Any

# 添加项目根目录到路径以访问core模块
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(parent_dir)  # 回到QuantDB根目录
if project_root not in sys.path:
    sys.path.append(project_root)

# 导入现有的后端服务（直接调用，不通过HTTP API）
try:
    from core.services import AssetInfoService, QueryService
    from core.database import get_db
    BACKEND_SERVICES_AVAILABLE = True
except ImportError as e:
    BACKEND_SERVICES_AVAILABLE = False

# 设置页面配置
st.set_page_config(
    page_title="资产信息 - QuantDB",
    page_icon="📊",
    layout="wide"
)

@st.cache_resource
def init_services():
    """初始化后端服务"""
    try:
        # 获取数据库会话
        db_session = next(get_db())

        # 初始化服务
        asset_service = AssetInfoService(db_session)
        query_service = QueryService(db_session)

        return asset_service, query_service
    except Exception as e:
        st.error(f"服务初始化失败: {e}")
        return None, None

def main():
    """主页面函数"""

    # 页面标题
    st.title("📊 资产信息")
    st.markdown("查看股票的详细资产信息，包括基本面数据、财务指标和市场表现。")
    st.markdown("---")

    # 检查后端服务是否可用
    if not BACKEND_SERVICES_AVAILABLE:
        st.warning("⚠️ 后端服务不可用，使用API模式")
        use_backend_services = False
        asset_service, query_service = None, None
    else:
        # 初始化后端服务
        services = init_services()
        if services and all(services):
            asset_service, query_service = services
            use_backend_services = True
        else:
            st.warning("⚠️ 后端服务初始化失败，使用API模式")
            use_backend_services = False
            asset_service, query_service = None, None

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
                    placeholder="如: 600000 或 00700",
                    help="支持A股(6位)和港股(5位)代码"
                )

                # 查询按钮
                query_button = st.button("🔍 查询资产信息", type="primary", use_container_width=True)

                # 刷新按钮 - 添加详细说明
                refresh_button = st.button(
                    "🔄 强制刷新资产数据",
                    use_container_width=True,
                    help="强制从AKShare获取最新资产信息，包括公司名称、财务指标等"
                )

                # 添加刷新说明
                with st.expander("ℹ️ 刷新数据说明", expanded=False):
                    st.markdown("""
                    **🔄 强制刷新功能：**

                    - **作用**: 强制从AKShare重新获取最新的资产信息
                    - **更新内容**: 公司名称、行业分类、财务指标(PE/PB/ROE)、市值数据等
                    - **使用场景**:
                      - 发现公司名称显示不正确时（如"HK Stock 02171"）
                      - 需要最新财务指标时
                      - 数据显示异常时
                    - **注意**: 刷新会调用外部API，可能需要几秒钟时间

                    **与普通查询的区别：**
                    - 🔍 **普通查询**：优先使用缓存数据（1天内有效）
                    - 🔄 **强制刷新**：忽略缓存，直接调用AKShare获取最新数据
                    """)

            else:
                # 浏览已有资产
                symbol, query_button, refresh_button = display_asset_browser(query_service)

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

            # 验证股票代码格式 - 简化的验证逻辑
            if not symbol or len(symbol) < 5 or len(symbol) > 6 or not symbol.isdigit():
                st.error("请输入有效的股票代码（5-6位数字）")
                return

            # 标准化股票代码（确保6位，前面补0）
            if len(symbol) == 5:
                symbol = symbol  # 港股保持5位
            elif len(symbol) == 6:
                symbol = symbol  # A股保持6位
            else:
                st.error("股票代码长度不正确")
                return

            # 显示查询信息
            st.info(f"正在查询股票 {symbol} 的资产信息...")

            # 查询数据
            with st.spinner("资产信息查询中..." if query_button else "强制刷新资产数据中..."):
                try:
                    if use_backend_services and asset_service:
                        # 根据按钮类型选择不同的处理方式
                        if refresh_button:
                            # 刷新按钮：强制更新资产信息
                            st.info("🔄 正在强制从AKShare获取最新资产信息...")
                            asset_obj = asset_service.update_asset_info(symbol)
                            metadata = {
                                'cache_info': {
                                    'cache_hit': False,
                                    'akshare_called': True,
                                    'force_refresh': True,
                                    'response_time_ms': 0  # 实际时间由服务层记录
                                }
                            }

                            if not asset_obj:
                                st.error(f"❌ 无法更新资产 {symbol}，可能是无效的股票代码或AKShare服务异常")
                                return

                        else:
                            # 查询按钮：正常查询（优先使用缓存）
                            asset_result = asset_service.get_or_create_asset(symbol)

                            if isinstance(asset_result, tuple):
                                asset_obj, metadata = asset_result
                            else:
                                asset_obj = asset_result
                                metadata = {}

                        # 调试信息：显示Asset对象的实际属性
                        st.info(f"🔍 Asset对象属性: {[attr for attr in dir(asset_obj) if not attr.startswith('_')]}")

                        # 转换为字典格式，使用实际的Asset模型字段
                        asset_data = {
                            'symbol': asset_obj.symbol,
                            'name': asset_obj.name,
                            'asset_type': asset_obj.asset_type,
                            'exchange': asset_obj.exchange,
                            'currency': getattr(asset_obj, 'currency', 'CNY'),
                            'industry': asset_obj.industry,
                            'concept': asset_obj.concept,
                            'area': '中国',  # Asset模型中没有area字段，使用默认值
                            'market': 'A股' if len(asset_obj.symbol) == 6 else '港股',  # 根据代码长度判断市场
                            'list_date': getattr(asset_obj, 'listing_date', None),  # 使用正确的字段名
                            'pe_ratio': asset_obj.pe_ratio,
                            'pb_ratio': asset_obj.pb_ratio,
                            'roe': asset_obj.roe,
                            'market_cap': asset_obj.market_cap,
                            'total_shares': asset_obj.total_shares,
                            'circulating_shares': asset_obj.circulating_shares,
                            'created_at': None,  # Asset模型中没有created_at字段
                            'updated_at': getattr(asset_obj, 'last_updated', None),  # 使用正确的字段名
                            'last_accessed': None  # Asset模型中没有last_accessed字段
                        }

                        asset_metadata = metadata

                    else:
                        # 降级到API模式（不应该在云端版本中使用）
                        st.error("❌ 后端服务不可用，云端版本不支持API模式")
                        return

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
                    with st.expander("Data Coverage Analysis", expanded=False):
                        display_data_coverage(symbol)

                except Exception as e:
                    st.error(f"❌ 查询过程中出现错误: {str(e)}")
                    st.info("请检查服务状态或稍后重试")
                    # 显示详细错误信息用于调试
                    with st.expander("🔍 错误详情", expanded=False):
                        st.code(str(e))
        else:
            # 显示使用指南
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
        st.write(f"**行业**: {asset_data.get('industry') or 'N/A'}")
        st.write(f"**概念**: {asset_data.get('concept') or 'N/A'}")
        st.write(f"**地区**: {asset_data.get('area') or 'N/A'}")
        st.write(f"**市场**: {asset_data.get('market') or 'N/A'}")
        st.write(f"**货币**: {asset_data.get('currency') or 'N/A'}")
    
    with col3:
        st.markdown("### 📅 时间信息")
        list_date = asset_data.get('list_date')
        if list_date:
            list_date_str = list_date.strftime('%Y-%m-%d') if hasattr(list_date, 'strftime') else str(list_date)
        else:
            list_date_str = 'N/A'
        st.write(f"**上市日期**: {list_date_str}")
        st.write(f"**数据来源**: AKShare")
        st.write(f"**更新时间**: {format_datetime(asset_data.get('updated_at'))}")
        st.write(f"**数据状态**: 已缓存")
    
    st.markdown("---")
    
    # 财务指标
    st.subheader("💰 财务指标")
    
    # 使用st.metric展示关键财务指标
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        pe_ratio = asset_data.get('pe_ratio')
        if pe_ratio is not None and pe_ratio > 0:
            pe_value = f"{pe_ratio:.2f}"
            pe_delta = "合理" if 10 <= pe_ratio <= 30 else ("偏低" if pe_ratio < 10 else "偏高")
        else:
            pe_value = "N/A"
            pe_delta = None
        st.metric(
            label="市盈率 (PE)",
            value=pe_value,
            delta=pe_delta,
            help="市盈率 = 股价 / 每股收益"
        )

    with col2:
        pb_ratio = asset_data.get('pb_ratio')
        if pb_ratio is not None and pb_ratio > 0:
            pb_value = f"{pb_ratio:.2f}"
            pb_delta = "合理" if 1 <= pb_ratio <= 3 else ("偏低" if pb_ratio < 1 else "偏高")
        else:
            pb_value = "N/A"
            pb_delta = None
        st.metric(
            label="市净率 (PB)",
            value=pb_value,
            delta=pb_delta,
            help="市净率 = 股价 / 每股净资产"
        )

    with col3:
        roe = asset_data.get('roe')
        if roe is not None and roe > 0:
            roe_value = f"{roe:.2f}%"
            roe_delta = "优秀" if roe >= 15 else ("良好" if roe >= 10 else "一般")
        else:
            roe_value = "N/A"
            roe_delta = None
        st.metric(
            label="净资产收益率 (ROE)",
            value=roe_value,
            delta=roe_delta,
            help="净资产收益率 = 净利润 / 净资产"
        )

    with col4:
        market_cap = asset_data.get('market_cap')
        if market_cap and market_cap > 0:
            market_cap_display = format_large_number(market_cap)
            if market_cap >= 1000e8:  # 1000亿以上
                cap_delta = "大盘股"
            elif market_cap >= 100e8:  # 100-1000亿
                cap_delta = "中盘股"
            else:  # 100亿以下
                cap_delta = "小盘股"
        else:
            market_cap_display = "N/A"
            cap_delta = None
        st.metric(
            label="总市值",
            value=market_cap_display,
            delta=cap_delta,
            help="总市值 = 股价 × 总股本"
        )

    # 第二行财务指标
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_shares = asset_data.get('total_shares')
        if total_shares and total_shares > 0:
            total_shares_display = format_large_number(total_shares)
            shares_delta = "股"
        else:
            total_shares_display = "N/A"
            shares_delta = None
        st.metric(
            label="总股本",
            value=total_shares_display,
            delta=shares_delta
        )

    with col2:
        circulating_shares = asset_data.get('circulating_shares')
        if circulating_shares and circulating_shares > 0:
            circulating_shares_display = format_large_number(circulating_shares)
            # 计算流通比例
            total_shares = asset_data.get('total_shares')
            if total_shares and total_shares > 0:
                ratio = (circulating_shares / total_shares) * 100
                circ_delta = f"{ratio:.1f}%流通"
            else:
                circ_delta = "股"
        else:
            circulating_shares_display = "N/A"
            circ_delta = None

        st.metric(
            label="流通股本",
            value=circulating_shares_display,
            delta=circ_delta
        )

    with col3:
        # 计算每股收益（如果有市盈率和市值数据）
        pe_ratio = asset_data.get('pe_ratio')
        market_cap = asset_data.get('market_cap')
        total_shares = asset_data.get('total_shares')

        if pe_ratio and market_cap and total_shares and pe_ratio > 0 and total_shares > 0:
            # 股价 = 市值 / 总股本
            stock_price = market_cap / total_shares
            # EPS = 股价 / PE
            eps = stock_price / pe_ratio
            eps_value = f"{eps:.2f}"
            eps_delta = "计算值"
        else:
            eps_value = "N/A"
            eps_delta = "数据不足"

        st.metric(
            label="每股收益 (EPS)",
            value=eps_value,
            delta=eps_delta,
            help="每股收益 = 股价 / 市盈率（计算值）"
        )

    with col4:
        # 计算每股净资产（如果有市净率和市值数据）
        pb_ratio = asset_data.get('pb_ratio')

        if pb_ratio and market_cap and total_shares and pb_ratio > 0 and total_shares > 0:
            # 股价 = 市值 / 总股本
            stock_price = market_cap / total_shares
            # BPS = 股价 / PB
            bps = stock_price / pb_ratio
            bps_value = f"{bps:.2f}"
            bps_delta = "计算值"
        else:
            bps_value = "N/A"
            bps_delta = "数据不足"

        st.metric(
            label="每股净资产 (BPS)",
            value=bps_value,
            delta=bps_delta,
            help="每股净资产 = 股价 / 市净率（计算值）"
        )


def display_asset_browser(query_service):
    """显示资产浏览器 - 查询数据库中的真实资产数据"""

    st.markdown("**📋 浏览已有资产**")

    try:
        if query_service:
            # 使用后端服务查询数据库中的真实资产数据
            with st.spinner("正在加载资产列表..."):
                assets, total_count = query_service.query_assets(
                    sort_by="symbol",
                    sort_order="asc",
                    limit=100  # 限制返回数量，避免加载过多数据
                )

            if not assets:
                # 如果数据库中没有资产数据，显示提示信息
                st.info("📊 数据库中暂无资产数据")
                st.markdown("""
                **💡 提示：**
                - 数据库中的资产数据会在您首次查询股票时自动创建
                - 您可以先使用"手动输入"方式查询一些股票，系统会自动保存资产信息
                - 推荐先查询：600000(浦发银行)、000001(平安银行)、600519(贵州茅台)
                """)
                return "", False, False

            # 转换为字典格式，便于处理
            asset_list = []
            for asset in assets:
                asset_dict = {
                    'symbol': asset.symbol,
                    'name': asset.name or f'Stock {asset.symbol}',
                    'industry': asset.industry or '其他'
                }
                asset_list.append(asset_dict)

            # 显示统计信息
            st.caption(f"📊 数据库中共有 {total_count} 只股票")

        else:
            # 后端服务不可用，显示错误信息
            st.error("❌ 后端服务不可用，无法加载资产列表")
            st.info("云端版本需要后端服务支持，请检查服务初始化状态")
            return "", False, False

        # 按行业分组
        industry_groups = {}
        for asset in asset_list:
            industry = asset.get('industry', '其他')
            if industry not in industry_groups:
                industry_groups[industry] = []
            industry_groups[industry].append(asset)

        # 行业筛选
        selected_industry = st.selectbox(
            "按行业筛选",
            ["全部"] + sorted(list(industry_groups.keys())),
            help="选择特定行业查看相关股票"
        )

        # 筛选资产
        if selected_industry == "全部":
            filtered_assets = asset_list
        else:
            filtered_assets = industry_groups[selected_industry]

        # 资产选择
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
        # 发生错误时，提供一些默认选项
        st.markdown("**🔄 使用默认资产列表：**")
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

        selected_symbol = default_options[selected_display]

        # 操作按钮
        col1, col2 = st.columns(2)
        with col1:
            query_button = st.button("🔍 查看详情", type="primary", use_container_width=True)
        with col2:
            refresh_button = st.button("🔄 刷新数据", use_container_width=True)

        return selected_symbol, query_button, refresh_button


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
        'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    # 移除重复项
    st.session_state.recent_asset_queries = [
        q for q in st.session_state.recent_asset_queries
        if q['symbol'] != symbol
    ]

    # 添加到开头
    st.session_state.recent_asset_queries.insert(0, query_record)

    # 保持最多10个记录
    st.session_state.recent_asset_queries = st.session_state.recent_asset_queries[:10]


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





def display_data_coverage(symbol: str):
    """显示数据覆盖情况"""

    try:
        # 使用后端服务直接查询数据库
        from core.database import get_db
        from core.models import DailyStockData, Asset
        from datetime import date, timedelta
        from sqlalchemy import func

        # 获取数据库会话
        db_session = next(get_db())

        try:
            # 查找资产
            asset = db_session.query(Asset).filter(Asset.symbol == symbol).first()
            if not asset:
                st.info("📝 暂无资产信息，请先查询该股票")
                return

            # 查询最近30天的数据覆盖情况
            end_date = date.today()
            start_date = end_date - timedelta(days=30)

            data_count = db_session.query(func.count(DailyStockData.id)).filter(
                DailyStockData.asset_id == asset.asset_id,
                DailyStockData.trade_date >= start_date,
                DailyStockData.trade_date <= end_date
            ).scalar()

            # 获取数据范围
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
                st.info("📝 暂无历史数据，请先在股票数据查询页面获取数据")

        finally:
            db_session.close()

    except Exception as e:
        st.warning(f"⚠️ 获取数据覆盖信息失败: {str(e)}")
        # 显示详细错误信息用于调试
        with st.expander("🔍 错误详情", expanded=False):
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

        # 其他情况直接转换为字符串
        return str(dt_obj)
    except Exception:
        return "N/A"


def format_large_number(num):
    """格式化大数字显示"""
    if not num or num == 0:
        return "N/A"

    try:
        num = float(num)
        if num >= 1e8:
            return f"{num/1e8:.2f}亿"
        elif num >= 1e4:
            return f"{num/1e4:.2f}万"
        else:
            return f"{num:.2f}"
    except:
        return "N/A"


def show_usage_guide():
    """显示使用指南"""

    st.markdown("### 📖 使用指南")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        #### 🔍 如何查询资产信息

        1. **选择查询方式**: 手动输入或浏览已有资产
        2. **输入股票代码**: 支持A股(6位)和港股(5位)代码
        3. **点击查询**: 点击"查询资产信息"按钮
        4. **查看详情**: 浏览基本信息、财务指标和数据覆盖
        5. **刷新数据**: 使用"刷新数据"获取最新信息

        #### 📊 信息内容

        - **基本信息**: 公司名称、行业、交易所等
        - **财务指标**: PE、PB、ROE、市值等关键指标
        - **数据覆盖**: 历史数据的完整性和质量信息
        """)

    with col2:
        st.markdown("""
        #### 💡 使用技巧

        - **浏览功能**: 使用"浏览已有资产"快速选择股票
        - **行业筛选**: 按行业分类查看相关股票
        - **港股支持**: 支持港股代码查询(如00700)
        - **最近查询**: 快速重新查看之前查询的股票

        #### 🎯 推荐查询

        **A股推荐**:
        - **600000**: 浦发银行 (银行业龙头)
        - **000001**: 平安银行 (股份制银行)
        - **600519**: 贵州茅台 (消费行业)

        **港股推荐**:
        - **00700**: 腾讯控股 (科技龙头)
        - **09988**: 阿里巴巴-SW (电商巨头)
        """)

    # 快速查询按钮
    st.markdown("### 🚀 快速查询")
    st.markdown("点击下方按钮快速查询热门股票的资产信息")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("浦发银行(600000)", use_container_width=True, key="quick_asset_600000"):
            st.session_state.update({
                'symbol': '600000',
                'auto_query_asset': True
            })
            st.rerun()

    with col2:
        if st.button("平安银行(000001)", use_container_width=True, key="quick_asset_000001"):
            st.session_state.update({
                'symbol': '000001',
                'auto_query_asset': True
            })
            st.rerun()

    with col3:
        if st.button("贵州茅台(600519)", use_container_width=True, key="quick_asset_600519"):
            st.session_state.update({
                'symbol': '600519',
                'auto_query_asset': True
            })
            st.rerun()

    with col4:
        if st.button("万科A(000002)", use_container_width=True, key="quick_asset_000002"):
            st.session_state.update({
                'symbol': '000002',
                'auto_query_asset': True
            })
            st.rerun()


if __name__ == "__main__":
    main()
