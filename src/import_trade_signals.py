# src\import_trade_signals.py
import sqlite3
import csv
import json
from datetime import datetime
from src.logger import logger
from src.config import DATABASE_PATH

def get_asset_id(conn, stock_code):
    cursor = conn.cursor()
    cursor.execute("SELECT asset_id FROM assets WHERE symbol = ?", (stock_code,))
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

def signal_exists(conn, asset_id, strategy_id, signal_date, signal_type):
    cursor = conn.cursor()
    cursor.execute('''
        SELECT 1 FROM trade_signals 
        WHERE asset_id = ? AND strategy_id = ? AND signal_date = ? AND signal_type = ?
    ''', (asset_id, strategy_id, signal_date, signal_type))
    return cursor.fetchone() is not None

def extract_macd_params(strategy_value):
    # 提取最优参数的第一部分，例如 "13-16-10"
    return strategy_value.split(' | ')[0]

def extract_notes(strategy_value):
    # 提取 strategy_value 的后续部分作为 notes
    return ' | '.join(strategy_value.split(' | ')[1:])

def import_signals_from_csv(csv_filename):
    # 连接到数据库
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # 读取 CSV 文件
    with open(csv_filename, 'r', encoding='utf-8-sig') as file:
        reader = csv.DictReader(file)
        for row in reader:
            try:
                # 补齐 stock_code 至6位
                stock_code = row['stock_code'].zfill(6)

                # 查找资产ID
                asset_id = get_asset_id(conn, stock_code)
                if asset_id is None:
                    logger.warning(f"股票代码 {stock_code} 在数据库中未找到")
                    continue

                # 获取策略ID
                strategy_name = row['best_strategy']
                strategy_id = get_strategy_id(conn, strategy_name)

                # 解析日期
                signal_date = datetime.strptime(row['date'], "%Y-%m-%d").date()

                # 解析其他字段
                signal_type = row['action'].upper()
                price_at_signal = float(row['price'])
                suggested_quantity = int(row['size'])
                signal_sent = row['notification'] == 'Y'
                
                optimal_result = json.dumps({
                    "strategy_value": row['strategy_value'].split(' | ')[0],  # 提取 strategy_value 的第一段
                    "return_ratio": row['return_ratio'],
                    "win_rate": row['win_rate'],
                    "profit_loss_ratio": row['profit_loss_ratio']
                })

                notes = row['strategy_value'].split(' | ', 1)[1] if ' | ' in row['strategy_value'] else ""

                # 检查信号是否已经存在
                if signal_exists(conn, asset_id, strategy_id, signal_date, signal_type):
                    logger.info(f"信号 {signal_date} {signal_type} 已存在，跳过插入")
                    continue

                # 插入信号到数据库
                cursor.execute('''
                    INSERT INTO trade_signals 
                    (strategy_id, asset_id, signal_date, signal_type, signal_strength, notes, signal_sent, price_at_signal, suggested_quantity, optimal_result) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    strategy_id,
                    asset_id,
                    signal_date,
                    signal_type,
                    None,  # 如果有 signal_strength 字段，将其替换
                    notes,
                    signal_sent,
                    price_at_signal,
                    suggested_quantity,
                    optimal_result
                ))

            except Exception as e:
                logger.error(f"处理信号时发生错误: {e}")

    conn.commit()
    conn.close()
    logger.info("信号导入完成")

# 调用函数导入信号
# 直接使用绝对路径
csv_filename = r'C:\cygwin64\home\frank\QuantAgent\result\trade_signals.csv'

import_signals_from_csv(csv_filename)
