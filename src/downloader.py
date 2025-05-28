# src/downloader.py

import akshare as ak
import pandas as pd
import sqlite3
from datetime import datetime, time, timedelta

from src.logger import logger
from src.api.database import get_asset_id,insert_daily_stock_data, insert_into_assets_and_index
from src.config import DATABASE_PATH

def save_raw_data(data: pd.DataFrame, filename: str):
    """保存原始数据到文件"""
    file_path = f"{filename}.csv"
    data.to_csv(file_path, index=False)
    print(f"Data saved to {file_path}")

def format_data_for_db(data: pd.DataFrame) -> pd.DataFrame:
    """格式化数据以适应数据库的结构"""
    return data[['品种代码', '品种名称', '纳入日期']].rename(
        columns={'品种代码': 'symbol', '品种名称': 'name', '纳入日期': 'inclusion_date'})

def download_index_data(index_symbol: str) -> pd.DataFrame:
    """下载指数成分股数据"""
    # return ak.index_stock_cons(symbol=index_symbol)
    return ak.index_stock_cons_sina(symbol=index_symbol)

def download_and_save_all_stocks(conn: sqlite3.Connection):
    """下载所有沪深股票信息，并保存到数据库中的assets表"""
    try:
        # 下载所有沪深股票信息
        stock_data = ak.stock_info_a_code_name()
        logger.info("所有沪深股票信息下载成功")

        # 格式化数据
        formatted_data = stock_data.rename(columns={'code': 'symbol', 'name': 'name'})
        formatted_data['isin'] = formatted_data['symbol']
        formatted_data['asset_type'] = 'stock'
        formatted_data['exchange'] = '沪深'  # 
        formatted_data['currency'] = 'CNY'

        # 插入数据到数据库
        for index, row in formatted_data.iterrows():
            try:
                conn.execute('''
                    INSERT OR IGNORE INTO assets (symbol, name, isin, asset_type, exchange, currency) 
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (row['symbol'], row['name'], row['isin'], row['asset_type'], row['exchange'], row['currency']))
            except Exception as e:
                logger.error(f"插入股票 {row['symbol']} ({row['name']}) 时发生错误: {e}")

        conn.commit()
        logger.info("所有股票信息成功保存到数据库")

    except Exception as e:
        logger.error(f"下载或保存所有沪深股票信息时发生错误: {e}")
        
def download_and_save_stock_data(symbol, start_date=None):
    """下载并保存股票的日数据"""
    try:
        today = datetime.now()
        if start_date and pd.to_datetime(start_date) > today:
            logger.warning(f"Start date {start_date} is greater than today, no operation will be performed.")
            return
                
        # 下载股票日数据
        df = ak.stock_zh_a_hist(symbol=symbol, start_date=start_date, end_date=pd.to_datetime("today").strftime('%Y%m%d'))
        
        if df.empty:
            logger.warning(f"没有下载到数据: {symbol}")
            return

        # 确保所有必要字段都存在，缺失的字段用默认值补全
        required_columns = [
            '日期', '股票代码', '开盘', '收盘', '最高', '最低', 
            '成交量', '成交额', '振幅', '涨跌幅', '涨跌额', '换手率'
        ]

        for col in required_columns:
            if col not in df.columns:
                df[col] = pd.NA
        
        conn = sqlite3.connect(DATABASE_PATH)
        asset_id = get_asset_id(conn, symbol)
        
        if asset_id is None:
            logger.error(f"资产ID不存在: {symbol}")
            conn.close()
            return

        # 遍历 DataFrame 并插入数据到数据库
        for _, row in df.iterrows():
            insert_daily_stock_data(
                conn,
                asset_id,
                row['日期'],
                row['开盘'],
                row['最高'],
                row['最低'],
                row['收盘'],
                row['成交量'],
                row.get('成交额', pd.NA),
                row.get('振幅', pd.NA),
                row.get('涨跌幅', pd.NA),
                row.get('涨跌额', pd.NA),
                row.get('换手率', pd.NA)
            )
        
        conn.close()
        logger.info(f"{symbol} 的数据已成功插入数据库")
    
    except Exception as e:
        logger.error(f"处理股票 {symbol} 时发生错误: {e}")

def download_index(index_code, index_name, csv_filename, conn):
    logger.info(f"开始下载{index_name}数据...")
    
    try:
        # 下载指数数据
        index_data = download_index_data(index_code)
        index_df = format_data_for_db(index_data)
        logger.info(f"{index_name}数据下载成功")
        
        # 保存原始数据到CSV文件
        save_raw_data(index_data, f'data/raw/{csv_filename}')
        logger.info(f"{index_name}原始数据保存成功")
        
        # 插入数据到数据库
        insert_into_assets_and_index(index_df, index_name, conn)
        logger.info(f"{index_name}数据成功插入数据库")

    except Exception as e:
        logger.error(f"下载或插入{index_name}数据时发生错误: {e}")
        
def download_and_save_index_data(index_code, start_date=None):
    """下载并保存指数的日数据"""
    try:
        # Download index daily data
        df = ak.stock_zh_index_daily_em(symbol=index_code, start_date=start_date)
        
        if df.empty:
            logger.warning(f"没有下载到指数数据: {index_code}")
            return
        
        # Ensure all required columns exist, filling missing ones with default values
        required_columns = ['date', 'open', 'high', 'low', 'close', 'volume']
        
        for col in required_columns:
            if col not in df.columns:
                df[col] = pd.NA
        
        conn = sqlite3.connect(DATABASE_PATH)
        asset_id = get_asset_id(conn, index_code)
        
        if asset_id is None:
            logger.error(f"资产ID不存在: {index_code}")
            conn.close()
            return
        
        # Insert data into the database
        for _, row in df.iterrows():
            insert_daily_stock_data(
                conn,
                asset_id,
                row['date'],
                row['open'],
                row['high'],
                row['low'],
                row['close'],
                row['volume'],
                None,  # 成交额
                None,  # 振幅
                None,  # 涨跌幅
                None,  # 涨跌额
                None   # 换手率
            )
        
        conn.close()
        logger.info(f"{index_code} 指数数据已成功插入数据库")
    
    except Exception as e:
        logger.error(f"处理指数 {index_code} 时发生错误: {e}")
        
def download_and_save_intraday_stock_data(conn, symbol=None):
    """
    下载并保存股票当天的实时数据
    """
    try:
        logger.info(f"开始下载实时（SPOT）数据")

        # 如果 symbol 为 None，下载所有股票的实时数据
        if symbol is None:
            df = ak.stock_zh_a_spot_em()  # 下载所有股票的实时数据
        else:
            df = ak.stock_zh_a_spot_em().query(f'代码 == "{symbol}"')  # 只下载指定 symbol 的实时数据

        if df.empty:
            logger.warning("没有下载到实时数据")
            return

        for _, row in df.iterrows():
            asset_id = get_asset_id(conn, row['代码'])
            if asset_id is None:
                logger.error(f"资产ID不存在: {row['代码']}")
                continue

            # 将下载到的实时数据插入数据库
            insert_daily_stock_data(
                conn,
                asset_id,
                trade_date=datetime.now().strftime('%Y-%m-%d'),  # 今天的日期
                open_price=row['今开'],
                high_price=row['最高'],
                low_price=row['最低'],
                close_price=row['最新价'],
                volume=row['成交量'],
                turnover=row['成交额'],
                amplitude=row['振幅'],
                pct_change=row['涨跌幅'],
                change=row['涨跌额'],
                turnover_rate=row['换手率']
            )

        logger.info("实时数据插入完成")
    
    except Exception as e:
        logger.error(f"下载或保存实时数据时发生错误: {e}")