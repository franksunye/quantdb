# src/database.py

import sqlite3
from src.config import DATABASE_PATH

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
    
import sqlite3
import pandas as pd

def insert_into_assets_and_index(df: pd.DataFrame, index_name: str, conn):
    cursor = conn.cursor()
    
    for _, row in df.iterrows():
        # 先插入到 assets 表
        cursor.execute('''
            INSERT OR IGNORE INTO assets (symbol, name, asset_type, exchange, currency) 
            VALUES (?, ?, ?, ?, ?)
            ''', (row['symbol'], row['name'], 'stock', '沪深', 'CNY'))  # 假设交易所为 '沪深', 货币为 'CNY'
        
        # 获取 asset_id
        cursor.execute('''
            SELECT asset_id FROM assets WHERE symbol=?
            ''', (row['symbol'],))
        asset_id = cursor.fetchone()[0]
        
        # 插入到 index_constituents 表
        cursor.execute('''
            INSERT INTO index_constituents (index_name, asset_id, inclusion_date) 
            VALUES (?, ?, ?)
            ''', (index_name, asset_id, row['inclusion_date']))
    
    conn.commit()


