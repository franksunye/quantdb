# src\import_optimization_results.py
import sqlite3
import csv
import os
from datetime import datetime
from src.logger import logger
from src.config import DATABASE_PATH

def get_asset_id(conn, stock_code):
    cursor = conn.cursor()
    cursor.execute("SELECT asset_id FROM assets WHERE symbol = ?", (stock_code,))
    result = cursor.fetchone()
    return result[0] if result else None

def get_asset_name(conn, stock_code):
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM assets WHERE symbol = ?", (stock_code,))
    result = cursor.fetchone()
    return result[0] if result else None

def get_strategy_id(conn, strategy_name):
    cursor = conn.cursor()
    cursor.execute("SELECT strategy_id FROM strategies WHERE name = ?", (strategy_name,))
    result = cursor.fetchone()
    if result:
        return result[0]
    else:
        # 如果策略不存在，插入新的策略
        cursor.execute("INSERT INTO strategies (name) VALUES (?)", (strategy_name,))
        conn.commit()
        return cursor.lastrowid

def get_or_create_backtest_id(conn, stock_code, start_date, end_date, strategy_id):
    cursor = conn.cursor()
    cursor.execute('''
        SELECT backtest_id FROM backtests 
        WHERE asset_id = (SELECT asset_id FROM assets WHERE symbol = ?) 
        AND start_date = ? AND end_date = ?
    ''', (stock_code, start_date, end_date))
    result = cursor.fetchone()
    
    if result:
        logger.info(f"Found existing backtest record for {stock_code} from {start_date} to {end_date}.")
        return result[0]
    else:
        # 如果回测记录不存在，插入新的回测记录
        asset_id = get_asset_id(conn, stock_code)
        asset_name = get_asset_name(conn, stock_code)
        if asset_id is None or asset_name is None:
            logger.warning(f"股票代码 {stock_code} 在数据库中未找到，无法创建回测记录")
            return None
        
        # 默认填写的基础信息
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # 提供 created_at 字段
        cursor.execute('''
            INSERT INTO backtests 
            (strategy_id, asset_id, asset_name, symbol, start_date, end_date, created_at) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            strategy_id,
            asset_id,
            asset_name,
            stock_code,
            start_date,
            end_date,
            created_at  # 提供 created_at 字段
        ))
        conn.commit()
        logger.info(f"Created new backtest record for {stock_code} from {start_date} to {end_date}.")
        return cursor.lastrowid

def import_optimization_results_from_csv(csv_filename):
    logger.info(f"Starting import for file: {csv_filename}")
    
    # 连接到数据库
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # 解析文件名以获取股票代码和策略名称
    file_name = os.path.basename(csv_filename)
    stock_code, strategy_name = file_name.split('_')[0], file_name.split('_')[1].replace('filtered_strategy_results.csv', '')

    # 查找资产ID和策略ID
    asset_id = get_asset_id(conn, stock_code.zfill(6))
    if asset_id is None:
        logger.warning(f"股票代码 {stock_code} 在数据库中未找到")
        conn.close()
        return
    
    strategy_id = get_strategy_id(conn, strategy_name.upper())

    # 默认的时间范围（实际使用时应调整为具体时间范围）
    start_date = '2024-01-01'
    end_date = '2024-12-31'
    
    # 获取或创建回测ID
    backtest_id = get_or_create_backtest_id(conn, stock_code.zfill(6), start_date, end_date, strategy_id)
    if backtest_id is None:
        logger.warning(f"无法创建或找到回测记录 {stock_code}")
        conn.close()
        return

    logger.info(f"Processing optimization results for {stock_code} with strategy {strategy_name}.")

    # 读取 CSV 文件
    with open(csv_filename, 'r', encoding='utf-8-sig') as file:
        reader = csv.DictReader(file)
        row_count = 0
        for row in reader:
            try:
                # 提取参数和其他字段
                macd_params = f"{row.get('MACD1', 'N/A')}-{row.get('MACD2', 'N/A')}-{row.get('MACDSIG', 'N/A')}"
                optimal_value = macd_params
                indicator_type = 'MACD'  # 根据文件内容确定，示例为 MACD

                # 提取其他性能数据，使用默认值处理缺失数据
                final_value = float(row.get('Final Value', 0))
                num_trades = int(row.get('Num Trades', 0))
                win_rate = float(row.get('Win Rate', 0))
                profit_loss_ratio = float(row.get('Profit/Loss Ratio', 0))
                return_ratio = float(row.get('Return Ratio', 0))

                # 兼容缺失列
                sharpe_ratio = float(row.get('Sharpe Ratio', 0))
                max_drawdown = float(row.get('Max Drawdown', 0))

                created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                # 插入优化结果到数据库
                cursor.execute('''
                    INSERT INTO optimization_results 
                    (backtest_id, asset_id, asset_name, symbol, indicator_type, optimal_value, final_value, num_trades, win_rate, profit_loss_ratio, return_ratio, sharpe_ratio, max_drawdown, created_at) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    backtest_id,
                    asset_id,
                    get_asset_name(conn, stock_code.zfill(6)),
                    stock_code.zfill(6),
                    indicator_type,
                    optimal_value,
                    final_value,
                    num_trades,
                    win_rate,
                    profit_loss_ratio,
                    return_ratio,
                    sharpe_ratio,
                    max_drawdown,
                    created_at
                ))

                row_count += 1

            except Exception as e:
                logger.error(f"处理回测优化结果时发生错误: {e}")

    conn.commit()
    conn.close()
    logger.info(f"回测优化结果导入完成，共处理了 {row_count} 条记录。")

# 目录中的所有 CSV 文件
result_directory = r'C:\cygwin64\home\frank\QuantAgent\result'
for filename in os.listdir(result_directory):
    if filename.endswith('filtered_strategy_results.csv'):
        csv_file_path = os.path.join(result_directory, filename)
        import_optimization_results_from_csv(csv_file_path)
