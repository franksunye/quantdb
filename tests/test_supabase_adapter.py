#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试Supabase适配器
用于验证Supabase适配器的功能
"""

import os
import sys
import unittest
import pandas as pd
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.db.supabase_adapter import SupabaseAdapter

class TestSupabaseAdapter(unittest.TestCase):
    """测试Supabase适配器类"""
    
    def setUp(self):
        """测试前的准备工作"""
        self.adapter = SupabaseAdapter()
        self.assertTrue(self.adapter.connect(), "无法连接到Supabase数据库")
    
    def tearDown(self):
        """测试后的清理工作"""
        self.adapter.disconnect()
    
    def test_connection(self):
        """测试数据库连接"""
        # 执行简单查询
        result = self.adapter.execute_query("SELECT 1 as test")
        self.assertIsNotNone(result, "查询失败")
        self.assertEqual(result[0]['test'], 1, "查询结果不正确")
    
    def test_get_asset_by_symbol(self):
        """测试根据股票代码获取资产信息"""
        # 注意：这个测试需要数据库中有测试数据
        # 这里假设数据库中有股票代码为'000001'的资产
        asset = self.adapter.get_asset_by_symbol('000001')
        self.assertIsNotNone(asset, "找不到测试资产")
        self.assertEqual(asset['symbol'], '000001', "资产代码不匹配")
    
    def test_get_stock_data(self):
        """测试获取股票历史数据"""
        # 注意：这个测试需要数据库中有测试数据
        # 这里假设数据库中有股票代码为'000001'的历史数据
        df = self.adapter.get_stock_data('000001')
        self.assertIsNotNone(df, "获取股票数据失败")
        self.assertGreater(len(df), 0, "股票数据为空")
        
        # 测试日期范围查询
        today = datetime.now().date()
        one_month_ago = today - timedelta(days=30)
        df_range = self.adapter.get_stock_data('000001', one_month_ago, today)
        self.assertIsNotNone(df_range, "获取日期范围内的股票数据失败")
    
    def test_save_stock_data(self):
        """测试保存股票历史数据"""
        # 创建测试数据
        test_data = {
            'trade_date': [datetime.now().date()],
            'open': [10.0],
            'high': [11.0],
            'low': [9.0],
            'close': [10.5],
            'volume': [1000000],
            'turnover': [10500000.0],
            'amplitude': [0.2],
            'pct_change': [0.05],
            'change': [0.5],
            'turnover_rate': [0.01]
        }
        df = pd.DataFrame(test_data)
        
        # 保存测试数据
        # 注意：这个测试需要数据库中有股票代码为'000001'的资产
        result = self.adapter.save_stock_data('000001', df)
        self.assertTrue(result, "保存股票数据失败")
        
        # 验证数据已保存
        saved_df = self.adapter.get_stock_data('000001', test_data['trade_date'][0], test_data['trade_date'][0])
        self.assertIsNotNone(saved_df, "获取保存的数据失败")
        self.assertEqual(len(saved_df), 1, "保存的数据记录数不正确")
        self.assertEqual(saved_df.iloc[0]['close'], 10.5, "保存的收盘价不正确")
    
    def test_get_data_date_range(self):
        """测试获取股票数据的日期范围"""
        # 注意：这个测试需要数据库中有股票代码为'000001'的历史数据
        min_date, max_date = self.adapter.get_data_date_range('000001')
        self.assertIsNotNone(min_date, "获取最早日期失败")
        self.assertIsNotNone(max_date, "获取最晚日期失败")
        self.assertLessEqual(min_date, max_date, "日期范围不正确")

if __name__ == '__main__':
    unittest.main()
