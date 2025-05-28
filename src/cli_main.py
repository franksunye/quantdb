import sqlite3
import argparse
from src.logger import logger
from src.updater import *
from src.downloader import download_and_save_all_stocks
        
def main():
    parser = argparse.ArgumentParser(description="股票和指数数据管理")
    parser.add_argument("--mode", choices=["index", "stock", "update_stock", "update_index", "all_stocks", "intraday_update"], required=True,
                        help="选择操作模式: 'index' 下载指数数据, 'stock' 下载股票日数据, 'update_stock' 更新股票日数据, 'update_index' 更新指数数据, 'all_stocks' 下载所有沪深股票信息, 'intraday_update' 更新当天股票实时数据")
    parser.add_argument("--symbols", nargs='+', help="指定股票代码列表，仅在 'stock', 'update_stock', 和 'intraday_update' 模式下使用")
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
    elif args.mode == "all_stocks":
        download_and_save_all_stocks(conn)
    elif args.mode == "intraday_update":
        handle_intraday_stock_update(args.symbols, conn)
    
    conn.close()
    logger.info("数据库连接已关闭")

if __name__ == "__main__":
    main()
