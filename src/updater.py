# src/updater.py
import akshare as ak
import pandas as pd
import sqlite3
import logging
from datetime import datetime, time, timedelta

from src.database import insert_daily_stock_data, get_asset_id, get_last_trade_date, get_all_stock_symbols
from src.logger import logger
from src.config import DATABASE_PATH

logger = logging.getLogger('quantdb')

def download_and_save_stock_data(symbol, start_date=None):
    """下载并保存股票的日数据"""
    try:
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

def is_market_closed():
    """判断当前时间是否处于闭市时间"""
    now = datetime.now().time()
    market_close_time = time(15, 0)  # 假设市场在下午3点闭市
    return now >= market_close_time

def update_stock_data(symbol):
    """更新指定股票的日数据"""
    try:
        logger.info(f"开始更新 {symbol} 的数据")
        logger.info(f"当前时间：{datetime.now()}")
                
        conn = sqlite3.connect(DATABASE_PATH)
        
        last_date = get_last_trade_date(conn, symbol)
        logger.info(f"上次交易日期：{last_date}")
        
        if last_date:
            start_date = (last_date + timedelta(days=1)).strftime('%Y%m%d')
            logger.info(f"使用上次交易日期作为起始日期：{start_date}")            
        else:
            # 如果没有数据，更新从默认的起始日期开始
            start_date = '20230101'
            logger.info(f"无上次交易记录，使用默认起始日期：{start_date}")

        # 获取今天的日期
        today = datetime.now().date()
        logger.info(f"今天的日期：{today}")

        # 将起始日期转化为date对象
        start_date_obj = datetime.strptime(start_date, '%Y%m%d').date()
        logger.info(f"起始日期（date格式）：{start_date_obj}")

        # 如果起始日期是今天，并且市场尚未闭市，则跳过更新
        if start_date_obj == today and not is_market_closed():
            logger.info(f"市场尚未闭市，跳过 {symbol} 今天的数据更新")
            conn.close()
            return

        logger.info(f"开始更新 {symbol} 数据，起始日期: {start_date}")
        download_and_save_stock_data(symbol, start_date)
        
        conn.close()
        logger.info(f"{symbol} 的数据更新完成")
    
    except Exception as e:
        logger.error(f"更新股票 {symbol} 的数据时发生错误: {e}")
        
def update_index_data(index_code, start_date=None):
    """更新指定指数的日数据"""
    try:
        logger.info(f"开始更新 {index_code} 的数据")
        logger.info(f"当前时间：{datetime.now()}")

        conn = sqlite3.connect(DATABASE_PATH)
        
        if start_date is None:
            last_date = get_last_trade_date(conn, index_code)
            logger.info(f"上次交易日期：{last_date}")

            if last_date:
                start_date = (last_date + timedelta(days=1)).strftime('%Y%m%d')
                logger.info(f"使用上次交易日期作为起始日期：{start_date}")
            else:
                # 如果没有数据，更新从默认的起始日期开始
                start_date = '20230101'
                logger.info(f"无上次交易记录，使用默认起始日期：{start_date}")
        else:
            logger.info(f"使用指定的起始日期：{start_date}")
        
        # 获取今天的日期
        today = datetime.now().date()
        logger.info(f"今天的日期：{today}")

        # 将起始日期转化为date对象
        start_date_obj = datetime.strptime(start_date, '%Y%m%d').date()
        logger.info(f"起始日期（date格式）：{start_date_obj}")

        # 如果起始日期是今天，并且市场尚未闭市，则跳过更新
        if start_date_obj == today and not is_market_closed():
            logger.info(f"市场尚未闭市，跳过 {index_code} 今天的数据更新")
            conn.close()
            return
        
        logger.info(f"开始更新 {index_code} 指数数据，起始日期：{start_date}")
        download_and_save_index_data(index_code, start_date=start_date)
        
        conn.close()
        logger.info(f"{index_code} 指数数据更新完成")
    
    except Exception as e:
        logger.error(f"更新指数 {index_code} 的数据时发生错误: {e}")
        
    if __name__ == "__main__":
        # Example usage
        update_stock_data("000001")  # Update stock data
        update_index_data("sh000300")  # Update Shanghai Composite Index data