#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
数据库适配器单元测试
"""

import unittest
import pandas as pd
from datetime import datetime, date
from unittest.mock import patch, MagicMock

from src.db.adapter_factory import create_db_adapter
from src.config import DB_TYPE

class TestDBAdapterFactory(unittest.TestCase):
    """测试数据库适配器工厂"""

    def test_create_db_adapter_explicit(self):
        """测试显式指定适配器类型"""
        adapter = create_db_adapter('sqlite')
        self.assertEqual(adapter.__class__.__name__, 'SQLiteAdapter')

        adapter = create_db_adapter('supabase')
        self.assertEqual(adapter.__class__.__name__, 'SupabaseAdapter')

class TestSQLiteAdapter(unittest.TestCase):
    """测试SQLite适配器"""

    def setUp(self):
        """测试前的准备工作"""
        # 使用内存数据库进行测试
        self.adapter = create_db_adapter('sqlite')
        self.adapter.db_path = ':memory:'
        self.adapter.connect()

        # 创建测试表
        self.adapter.execute_update("""
        CREATE TABLE assets (
            asset_id INTEGER PRIMARY KEY,
            symbol TEXT NOT NULL,
            name TEXT NOT NULL,
            isin TEXT NOT NULL UNIQUE,
            asset_type TEXT NOT NULL,
            exchange TEXT NOT NULL,
            currency TEXT NOT NULL
        )
        """)

        self.adapter.execute_update("""
        CREATE TABLE daily_stock_data (
            id INTEGER PRIMARY KEY,
            asset_id INTEGER NOT NULL,
            trade_date DATE NOT NULL,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume INTEGER,
            turnover REAL,
            amplitude REAL,
            pct_change REAL,
            change REAL,
            turnover_rate REAL,
            FOREIGN KEY (asset_id) REFERENCES assets (asset_id),
            UNIQUE (asset_id, trade_date)
        )
        """)

        # 插入测试数据
        self.adapter.execute_update("""
        INSERT INTO assets (asset_id, symbol, name, isin, asset_type, exchange, currency)
        VALUES (1, '000001', '平安银行', 'CNE000000040', 'STOCK', 'SZSE', 'CNY')
        """)

    def tearDown(self):
        """测试后的清理工作"""
        self.adapter.disconnect()

    def test_get_asset_by_symbol(self):
        """测试根据股票代码获取资产信息"""
        asset = self.adapter.get_asset_by_symbol('000001')
        self.assertIsNotNone(asset)
        self.assertEqual(asset['symbol'], '000001')
        self.assertEqual(asset['name'], '平安银行')

    def test_get_asset_by_symbol_not_found(self):
        """测试获取不存在的资产"""
        asset = self.adapter.get_asset_by_symbol('999999')
        self.assertIsNone(asset)

    def test_save_and_get_stock_data(self):
        """测试保存和获取股票数据"""
        # 创建测试数据
        data = {
            'trade_date': [date(2025, 1, 1), date(2025, 1, 2)],
            'open': [10.0, 10.5],
            'high': [11.0, 11.5],
            'low': [9.5, 10.0],
            'close': [10.8, 11.2],
            'volume': [1000000, 1200000],
            'turnover': [10800000, 13440000],
            'amplitude': [0.15, 0.14],
            'pct_change': [0.03, 0.04],
            'change': [0.3, 0.4],
            'turnover_rate': [0.01, 0.012]
        }
        df = pd.DataFrame(data)

        # 保存数据
        result = self.adapter.save_stock_data('000001', df)
        self.assertTrue(result)

        # 获取数据
        result_df = self.adapter.get_stock_data('000001')
        self.assertIsNotNone(result_df)
        self.assertEqual(len(result_df), 2)

        # 验证数据内容
        self.assertEqual(result_df.iloc[0]['close'], 10.8)
        self.assertEqual(result_df.iloc[1]['volume'], 1200000)

    def test_get_data_date_range(self):
        """测试获取数据日期范围"""
        # 创建测试数据
        data = {
            'trade_date': [date(2025, 1, 1), date(2025, 1, 10)],
            'open': [10.0, 10.5],
            'high': [11.0, 11.5],
            'low': [9.5, 10.0],
            'close': [10.8, 11.2],
            'volume': [1000000, 1200000]
        }
        df = pd.DataFrame(data)

        # 保存数据
        self.adapter.save_stock_data('000001', df)

        # 获取日期范围
        min_date, max_date = self.adapter.get_data_date_range('000001')
        self.assertEqual(min_date, '2025-01-01')
        self.assertEqual(max_date, '2025-01-10')

class TestSupabaseAdapter(unittest.TestCase):
    """测试Supabase适配器"""

    def setUp(self):
        """测试前的准备工作"""
        # 使用模拟对象替代真实的Supabase连接
        self.patcher = patch('psycopg2.connect')
        self.mock_connect = self.patcher.start()

        # 创建模拟的连接和游标
        self.mock_conn = MagicMock()
        self.mock_cursor = MagicMock()
        self.mock_conn.cursor.return_value = self.mock_cursor
        self.mock_connect.return_value = self.mock_conn

        # 创建适配器
        self.adapter = create_db_adapter('supabase')
        self.adapter.connect()

    def tearDown(self):
        """测试后的清理工作"""
        self.patcher.stop()

    def test_get_asset_by_symbol(self):
        """测试根据股票代码获取资产信息"""
        # 设置模拟返回值
        mock_result = [
            {
                'asset_id': 'fc2007e9-c5ef-4682-9440-847b3eb87718',
                'symbol': '000001',
                'name': '平安银行',
                'isin': 'CNE000000040',
                'asset_type': 'STOCK',
                'exchange': 'SZSE',
                'currency': 'CNY'
            }
        ]
        self.mock_cursor.fetchall.return_value = mock_result

        # 调用方法
        asset = self.adapter.get_asset_by_symbol('000001')

        # 验证结果
        self.assertIsNotNone(asset)
        self.assertEqual(asset['symbol'], '000001')
        self.assertEqual(asset['name'], '平安银行')

        # 验证SQL查询
        self.mock_cursor.execute.assert_called_with(
            "SELECT * FROM assets WHERE symbol = %s",
            ('000001',)
        )

    def test_save_stock_data(self):
        """测试保存股票数据"""
        # 设置模拟返回值
        self.mock_cursor.fetchall.return_value = [
            {'asset_id': 'fc2007e9-c5ef-4682-9440-847b3eb87718'}
        ]
        self.mock_cursor.rowcount = 1

        # 创建测试数据
        data = {
            'trade_date': [date(2025, 1, 1)],
            'open': [10.0],
            'high': [11.0],
            'low': [9.5],
            'close': [10.8],
            'volume': [1000000],
            'turnover': [10800000],
            'amplitude': [0.15],
            'pct_change': [0.03],
            'change': [0.3],
            'turnover_rate': [0.01]
        }
        df = pd.DataFrame(data)

        # 调用方法
        result = self.adapter.save_stock_data('000001', df)

        # 验证结果
        self.assertTrue(result)

        # 验证SQL查询
        self.mock_cursor.execute.assert_any_call(
            "SELECT * FROM assets WHERE symbol = %s",
            ('000001',)
        )

if __name__ == '__main__':
    unittest.main()
