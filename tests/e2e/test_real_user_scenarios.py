#!/usr/bin/env python3
"""
真实用户场景的端到端测试

这些测试模拟真实用户的使用场景，使用真实的HTTP请求和真实的数据源。
测试目标：
1. 验证完整的用户工作流程
2. 确保API在生产环境中的行为
3. 测试真实数据获取和缓存机制
4. 验证错误处理和边界情况

运行方式：
python scripts/test_runner.py --e2e --auto-start-server
"""

import unittest
import requests
import time
import json
from datetime import datetime, timedelta
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.logger_unified import get_logger

# Setup test logger
logger = get_logger("real_user_scenarios_e2e")

class TestRealUserScenarios(unittest.TestCase):
    """测试真实用户使用场景的端到端测试"""

    @classmethod
    def setUpClass(cls):
        """设置测试环境"""
        cls.base_url = "http://localhost:8000"
        cls.api_prefix = "/api/v1"
        
        # 等待API服务器启动
        cls._wait_for_api_server()
        
        logger.info("=== 开始真实用户场景E2E测试 ===")

    @classmethod
    def _wait_for_api_server(cls, max_retries=30, retry_delay=1):
        """等待API服务器启动"""
        logger.info("等待API服务器启动...")
        
        for attempt in range(max_retries):
            try:
                response = requests.get(f"{cls.base_url}{cls.api_prefix}/health", timeout=5)
                if response.status_code == 200:
                    logger.info("API服务器已启动并响应正常")
                    return True
            except requests.exceptions.RequestException:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    
        raise Exception("API服务器启动超时")

    def setUp(self):
        """每个测试前的设置"""
        self.test_symbol = "000001"  # 平安银行
        self.test_start_date = "20240101"
        self.test_end_date = "20240105"
        
        # 清理测试数据
        self._cleanup_test_data()

    def _cleanup_test_data(self):
        """清理测试数据"""
        try:
            # 清理特定股票的缓存数据
            response = requests.delete(
                f"{self.base_url}{self.api_prefix}/cache/clear/symbol/{self.test_symbol}",
                timeout=10
            )
            if response.status_code == 200:
                logger.info(f"已清理 {self.test_symbol} 的缓存数据")
        except requests.exceptions.RequestException as e:
            logger.warning(f"清理缓存数据时出错: {e}")

    def test_scenario_1_new_user_first_request(self):
        """场景1: 新用户首次请求股票数据"""
        logger.info("=== 场景1: 新用户首次请求 ===")
        
        # 步骤1: 用户访问API健康检查
        logger.info("步骤1: 检查API健康状态")
        response = requests.get(f"{self.base_url}{self.api_prefix}/health")
        self.assertEqual(response.status_code, 200)
        health_data = response.json()
        self.assertEqual(health_data["status"], "ok")
        logger.info("✓ API健康检查通过")

        # 步骤2: 用户查看可用资产
        logger.info("步骤2: 查看可用资产列表")
        response = requests.get(f"{self.base_url}{self.api_prefix}/assets")
        self.assertEqual(response.status_code, 200)
        assets_data = response.json()
        self.assertIsInstance(assets_data, list)
        logger.info(f"✓ 获取到 {len(assets_data)} 个资产")

        # 步骤3: 用户请求股票历史数据（数据库为空）
        logger.info("步骤3: 请求股票历史数据（首次请求，从AKShare获取）")
        start_time = time.time()
        response = requests.get(
            f"{self.base_url}{self.api_prefix}/historical/stock/{self.test_symbol}",
            params={
                "start_date": self.test_start_date,
                "end_date": self.test_end_date
            },
            timeout=30  # 增加超时时间，因为首次请求需要从AKShare获取数据
        )
        first_request_time = time.time() - start_time
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # 验证响应结构
        self.assertIn("symbol", data)
        self.assertIn("data", data)
        self.assertIn("metadata", data)
        self.assertEqual(data["symbol"], self.test_symbol)
        
        # 验证数据内容
        stock_data = data["data"]
        self.assertGreater(len(stock_data), 0, "应该返回股票数据")
        
        # 验证数据字段
        first_record = stock_data[0]
        required_fields = ["date", "open", "high", "low", "close", "volume"]
        for field in required_fields:
            self.assertIn(field, first_record, f"缺少必需字段: {field}")
        
        logger.info(f"✓ 首次请求成功，耗时 {first_request_time:.2f}秒，获取 {len(stock_data)} 条记录")
        
        # 步骤4: 验证数据已缓存
        logger.info("步骤4: 验证数据已缓存到数据库")
        # 通过再次请求相同数据来验证缓存
        start_time = time.time()
        response2 = requests.get(
            f"{self.base_url}{self.api_prefix}/historical/stock/{self.test_symbol}",
            params={
                "start_date": self.test_start_date,
                "end_date": self.test_end_date
            }
        )
        second_request_time = time.time() - start_time
        
        self.assertEqual(response2.status_code, 200)
        data2 = response2.json()
        
        # 验证数据一致性
        self.assertEqual(len(data2["data"]), len(stock_data))
        self.assertEqual(data2["symbol"], data["symbol"])
        
        # 验证缓存性能提升
        self.assertLess(second_request_time, first_request_time, "缓存请求应该更快")
        
        performance_improvement = (first_request_time - second_request_time) / first_request_time * 100
        logger.info(f"✓ 缓存命中，耗时 {second_request_time:.2f}秒，性能提升 {performance_improvement:.1f}%")

    def test_scenario_2_data_range_expansion(self):
        """场景2: 用户扩展数据查询范围"""
        logger.info("=== 场景2: 数据范围扩展 ===")
        
        # 步骤1: 用户首先请求小范围数据
        logger.info("步骤1: 请求小范围数据")
        small_end_date = "20240103"  # 只请求3天数据
        
        response1 = requests.get(
            f"{self.base_url}{self.api_prefix}/historical/stock/{self.test_symbol}",
            params={
                "start_date": self.test_start_date,
                "end_date": small_end_date
            }
        )
        
        self.assertEqual(response1.status_code, 200)
        data1 = response1.json()
        small_range_count = len(data1["data"])
        logger.info(f"✓ 小范围请求成功，获取 {small_range_count} 条记录")
        
        # 步骤2: 用户扩展查询范围
        logger.info("步骤2: 扩展查询范围（部分缓存命中）")
        expanded_end_date = "20240110"  # 扩展到10天
        
        start_time = time.time()
        response2 = requests.get(
            f"{self.base_url}{self.api_prefix}/historical/stock/{self.test_symbol}",
            params={
                "start_date": self.test_start_date,
                "end_date": expanded_end_date
            }
        )
        expanded_request_time = time.time() - start_time
        
        self.assertEqual(response2.status_code, 200)
        data2 = response2.json()
        expanded_range_count = len(data2["data"])
        
        # 验证数据范围扩展
        self.assertGreaterEqual(expanded_range_count, small_range_count, "扩展范围应该包含更多数据")
        
        logger.info(f"✓ 扩展范围请求成功，耗时 {expanded_request_time:.2f}秒，获取 {expanded_range_count} 条记录")
        
        # 验证原有数据包含在扩展数据中
        original_dates = {record["date"] for record in data1["data"]}
        expanded_dates = {record["date"] for record in data2["data"]}
        self.assertTrue(original_dates.issubset(expanded_dates), "扩展数据应该包含原有数据")
        
        logger.info("✓ 数据一致性验证通过")

    def test_scenario_3_error_handling(self):
        """场景3: 错误处理场景"""
        logger.info("=== 场景3: 错误处理 ===")
        
        # 测试无效股票代码
        logger.info("测试无效股票代码")
        invalid_symbol = "INVALID"
        response = requests.get(
            f"{self.base_url}{self.api_prefix}/historical/stock/{invalid_symbol}",
            params={
                "start_date": self.test_start_date,
                "end_date": self.test_end_date
            }
        )
        
        # 验证错误响应
        self.assertEqual(response.status_code, 400)
        error_data = response.json()
        self.assertIn("detail", error_data)
        logger.info("✓ 无效股票代码错误处理正确")
        
        # 测试无效日期格式
        logger.info("测试无效日期格式")
        response = requests.get(
            f"{self.base_url}{self.api_prefix}/historical/stock/{self.test_symbol}",
            params={
                "start_date": "invalid-date",
                "end_date": self.test_end_date
            }
        )
        
        # 验证错误响应
        self.assertEqual(response.status_code, 422)
        error_data = response.json()
        self.assertIn("error", error_data)
        logger.info("✓ 无效日期格式错误处理正确")

if __name__ == '__main__':
    unittest.main()
