# src/updater.py
import akshare as ak
import pandas as pd
import sqlite3
from src.logger import logger
from datetime import datetime, time, timedelta

from src.logger import logger
from src.config import DATABASE_PATH, INDICES
from src.api.database import get_last_trade_date, get_all_stock_symbols
from src.downloader import *

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

def handle_stock_data(symbols, update_only=False, conn=None):
    # 如果没有指定股票编码，则从数据库中获取所有股票编码
    if not symbols:
        logger.info("未指定股票编码，从数据库中获取所有股票编码...")
        symbols = get_all_stock_symbols(conn)
        if not symbols:
            logger.error("未找到任何股票编码")
            return

    # 处理股票日数据的下载和更新
    for symbol in symbols:
        if update_only:
            update_stock_data(symbol)
        else:
            download_and_save_stock_data(symbol)
            
def handle_index_data_update(index_codes, conn, start_date=None):
    for index_code in index_codes:
        update_index_data(index_code, start_date)

def handle_index_data(conn):
    for index in INDICES:
        download_index(index["code"], index["name"], index["csv"], conn)
        
def handle_intraday_stock_update(symbols, conn):
    """处理每日股票数据更新"""
    if not is_market_closed():
        logger.info("市场尚未闭市，每日股票数据更新操作跳过")
        return

    if symbols:
        for symbol in symbols:
            download_and_save_intraday_stock_data(conn, symbol)
    else:
        download_and_save_intraday_stock_data(conn)
        
if __name__ == "__main__":
    # Example usage
    update_stock_data("000001")  # Update stock data
    update_index_data("sh000300")  # Update Shanghai Composite Index data