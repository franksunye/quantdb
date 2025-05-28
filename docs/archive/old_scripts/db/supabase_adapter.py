#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Supabase数据库适配器
用于连接和操作Supabase PostgreSQL数据库
"""

import os
import logging
import psycopg2
import psycopg2.extras
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("supabase_adapter")

# 从.env文件加载环境变量
load_dotenv()

class SupabaseAdapter:
    """Supabase数据库适配器类"""

    def __init__(self):
        """初始化适配器"""
        # 获取Supabase配置
        self.db_host = os.getenv('SUPABASE_DB_HOST', 'aws-0-us-west-1.pooler.supabase.com')
        self.db_port = os.getenv('SUPABASE_DB_PORT', '6543')  # Transaction Pooler端口
        self.db_name = os.getenv('SUPABASE_DB_NAME', 'postgres')
        self.db_user = os.getenv('SUPABASE_DB_USER', 'postgres.dvusiqfijdmjcsubyapw')
        self.db_password = os.getenv('SUPABASE_DB_PASSWORD')
        self.ssl_cert = os.getenv('SUPABASE_SSL_CERT', 'prod-ca-2021.crt')

        # 连接池
        self.conn = None

    def connect(self):
        """连接到Supabase PostgreSQL数据库"""
        try:
            # 保存原始环境变量
            old_pgpassword = os.environ.get('PGPASSWORD', '')

            # 设置环境变量
            os.environ['PGPASSWORD'] = self.db_password

            try:
                # 构建连接字符串（与PowerShell脚本相同）
                conn_string = f"sslmode=verify-full sslrootcert={self.ssl_cert} host={self.db_host} port={self.db_port} dbname={self.db_name} user={self.db_user}"

                # 连接到数据库
                self.conn = psycopg2.connect(conn_string)
                logger.info(f"成功连接到Supabase PostgreSQL数据库: {self.db_host}")
                return True
            finally:
                # 恢复原始环境变量
                os.environ['PGPASSWORD'] = old_pgpassword
        except Exception as e:
            logger.error(f"连接Supabase数据库失败: {e}")
            return False

    def disconnect(self):
        """断开数据库连接"""
        if self.conn:
            self.conn.close()
            self.conn = None
            logger.info("已断开Supabase数据库连接")

    def execute_query(self, query, params=None):
        """执行SQL查询"""
        if not self.conn:
            if not self.connect():
                return None

        try:
            cursor = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cursor.execute(query, params)
            result = cursor.fetchall()
            cursor.close()
            return result
        except Exception as e:
            logger.error(f"执行查询失败: {e}")
            return None

    def execute_update(self, query, params=None):
        """执行SQL更新（INSERT, UPDATE, DELETE）"""
        if not self.conn:
            if not self.connect():
                return False

        try:
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            affected_rows = cursor.rowcount
            self.conn.commit()
            cursor.close()
            return affected_rows
        except Exception as e:
            logger.error(f"执行更新失败: {e}")
            self.conn.rollback()
            return 0

    def get_asset_by_symbol(self, symbol):
        """根据股票代码获取资产信息"""
        query = "SELECT * FROM assets WHERE symbol = %s"
        result = self.execute_query(query, (symbol,))
        if result and len(result) > 0:
            return dict(result[0])
        return None

    def get_stock_data(self, symbol, start_date=None, end_date=None):
        """获取股票历史数据"""
        # 获取资产ID
        asset = self.get_asset_by_symbol(symbol)
        if not asset:
            logger.warning(f"找不到股票代码为 {symbol} 的资产")
            return None

        asset_id = asset['asset_id']

        # 构建查询
        query = """
        SELECT d.* FROM daily_stock_data d
        WHERE d.asset_id = %s
        """
        params = [asset_id]

        if start_date:
            query += " AND d.trade_date >= %s"
            params.append(start_date)

        if end_date:
            query += " AND d.trade_date <= %s"
            params.append(end_date)

        query += " ORDER BY d.trade_date"

        # 执行查询
        result = self.execute_query(query, params)
        if not result:
            return None

        # 转换为DataFrame
        df = pd.DataFrame(result)
        return df

    def save_stock_data(self, symbol, data_df):
        """保存股票历史数据"""
        # 获取资产ID
        asset = self.get_asset_by_symbol(symbol)
        if not asset:
            logger.warning(f"找不到股票代码为 {symbol} 的资产")
            return False

        asset_id = asset['asset_id']

        # 准备插入数据
        success_count = 0
        for _, row in data_df.iterrows():
            # 检查记录是否已存在
            check_query = """
            SELECT id FROM daily_stock_data
            WHERE asset_id = %s AND trade_date = %s
            """
            existing = self.execute_query(check_query, (asset_id, row['trade_date']))

            if existing:
                # 更新现有记录
                update_query = """
                UPDATE daily_stock_data SET
                    open = %s,
                    high = %s,
                    low = %s,
                    close = %s,
                    volume = %s,
                    turnover = %s,
                    amplitude = %s,
                    pct_change = %s,
                    change = %s,
                    turnover_rate = %s,
                    updated_at = %s
                WHERE asset_id = %s AND trade_date = %s
                """
                params = (
                    row['open'], row['high'], row['low'], row['close'],
                    row['volume'], row.get('turnover', 0), row.get('amplitude', 0),
                    row.get('pct_change', 0), row.get('change', 0), row.get('turnover_rate', 0),
                    datetime.now(), asset_id, row['trade_date']
                )
                affected = self.execute_update(update_query, params)
            else:
                # 插入新记录
                insert_query = """
                INSERT INTO daily_stock_data (
                    id, asset_id, trade_date, open, high, low, close, volume,
                    turnover, amplitude, pct_change, change, turnover_rate,
                    created_at, updated_at
                ) VALUES (
                    gen_random_uuid(), %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s
                )
                """
                params = (
                    asset_id, row['trade_date'],
                    row['open'], row['high'], row['low'], row['close'], row['volume'],
                    row.get('turnover', 0), row.get('amplitude', 0),
                    row.get('pct_change', 0), row.get('change', 0), row.get('turnover_rate', 0),
                    datetime.now(), datetime.now()
                )
                affected = self.execute_update(insert_query, params)

            if affected > 0:
                success_count += 1

        logger.info(f"成功保存 {success_count}/{len(data_df)} 条股票数据记录")
        return success_count > 0

    def get_data_date_range(self, symbol):
        """获取股票数据的日期范围"""
        # 获取资产ID
        asset = self.get_asset_by_symbol(symbol)
        if not asset:
            logger.warning(f"找不到股票代码为 {symbol} 的资产")
            return None, None

        asset_id = asset['asset_id']

        # 查询最早和最晚的日期
        query = """
        SELECT MIN(trade_date) as min_date, MAX(trade_date) as max_date
        FROM daily_stock_data
        WHERE asset_id = %s
        """
        result = self.execute_query(query, (asset_id,))

        if result and len(result) > 0:
            min_date = result[0]['min_date']
            max_date = result[0]['max_date']
            return min_date, max_date

        return None, None
