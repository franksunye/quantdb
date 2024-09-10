# src/database.py
import sqlite3
import pandas as pd
from src.config import DATABASE_PATH
from src.logger import logger

def initialize_database():
    """初始化数据库，创建表格"""
    with open('database/schema.sql', 'r', encoding='utf-8') as f:
        schema = f.read()

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.executescript(schema)
    conn.commit()
    conn.close()
    print("Database initialized.")

def insert_asset(symbol, name, isin, asset_type, exchange, currency):
    """插入一条资产记录"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO ASSETS (symbol, name, isin, asset_type, exchange, currency)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (symbol, name, isin, asset_type, exchange, currency))
    conn.commit()
    conn.close()

def insert_into_assets_and_index(df: pd.DataFrame, index_name: str, conn):
    cursor = conn.cursor()
    
    for _, row in df.iterrows():
        # 插入或忽略资产记录（忽略重复）
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO assets (symbol, name, isin, asset_type, exchange, currency) 
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (row['symbol'], row['name'], row['symbol'], 'stock', '沪深', 'CNY'))
        except sqlite3.IntegrityError as e:
            logger.warning(f"资产 {row['symbol']} 已存在: {e}")

        # 获取 asset_id
        cursor.execute('''
            SELECT asset_id FROM assets WHERE symbol=?
        ''', (row['symbol'],))
        result = cursor.fetchone()
        if result is None:
            logger.error(f"无法找到资产ID: {row['symbol']}")
            continue
        asset_id = result[0]
        
        # 检查 index_constituents 表中是否已经存在相同记录
        cursor.execute('''
            SELECT 1 FROM index_constituents 
            WHERE index_name = ? AND asset_id = ? AND inclusion_date = ?
        ''', (index_name, asset_id, row['inclusion_date']))
        
        if cursor.fetchone() is None:
            # 插入到 index_constituents 表
            cursor.execute('''
                INSERT INTO index_constituents (index_name, asset_id, inclusion_date) 
                VALUES (?, ?, ?)
            ''', (index_name, asset_id, row['inclusion_date']))
        else:
            logger.info(f"Index constituent already exists: {index_name}, {asset_id}, {row['inclusion_date']}")
    
    conn.commit()

def get_asset_id(conn, symbol):
    """通过 symbol 获取 asset_id"""
    cursor = conn.cursor()
    cursor.execute("SELECT asset_id FROM assets WHERE symbol = ?", (symbol,))
    result = cursor.fetchone()
    return result[0] if result else None

def insert_daily_stock_data(conn, asset_id, trade_date, open_price, high_price, low_price, close_price, volume, turnover=None, amplitude=None, pct_change=None, change=None, turnover_rate=None):
    cursor = conn.cursor()
    try:
        # 检查是否已经存在相同日期和资产的记录
        cursor.execute("""
            SELECT COUNT(*)
            FROM daily_stock_data
            WHERE asset_id = ? AND trade_date = ?
        """, (asset_id, trade_date))
        
        # 如果记录已存在，则跳过插入
        if cursor.fetchone()[0] > 0:
            logger.warning(f"数据已存在，跳过插入: {asset_id} 在 {trade_date}")
            return

        # 如果记录不存在，则插入新数据
        cursor.execute("""
            INSERT INTO daily_stock_data (asset_id, trade_date, open, high, low, close, volume, turnover, amplitude, pct_change, change, turnover_rate)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (asset_id, trade_date, open_price, high_price, low_price, close_price, volume, turnover, amplitude, pct_change, change, turnover_rate))

        # 提交更改到数据库
        conn.commit()
        logger.info(f"成功插入数据: {asset_id} 在 {trade_date}")

    except sqlite3.Error as e:
        logger.error(f"插入数据时发生错误: {e}")

def get_all_stock_symbols(conn):
    """从 assets 表中获取所有股票的编码"""
    cursor = conn.cursor()
    cursor.execute("SELECT symbol FROM assets WHERE asset_type = 'stock'")
    results = cursor.fetchall()
    return [row[0] for row in results]

def get_last_trade_date(conn, symbol):
    """获取某只股票的最后交易日期"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT MAX(trade_date) FROM daily_stock_data
        WHERE asset_id = (SELECT asset_id FROM assets WHERE symbol = ?)
    """, (symbol,))
    result = cursor.fetchone()
    return pd.to_datetime(result[0]) if result[0] else None

def get_pending_signals(conn):
    """获取所有待发送的交易信号"""
    query = '''
    SELECT signal_id, strategy_id, asset_id, signal_date, signal_type, signal_strength, 
           price_at_signal, suggested_quantity, optimal_result, notes
    FROM trade_signals
    WHERE signal_sent = 0
    '''
    cursor = conn.cursor()
    cursor.execute(query)
    return cursor.fetchall()

def mark_signal_as_sent(conn, signal_id):
    """将信号标记为已发送"""
    query = '''
    UPDATE trade_signals
    SET signal_sent = 1
    WHERE signal_id = ?
    '''
    cursor = conn.cursor()
    cursor.execute(query, (signal_id,))
    conn.commit()
    
def fetch_signal_target():
    """获取信号的发送目标，例如Webhook URL"""
    # 你可以从配置文件或环境变量中获取
    return 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=4fbae71d-8d83-479f-a2db-7690eeb37a5c'

def get_signals_pending_plan(conn):
    """获取所有待生成计划的交易信号"""
    query = '''
    SELECT signal_id, strategy_id, asset_id, signal_date, signal_type, signal_strength, 
           price_at_signal, suggested_quantity, optimal_result, notes
    FROM trade_signals
    WHERE signal_sent = 1 AND plan_generated = 0
    '''
    cursor = conn.cursor()
    cursor.execute(query)
    return cursor.fetchall()

def mark_plan_as_generated(conn, signal_id):
    """将信号标记为已生成计划"""
    query = '''
    UPDATE trade_signals
    SET plan_generated = 1
    WHERE signal_id = ?
    '''
    cursor = conn.cursor()
    cursor.execute(query, (signal_id,))
    conn.commit()
