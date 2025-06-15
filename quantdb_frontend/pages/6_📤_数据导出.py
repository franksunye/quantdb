"""
数据导出页面

提供股票数据的导出功能，支持CSV、Excel格式，可自定义导出范围和格式。
"""

import streamlit as st
import pandas as pd
import io
from datetime import datetime, date, timedelta
import sys
import os

# 添加项目路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from utils.api_client import get_api_client, QuantDBAPIError, format_date_for_api
from utils.config import config

# 页面配置
st.set_page_config(
    page_title="数据导出 - QuantDB",
    page_icon="📤",
    layout="wide"
)

def main():
    """主页面函数"""
    
    # 页面标题
    st.title("📤 数据导出")
    st.markdown("---")
    
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
            symbols = [config.normalize_symbol(s) for s in symbols if config.validate_symbol(s)]
            
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
                export_stock_data(symbols, start_date, end_date, export_format)
            else:
                st.error("请检查股票代码和日期范围")
        
        elif export_type == "资产信息":
            if symbols:
                export_asset_info(symbols, export_format)
            else:
                st.error("请输入有效的股票代码")
        
        elif export_type == "自选股列表":
            export_watchlist(export_format)
    
    # 导出历史
    st.markdown("---")
    st.subheader("📁 导出历史")
    display_export_history()

def export_stock_data(symbols, start_date, end_date, export_format):
    """导出股票历史数据"""
    
    try:
        client = get_api_client()
        
        start_date_str = format_date_for_api(start_date)
        end_date_str = format_date_for_api(end_date)
        
        all_data = []
        
        # 进度条
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for idx, symbol in enumerate(symbols):
            status_text.text(f"正在获取 {symbol} 的数据...")
            
            try:
                # 获取股票数据
                stock_data = client.get_stock_data(symbol, start_date_str, end_date_str)
                
                if stock_data and 'data' in stock_data:
                    df = pd.DataFrame(stock_data['data'])
                    df['symbol'] = symbol
                    
                    # 获取股票名称
                    try:
                        asset_info = client.get_asset_info(symbol)
                        stock_name = asset_info.get('name', f'股票{symbol}') if asset_info else f'股票{symbol}'
                        df['name'] = stock_name
                    except:
                        df['name'] = f'股票{symbol}'
                    
                    all_data.append(df)
                
            except Exception as e:
                st.warning(f"获取 {symbol} 数据失败: {str(e)}")
            
            progress_bar.progress((idx + 1) / len(symbols))
        
        status_text.text("数据获取完成，正在生成文件...")
        
        if all_data:
            # 合并所有数据
            combined_df = pd.concat(all_data, ignore_index=True)
            
            # 重新排列列顺序
            columns_order = ['symbol', 'name', 'date', 'open', 'high', 'low', 'close', 'volume']
            if 'amount' in combined_df.columns:
                columns_order.append('amount')
            
            combined_df = combined_df[[col for col in columns_order if col in combined_df.columns]]
            
            # 重命名列
            column_names = {
                'symbol': '股票代码',
                'name': '股票名称',
                'date': '日期',
                'open': '开盘价',
                'high': '最高价',
                'low': '最低价',
                'close': '收盘价',
                'volume': '成交量',
                'amount': '成交额'
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
                excel_buffer = io.BytesIO()
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

def export_asset_info(symbols, export_format):
    """导出资产信息"""
    
    try:
        client = get_api_client()
        
        asset_data = []
        
        # 进度条
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for idx, symbol in enumerate(symbols):
            status_text.text(f"正在获取 {symbol} 的资产信息...")
            
            try:
                asset_info = client.get_asset_info(symbol)
                
                if asset_info:
                    asset_data.append(asset_info)
                
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
                'concept': '概念',
                'area': '地区',
                'market': '市场',
                'list_date': '上市日期',
                'pe_ratio': '市盈率',
                'pb_ratio': '市净率',
                'roe': '净资产收益率',
                'market_cap': '总市值',
                'total_share': '总股本',
                'float_share': '流通股本',
                'eps': '每股收益',
                'bps': '每股净资产'
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
                excel_buffer = io.BytesIO()
                with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                    df.to_excel(writer, sheet_name='资产信息', index=False)
                
                excel_data = excel_buffer.getvalue()
                st.download_button(
                    label="📥 下载Excel文件",
                    data=excel_data,
                    file_name=f"{filename}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            
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
        watchlist_file = os.path.join(os.path.dirname(__file__), "..", "data", "watchlist.json")
        
        if os.path.exists(watchlist_file):
            import json
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
                excel_buffer = io.BytesIO()
                with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                    df.to_excel(writer, sheet_name='自选股', index=False)
                
                excel_data = excel_buffer.getvalue()
                st.download_button(
                    label="📥 下载Excel文件",
                    data=excel_data,
                    file_name=f"{filename}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            
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
        export_history_file = os.path.join(os.path.dirname(__file__), "..", "data", "export_history.json")
        
        # 加载现有记录
        if os.path.exists(export_history_file):
            import json
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
        os.makedirs(os.path.dirname(export_history_file), exist_ok=True)
        import json
        with open(export_history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    
    except Exception as e:
        st.warning(f"保存导出记录失败: {str(e)}")

def display_export_history():
    """显示导出历史"""
    try:
        export_history_file = os.path.join(os.path.dirname(__file__), "..", "data", "export_history.json")
        
        if os.path.exists(export_history_file):
            import json
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
