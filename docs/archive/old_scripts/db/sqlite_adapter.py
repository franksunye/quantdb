#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
SQLite数据库适配器
用于连接和操作SQLite数据库
"""

import os
import logging
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv
from typing import Optional, List, Dict, Tuple, Any

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("sqlite_adapter")

# 从.env文件加载环境变量
load_dotenv()

class SQLiteAdapter:
    """SQLite数据库适配器类"""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        初始化适配器
        
        Args:
            db_path: SQLite数据库文件路径，如果为None，则使用环境变量DATABASE_URL
        """
        # 获取数据库路径
        if db_path is None:
            database_url = os.getenv('DATABASE_URL', 'sqlite:///./database/stock_data.db')
            if database_url.startswith('sqlite:///'):
                db_path = database_url[10:]
        
        self.db_path = db_path
        logger.info(f"SQLite数据库路径: {self.db_path}")
        
        # 连接
        self.conn = None
    
    def connect(self) -> bool:
        """
        连接到SQLite数据库
        
        Returns:
            连接是否成功
        """
        try:
            self.conn = sqlite3.connect(self.db_path)
            # 启用外键约束
            self.conn.execute("PRAGMA foreign_keys = ON")
            # 设置行工厂，使结果可以通过列名访问
            self.conn.row_factory = sqlite3.Row
            logger.info(f"成功连接到SQLite数据库: {self.db_path}")
            return True
        except Exception as e:
            logger.error(f"连接SQLite数据库失败: {e}")
            return False
    
    def disconnect(self) -> None:
        """断开数据库连接"""
        if self.conn:
            self.conn.close()
            self.conn = None
            logger.info("已断开SQLite数据库连接")
    
    def execute_query(self, query: str, params: Optional[Tuple] = None) -> List[Dict]:
        """
        执行SQL查询
        
        Args:
            query: SQL查询语句
            params: 查询参数
        
        Returns:
            查询结果列表，每个元素是一个字典
        """
        if not self.conn:
            if not self.connect():
                return None
        
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, params or ())
            result = cursor.fetchall()
            # 转换为字典列表
            dict_result = [dict(row) for row in result]
            cursor.close()
            return dict_result
        except Exception as e:
            logger.error(f"执行查询失败: {e}")
            return None
    
    def execute_update(self, query: str, params: Optional[Tuple] = None) -> int:
        """
        执行SQL更新（INSERT, UPDATE, DELETE）
        
        Args:
            query: SQL更新语句
            params: 更新参数
        
        Returns:
            受影响的行数
        """
        if not self.conn:
            if not self.connect():
                return 0
        
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, params or ())
            affected_rows = cursor.rowcount
            self.conn.commit()
            cursor.close()
            return affected_rows
        except Exception as e:
            logger.error(f"执行更新失败: {e}")
            self.conn.rollback()
            return 0
    
    def get_asset_by_symbol(self, symbol: str) -> Optional[Dict]:
        """
        根据股票代码获取资产信息
        
        Args:
            symbol: 股票代码
        
        Returns:
            资产信息字典，如果找不到则返回None
        """
        query = "SELECT * FROM assets WHERE symbol = ?"
        result = self.execute_query(query, (symbol,))
        if result and len(result) > 0:
            return result[0]
        return None
    
    def get_stock_data(self, symbol: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Optional[pd.DataFrame]:
        """
        获取股票历史数据
        
        Args:
            symbol: 股票代码
            start_date: 开始日期，格式为YYYY-MM-DD
            end_date: 结束日期，格式为YYYY-MM-DD
        
        Returns:
            股票历史数据DataFrame，如果找不到则返回None
        """
        # 获取资产ID
        asset = self.get_asset_by_symbol(symbol)
        if not asset:
            logger.warning(f"找不到股票代码为 {symbol} 的资产")
            return None
        
        asset_id = asset['asset_id']
        
        # 构建查询
        query = """
        SELECT d.* FROM daily_stock_data d
        WHERE d.asset_id = ?
        """
        params = [asset_id]
        
        if start_date:
            query += " AND d.trade_date >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND d.trade_date <= ?"
            params.append(end_date)
        
        query += " ORDER BY d.trade_date"
        
        # 执行查询
        result = self.execute_query(query, tuple(params))
        if not result:
            return None
        
        # 转换为DataFrame
        df = pd.DataFrame(result)
        return df
    
    def save_stock_data(self, symbol: str, data_df: pd.DataFrame) -> bool:
        """
        保存股票历史数据
        
        Args:
            symbol: 股票代码
            data_df: 股票历史数据DataFrame
        
        Returns:
            是否成功保存
        """
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
            WHERE asset_id = ? AND trade_date = ?
            """
            existing = self.execute_query(check_query, (asset_id, row['trade_date']))
            
            if existing:
                # 更新现有记录
                update_query = """
                UPDATE daily_stock_data SET
                    open = ?,
                    high = ?,
                    low = ?,
                    close = ?,
                    volume = ?,
                    turnover = ?,
                    amplitude = ?,
                    pct_change = ?,
                    change = ?,
                    turnover_rate = ?
                WHERE asset_id = ? AND trade_date = ?
                """
                params = (
                    row['open'], row['high'], row['low'], row['close'],
                    row['volume'], row.get('turnover', 0), row.get('amplitude', 0),
                    row.get('pct_change', 0), row.get('change', 0), row.get('turnover_rate', 0),
                    asset_id, row['trade_date']
                )
                affected = self.execute_update(update_query, params)
            else:
                # 插入新记录
                insert_query = """
                INSERT INTO daily_stock_data (
                    asset_id, trade_date, open, high, low, close, volume,
                    turnover, amplitude, pct_change, change, turnover_rate
                ) VALUES (
                    ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?
                )
                """
                params = (
                    asset_id, row['trade_date'],
                    row['open'], row['high'], row['low'], row['close'], row['volume'],
                    row.get('turnover', 0), row.get('amplitude', 0),
                    row.get('pct_change', 0), row.get('change', 0), row.get('turnover_rate', 0)
                )
                affected = self.execute_update(insert_query, params)
            
            if affected > 0:
                success_count += 1
        
        logger.info(f"成功保存 {success_count}/{len(data_df)} 条股票数据记录")
        return success_count > 0
    
    def get_data_date_range(self, symbol: str) -> Tuple[Optional[str], Optional[str]]:
        """
        获取股票数据的日期范围
        
        Args:
            symbol: 股票代码
        
        Returns:
            (最早日期, 最晚日期)元组，如果找不到则返回(None, None)
        """
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
        WHERE asset_id = ?
        """
        result = self.execute_query(query, (asset_id,))
        
        if result and len(result) > 0:
            min_date = result[0]['min_date']
            max_date = result[0]['max_date']
            return min_date, max_date
        
        return None, None
