#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Supabase集成测试
测试QuantDB系统与Supabase的集成
"""

import os
import sys
import unittest
import pandas as pd
from datetime import datetime, timedelta, date
import logging
from dotenv import load_dotenv

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("supabase_integration_test")

# 从.env文件加载环境变量
load_dotenv()

# 导入测试目标
from src.db.adapter_factory import create_db_adapter
from src.cache.akshare_adapter_simplified import AKShareAdapter
from src.services.stock_data_service import StockDataService
from src.api.database import get_db
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient
from src.api.main import app

class TestSupabaseIntegration(unittest.TestCase):
    """测试Supabase集成"""
    
    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        # 检查是否配置了Supabase
        if not os.getenv('SUPABASE_DB_PASSWORD'):
            raise unittest.SkipTest("缺少Supabase配置，跳过测试")
        
        # 切换到Supabase数据库
        from scripts.switch_database import update_env_file
        update_env_file('supabase')
        
        # 创建Supabase适配器
        cls.db_adapter = create_db_adapter('supabase')
        if not cls.db_adapter.connect():
            raise unittest.SkipTest("无法连接到Supabase数据库，跳过测试")
        
        # 创建测试客户端
        cls.client = TestClient(app)
        
        # 记录测试开始时间
        cls.start_time = datetime.now()
        logger.info(f"测试开始时间: {cls.start_time}")
    
    @classmethod
    def tearDownClass(cls):
        """测试类清理"""
        # 断开数据库连接
        if hasattr(cls, 'db_adapter') and cls.db_adapter:
            cls.db_adapter.disconnect()
        
        # 切换回SQLite数据库
        from scripts.switch_database import update_env_file
        update_env_file('sqlite')
        
        # 记录测试结束时间
        end_time = datetime.now()
        duration = end_time - cls.start_time
        logger.info(f"测试结束时间: {end_time}")
        logger.info(f"测试总耗时: {duration}")
    
    def setUp(self):
        """测试前的准备工作"""
        # 确保连接到数据库
        if not self.db_adapter.conn:
            self.db_adapter.connect()
    
    def test_01_database_connection(self):
        """测试数据库连接"""
        # 执行简单查询
        result = self.db_adapter.execute_query("SELECT 1 as test")
        self.assertIsNotNone(result)
        self.assertEqual(result[0]['test'], 1)
    
    def test_02_create_test_asset(self):
        """测试创建测试资产"""
        # 生成唯一的测试资产代码
        test_symbol = f"TEST{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # 检查资产是否已存在
        existing = self.db_adapter.get_asset_by_symbol(test_symbol)
        if existing:
            logger.info(f"测试资产已存在: {test_symbol}")
            return
        
        # 插入测试资产
        query = """
        INSERT INTO assets (asset_id, symbol, name, isin, asset_type, exchange, currency, created_at, updated_at)
        VALUES (gen_random_uuid(), %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING asset_id, symbol, name
        """
        params = (
            test_symbol,
            f"测试资产 {test_symbol}",
            f"TEST{test_symbol}",
            "STOCK",
            "TEST",
            "CNY",
            datetime.now(),
            datetime.now()
        )
        
        result = self.db_adapter.execute_query(query, params)
        self.assertIsNotNone(result)
        self.assertEqual(result[0]['symbol'], test_symbol)
        
        # 保存测试资产代码供后续测试使用
        self.__class__.test_symbol = test_symbol
        logger.info(f"创建测试资产: {test_symbol}")
    
    def test_03_save_and_get_stock_data(self):
        """测试保存和获取股票数据"""
        # 确保测试资产已创建
        if not hasattr(self.__class__, 'test_symbol'):
            self.test_02_create_test_asset()
        
        test_symbol = self.__class__.test_symbol
        
        # 创建测试数据
        today = date.today()
        data = {
            'trade_date': [today - timedelta(days=1), today],
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
        result = self.db_adapter.save_stock_data(test_symbol, df)
        self.assertTrue(result)
        
        # 获取数据
        result_df = self.db_adapter.get_stock_data(test_symbol)
        self.assertIsNotNone(result_df)
        self.assertEqual(len(result_df), 2)
        
        # 验证数据内容
        self.assertEqual(float(result_df.iloc[0]['close']), 10.8)
        self.assertEqual(int(result_df.iloc[1]['volume']), 1200000)
    
    def test_04_get_data_date_range(self):
        """测试获取数据日期范围"""
        # 确保测试资产已创建
        if not hasattr(self.__class__, 'test_symbol'):
            self.test_02_create_test_asset()
        
        test_symbol = self.__class__.test_symbol
        
        # 获取日期范围
        min_date, max_date = self.db_adapter.get_data_date_range(test_symbol)
        self.assertIsNotNone(min_date)
        self.assertIsNotNone(max_date)
        
        # 验证日期范围
        today = date.today()
        yesterday = today - timedelta(days=1)
        self.assertEqual(min_date.strftime('%Y-%m-%d'), yesterday.strftime('%Y-%m-%d'))
        self.assertEqual(max_date.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d'))
    
    def test_05_api_health_check(self):
        """测试API健康检查"""
        response = self.client.get("/api/v1/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})
    
    def test_06_api_stock_data(self):
        """测试API股票数据"""
        # 使用真实股票代码
        symbol = "000001"  # 平安银行
        
        # 获取今天和30天前的日期
        today = date.today()
        start_date = (today - timedelta(days=30)).strftime('%Y%m%d')
        end_date = today.strftime('%Y%m%d')
        
        # 调用API
        response = self.client.get(f"/api/v1/stock/{symbol}?start_date={start_date}&end_date={end_date}")
        
        # 验证响应
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("symbol", data)
        self.assertEqual(data["symbol"], symbol)
        self.assertIn("prices", data)
        
        # 记录数据量
        logger.info(f"获取到 {len(data['prices'])} 条股票数据")
        
        # 再次调用API，验证缓存机制
        response2 = self.client.get(f"/api/v1/stock/{symbol}?start_date={start_date}&end_date={end_date}")
        self.assertEqual(response2.status_code, 200)
        data2 = response2.json()
        self.assertEqual(len(data2['prices']), len(data['prices']))


if __name__ == '__main__':
    unittest.main()
