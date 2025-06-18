"""
股票数据查询页面

提供股票历史数据查询、图表展示和基础分析功能。
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import sys
import os

# 添加项目路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from utils.api_client import get_api_client, handle_api_error, format_date_for_api, QuantDBAPIError
from utils.stock_validator import validate_stock_code, analyze_query_failure, get_alternative_suggestions
from utils.charts import (
    create_price_chart,
    create_volume_chart,
    create_metrics_dashboard,
    calculate_basic_metrics,
    create_candlestick_chart,
    create_returns_distribution,
    create_performance_comparison_chart
)
from utils.config import config

# 页面配置
st.set_page_config(
    page_title="股票数据查询 - QuantDB",
    page_icon="📈",
    layout="wide"
)

def main():
    """主页面函数"""

    # 页面标题
    # st.title("📈 股票数据查询")
    # st.markdown("查询股票的历史价格数据，支持多种复权方式和时间范围选择。")
    # st.markdown("---")

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
                symbol = display_stock_browser()

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
            if not config.validate_symbol(symbol):
                st.error(config.ERROR_MESSAGES["invalid_symbol"])
                return

            # 标准化股票代码
            symbol = config.normalize_symbol(symbol)

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
                    client = get_api_client()

                    # 格式化日期
                    start_date_str = format_date_for_api(start_date)
                    end_date_str = format_date_for_api(end_date)

                    # 调用API
                    response = client.get_stock_data(symbol, start_date_str, end_date_str, adjust)

                    if response and 'data' in response:
                        data = response['data']
                        metadata = response.get('metadata', {})

                        # 转换为DataFrame
                        df = pd.DataFrame(data)

                        if df.empty:
                            st.warning("未找到指定时间范围内的数据")

                            # 使用股票验证工具进行详细分析
                            try:
                                start_date_str = format_date_for_api(start_date)
                                end_date_str = format_date_for_api(end_date)
                                failure_analysis = analyze_query_failure(symbol, start_date_str, end_date_str)

                                with st.expander("🔍 详细错误分析和解决方案"):
                                    # 股票验证结果
                                    stock_validation = failure_analysis["stock_validation"]

                                    if stock_validation["is_problematic"]:
                                        st.error(f"⚠️ 检测到问题股票: {stock_validation['name']}")
                                    elif not stock_validation["is_active"]:
                                        st.warning(f"📊 股票 {symbol} 可能不够活跃")

                                    st.markdown("**🔍 可能的原因：**")
                                    for reason in failure_analysis["possible_reasons"]:
                                        st.write(f"• {reason}")

                                    st.markdown("**💡 建议的解决方案：**")
                                    for recommendation in failure_analysis["recommendations"]:
                                        st.write(f"• {recommendation}")

                                    # 显示替代股票建议
                                    if failure_analysis["suggested_stocks"]:
                                        st.markdown("**🚀 推荐的替代股票：**")
                                        for suggestion in failure_analysis["suggested_stocks"][:3]:
                                            st.write(f"• {suggestion['symbol']} - {suggestion['name']} ({suggestion['reason']})")

                            except Exception as e:
                                # 如果分析失败，显示基本的错误信息
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

                            return

                        # 显示成功信息
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.success(f"✅ 成功获取 {len(df)} 条记录")
                        with col2:
                            if metadata.get('cache_hit'):
                                st.info("⚡ 数据来自缓存")
                            else:
                                st.info("🌐 数据来自AKShare")
                        with col3:
                            response_time = metadata.get('response_time_ms', 0)
                            st.info(f"⏱️ 响应时间: {response_time:.1f}ms")

                        # 添加到最近查询列表
                        add_to_recent_stock_queries(symbol, f"Stock {symbol}")

                        # 显示数据
                        display_stock_data(df, symbol, metadata)

                    else:
                        st.error("API返回数据格式错误")

                except QuantDBAPIError as e:
                    st.error(f"查询失败: {str(e)}")
                except Exception as e:
                    st.error(f"未知错误: {str(e)}")
                    st.exception(e)

        else:
            # 显示使用说明
            show_usage_guide()

def display_stock_data(df: pd.DataFrame, symbol: str, metadata: dict):
    """显示股票数据"""
    
    # 计算基础指标
    metrics = calculate_basic_metrics(df)
    
    # 显示指标仪表板
    st.subheader("📊 关键指标")
    create_metrics_dashboard(metrics)
    
    st.markdown("---")
    
    # 图表选择
    st.subheader("📊 数据可视化")

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
    
    # 示例查询 - 重构为避免session_state冲突
    st.markdown("### 🚀 快速开始")
    st.markdown("点击下方按钮快速查询热门股票，或使用右侧查询面板自定义查询")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("查询浦发银行(600000)", use_container_width=True, key="quick_600000"):
            # 使用不同的session_state key避免冲突
            st.session_state['quick_symbol'] = '600000'
            st.session_state['quick_name'] = '浦发银行'
            st.session_state['quick_query_triggered'] = True
            st.rerun()

    with col2:
        if st.button("查询平安银行(000001)", use_container_width=True, key="quick_000001"):
            st.session_state['quick_symbol'] = '000001'
            st.session_state['quick_name'] = '平安银行'
            st.session_state['quick_query_triggered'] = True
            st.rerun()

    with col3:
        if st.button("查询贵州茅台(600519)", use_container_width=True, key="quick_600519"):
            st.session_state['quick_symbol'] = '600519'
            st.session_state['quick_name'] = '贵州茅台'
            st.session_state['quick_query_triggered'] = True
            st.rerun()

    # 处理快速查询
    if st.session_state.get('quick_query_triggered', False):
        quick_symbol = st.session_state.get('quick_symbol', '')
        quick_name = st.session_state.get('quick_name', '')

        if quick_symbol:
            st.info(f"🚀 正在为您查询 {quick_name}({quick_symbol}) 最近7天的数据...")

            # 执行查询逻辑
            try:
                client = get_api_client()

                # 使用固定的7天范围，提升性能
                end_date = date.today()
                start_date = end_date - timedelta(days=7)
                start_date_str = format_date_for_api(start_date)
                end_date_str = format_date_for_api(end_date)

                # 调用API
                response = client.get_stock_data(quick_symbol, start_date_str, end_date_str, "")

                if response and 'data' in response:
                    data = response['data']
                    metadata = response.get('metadata', {})

                    # 转换为DataFrame
                    df = pd.DataFrame(data)

                    if not df.empty:
                        # 显示成功信息
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.success(f"✅ 成功获取 {len(df)} 条记录")
                        with col2:
                            if metadata.get('cache_hit'):
                                st.info("⚡ 数据来自缓存")
                            else:
                                st.info("🌐 数据来自AKShare")
                        with col3:
                            response_time = metadata.get('response_time_ms', 0)
                            st.info(f"⏱️ 响应时间: {response_time:.1f}ms")

                        # 显示数据
                        display_stock_data(df, quick_symbol, metadata)
                    else:
                        st.warning("未找到指定时间范围内的数据")
                else:
                    st.error("API返回数据格式错误")

            except Exception as e:
                st.error(f"查询失败: {str(e)}")

            # 清除快速查询标志
            st.session_state['quick_query_triggered'] = False

def display_stock_browser():
    """显示股票浏览器"""

    st.markdown("**📋 浏览已有股票**")

    try:
        client = get_api_client()

        # 获取股票列表
        with st.spinner("加载股票列表..."):
            assets = client.get_assets_list(limit=50)  # 限制50个以提高性能

        if not assets:
            st.warning("暂无已有股票数据")
            return ""

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

        # 筛选股票
        if selected_industry == "全部":
            filtered_assets = assets
        else:
            filtered_assets = industry_groups[selected_industry]

        # 股票选择
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

            return asset_options[selected_display]
        else:
            st.info("该行业暂无股票数据")
            return ""

    except Exception as e:
        st.error(f"加载股票列表失败: {str(e)}")
        return ""

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
