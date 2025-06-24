"""
Data Export Page - Cloud Version

Provides stock data export functionality, supports CSV and Excel formats,
with customizable export range and format options.
"""

import streamlit as st
import pandas as pd
import io
from datetime import datetime, date, timedelta
import sys
import json
from pathlib import Path

# 添加项目根目录到Python路径以访问core模块
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent  # 回到QuantDB根目录
sys.path.insert(0, str(project_root))

# 检测运行环境
CLOUD_MODE = True
try:
    # 检测是否在Streamlit Cloud环境
    import os
    if 'STREAMLIT_SHARING' in os.environ or 'STREAMLIT_CLOUD' in os.environ:
        CLOUD_MODE = True
    else:
        # 测试是否可以导入core模块
        from core.services import StockDataService
        CLOUD_MODE = False
except Exception:
    CLOUD_MODE = True

# 导入Excel支持
try:
    import openpyxl
    EXCEL_SUPPORT = True
except ImportError:
    EXCEL_SUPPORT = False

# 页面配置
st.set_page_config(
    page_title="Data Export - QuantDB",
    page_icon="📊",
    layout="wide"
)

@st.cache_resource
def init_services():
    """初始化服务实例 - 云端优化版本"""
    try:
        if not CLOUD_MODE:
            # 完整模式：使用core模块
            from core.services import StockDataService, AssetInfoService
            from core.cache import AKShareAdapter
            from core.database import get_db

            db_session = next(get_db())
            akshare_adapter = AKShareAdapter()

            return {
                'stock_service': StockDataService(db_session, akshare_adapter),
                'asset_service': AssetInfoService(db_session),
                'db_session': db_session,
                'mode': 'full'
            }
        else:
            # 云端模式：简化的服务初始化
            import sqlite3

            db_path = current_dir / "database" / "stock_data.db"

            # 测试SQLite连接
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            # 获取基本信息
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]

            conn.close()

            return {
                'db_path': str(db_path),
                'tables': tables,
                'mode': 'cloud'
            }

    except Exception as e:
        st.error(f"服务初始化失败: {e}")
        # 返回最小服务对象
        return {
            'mode': 'minimal',
            'error': str(e)
        }

def main():
    """主页面函数"""
    
    # Page title
    st.title("📤 Data Export")
    st.markdown("Export stock data, asset information and watchlist")
    st.markdown("---")
    
    # 初始化服务
    services = init_services()
    if not services:
        st.error("❌ 服务初始化失败，请刷新页面重试")
        return

    # 显示运行模式
    mode = services.get('mode', 'unknown')
    if mode == 'full':
        st.info("🖥️ 运行模式: 完整模式 (使用core服务)")
    elif mode == 'cloud':
        st.info("☁️ 运行模式: 云端模式 (SQLite直连)")
    elif mode == 'minimal':
        st.warning("⚠️ 运行模式: 最小模式 (功能受限)")
        st.error(f"初始化错误: {services.get('error', '未知错误')}")

    # Excel支持提示
    if not EXCEL_SUPPORT:
        st.warning("⚠️ Excel导出功能不可用，请使用CSV格式")
    
    # 导出选项
    st.subheader("📋 导出配置")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 数据类型选择
        export_type = st.selectbox(
            "导出数据类型",
            ["股票历史数据", "资产信息", "自选股列表"],
            help="选择要导出的数据类型"
        )
        
        # 导出格式
        export_format = st.selectbox(
            "导出格式",
            ["CSV", "Excel"],
            help="选择导出文件格式"
        )
    
    with col2:
        # 股票代码输入（仅对股票数据有效）
        if export_type in ["股票历史数据", "资产信息"]:
            symbols_input = st.text_area(
                "股票代码",
                value="600000\n000001\n600519",
                help="每行输入一个股票代码，支持批量导出",
                height=100
            )
            
            # 解析股票代码
            symbols = [s.strip() for s in symbols_input.split('\n') if s.strip()]
            
            # 简化的股票代码验证
            valid_symbols = []
            for symbol in symbols:
                # 基本验证：5-6位数字
                if symbol.isdigit() and 5 <= len(symbol) <= 6:
                    valid_symbols.append(symbol)
                else:
                    st.warning(f"⚠️ 无效股票代码: {symbol}")

            symbols = valid_symbols
            
            if symbols:
                st.success(f"✅ 有效股票代码: {len(symbols)}个")
                st.write("股票列表:", ", ".join(symbols))
            else:
                st.error("❌ 请输入有效的股票代码")
        
        # 日期范围（仅对历史数据有效）
        if export_type == "股票历史数据":
            st.markdown("**日期范围**")
            
            col_start, col_end = st.columns(2)
            with col_start:
                start_date = st.date_input(
                    "开始日期",
                    value=date.today() - timedelta(days=30),
                    max_value=date.today()
                )
            
            with col_end:
                end_date = st.date_input(
                    "结束日期",
                    value=date.today(),
                    max_value=date.today()
                )
    
    # 导出按钮
    st.markdown("---")
    
    if st.button("🚀 开始导出", type="primary", use_container_width=True):
        if export_type == "股票历史数据":
            if symbols and start_date < end_date:
                export_stock_data(symbols, start_date, end_date, export_format, services)
            else:
                st.error("请检查股票代码和日期范围")
        
        elif export_type == "资产信息":
            if symbols:
                export_asset_info(symbols, export_format, services)
            else:
                st.error("请输入有效的股票代码")
        
        elif export_type == "自选股列表":
            export_watchlist(export_format)
    
    # 导出历史
    st.markdown("---")
    st.subheader("📁 导出历史")
    display_export_history()

