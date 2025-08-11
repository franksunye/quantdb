"""
专门用于提升qdb包覆盖率的测试

重点测试未覆盖的代码路径和边界条件
"""

import os
import shutil
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

import pandas as pd

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import qdb
from qdb.exceptions import CacheError, DataError, QDBError
from qdb.simple_client import SimpleQDBClient


class TestQDBCoverageBoost(unittest.TestCase):
    """提升qdb包覆盖率的专门测试"""

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

    def test_qdb_init_with_cache_dir(self):
        """测试qdb.init带缓存目录参数"""
        qdb.init(self.cache_dir)
        self.assertIsNotNone(qdb.client._global_client)
        self.assertEqual(qdb.client._global_client.cache_dir, self.cache_dir)

    def test_qdb_init_without_cache_dir(self):
        """测试qdb.init不带参数"""
        qdb.init()
        self.assertIsNotNone(qdb.client._global_client)

    def test_get_stock_data_with_days_parameter(self):
        """测试get_stock_data的days参数"""
        with patch('qdb.client._get_client') as mock_get_client:
            mock_client = MagicMock()
            mock_data = pd.DataFrame({'close': [10.0, 11.0]})
            mock_client.get_stock_data.return_value = mock_data
            mock_get_client.return_value = mock_client
            
            result = qdb.get_stock_data("000001", days=30)
            
            self.assertIsInstance(result, pd.DataFrame)
            mock_client.get_stock_data.assert_called()

    def test_get_stock_data_with_adjust_parameter(self):
        """测试get_stock_data的adjust参数"""
        with patch('qdb.client._get_client') as mock_get_client:
            mock_client = MagicMock()
            mock_data = pd.DataFrame({'close': [10.0, 11.0]})
            mock_client.get_stock_data.return_value = mock_data
            mock_get_client.return_value = mock_client
            
            result = qdb.get_stock_data("000001", adjust="qfq")
            
            self.assertIsInstance(result, pd.DataFrame)
            mock_client.get_stock_data.assert_called()

    def test_get_multiple_stocks_with_various_params(self):
        """测试get_multiple_stocks的各种参数"""
        with patch('qdb.client._get_client') as mock_get_client:
            mock_client = MagicMock()
            mock_data = {"000001": pd.DataFrame({'close': [10.0]})}
            mock_client.get_multiple_stocks.return_value = mock_data
            mock_get_client.return_value = mock_client
            
            # 测试不同参数组合
            result1 = qdb.get_multiple_stocks(["000001"], days=30)
            result2 = qdb.get_multiple_stocks(["000001"], start_date="20240101")
            result3 = qdb.get_multiple_stocks(["000001"], end_date="20240201")
            
            self.assertIsInstance(result1, dict)
            self.assertIsInstance(result2, dict)
            self.assertIsInstance(result3, dict)

    def test_stock_zh_a_hist_compatibility(self):
        """测试AKShare兼容性接口的各种调用方式"""
        with patch('qdb.client._get_client') as mock_get_client:
            mock_client = MagicMock()
            mock_data = pd.DataFrame({'close': [10.0, 11.0]})
            mock_client.get_stock_data.return_value = mock_data
            mock_get_client.return_value = mock_client
            
            # 测试不同参数组合
            result1 = qdb.stock_zh_a_hist("000001")
            result2 = qdb.stock_zh_a_hist("000001", start_date="20240101")
            result3 = qdb.stock_zh_a_hist("000001", period="daily")
            result4 = qdb.stock_zh_a_hist("000001", adjust="qfq")
            
            self.assertIsInstance(result1, pd.DataFrame)
            self.assertIsInstance(result2, pd.DataFrame)
            self.assertIsInstance(result3, pd.DataFrame)
            self.assertIsInstance(result4, pd.DataFrame)

    def test_financial_summary_with_force_refresh(self):
        """测试get_financial_summary的force_refresh参数"""
        with patch('qdb.client._get_client') as mock_get_client:
            mock_client = MagicMock()
            mock_data = {"quarters": [{"period": "2024Q1"}]}
            mock_client.get_financial_summary.return_value = mock_data
            mock_get_client.return_value = mock_client
            
            # 测试force_refresh参数
            result1 = qdb.get_financial_summary("000001")
            result2 = qdb.get_financial_summary("000001", force_refresh=True)
            result3 = qdb.get_financial_summary("000001", force_refresh=False)
            
            self.assertIsInstance(result1, dict)
            self.assertIsInstance(result2, dict)
            self.assertIsInstance(result3, dict)

    def test_realtime_data_with_force_refresh(self):
        """测试实时数据的force_refresh参数"""
        with patch('qdb.client._get_client') as mock_get_client:
            mock_client = MagicMock()
            mock_data = {"symbol": "000001", "current_price": 10.5}
            mock_client.get_realtime_data.return_value = mock_data
            mock_get_client.return_value = mock_client
            
            # 测试force_refresh参数
            result1 = qdb.get_realtime_data("000001")
            result2 = qdb.get_realtime_data("000001", force_refresh=True)
            result3 = qdb.get_realtime_data("000001", force_refresh=False)
            
            self.assertIsInstance(result1, dict)
            self.assertIsInstance(result2, dict)
            self.assertIsInstance(result3, dict)

    def test_index_data_with_various_params(self):
        """测试指数数据的各种参数"""
        with patch('qdb.client._get_client') as mock_get_client:
            mock_client = MagicMock()
            mock_data = pd.DataFrame({'close': [3000.0]})
            mock_client.get_index_data.return_value = mock_data
            mock_get_client.return_value = mock_client
            
            # 测试不同参数组合
            result1 = qdb.get_index_data("000001")
            result2 = qdb.get_index_data("000001", "20240101")
            result3 = qdb.get_index_data("000001", "20240101", "20240201")
            result4 = qdb.get_index_data("000001", period="weekly")
            result5 = qdb.get_index_data("000001", force_refresh=True)
            
            for result in [result1, result2, result3, result4, result5]:
                self.assertIsInstance(result, pd.DataFrame)

    def test_index_realtime_with_force_refresh(self):
        """测试指数实时数据的force_refresh参数"""
        with patch('qdb.client._get_client') as mock_get_client:
            mock_client = MagicMock()
            mock_data = {"symbol": "000001", "current": 3000.0}
            mock_client.get_index_realtime.return_value = mock_data
            mock_get_client.return_value = mock_client
            
            result1 = qdb.get_index_realtime("000001")
            result2 = qdb.get_index_realtime("000001", force_refresh=True)
            
            self.assertIsInstance(result1, dict)
            self.assertIsInstance(result2, dict)

    def test_batch_realtime_data_with_force_refresh(self):
        """测试批量实时数据的force_refresh参数"""
        with patch('qdb.client._get_client') as mock_get_client:
            mock_client = MagicMock()
            mock_data = {"000001": {"current_price": 10.5}}
            mock_client.get_realtime_data_batch.return_value = mock_data
            mock_get_client.return_value = mock_client
            
            result1 = qdb.get_realtime_data_batch(["000001"])
            result2 = qdb.get_realtime_data_batch(["000001"], force_refresh=True)
            
            self.assertIsInstance(result1, dict)
            self.assertIsInstance(result2, dict)

    def test_configuration_functions(self):
        """测试配置函数"""
        # 测试set_cache_dir
        original_client = qdb.client._global_client
        qdb.set_cache_dir(self.cache_dir)
        self.assertIsNotNone(qdb.client._global_client)
        
        # 测试set_log_level
        original_level = os.environ.get("LOG_LEVEL")
        qdb.set_log_level("INFO")
        self.assertEqual(os.environ.get("LOG_LEVEL"), "INFO")
        
        qdb.set_log_level("DEBUG")
        self.assertEqual(os.environ.get("LOG_LEVEL"), "DEBUG")
        
        # 恢复原始状态
        if original_level:
            os.environ["LOG_LEVEL"] = original_level
        elif "LOG_LEVEL" in os.environ:
            del os.environ["LOG_LEVEL"]

    def test_client_reuse(self):
        """测试客户端重用机制"""
        # 第一次获取客户端
        client1 = qdb.client._get_client()
        
        # 第二次获取应该是同一个客户端
        client2 = qdb.client._get_client()
        
        self.assertEqual(client1, client2)

    def test_simple_client_direct_usage(self):
        """测试直接使用SimpleQDBClient"""
        with patch('qdb.simple_client.AKSHARE_AVAILABLE', True):
            with patch('qdb.simple_client.ak') as mock_ak:
                mock_ak.stock_zh_a_hist.return_value = pd.DataFrame({'close': [10.0]})
                
                client = SimpleQDBClient(self.cache_dir)
                
                # 测试各种方法
                result1 = client.get_stock_data("000001")
                stats = client.cache_stats()
                
                self.assertIsInstance(result1, pd.DataFrame)
                self.assertIsInstance(stats, dict)

    def test_error_scenarios(self):
        """测试各种错误场景"""
        with patch('qdb.client._get_client') as mock_get_client:
            mock_client = MagicMock()
            
            # 测试不同类型的异常
            mock_client.get_stock_data.side_effect = [
                ConnectionError("Network error"),
                ValueError("Invalid data"),
                Exception("Unknown error")
            ]
            mock_get_client.return_value = mock_client
            
            # 这些调用应该传播异常
            for i in range(3):
                with self.assertRaises(Exception):
                    qdb.get_stock_data("000001")

    def test_all_api_functions_exist(self):
        """测试所有API函数都存在且可调用"""
        api_functions = [
            'init', 'get_stock_data', 'get_multiple_stocks', 'get_asset_info',
            'get_realtime_data', 'get_realtime_data_batch', 'get_stock_list',
            'get_index_data', 'get_index_realtime', 'get_index_list',
            'get_financial_summary', 'get_financial_indicators',
            'cache_stats', 'clear_cache', 'stock_zh_a_hist',
            'set_cache_dir', 'set_log_level'
        ]
        
        for func_name in api_functions:
            with self.subTest(function=func_name):
                self.assertTrue(hasattr(qdb, func_name))
                func = getattr(qdb, func_name)
                self.assertTrue(callable(func))

    def test_version_and_metadata(self):
        """测试版本和元数据"""
        self.assertTrue(hasattr(qdb, '__version__'))
        self.assertTrue(hasattr(qdb, '__author__'))
        self.assertTrue(hasattr(qdb, '__email__'))
        self.assertTrue(hasattr(qdb, '__description__'))
        
        # 验证版本格式
        version = qdb.__version__
        self.assertIsInstance(version, str)
        self.assertRegex(version, r'^\d+\.\d+\.\d+.*$')


if __name__ == '__main__':
    unittest.main()
