#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
蓄水池机制测试
测试QuantDB系统的蓄水池机制在Supabase环境下的正确性
"""

import os
import sys
import unittest
import pandas as pd
from datetime import datetime, timedelta, date
import logging
import time
import requests
from dotenv import load_dotenv

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("reservoir_mechanism_test")

# 从.env文件加载环境变量
load_dotenv()

# 导入测试目标
from src.db.adapter_factory import create_db_adapter
from src.cache.akshare_adapter_simplified import AKShareAdapter
from src.services.stock_data_service import StockDataService
from src.api.database import get_db
from sqlalchemy.orm import Session
import subprocess

class TestReservoirMechanism(unittest.TestCase):
    """测试蓄水池机制"""
    
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
        
        # 启动API服务
        cls.api_port = 8766
        cls.api_url = f"http://localhost:{cls.api_port}"
        cls.api_process = subprocess.Popen(
            ['python', '-m', 'uvicorn', 'src.api.main:app', '--host', '0.0.0.0', '--port', str(cls.api_port)]
        )
        
        # 等待API服务启动
        logger.info("等待API服务启动...")
        time.sleep(3)
        
        # 记录测试开始时间
        cls.start_time = datetime.now()
        logger.info(f"测试开始时间: {cls.start_time}")
    
    @classmethod
    def tearDownClass(cls):
        """测试类清理"""
        # 停止API服务
        if hasattr(cls, 'api_process') and cls.api_process:
            cls.api_process.terminate()
            cls.api_process.wait()
            logger.info("API服务已停止")
        
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
    
    def test_01_api_health_check(self):
        """测试API健康检查"""
        response = requests.get(f"{self.api_url}/api/v1/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})
    
    def test_02_clear_test_data(self):
        """清除测试数据"""
        # 使用测试股票代码
        symbol = "000001"  # 平安银行
        
        # 获取资产ID
        asset = self.db_adapter.get_asset_by_symbol(symbol)
        if not asset:
            logger.warning(f"找不到股票代码为 {symbol} 的资产，跳过清除测试数据")
            return
        
        asset_id = asset['asset_id']
        
        # 清除股票数据
        query = "DELETE FROM daily_stock_data WHERE asset_id = %s"
        affected = self.db_adapter.execute_update(query, (asset_id,))
        logger.info(f"清除了 {affected} 条股票数据记录")
    
    def test_03_first_request(self):
        """测试首次请求（数据库为空）"""
        # 使用测试股票代码
        symbol = "000001"  # 平安银行
        
        # 获取今天和10天前的日期
        today = date.today()
        start_date = (today - timedelta(days=10)).strftime('%Y%m%d')
        end_date = today.strftime('%Y%m%d')
        
        # 记录请求开始时间
        request_start = datetime.now()
        
        # 调用API
        response = requests.get(f"{self.api_url}/api/v1/stock/{symbol}?start_date={start_date}&end_date={end_date}")
        
        # 记录请求结束时间
        request_end = datetime.now()
        request_duration = request_end - request_start
        
        # 验证响应
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("symbol", data)
        self.assertEqual(data["symbol"], symbol)
        self.assertIn("prices", data)
        
        # 记录数据量和请求耗时
        logger.info(f"首次请求获取到 {len(data['prices'])} 条股票数据，耗时: {request_duration}")
        
        # 验证数据已保存到数据库
        db_data = self.db_adapter.get_stock_data(symbol, start_date, end_date)
        self.assertIsNotNone(db_data)
        self.assertGreater(len(db_data), 0)
        logger.info(f"数据库中有 {len(db_data)} 条股票数据记录")
    
    def test_04_second_request_same_range(self):
        """测试第二次请求（相同日期范围）"""
        # 使用测试股票代码
        symbol = "000001"  # 平安银行
        
        # 获取今天和10天前的日期
        today = date.today()
        start_date = (today - timedelta(days=10)).strftime('%Y%m%d')
        end_date = today.strftime('%Y%m%d')
        
        # 记录请求开始时间
        request_start = datetime.now()
        
        # 调用API
        response = requests.get(f"{self.api_url}/api/v1/stock/{symbol}?start_date={start_date}&end_date={end_date}")
        
        # 记录请求结束时间
        request_end = datetime.now()
        request_duration = request_end - request_start
        
        # 验证响应
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("prices", data)
        
        # 记录数据量和请求耗时
        logger.info(f"第二次请求获取到 {len(data['prices'])} 条股票数据，耗时: {request_duration}")
        
        # 验证第二次请求比首次请求快
        self.assertLess(request_duration.total_seconds(), 1.0)  # 应该非常快，因为数据已缓存
    
    def test_05_third_request_extended_range(self):
        """测试第三次请求（扩展日期范围）"""
        # 使用测试股票代码
        symbol = "000001"  # 平安银行
        
        # 获取今天和20天前的日期（比之前的范围更大）
        today = date.today()
        start_date = (today - timedelta(days=20)).strftime('%Y%m%d')
        end_date = today.strftime('%Y%m%d')
        
        # 记录请求开始时间
        request_start = datetime.now()
        
        # 调用API
        response = requests.get(f"{self.api_url}/api/v1/stock/{symbol}?start_date={start_date}&end_date={end_date}")
        
        # 记录请求结束时间
        request_end = datetime.now()
        request_duration = request_end - request_start
        
        # 验证响应
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("prices", data)
        
        # 记录数据量和请求耗时
        logger.info(f"第三次请求获取到 {len(data['prices'])} 条股票数据，耗时: {request_duration}")
        
        # 验证数据量比之前的请求多
        self.assertGreater(len(data['prices']), 10)
        
        # 验证数据已保存到数据库
        db_data = self.db_adapter.get_stock_data(symbol, start_date, end_date)
        self.assertIsNotNone(db_data)
        self.assertGreater(len(db_data), 10)
        logger.info(f"数据库中有 {len(db_data)} 条股票数据记录")


if __name__ == '__main__':
    unittest.main()
