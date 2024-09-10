import sqlite3
import argparse
from src.database import initialize_database, insert_into_assets_and_index, get_all_stock_symbols, get_last_trade_date
from src.scheduler import start_scheduler
from src.downloader import download_index_data, save_raw_data, format_data_for_db
from src.updater import download_and_save_stock_data, update_stock_data,update_index_data
from src.logger import logger
from src.config import INDICES

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

def handle_index_data(conn):
    for index in INDICES:
        download_index(index["code"], index["name"], index["csv"], conn)

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
        
def main():
    parser = argparse.ArgumentParser(description="股票和指数数据管理")
    parser.add_argument("--mode", choices=["index", "stock", "update_stock", "update_index"], required=True, 
                        help="选择操作模式: 'index' 下载指数数据, 'stock' 下载股票日数据, 'update_stock' 更新股票日数据, 'update_index' 更新指数数据")
    parser.add_argument("--symbols", nargs='+', help="指定股票代码列表，仅在 'stock' 和 'update_stock' 模式下使用")
    parser.add_argument("--index_codes", nargs='+', help="指定指数代码列表，仅在 'index' 和 'update_index' 模式下使用")
    parser.add_argument("--start_date", help="指定更新的起始日期（格式YYYYMMDD），仅在 'update_index' 模式下使用")
    
    args = parser.parse_args()

    # 初始化数据库（如果尚未初始化）
    # if args.mode in ["index", "stock", "update_stock"]:
    #     # initialize_database()

    conn = sqlite3.connect('database/stock_data.db')

    if args.mode == "index":
        handle_index_data(conn)
    elif args.mode == "update_index":
        if args.start_date:
            start_date = args.start_date
        else:
            start_date = None
        handle_index_data_update([args.index_codes[0]], conn, start_date)
    elif args.mode in ["stock", "update_stock"]:
        handle_stock_data(args.symbols, update_only=(args.mode == "update_stock"), conn=conn)
    
    conn.close()
    logger.info("数据库连接已关闭")

if __name__ == "__main__":
    main()
