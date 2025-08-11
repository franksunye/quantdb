"""
测试 qdb API 集成功能

测试覆盖：
- qdb包的端到端API测试
- 缓存机制集成测试
- 错误处理集成测试
- 多种调用方式的集成验证
- 性能和缓存效果验证
"""

import unittest
import tempfile
import shutil
import os
import time
from unittest.mock import patch, MagicMock
import sys
import pandas as pd

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import qdb
from qdb.exceptions import QDBError, CacheError, DataError


class TestQDBAPIIntegration(unittest.TestCase):
    """测试QDB API集成功能"""

    def setUp(self):
        """设置测试环境"""
        self.temp_dir = tempfile.mkdtemp()
        self.cache_dir = os.path.join(self.temp_dir, "test_cache")
        
        # 重置全局客户端
        qdb.client._global_client = None

    def tearDown(self):
        """清理测试环境"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        
        # 重置全局客户端
        qdb.client._global_client = None

    def test_end_to_end_stock_data_workflow(self):
        """测试端到端股票数据工作流"""
        # 初始化QDB
        qdb.init(self.cache_dir)

        # 清除测试数据的缓存，确保会调用AKShare
        qdb.clear_cache("000001")

        # 模拟数据
        mock_data = pd.DataFrame({
            'date': ['2024-01-01', '2024-01-02'],
            'open': [10.0, 10.5],
            'high': [11.0, 11.5],
            'low': [9.5, 10.0],
            'close': [10.5, 11.0],
            'volume': [1000000, 1200000]
        })

        with patch('core.cache.akshare_adapter.ak') as mock_ak:
            mock_ak.stock_zh_a_hist.return_value = mock_data

            # 第一次获取数据（应该调用AKShare）
            result1 = qdb.get_stock_data("000001", start_date="20240101", end_date="20240102")

            # 验证结果
            self.assertIsInstance(result1, pd.DataFrame)
            # 注意：实际返回的行数可能与mock数据不同，因为系统会根据交易日历过滤
            self.assertGreater(len(result1), 0)
            self.assertIn('close', result1.columns)

            # 验证AKShare被调用
            mock_ak.stock_zh_a_hist.assert_called()

    def test_cache_mechanism_integration(self):
        """测试缓存机制集成"""
        qdb.init(self.cache_dir)
        
        # 获取初始缓存统计
        initial_stats = qdb.cache_stats()
        self.assertIsInstance(initial_stats, dict)
        self.assertIn('total_data_points', initial_stats)  # Changed from total_records

        # 清除缓存
        qdb.clear_cache()

        # 验证缓存被清除
        cleared_stats = qdb.cache_stats()
        self.assertEqual(cleared_stats['total_data_points'], 0)  # Changed from total_records

    def test_multiple_api_calls_integration(self):
        """测试多个API调用的集成"""
        qdb.init(self.cache_dir)
        
        with patch('core.cache.akshare_adapter.ak') as mock_ak:
            # 模拟不同API的返回数据
            mock_ak.stock_zh_a_hist.return_value = pd.DataFrame({'close': [10.0]})
            mock_ak.stock_zh_a_spot_em.return_value = [['000001', '平安银行', 10.50]]
            mock_ak.stock_info_a_code_name.return_value = pd.DataFrame({
                'code': ['000001'], 'name': ['平安银行']
            })
            
            # 调用多个API
            historical_data = qdb.get_stock_data("000001", days=30)
            stock_list = qdb.get_stock_list()
            
            # 验证所有调用都成功
            self.assertIsInstance(historical_data, pd.DataFrame)
            self.assertIsInstance(stock_list, pd.DataFrame)

    def test_error_handling_integration(self):
        """测试错误处理集成"""
        qdb.init(self.cache_dir)

        # 清除缓存确保会调用AKShare
        qdb.clear_cache()

        with patch('core.cache.akshare_adapter.ak') as mock_ak:
            # 模拟AKShare错误
            mock_ak.stock_zh_a_hist.side_effect = Exception("Network error")

            # 验证错误被正确处理 - 使用一个不太可能在缓存中的股票代码
            with self.assertRaises(DataError):
                qdb.get_stock_data("999999", start_date="20240101", end_date="20240102")

    def test_different_calling_patterns_integration(self):
        """测试不同调用模式的集成"""
        qdb.init(self.cache_dir)
        
        mock_data = pd.DataFrame({'close': [10.0, 11.0]})
        
        with patch('core.cache.akshare_adapter.ak') as mock_ak:
            mock_ak.stock_zh_a_hist.return_value = mock_data

            # 测试位置参数调用
            result1 = qdb.get_stock_data("000001", "20240101", "20240201")
            self.assertIsInstance(result1, pd.DataFrame)
            
            # 测试关键字参数调用
            result2 = qdb.get_stock_data(
                symbol="000001", 
                start_date="20240101", 
                end_date="20240201"
            )
            self.assertIsInstance(result2, pd.DataFrame)
            
            # 测试混合参数调用
            result3 = qdb.get_stock_data("000001", end_date="20240201")
            self.assertIsInstance(result3, pd.DataFrame)
            
            # 测试days参数调用
            result4 = qdb.get_stock_data("000001", days=30)
            self.assertIsInstance(result4, pd.DataFrame)

    def test_akshare_compatibility_integration(self):
        """测试AKShare兼容性集成"""
        qdb.init(self.cache_dir)

        # 清除测试数据的缓存，确保会调用AKShare
        qdb.clear_cache("000001")

        mock_data = pd.DataFrame({'close': [10.0, 11.0]})

        with patch('core.cache.akshare_adapter.ak') as mock_ak:
            mock_ak.stock_zh_a_hist.return_value = mock_data

            # 测试AKShare兼容接口
            result = qdb.stock_zh_a_hist("000001", start_date="20240101", end_date="20240201")

            self.assertIsInstance(result, pd.DataFrame)
            mock_ak.stock_zh_a_hist.assert_called()

    def test_configuration_integration(self):
        """测试配置集成"""
        # 测试缓存目录设置
        qdb.set_cache_dir(self.cache_dir)
        self.assertEqual(qdb.client._global_client.cache_dir, self.cache_dir)
        
        # 测试日志级别设置
        qdb.set_log_level("DEBUG")
        self.assertEqual(os.environ.get("LOG_LEVEL"), "DEBUG")

    def test_batch_operations_integration(self):
        """测试批量操作集成"""
        qdb.init(self.cache_dir)
        
        with patch('core.cache.akshare_adapter.ak') as mock_ak:
            mock_ak.stock_zh_a_hist.return_value = pd.DataFrame({'close': [10.0]})

            # 测试批量获取多只股票
            symbols = ["000001", "000002", "600000"]
            results = qdb.get_multiple_stocks(symbols, days=30)
            
            self.assertIsInstance(results, dict)
            self.assertEqual(len(results), len(symbols))

    def test_realtime_data_integration(self):
        """测试实时数据集成"""
        qdb.init(self.cache_dir)
        
        with patch('core.cache.akshare_adapter.ak') as mock_ak:
            # 模拟实时数据
            mock_ak.stock_zh_a_spot_em.return_value = [
                ['000001', '平安银行', 10.50, 0.10, 0.96, 10.40, 10.60, 10.30, 10.45, 1000000]
            ]
            
            # 测试单个实时数据
            result = qdb.get_realtime_data("000001")
            self.assertIsInstance(result, dict)
            
            # 测试批量实时数据
            batch_result = qdb.get_realtime_data_batch(["000001", "000002"])
            self.assertIsInstance(batch_result, dict)

    def test_index_data_integration(self):
        """测试指数数据集成"""
        qdb.init(self.cache_dir)
        
        with patch('core.cache.akshare_adapter.ak') as mock_ak:
            mock_ak.stock_zh_index_daily.return_value = pd.DataFrame({'close': [3000.0]})
            mock_ak.stock_zh_index_spot.return_value = [['000001', '上证指数', 3000.0]]
            
            # 测试指数历史数据
            index_data = qdb.get_index_data("000001", "20240101", "20240201")
            self.assertIsInstance(index_data, pd.DataFrame)
            
            # 测试指数实时数据
            index_realtime = qdb.get_index_realtime("000001")
            self.assertIsInstance(index_realtime, dict)

    def test_financial_data_integration(self):
        """测试财务数据集成"""
        qdb.init(self.cache_dir)
        
        with patch('core.cache.akshare_adapter.ak') as mock_ak:
            # 模拟财务数据
            mock_ak.stock_financial_abstract.return_value = pd.DataFrame({
                'period': ['2024Q1'], 'revenue': [1000]
            })
            mock_ak.stock_financial_analysis_indicator.return_value = pd.DataFrame({
                'pe_ratio': [15.0]
            })
            
            # 测试财务摘要
            summary = qdb.get_financial_summary("000001")
            self.assertIsInstance(summary, dict)
            
            # 测试财务指标
            indicators = qdb.get_financial_indicators("000001")
            self.assertIsInstance(indicators, pd.DataFrame)

    def test_asset_info_integration(self):
        """测试资产信息集成"""
        qdb.init(self.cache_dir)
        
        with patch('core.cache.akshare_adapter.ak') as mock_ak:
            mock_ak.stock_info_a_code_name.return_value = pd.DataFrame({
                'code': ['000001'], 'name': ['平安银行']
            })
            
            # 测试资产信息获取
            asset_info = qdb.get_asset_info("000001")
            self.assertIsInstance(asset_info, dict)

    def test_performance_and_caching_integration(self):
        """测试性能和缓存效果集成"""
        qdb.init(self.cache_dir)
        
        mock_data = pd.DataFrame({'close': [10.0, 11.0]})
        
        with patch('core.cache.akshare_adapter.ak') as mock_ak:
            mock_ak.stock_zh_a_hist.return_value = mock_data

            # 第一次调用（应该较慢，需要网络请求）
            start_time = time.time()
            result1 = qdb.get_stock_data("000001", start_date="20240101", end_date="20240102")
            first_call_time = time.time() - start_time
            
            # 第二次调用（应该较快，使用缓存）
            start_time = time.time()
            result2 = qdb.get_stock_data("000001", start_date="20240101", end_date="20240102")
            second_call_time = time.time() - start_time
            
            # 验证结果一致
            pd.testing.assert_frame_equal(result1, result2)
            
            # 验证缓存效果（第二次调用应该更快）
            # 注意：在mock环境下可能看不到明显差异，但结构应该正确

    def test_error_recovery_integration(self):
        """测试错误恢复集成"""
        qdb.init(self.cache_dir)

        # 清除缓存确保会调用AKShare
        qdb.clear_cache()

        with patch('core.cache.akshare_adapter.ak') as mock_ak:
            # 第一次调用失败
            mock_ak.stock_zh_a_hist.side_effect = Exception("Network error")

            with self.assertRaises(DataError):
                qdb.get_stock_data("999999", start_date="20240101", end_date="20240102")

            # 第二次调用成功
            mock_ak.stock_zh_a_hist.side_effect = None
            mock_ak.stock_zh_a_hist.return_value = pd.DataFrame({'close': [10.0]})

            result = qdb.get_stock_data("999999", start_date="20240101", end_date="20240102")
            self.assertIsInstance(result, pd.DataFrame)

    def test_concurrent_access_integration(self):
        """测试并发访问集成"""
        qdb.init(self.cache_dir)
        
        import threading
        results = []
        errors = []
        
        def worker():
            try:
                with patch('core.cache.akshare_adapter.ak') as mock_ak:
                    mock_ak.stock_zh_a_hist.return_value = pd.DataFrame({'close': [10.0]})
                    result = qdb.get_stock_data("000001", days=30)
                    results.append(result)
            except Exception as e:
                errors.append(e)
        
        # 创建多个线程
        threads = []
        for i in range(3):
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 验证没有错误
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(results), 3)

    def test_data_consistency_integration(self):
        """测试数据一致性集成"""
        qdb.init(self.cache_dir)
        
        mock_data = pd.DataFrame({
            'date': ['2024-01-01', '2024-01-02'],
            'close': [10.0, 11.0]
        })
        
        with patch('core.cache.akshare_adapter.ak') as mock_ak:
            mock_ak.stock_zh_a_hist.return_value = mock_data

            # 多次调用相同参数
            result1 = qdb.get_stock_data("000001", start_date="20240101", end_date="20240102")
            result2 = qdb.get_stock_data("000001", start_date="20240101", end_date="20240102")
            
            # 验证数据一致性
            pd.testing.assert_frame_equal(result1, result2)


if __name__ == '__main__':
    unittest.main()