def export_stock_data(symbols, start_date, end_date, export_format, services):
    """导出股票历史数据"""

    try:
        mode = services.get('mode', 'unknown')
        start_date_str = start_date.strftime('%Y%m%d')
        end_date_str = end_date.strftime('%Y%m%d')

        all_data = []

        # 进度条
        progress_bar = st.progress(0)
        status_text = st.empty()

        for idx, symbol in enumerate(symbols):
            status_text.text(f"正在获取 {symbol} 的数据...")

            try:
                if mode == 'full':
                    # 完整模式：使用stock_service
                    stock_data = services['stock_service'].get_stock_data(
                        symbol=symbol,
                        start_date=start_date_str,
                        end_date=end_date_str
                    )

                    if stock_data is not None and not stock_data.empty:
                        df = stock_data.copy()
                        df['symbol'] = symbol

                        # 获取股票名称
                        try:
                            asset_info, metadata = services['asset_service'].get_or_create_asset(symbol)
                            stock_name = asset_info.name if asset_info else f'股票{symbol}'
                            df['name'] = stock_name
                        except:
                            df['name'] = f'股票{symbol}'

                        all_data.append(df)

                elif mode == 'cloud':
                    # 云端模式：直接查询SQLite数据库
                    import sqlite3
                    conn = sqlite3.connect(services['db_path'])

                    # 查询股票数据
                    query = """
                    SELECT a.symbol, a.name, d.date, d.open, d.high, d.low, d.close, d.volume, d.turnover
                    FROM daily_stock_data d
                    JOIN assets a ON d.asset_id = a.asset_id
                    WHERE a.symbol = ? AND d.date BETWEEN ? AND ?
                    ORDER BY d.date
                    """

                    df = pd.read_sql_query(query, conn, params=(symbol, start_date, end_date))
                    conn.close()

                    if not df.empty:
                        # 格式化日期
                        df['trade_date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
                        all_data.append(df)

                else:
                    # 最小模式：创建示例数据
                    df = pd.DataFrame({
                        'symbol': [symbol],
                        'name': [f'股票{symbol}'],
                        'trade_date': [start_date.strftime('%Y-%m-%d')],
                        'open': [0.0],
                        'high': [0.0],
                        'low': [0.0],
                        'close': [0.0],
                        'volume': [0]
                    })
                    all_data.append(df)

            except Exception as e:
                st.warning(f"获取 {symbol} 数据失败: {str(e)}")

            progress_bar.progress((idx + 1) / len(symbols))
        
        status_text.text("数据获取完成，正在生成文件...")
        
        if all_data:
            # 合并所有数据
            combined_df = pd.concat(all_data, ignore_index=True)
            
            # 重新排列列顺序
            columns_order = ['symbol', 'name', 'trade_date', 'open', 'high', 'low', 'close', 'volume']
            if 'turnover' in combined_df.columns:
                columns_order.append('turnover')
            
            combined_df = combined_df[[col for col in columns_order if col in combined_df.columns]]
            
            # 重命名列
            column_names = {
                'symbol': '股票代码',
                'name': '股票名称',
                'trade_date': '日期',
                'open': '开盘价',
                'high': '最高价',
                'low': '最低价',
                'close': '收盘价',
                'volume': '成交量',
                'turnover': '成交额'
            }
            combined_df = combined_df.rename(columns=column_names)
            
            # 生成文件
            filename = f"股票历史数据_{start_date_str}_{end_date_str}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            if export_format == "CSV":
                csv_data = combined_df.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="📥 下载CSV文件",
                    data=csv_data,
                    file_name=f"{filename}.csv",
                    mime="text/csv"
                )
            
            elif export_format == "Excel":
                if EXCEL_SUPPORT:
                    excel_buffer = io.BytesIO()
                    try:
                        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                            combined_df.to_excel(writer, sheet_name='股票数据', index=False)

                            # 添加汇总信息
                            summary_df = pd.DataFrame({
                                '导出信息': ['导出时间', '数据范围', '股票数量', '记录总数'],
                                '值': [
                                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                    f"{start_date} 至 {end_date}",
                                    len(symbols),
                                    len(combined_df)
                                ]
                            })
                            summary_df.to_excel(writer, sheet_name='导出信息', index=False)

                        excel_data = excel_buffer.getvalue()
                        st.download_button(
                            label="📥 下载Excel文件",
                            data=excel_data,
                            file_name=f"{filename}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                    except Exception as e:
                        st.error(f"Excel导出失败: {e}")
                        st.info("请尝试使用CSV格式")
                        return
                else:
                    st.error("Excel导出需要安装openpyxl库，请使用CSV格式")
                    return
            
            # 显示预览
            st.success(f"✅ 导出完成！共 {len(combined_df)} 条记录")
            
            st.markdown("### 📊 数据预览")
            st.dataframe(combined_df.head(10), use_container_width=True)
            
            # 保存导出记录
            save_export_record("股票历史数据", len(symbols), len(combined_df), export_format)
        
        else:
            st.error("❌ 未获取到任何数据")
    
    except Exception as e:
        st.error(f"导出失败: {str(e)}")
        import traceback
        st.code(traceback.format_exc())

def export_asset_info(symbols, export_format, services):
    """导出资产信息"""

    try:
        mode = services.get('mode', 'unknown')
        asset_data = []

        # 进度条
        progress_bar = st.progress(0)
        status_text = st.empty()

        for idx, symbol in enumerate(symbols):
            status_text.text(f"正在获取 {symbol} 的资产信息...")

            try:
                if mode == 'full':
                    # 完整模式：使用asset_service
                    asset_info, metadata = services['asset_service'].get_or_create_asset(symbol)

                    if asset_info:
                        asset_dict = {
                            'symbol': asset_info.symbol,
                            'name': asset_info.name,
                            'asset_type': asset_info.asset_type,
                            'exchange': asset_info.exchange,
                            'industry': asset_info.industry,
                            'data_source': asset_info.data_source,
                            'last_updated': asset_info.last_updated.strftime('%Y-%m-%d %H:%M:%S') if asset_info.last_updated else None
                        }
                        asset_data.append(asset_dict)

                elif mode == 'cloud':
                    # 云端模式：直接查询SQLite数据库
                    import sqlite3
                    conn = sqlite3.connect(services['db_path'])

                    query = """
                    SELECT symbol, name, asset_type, exchange, industry, data_source, last_updated
                    FROM assets
                    WHERE symbol = ?
                    """

                    cursor = conn.cursor()
                    cursor.execute(query, (symbol,))
                    result = cursor.fetchone()

                    if result:
                        asset_dict = {
                            'symbol': result[0],
                            'name': result[1],
                            'asset_type': result[2],
                            'exchange': result[3],
                            'industry': result[4],
                            'data_source': result[5],
                            'last_updated': result[6]
                        }
                        asset_data.append(asset_dict)

                    conn.close()

                else:
                    # 最小模式：创建基本信息
                    asset_dict = {
                        'symbol': symbol,
                        'name': f'股票{symbol}',
                        'asset_type': '股票',
                        'exchange': 'N/A',
                        'industry': 'N/A',
                        'data_source': 'N/A',
                        'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    asset_data.append(asset_dict)

            except Exception as e:
                st.warning(f"获取 {symbol} 资产信息失败: {str(e)}")

            progress_bar.progress((idx + 1) / len(symbols))

        status_text.text("数据获取完成，正在生成文件...")

        if asset_data:
            df = pd.DataFrame(asset_data)

            # 重命名列
            column_names = {
                'symbol': '股票代码',
                'name': '股票名称',
                'asset_type': '资产类型',
                'exchange': '交易所',
                'industry': '行业',
                'data_source': '数据来源',
                'last_updated': '最后更新时间'
            }

            # 只保留存在的列
            df = df.rename(columns={k: v for k, v in column_names.items() if k in df.columns})

            # 生成文件
            filename = f"资产信息_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            if export_format == "CSV":
                csv_data = df.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="📥 下载CSV文件",
                    data=csv_data,
                    file_name=f"{filename}.csv",
                    mime="text/csv"
                )

            elif export_format == "Excel":
                if EXCEL_SUPPORT:
                    excel_buffer = io.BytesIO()
                    try:
                        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                            df.to_excel(writer, sheet_name='资产信息', index=False)

                        excel_data = excel_buffer.getvalue()
                        st.download_button(
                            label="📥 下载Excel文件",
                            data=excel_data,
                            file_name=f"{filename}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                    except Exception as e:
                        st.error(f"Excel导出失败: {e}")
                        st.info("请尝试使用CSV格式")
                        return
                else:
                    st.error("Excel导出需要安装openpyxl库，请使用CSV格式")
                    return

            # 显示预览
            st.success(f"✅ 导出完成！共 {len(df)} 条记录")

            st.markdown("### 📊 数据预览")
            st.dataframe(df, use_container_width=True)

            # 保存导出记录
            save_export_record("资产信息", len(symbols), len(df), export_format)

        else:
            st.error("❌ 未获取到任何资产信息")

    except Exception as e:
        st.error(f"导出失败: {str(e)}")

def export_watchlist(export_format):
    """导出自选股列表"""

    try:
        # 加载自选股数据
        watchlist_file = current_dir / "data" / "watchlist.json"

        if watchlist_file.exists():
            with open(watchlist_file, 'r', encoding='utf-8') as f:
                watchlist = json.load(f)
        else:
            watchlist = {}

        if watchlist:
            # 转换为DataFrame
            data = []
            for symbol, info in watchlist.items():
                data.append({
                    '股票代码': symbol,
                    '股票名称': info['name'],
                    '添加日期': info['added_date']
                })

            df = pd.DataFrame(data)

            # 生成文件
            filename = f"自选股列表_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            if export_format == "CSV":
                csv_data = df.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="📥 下载CSV文件",
                    data=csv_data,
                    file_name=f"{filename}.csv",
                    mime="text/csv"
                )

            elif export_format == "Excel":
                if EXCEL_SUPPORT:
                    excel_buffer = io.BytesIO()
                    try:
                        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                            df.to_excel(writer, sheet_name='自选股', index=False)

                        excel_data = excel_buffer.getvalue()
                        st.download_button(
                            label="📥 下载Excel文件",
                            data=excel_data,
                            file_name=f"{filename}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                    except Exception as e:
                        st.error(f"Excel导出失败: {e}")
                        st.info("请尝试使用CSV格式")
                        return
                else:
                    st.error("Excel导出需要安装openpyxl库，请使用CSV格式")
                    return

            # 显示预览
            st.success(f"✅ 导出完成！共 {len(df)} 只自选股")

            st.markdown("### 📊 数据预览")
            st.dataframe(df, use_container_width=True)

            # 保存导出记录
            save_export_record("自选股列表", 1, len(df), export_format)

        else:
            st.info("暂无自选股数据可导出")

    except Exception as e:
        st.error(f"导出失败: {str(e)}")

def save_export_record(data_type, symbol_count, record_count, export_format):
    """保存导出记录"""
    try:
        export_history_file = current_dir / "data" / "export_history.json"

        # 加载现有记录
        if export_history_file.exists():
            with open(export_history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
        else:
            history = []

        # 添加新记录
        new_record = {
            "timestamp": datetime.now().isoformat(),
            "data_type": data_type,
            "symbol_count": symbol_count,
            "record_count": record_count,
            "export_format": export_format
        }

        history.append(new_record)

        # 只保留最近50条记录
        history = history[-50:]

        # 保存记录
        export_history_file.parent.mkdir(exist_ok=True)
        with open(export_history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)

    except Exception as e:
        st.warning(f"保存导出记录失败: {str(e)}")

def display_export_history():
    """显示导出历史"""
    try:
        export_history_file = current_dir / "data" / "export_history.json"

        if export_history_file.exists():
            with open(export_history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)

            if history:
                # 转换为DataFrame
                df = pd.DataFrame(history)
                df['timestamp'] = pd.to_datetime(df['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')

                # 重命名列
                df = df.rename(columns={
                    'timestamp': '导出时间',
                    'data_type': '数据类型',
                    'symbol_count': '股票数量',
                    'record_count': '记录数量',
                    'export_format': '导出格式'
                })

                # 按时间倒序排列
                df = df.sort_values('导出时间', ascending=False)

                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("暂无导出历史")
        else:
            st.info("暂无导出历史")

    except Exception as e:
        st.error(f"加载导出历史失败: {str(e)}")

if __name__ == "__main__":
    main()
