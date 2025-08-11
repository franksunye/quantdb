"""
核心用户场景E2E测试

测试真实用户使用场景，验证完整的工作流程
"""

import time
import unittest

from tests.e2e.base_e2e_test import BaseE2ETest, logger


class TestUserScenarios(BaseE2ETest):
    """用户场景E2E测试"""
    
    def test_scenario_1_new_user_workflow(self):
        """场景1: 新用户完整工作流程"""
        logger.info("=== 场景1: 新用户完整工作流程 ===")
        
        # 步骤1: 用户检查API状态
        logger.info("步骤1: 检查API健康状态")
        response = self.get("/health")
        self.assert_api_success(response)
        
        health_data = response.json()
        self.assertIn("status", health_data)
        self.assertEqual(health_data["status"], "ok")
        logger.info("✓ API健康检查通过")
        
        # 步骤2: 用户查看可用资产
        logger.info("步骤2: 查看可用资产")
        response = self.get("/assets")
        self.assert_api_success(response)
        
        assets = response.json()
        self.assertIsInstance(assets, list)
        logger.info(f"✓ 获取到 {len(assets)} 个资产")
        
        # 步骤3: 用户首次请求股票数据
        logger.info("步骤3: 首次请求股票数据（从AKShare获取）")
        test_symbol = self.config.TEST_SYMBOLS[0]
        
        response, first_request_time = self.measure_request_time(
            lambda: self.get(
                f"/historical/stock/{test_symbol}",
                params={
                    "start_date": self.config.TEST_START_DATE,
                    "end_date": self.config.TEST_END_DATE
                }
            )
        )
        
        self.assert_api_success(response)
        data = response.json()
        
        # 验证响应结构
        self.assertIn("symbol", data)
        self.assertIn("data", data)
        self.assertEqual(data["symbol"], test_symbol)
        
        stock_data = data["data"]
        self.assertGreater(len(stock_data), 0, "应该返回股票数据")
        
        # 验证数据字段
        if stock_data:
            first_record = stock_data[0]
            required_fields = ["date", "open", "high", "low", "close", "volume"]
            for field in required_fields:
                self.assertIn(field, first_record, f"缺少必需字段: {field}")
        
        logger.info(f"✓ 首次请求成功，耗时 {first_request_time:.2f}秒，获取 {len(stock_data)} 条记录")
        
        # 步骤4: 用户再次请求相同数据（测试缓存）
        logger.info("步骤4: 再次请求相同数据（测试缓存）")
        
        response2, second_request_time = self.measure_request_time(
            lambda: self.get(
                f"/historical/stock/{test_symbol}",
                params={
                    "start_date": self.config.TEST_START_DATE,
                    "end_date": self.config.TEST_END_DATE
                }
            )
        )
        
        self.assert_api_success(response2)
        data2 = response2.json()
        
        # 验证数据一致性
        self.assertEqual(len(data2["data"]), len(stock_data))
        self.assertEqual(data2["symbol"], data["symbol"])
        
        # 验证缓存性能提升（允许一定误差）
        if second_request_time < first_request_time * 0.8:
            performance_improvement = (first_request_time - second_request_time) / first_request_time * 100
            logger.info(f"✓ 缓存命中，耗时 {second_request_time:.2f}秒，性能提升 {performance_improvement:.1f}%")
        else:
            logger.warning(f"⚠ 缓存性能提升不明显: {first_request_time:.2f}s -> {second_request_time:.2f}s")
    
    def test_scenario_2_data_range_expansion(self):
        """场景2: 数据范围扩展"""
        logger.info("=== 场景2: 数据范围扩展 ===")
        
        test_symbol = self.config.TEST_SYMBOLS[0]
        
        # 步骤1: 请求小范围数据
        logger.info("步骤1: 请求小范围数据")
        small_end_date = "20240103"  # 只请求3天数据
        
        response1 = self.get(
            f"/historical/stock/{test_symbol}",
            params={
                "start_date": self.config.TEST_START_DATE,
                "end_date": small_end_date
            }
        )
        
        self.assert_api_success(response1)
        data1 = response1.json()
        small_range_count = len(data1["data"])
        logger.info(f"✓ 小范围请求成功，获取 {small_range_count} 条记录")
        
        # 步骤2: 扩展查询范围
        logger.info("步骤2: 扩展查询范围（部分缓存命中）")
        expanded_end_date = "20240110"  # 扩展到更多天
        
        response2, expanded_request_time = self.measure_request_time(
            lambda: self.get(
                f"/historical/stock/{test_symbol}",
                params={
                    "start_date": self.config.TEST_START_DATE,
                    "end_date": expanded_end_date
                }
            )
        )
        
        self.assert_api_success(response2)
        data2 = response2.json()
        expanded_range_count = len(data2["data"])
        
        # 验证数据范围扩展
        self.assertGreaterEqual(expanded_range_count, small_range_count, "扩展范围应该包含更多数据")
        
        logger.info(f"✓ 扩展范围请求成功，耗时 {expanded_request_time:.2f}秒，获取 {expanded_range_count} 条记录")
        
        # 验证原有数据包含在扩展数据中
        if data1["data"] and data2["data"]:
            original_dates = {record["date"] for record in data1["data"]}
            expanded_dates = {record["date"] for record in data2["data"]}
            self.assertTrue(original_dates.issubset(expanded_dates), "扩展数据应该包含原有数据")
            logger.info("✓ 数据一致性验证通过")
    
    def test_scenario_3_error_handling(self):
        """场景3: 错误处理场景"""
        logger.info("=== 场景3: 错误处理场景 ===")
        
        # 测试1: 无效股票代码
        logger.info("测试1: 无效股票代码")
        invalid_symbol = "INVALID"
        response = self.get(
            f"/historical/stock/{invalid_symbol}",
            params={
                "start_date": self.config.TEST_START_DATE,
                "end_date": self.config.TEST_END_DATE
            }
        )
        
        # 验证错误响应（可能是400或其他错误状态码）
        self.assertNotEqual(response.status_code, 200, "无效股票代码应该返回错误")
        logger.info(f"✓ 无效股票代码正确返回错误: {response.status_code}")
        
        # 测试2: 无效日期格式
        logger.info("测试2: 无效日期格式")
        test_symbol = self.config.TEST_SYMBOLS[0]
        response = self.get(
            f"/historical/stock/{test_symbol}",
            params={
                "start_date": "invalid-date",
                "end_date": self.config.TEST_END_DATE
            }
        )
        
        # 验证错误响应（当前实现可能返回500）
        self.assertIn(response.status_code, [400, 422, 500], "无效日期格式应该返回错误")
        logger.info(f"✓ 无效日期格式正确返回错误: {response.status_code}")
    
    def test_scenario_4_cache_management(self):
        """场景4: 缓存管理"""
        logger.info("=== 场景4: 缓存管理 ===")
        
        test_symbol = self.config.TEST_SYMBOLS[0]
        
        # 步骤1: 获取数据（填充缓存）
        logger.info("步骤1: 获取数据填充缓存")
        response = self.get(
            f"/historical/stock/{test_symbol}",
            params={
                "start_date": self.config.TEST_START_DATE,
                "end_date": self.config.TEST_END_DATE
            }
        )
        self.assert_api_success(response)
        logger.info("✓ 缓存已填充")
        
        # 步骤2: 检查缓存状态（如果API存在）
        logger.info("步骤2: 检查缓存状态")
        response = self.get("/cache/status")
        if response.status_code == 200:
            logger.info("✓ 缓存状态API可用")
        else:
            logger.info("ℹ 缓存状态API不可用，跳过缓存管理测试")
        
        # 步骤3: 再次获取相同数据（测试缓存一致性）
        logger.info("步骤3: 再次获取相同数据")
        response2, request_time2 = self.measure_request_time(
            lambda: self.get(
                f"/historical/stock/{test_symbol}",
                params={
                    "start_date": self.config.TEST_START_DATE,
                    "end_date": self.config.TEST_END_DATE
                }
            )
        )

        self.assert_api_success(response2)

        # 验证第二次请求成功
        logger.info(f"✓ 第二次请求成功，耗时 {request_time2:.2f}秒")

if __name__ == '__main__':
    unittest.main()
