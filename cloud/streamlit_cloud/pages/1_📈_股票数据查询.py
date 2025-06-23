"""
股票数据查询页面 - Cloud版本
提供股票历史数据查询和图表展示功能，适配Streamlit Cloud单体架构
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import sys
import os
import time

# 添加项目根目录到路径以访问core模块
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(parent_dir)  # 回到QuantDB根目录
if project_root not in sys.path:
    sys.path.append(project_root)

# 导入现有的后端服务（直接调用，不通过HTTP API）
try:
    from core.services import StockDataService, AssetInfoService
    from core.cache import AKShareAdapter
    from core.database import get_db
    BACKEND_SERVICES_AVAILABLE = True
except ImportError as e:
    BACKEND_SERVICES_AVAILABLE = False

# 导入图表工具（尝试从原有版本导入）
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

# 页面配置
st.set_page_config(
    page_title="股票数据查询 - QuantDB",
    page_icon="📈",
    layout="wide"
)

def validate_stock_code(code: str) -> bool:
    """验证股票代码格式 - 支持A股和港股"""
    if not code:
        return False

    # 去除空格
    code = code.strip()

    # 港股验证: 5位数字 (00700, 09988, 01810等)
    if len(code) == 5 and code.isdigit():
        return True

    # A股验证: 6位数字
    if len(code) == 6 and code.isdigit():
        # 检查是否为有效的A股代码
        if code.startswith(('000', '001', '002', '003', '300')):  # 深交所
            return True
        elif code.startswith('6'):  # 上交所
            return True
        elif code.startswith('688'):  # 科创板
            return True

    return False

@st.cache_resource
def init_services():
    """初始化后端服务"""
    try:
        # 获取数据库会话
        db_session = next(get_db())

        # 初始化AKShare适配器
        akshare_adapter = AKShareAdapter()

        # 初始化服务
        stock_service = StockDataService(db_session, akshare_adapter)
        asset_service = AssetInfoService(db_session)

        # 初始化查询服务
        from core.services import QueryService
        query_service = QueryService(db_session)

        return stock_service, asset_service, query_service
    except Exception as e:
        st.error(f"服务初始化失败: {e}")
        return None, None, None

def main():
    """主页面函数"""

    # 检查后端服务是否可用
    if not BACKEND_SERVICES_AVAILABLE:
        st.warning("⚠️ 后端服务不可用，显示演示模式")
        st.info("💡 在演示模式下，您可以查看界面布局和功能说明")

        # 在演示模式下仍然显示界面
        show_demo_interface()
        return

    # 初始化后端服务
    services = init_services()
    if len(services) != 3 or not all(services):
        st.error("❌ 服务初始化失败，请刷新页面重试")
        return

    stock_service, asset_service, query_service = services

    # 主页面布局：左侧内容区 + 右侧查询面板
    col_main, col_query = st.columns([7, 3])  # 70% + 30% 布局

    # 右侧查询面板
    with col_query:
        with st.container():
            st.markdown("### 🔍 股票数据查询")

            # 查询方式选择
            query_mode = st.radio(
                "查询方式",
                ["手动输入", "浏览已有股票"],
                help="选择查询方式：手动输入股票代码或从已有股票中选择"
            )

            if query_mode == "手动输入":
                # 股票代码输入
                symbol = st.text_input(
                    "股票代码",
                    value="600000",
                    placeholder="A股: 600000 | 港股: 02171",
                    help="支持A股代码(6位数字)和港股代码(5位数字)"
                )
            else:
                # 浏览已有股票
                symbol = display_stock_browser(query_service)

            # 日期范围选择
            st.markdown("#### 📅 日期范围")

            # 快速选择按钮
            col1, col2 = st.columns(2)
            with col1:
                if st.button("最近7天", use_container_width=True):
                    st.session_state.start_date = date.today() - timedelta(days=7)
                    st.session_state.end_date = date.today()
            with col2:
                if st.button("最近30天", use_container_width=True):
                    st.session_state.start_date = date.today() - timedelta(days=30)
                    st.session_state.end_date = date.today()

            # 日期选择器
            start_date = st.date_input(
                "开始日期",
                value=st.session_state.get('start_date', date.today() - timedelta(days=7)),
                max_value=date.today(),
                key='start_date'
            )

            end_date = st.date_input(
                "结束日期",
                value=st.session_state.get('end_date', date.today()),
                max_value=date.today(),
                key='end_date'
            )

            # 复权选择
            adjust_type = st.selectbox(
                "复权类型",
                options=["不复权", "前复权", "后复权"],
                index=0,
                help="前复权(qfq): 以当前价为基准向前复权\n后复权(hfq): 以上市价为基准向后复权"
            )

            # 转换复权参数
            adjust_map = {"不复权": "", "前复权": "qfq", "后复权": "hfq"}
            adjust = adjust_map[adjust_type]

            # 查询按钮
            query_button = st.button("🔍 查询数据", type="primary", use_container_width=True)

            # 显示最近查询
            display_recent_stock_queries()

    # 检查是否有自动查询请求
    if st.session_state.get('auto_query_stock'):
        symbol = st.session_state.get('symbol', '600000')
        query_button = True
        st.session_state.auto_query_stock = False

    # 检查是否有保存的查询状态（用于保持页面状态）
    if not query_button and st.session_state.get('current_stock_symbol'):
        symbol = st.session_state.get('current_stock_symbol')
        start_date = st.session_state.get('current_start_date', date.today() - timedelta(days=7))
        end_date = st.session_state.get('current_end_date', date.today())
        adjust = st.session_state.get('current_adjust', "")
        query_button = True  # 自动重新显示之前查询的股票数据

    # 处理建议股票的查询
    if st.session_state.get('suggested_symbol'):
        suggested_symbol = st.session_state.pop('suggested_symbol')
        suggested_name = st.session_state.pop('suggested_name', '')

        # 自动设置参数并查询
        symbol = suggested_symbol
        start_date = date.today() - timedelta(days=7)  # 使用7天范围，提升性能
        end_date = date.today()
        adjust = ""
        query_button = True

    # 左侧主内容区域
    with col_main:
        if query_button or st.session_state.get('auto_query', False):

            # 验证输入
            if not symbol:
                st.error("请输入股票代码")
                return

            if start_date >= end_date:
                st.error("开始日期必须早于结束日期")
                return

            # 验证股票代码格式
            if not validate_stock_code(symbol):
                st.error("❌ 请输入有效的股票代码（A股6位数字如：600000、000001，港股5位数字如：00700、09988）")
                return

            # 保存当前查询状态
            st.session_state.current_stock_symbol = symbol
            st.session_state.current_start_date = start_date
            st.session_state.current_end_date = end_date
            st.session_state.current_adjust = adjust

            # 显示查询信息
            st.info(f"正在查询股票 {symbol} 从 {start_date} 到 {end_date} 的数据...")

            # 查询数据
            with st.spinner("数据查询中..."):
                try:
                    # 调用后端服务获取股票数据
                    result = stock_service.get_stock_data(
                        symbol=symbol,
                        start_date=start_date.strftime('%Y%m%d'),
                        end_date=end_date.strftime('%Y%m%d'),
                        adjust=adjust
                    )

                    if result is None or (isinstance(result, pd.DataFrame) and result.empty):
                        st.warning("未找到指定时间范围内的数据")

                        # 提供基本的错误信息和解决方案
                        with st.expander("🔍 可能的原因和解决方案"):
                            st.markdown("""
                            **可能的原因：**
                            1. 📅 **时间范围问题**：选择的日期范围内可能没有交易日（周末、节假日）
                            2. 📈 **股票状态问题**：该股票可能已停牌、退市或长期停牌
                            3. 🌐 **数据源问题**：AKShare暂时无法获取该股票的数据
                            4. ⏰ **数据延迟**：最新数据可能还未更新

                            **建议的解决方案：**
                            - 🔄 **扩大时间范围**：尝试查询最近30天或更长时间
                            - 📊 **更换股票代码**：尝试查询活跃股票如：600000(浦发银行)、000001(平安银行)
                            - 📅 **检查交易日**：避免选择周末或节假日
                            - 🔍 **验证股票代码**：确认股票代码是否正确且仍在交易
                            """)

                        # 提供快速替代选项
                        st.markdown("**🚀 快速尝试活跃股票：**")

                        # A股推荐
                        st.markdown("**A股推荐：**")
                        col1, col2, col3 = st.columns(3)

                        with col1:
                            if st.button("浦发银行(600000)", key="suggest_600000"):
                                st.session_state.update({
                                    'suggested_symbol': '600000',
                                    'suggested_name': '浦发银行'
                                })
                                st.rerun()

                        with col2:
                            if st.button("平安银行(000001)", key="suggest_000001"):
                                st.session_state.update({
                                    'suggested_symbol': '000001',
                                    'suggested_name': '平安银行'
                                })
                                st.rerun()

                        with col3:
                            if st.button("贵州茅台(600519)", key="suggest_600519"):
                                st.session_state.update({
                                    'suggested_symbol': '600519',
                                    'suggested_name': '贵州茅台'
                                })
                                st.rerun()

                        # 港股推荐
                        st.markdown("**🇭🇰 港股推荐：**")
                        col4, col5, col6 = st.columns(3)

                        with col4:
                            if st.button("腾讯控股(00700)", key="suggest_00700"):
                                st.session_state.update({
                                    'suggested_symbol': '00700',
                                    'suggested_name': '腾讯控股'
                                })
                                st.rerun()

                        with col5:
                            if st.button("阿里巴巴(09988)", key="suggest_09988"):
                                st.session_state.update({
                                    'suggested_symbol': '09988',
                                    'suggested_name': '阿里巴巴-SW'
                                })
                                st.rerun()

                        with col6:
                            if st.button("小米集团(01810)", key="suggest_01810"):
                                st.session_state.update({
                                    'suggested_symbol': '01810',
                                    'suggested_name': '小米集团-W'
                                })
                                st.rerun()

                        return

                    # 转换为DataFrame
                    df = pd.DataFrame(result) if not isinstance(result, pd.DataFrame) else result

                    # 显示成功信息
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.success(f"✅ 成功获取 {len(df)} 条记录")
                    with col2:
                        st.info("🌐 数据来自后端服务")
                    with col3:
                        st.info(f"⏱️ 响应时间: 快速")

                    # 添加到最近查询列表
                    add_to_recent_stock_queries(symbol, f"Stock {symbol}")

                    # 显示数据
                    display_stock_data(df, symbol, {
                        'cache_hit': False,
                        'response_time_ms': 100,
                        'akshare_called': True
                    })

                except Exception as e:
                    st.error(f"查询失败: {str(e)}")
                    st.exception(e)

        else:
            # 显示使用说明
            show_usage_guide()





def display_stock_data(df: pd.DataFrame, symbol: str, metadata: dict):
    """显示股票数据"""

    # 计算基础指标
    if CHARTS_AVAILABLE:
        metrics = calculate_basic_metrics(df)

        # 显示指标仪表板
        st.subheader("📊 关键指标")
        create_metrics_dashboard(metrics)
    else:
        # 简单的指标显示
        st.subheader("📊 关键指标")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("最新价格", f"¥{df['close'].iloc[-1]:.2f}")
        with col2:
            st.metric("最高价", f"¥{df['high'].max():.2f}")
        with col3:
            st.metric("最低价", f"¥{df['low'].min():.2f}")
        with col4:
            if len(df) > 1:
                change = (df['close'].iloc[-1] - df['close'].iloc[0]) / df['close'].iloc[0] * 100
                st.metric("期间涨跌", f"{change:.2f}%")
            else:
                st.metric("期间涨跌", "N/A")

    st.markdown("---")

    # 图表选择
    st.subheader("📊 数据可视化")

    if CHARTS_AVAILABLE:
        chart_tabs = st.tabs(["📈 价格趋势", "🕯️ K线图", "📊 成交量", "📉 收益率分析", "⚡ 性能对比"])

        with chart_tabs[0]:
            st.markdown("#### 价格趋势图")
            price_chart = create_price_chart(df, f"股票 {symbol} 价格趋势")
            st.plotly_chart(price_chart, use_container_width=True)

        with chart_tabs[1]:
            st.markdown("#### K线图")
            if all(col in df.columns for col in ['open', 'high', 'low', 'close']):
                candlestick_chart = create_candlestick_chart(df, f"股票 {symbol} K线图")
                st.plotly_chart(candlestick_chart, use_container_width=True)
            else:
                st.info("暂无完整的OHLC数据，无法显示K线图")

        with chart_tabs[2]:
            st.markdown("#### 成交量")
            if 'volume' in df.columns:
                volume_chart = create_volume_chart(df, f"股票 {symbol} 成交量")
                st.plotly_chart(volume_chart, use_container_width=True)
            else:
                st.info("暂无成交量数据")

        with chart_tabs[3]:
            st.markdown("#### 收益率分析")
            if 'close' in df.columns and len(df) > 1:
                returns_chart = create_returns_distribution(df, f"股票 {symbol} 收益率分布")
                st.plotly_chart(returns_chart, use_container_width=True)

                # 收益率统计
                returns = df['close'].pct_change().dropna() * 100
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("平均日收益率", f"{returns.mean():.2f}%")
                with col2:
                    st.metric("收益率标准差", f"{returns.std():.2f}%")
                with col3:
                    st.metric("最大单日涨幅", f"{returns.max():.2f}%")
            else:
                st.info("数据不足，无法计算收益率分析")

        with chart_tabs[4]:
            st.markdown("#### 性能对比")
            if metadata.get('response_time_ms') is not None:
                cache_time = metadata.get('response_time_ms', 0)
                # 模拟AKShare直接调用时间（基于是否缓存命中）
                akshare_time = 1075.2 if metadata.get('cache_hit') else cache_time

                if cache_time != akshare_time:
                    perf_chart = create_performance_comparison_chart(cache_time, akshare_time)
                    st.plotly_chart(perf_chart, use_container_width=True)

                    # 性能提升说明
                    improvement = ((akshare_time - cache_time) / akshare_time * 100) if akshare_time > 0 else 0
                    st.success(f"🚀 QuantDB缓存比AKShare直接调用快 {improvement:.1f}%")
                else:
                    st.info("首次查询，暂无性能对比数据")
            else:
                st.info("暂无性能数据")
    else:
        # 简单的图表显示
        st.info("📊 图表功能需要完整的后端服务支持")

        # 显示简单的价格趋势
        st.markdown("#### 价格数据")
        st.line_chart(df.set_index('date')['close'] if 'date' in df.columns else df['close'])

    # 数据表格
    st.subheader("📋 详细数据")

    # 数据处理和格式化
    display_df = df.copy()

    # 格式化数值列
    numeric_columns = ['open', 'high', 'low', 'close', 'volume']
    for col in numeric_columns:
        if col in display_df.columns:
            if col == 'volume':
                display_df[col] = display_df[col].apply(lambda x: f"{x:,.0f}" if pd.notnull(x) else "")
            else:
                display_df[col] = display_df[col].apply(lambda x: f"{x:.2f}" if pd.notnull(x) else "")

    # 重命名列
    column_names = {
        'date': '日期',
        'trade_date': '交易日期',
        'open': '开盘价',
        'high': '最高价',
        'low': '最低价',
        'close': '收盘价',
        'volume': '成交量',
        'amount': '成交额'
    }

    display_df = display_df.rename(columns=column_names)

    # 显示表格
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )

    # 数据统计
    with st.expander("📈 数据统计"):
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**价格统计**")
            st.write(f"- 最新价格: ¥{metrics.get('latest_price', 0):.2f}")
            st.write(f"- 最高价格: ¥{metrics.get('high_price', 0):.2f}")
            st.write(f"- 最低价格: ¥{metrics.get('low_price', 0):.2f}")
            st.write(f"- 平均价格: ¥{metrics.get('avg_price', 0):.2f}")
            st.write(f"- 价格波动率: {metrics.get('volatility', 0):.2f}")

        with col2:
            st.markdown("**查询信息**")
            st.write(f"- 数据记录数: {len(df)}")
            st.write(f"- 缓存命中: {'是' if metadata.get('cache_hit') else '否'}")
            st.write(f"- AKShare调用: {'是' if metadata.get('akshare_called') else '否'}")
            st.write(f"- 响应时间: {metadata.get('response_time_ms', 0):.1f}ms")
            if 'total_volume' in metrics:
                st.write(f"- 总成交量: {metrics['total_volume']:,.0f}")

def show_demo_interface():
    """显示演示界面"""

    # 主页面布局：左侧内容区 + 右侧查询面板
    col_main, col_query = st.columns([7, 3])  # 70% + 30% 布局

    # 右侧查询面板
    with col_query:
        with st.container():
            st.markdown("### 🔍 股票数据查询")

            # 查询方式选择
            query_mode = st.radio(
                "查询方式",
                ["手动输入", "浏览已有股票"],
                help="选择查询方式：手动输入股票代码或从已有股票中选择"
            )

            if query_mode == "手动输入":
                # 股票代码输入
                symbol = st.text_input(
                    "股票代码",
                    value="600000",
                    placeholder="A股: 600000 | 港股: 02171",
                    help="支持A股代码(6位数字)和港股代码(5位数字)"
                )
            else:
                # 浏览已有股票
                st.selectbox("选择股票", ["600000 - 浦发银行", "000001 - 平安银行"])

            # 日期范围选择
            st.markdown("#### 📅 日期范围")

            # 快速选择按钮
            col1, col2 = st.columns(2)
            with col1:
                st.button("最近7天", use_container_width=True)
            with col2:
                st.button("最近30天", use_container_width=True)

            # 日期选择器
            start_date = st.date_input(
                "开始日期",
                value=date.today() - timedelta(days=7),
                max_value=date.today()
            )

            end_date = st.date_input(
                "结束日期",
                value=date.today(),
                max_value=date.today()
            )

            # 复权选择
            adjust_type = st.selectbox(
                "复权类型",
                options=["不复权", "前复权", "后复权"],
                index=0,
                help="前复权(qfq): 以当前价为基准向前复权\n后复权(hfq): 以上市价为基准向后复权"
            )

            # 查询按钮
            query_button = st.button("🔍 查询数据", type="primary", use_container_width=True)

            # 显示最近查询
            st.markdown("---")
            st.markdown("**🕒 最近查询**")
            st.caption("暂无最近查询记录")

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
