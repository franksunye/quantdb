#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
QuantDB数据迁移工具 - SQLite到Supabase
用于将本地SQLite数据库中的数据迁移到Supabase PostgreSQL数据库
"""

import os
import sys
import json
import uuid
import logging
import sqlite3
import psycopg2
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime
from psycopg2.extras import execute_values

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("supabase_migration")

# 从.env文件加载环境变量
load_dotenv()

# 获取Supabase配置
SUPABASE_DB_HOST = os.getenv('SUPABASE_DB_HOST', 'aws-0-us-west-1.pooler.supabase.com')
SUPABASE_DB_PORT = os.getenv('SUPABASE_DB_PORT', '6543')  # Transaction Pooler端口
SUPABASE_DB_NAME = os.getenv('SUPABASE_DB_NAME', 'postgres')
SUPABASE_DB_USER = os.getenv('SUPABASE_DB_USER', 'postgres.dvusiqfijdmjcsubyapw')
SUPABASE_DB_PASSWORD = os.getenv('SUPABASE_DB_PASSWORD')
SUPABASE_SSL_CERT = os.getenv('SUPABASE_SSL_CERT', 'prod-ca-2021.crt')

# SQLite数据库路径
SQLITE_DB_PATH = os.getenv('SQLITE_DB_PATH', 'database/stock_data.db')

# 批量插入的大小
BATCH_SIZE = 1000

def connect_to_sqlite():
    """连接到SQLite数据库"""
    try:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        conn.row_factory = sqlite3.Row  # 使结果可以通过列名访问
        logger.info(f"成功连接到SQLite数据库: {SQLITE_DB_PATH}")
        return conn
    except Exception as e:
        logger.error(f"连接SQLite数据库失败: {e}")
        sys.exit(1)

def connect_to_supabase():
    """连接到Supabase PostgreSQL数据库"""
    try:
        # 构建连接参数
        conn_params = {
            'host': SUPABASE_DB_HOST,
            'port': SUPABASE_DB_PORT,
            'dbname': SUPABASE_DB_NAME,
            'user': SUPABASE_DB_USER,
            'password': SUPABASE_DB_PASSWORD,
            'sslmode': 'verify-full',
            'sslrootcert': SUPABASE_SSL_CERT
        }
        
        # 连接到数据库
        conn = psycopg2.connect(**conn_params)
        logger.info(f"成功连接到Supabase PostgreSQL数据库: {SUPABASE_DB_HOST}")
        return conn
    except Exception as e:
        logger.error(f"连接Supabase数据库失败: {e}")
        sys.exit(1)

def migrate_assets(sqlite_conn, pg_conn):
    """迁移assets表数据"""
    logger.info("开始迁移assets表数据...")
    
    # 从SQLite读取数据
    cursor = sqlite_conn.cursor()
    cursor.execute("SELECT * FROM assets")
    assets = cursor.fetchall()
    
    if not assets:
        logger.warning("assets表中没有数据")
        return
    
    logger.info(f"从SQLite读取了{len(assets)}条assets记录")
    
    # 准备插入PostgreSQL
    pg_cursor = pg_conn.cursor()
    
    # 清空目标表（如果需要）
    pg_cursor.execute("TRUNCATE TABLE assets CASCADE")
    
    # 准备批量插入数据
    asset_data = []
    for asset in assets:
        asset_data.append((
            str(uuid.uuid4()),  # 生成新的UUID
            asset['symbol'],
            asset['name'],
            asset['isin'],
            asset['asset_type'],
            asset['exchange'],
            asset['currency'],
            datetime.now(),
            datetime.now()
        ))
    
    # 执行批量插入
    insert_query = """
    INSERT INTO assets (asset_id, symbol, name, isin, asset_type, exchange, currency, created_at, updated_at)
    VALUES %s
    RETURNING asset_id, symbol
    """
    
    # 使用execute_values进行批量插入
    from psycopg2.extras import execute_values
    results = execute_values(pg_cursor, insert_query, asset_data, fetch=True)
    
    # 创建asset_id映射表（SQLite ID -> Supabase UUID）
    asset_id_map = {}
    for i, result in enumerate(results):
        supabase_id = result[0]
        symbol = result[1]
        sqlite_id = assets[i]['asset_id']
        asset_id_map[sqlite_id] = supabase_id
    
    # 保存asset_id映射表，用于后续表的迁移
    with open('asset_id_map.json', 'w') as f:
        json.dump(asset_id_map, f)
    
    pg_conn.commit()
    logger.info(f"成功迁移{len(asset_data)}条assets记录到Supabase")
    
    return asset_id_map

def migrate_daily_stock_data(sqlite_conn, pg_conn, asset_id_map):
    """迁移daily_stock_data表数据"""
    logger.info("开始迁移daily_stock_data表数据...")
    
    # 从SQLite读取数据
    cursor = sqlite_conn.cursor()
    cursor.execute("SELECT * FROM daily_stock_data")
    stock_data = cursor.fetchall()
    
    if not stock_data:
        logger.warning("daily_stock_data表中没有数据")
        return
    
    logger.info(f"从SQLite读取了{len(stock_data)}条daily_stock_data记录")
    
    # 准备插入PostgreSQL
    pg_cursor = pg_conn.cursor()
    
    # 清空目标表（如果需要）
    pg_cursor.execute("TRUNCATE TABLE daily_stock_data")
    
    # 分批处理数据
    total_records = len(stock_data)
    processed_records = 0
    
    for i in range(0, total_records, BATCH_SIZE):
        batch = stock_data[i:i+BATCH_SIZE]
        batch_data = []
        
        for record in batch:
            sqlite_asset_id = record['asset_id']
            if sqlite_asset_id not in asset_id_map:
                logger.warning(f"找不到asset_id {sqlite_asset_id}的映射，跳过此记录")
                continue
                
            supabase_asset_id = asset_id_map[sqlite_asset_id]
            
            batch_data.append((
                str(uuid.uuid4()),  # 生成新的UUID
                supabase_asset_id,
                record['trade_date'],
                record['open'],
                record['high'],
                record['low'],
                record['close'],
                record['volume'],
                record['turnover'],
                record['amplitude'],
                record['pct_change'],
                record['change'],
                record['turnover_rate'],
                datetime.now(),
                datetime.now()
            ))
        
        # 执行批量插入
        insert_query = """
        INSERT INTO daily_stock_data (
            id, asset_id, trade_date, open, high, low, close, volume, 
            turnover, amplitude, pct_change, change, turnover_rate, created_at, updated_at
        )
        VALUES %s
        """
        
        execute_values(pg_cursor, insert_query, batch_data)
        processed_records += len(batch_data)
        logger.info(f"已处理 {processed_records}/{total_records} 条记录")
    
    pg_conn.commit()
    logger.info(f"成功迁移{processed_records}条daily_stock_data记录到Supabase")

def main():
    """主函数"""
    logger.info("开始数据迁移过程...")
    
    # 连接数据库
    sqlite_conn = connect_to_sqlite()
    pg_conn = connect_to_supabase()
    
    try:
        # 迁移assets表
        asset_id_map = migrate_assets(sqlite_conn, pg_conn)
        
        # 迁移daily_stock_data表
        migrate_daily_stock_data(sqlite_conn, pg_conn, asset_id_map)
        
        # 可以继续添加其他表的迁移
        
        logger.info("数据迁移完成")
    except Exception as e:
        logger.error(f"迁移过程中出错: {e}")
        pg_conn.rollback()
    finally:
        # 关闭连接
        sqlite_conn.close()
        pg_conn.close()

if __name__ == "__main__":
    main()
