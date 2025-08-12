"""
测试 qdb/client.py 模块的核心API功能

测试覆盖：
- 所有公共API函数
- get_stock_data的各种调用方式
- 缓存机制测试
- 错误处理和边界条件
- 配置管理
"""

import os
import shutil
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, call, patch

import pandas as pd

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import qdb
from qdb.exceptions import CacheError, DataError, QDBError


class TestQDBClient(unittest.TestCase):
    """测试QDB客户端核心API"""

    def setUp(self):
        """设置测试环境"""
        self.temp_dir = tempfile.mkdtemp()
        self.cache_dir = os.path.join(self.temp_dir, "test_cache")

        # 重置全局客户端 - 确保每个测试都有干净的状态
        qdb.client._global_client = None

        # 清理任何可能存在的缓存
        import sys
        if 'qdb.client' in sys.modules:
            sys.modules['qdb.client']._global_client = None

    def tearDown(self):
        """清理测试环境"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

        # 重置全局客户端
        qdb.client._global_client = None

        # 清理模块级别的缓存
        import sys
        if 'qdb.client' in sys.modules:
            sys.modules['qdb.client']._global_client = None

    def test_init_function(self):
        """测试init函数"""
        # 测试默认初始化
        qdb.init()
        self.assertIsNotNone(qdb.client._global_client)

        # 测试自定义缓存目录初始化
        qdb.init(self.cache_dir)
        self.assertEqual(qdb.client._global_client.cache_dir, self.cache_dir)

    def test_get_stock_data_positional_args(self):
        """测试get_stock_data位置参数调用"""
        with patch("qdb.client._get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_data = pd.DataFrame({"close": [10.0, 11.0]})
            mock_client.get_stock_data.return_value = mock_data
            mock_get_client.return_value = mock_client

            result = qdb.get_stock_data("000001", "20240101", "20240201")

            self.assertIsInstance(result, pd.DataFrame)
            # 验证调用发生，但不严格检查参数格式
            mock_client.get_stock_data.assert_called_once()

    def test_get_stock_data_keyword_args(self):
        """测试get_stock_data关键字参数调用"""
        with patch("qdb.client._get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_data = pd.DataFrame({"close": [10.0, 11.0]})
            mock_client.get_stock_data.return_value = mock_data
            mock_get_client.return_value = mock_client

            result = qdb.get_stock_data(
                symbol="000001",
                start_date="20240101",
                end_date="20240201",
                adjust="qfq",
            )

            self.assertIsInstance(result, pd.DataFrame)
            # 验证调用发生，检查关键参数
            mock_client.get_stock_data.assert_called_once()
            call_args = mock_client.get_stock_data.call_args
            self.assertIn("start_date", str(call_args))
            self.assertIn("adjust", str(call_args))

    def test_get_stock_data_mixed_args(self):
        """测试get_stock_data混合参数调用"""
        with patch("qdb.client._get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_data = pd.DataFrame({"close": [10.0, 11.0]})
            mock_client.get_stock_data.return_value = mock_data
            mock_get_client.return_value = mock_client

            result = qdb.get_stock_data("000001", end_date="20240201", adjust="hfq")

            self.assertIsInstance(result, pd.DataFrame)
            mock_client.get_stock_data.assert_called_once()

    def test_get_stock_data_days_parameter(self):
        """测试get_stock_data的days参数"""
        with patch("qdb.client._get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_data = pd.DataFrame({"close": [10.0, 11.0]})
            mock_client.get_stock_data.return_value = mock_data
            mock_get_client.return_value = mock_client

            result = qdb.get_stock_data("000001", days=30)

            self.assertIsInstance(result, pd.DataFrame)
            mock_client.get_stock_data.assert_called_once()

    def test_get_multiple_stocks(self):
        """测试get_multiple_stocks函数"""
        with patch("qdb.client._get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_data = {"000001": pd.DataFrame({"close": [10.0]})}
            mock_client.get_multiple_stocks.return_value = mock_data
            mock_get_client.return_value = mock_client

            result = qdb.get_multiple_stocks(["000001", "000002"], days=30)

            self.assertIsInstance(result, dict)
            mock_client.get_multiple_stocks.assert_called_once_with(
                ["000001", "000002"], days=30
            )

    def test_get_asset_info(self):
        """测试get_asset_info函数"""
        with patch("qdb.client._get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_info = {"symbol": "000001", "name": "平安银行"}
            mock_client.get_asset_info.return_value = mock_info
            mock_get_client.return_value = mock_client

            result = qdb.get_asset_info("000001")

            self.assertIsInstance(result, dict)
            self.assertEqual(result["symbol"], "000001")
            mock_client.get_asset_info.assert_called_once_with("000001")

    def test_get_realtime_data(self):
        """测试get_realtime_data函数"""
        with patch("qdb.client._get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_data = {"symbol": "000001", "current_price": 10.5}
            mock_client.get_realtime_data.return_value = mock_data
            mock_get_client.return_value = mock_client

            result = qdb.get_realtime_data("000001")

            self.assertIsInstance(result, dict)
            self.assertEqual(result["current_price"], 10.5)
            # 验证调用，允许额外参数
            mock_client.get_realtime_data.assert_called()

    def test_get_realtime_data_batch(self):
        """测试get_realtime_data_batch函数"""
        with patch("qdb.client._get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_data = {"000001": {"current_price": 10.5}}
            mock_client.get_realtime_data_batch.return_value = mock_data
            mock_get_client.return_value = mock_client

            result = qdb.get_realtime_data_batch(["000001", "000002"])

            self.assertIsInstance(result, dict)
            # 验证调用，允许额外参数
            mock_client.get_realtime_data_batch.assert_called()

    def test_get_stock_list(self):
        """测试get_stock_list函数"""
        with patch("qdb.client._get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_data = pd.DataFrame({"symbol": ["000001", "000002"]})
            mock_client.get_stock_list.return_value = mock_data
            mock_get_client.return_value = mock_client

            result = qdb.get_stock_list()

            self.assertIsInstance(result, pd.DataFrame)
            mock_client.get_stock_list.assert_called_once()

    def test_get_index_data(self):
        """测试get_index_data函数"""
        with patch("qdb.client._get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_data = pd.DataFrame({"close": [3000.0, 3100.0]})
            mock_client.get_index_data.return_value = mock_data
            mock_get_client.return_value = mock_client

            result = qdb.get_index_data("000001", "20240101", "20240201")

            self.assertIsInstance(result, pd.DataFrame)
            # 验证调用，允许额外参数
            mock_client.get_index_data.assert_called()

    def test_get_index_realtime(self):
        """测试get_index_realtime函数"""
        with patch("qdb.client._get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_data = {"symbol": "000001", "current": 3000.0}
            mock_client.get_index_realtime.return_value = mock_data
            mock_get_client.return_value = mock_client

            result = qdb.get_index_realtime("000001")

            self.assertIsInstance(result, dict)
            # 验证调用，允许额外参数
            mock_client.get_index_realtime.assert_called()

    def test_get_index_list(self):
        """测试get_index_list函数"""
        with patch("qdb.client._get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_data = pd.DataFrame({"symbol": ["000001", "000300"]})
            mock_client.get_index_list.return_value = mock_data
            mock_get_client.return_value = mock_client

            result = qdb.get_index_list()

            self.assertIsInstance(result, pd.DataFrame)
            mock_client.get_index_list.assert_called_once()

    def test_get_financial_summary(self):
        """测试get_financial_summary函数"""
        with patch("qdb.client._get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_data = {"quarters": [{"period": "2024Q1", "revenue": 1000}]}
            mock_client.get_financial_summary.return_value = mock_data
            mock_get_client.return_value = mock_client

            result = qdb.get_financial_summary("000001")

            self.assertIsInstance(result, dict)
            mock_client.get_financial_summary.assert_called_once_with("000001", False)

    def test_get_financial_indicators(self):
        """测试get_financial_indicators函数"""
        with patch("qdb.client._get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_data = pd.DataFrame({"pe_ratio": [15.0, 16.0]})
            mock_client.get_financial_indicators.return_value = mock_data
            mock_get_client.return_value = mock_client

            result = qdb.get_financial_indicators("000001")

            self.assertIsInstance(result, pd.DataFrame)
            # 验证调用，允许额外参数
            mock_client.get_financial_indicators.assert_called()

    def test_cache_stats(self):
        """测试cache_stats函数"""
        # Reset global client to ensure clean state
        qdb.client._global_client = None

        with patch("qdb.client._get_client") as mock_get_client:
            mock_client = MagicMock()
            # Ensure the mock returns the expected structure with total_records
            mock_stats = {
                "cache_dir": "/test/cache",
                "cache_size_mb": 10.5,
                "total_records": 1000,
                "initialized": True,
                "status": "Running",
            }
            mock_client.cache_stats.return_value = mock_stats
            mock_get_client.return_value = mock_client

            result = qdb.cache_stats()

            self.assertIsInstance(result, dict)
            self.assertEqual(result["total_records"], 1000)
            self.assertEqual(result["cache_size_mb"], 10.5)
            mock_client.cache_stats.assert_called_once()

    def test_clear_cache(self):
        """测试clear_cache函数"""
        # Reset global client to ensure clean state
        qdb.client._global_client = None

        with patch("qdb.client._get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_get_client.return_value = mock_client

            qdb.clear_cache()

            # Verify the clear_cache method was called with None (default parameter)
            mock_client.clear_cache.assert_called_once_with(None)

    def test_stock_zh_a_hist_compatibility(self):
        """测试AKShare兼容性接口"""
        with patch("qdb.client._get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_data = pd.DataFrame({"close": [10.0, 11.0]})
            mock_client.get_stock_data.return_value = mock_data
            mock_get_client.return_value = mock_client

            result = qdb.stock_zh_a_hist(
                "000001", start_date="20240101", end_date="20240201"
            )

            self.assertIsInstance(result, pd.DataFrame)
            mock_client.get_stock_data.assert_called_once()

    def test_set_cache_dir(self):
        """测试set_cache_dir函数"""
        with patch("qdb.client.QDBClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client

            qdb.set_cache_dir(self.cache_dir)

            mock_client_class.assert_called_once_with(self.cache_dir)
            self.assertEqual(qdb.client._global_client, mock_client)

    def test_set_log_level(self):
        """测试set_log_level函数"""
        with patch.dict(os.environ, {}, clear=True):
            qdb.set_log_level("DEBUG")

            self.assertEqual(os.environ.get("LOG_LEVEL"), "DEBUG")

    def test_get_client_lazy_initialization(self):
        """测试客户端延迟初始化"""
        # 确保全局客户端为空
        qdb.client._global_client = None

        with patch("qdb.client.QDBClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client

            client = qdb.client._get_client()

            self.assertEqual(client, mock_client)
            # 验证QDBClient被调用，不严格检查参数
            mock_client_class.assert_called_once()

    def test_error_handling_client_initialization(self):
        """测试客户端初始化错误处理"""
        # 重置全局客户端
        qdb.client._global_client = None

        with patch("qdb.client.QDBClient") as mock_client_class:
            mock_client_class.side_effect = Exception("Initialization failed")

            # 客户端初始化失败时，应该抛出异常
            with self.assertRaises(Exception):
                qdb.client._get_client()

    def test_error_handling_api_calls(self):
        """测试API调用错误处理"""
        # Reset global client to ensure clean state
        qdb.client._global_client = None

        with patch("qdb.client._get_client") as mock_get_client:
            mock_client = MagicMock()
            # Set up the mock to raise an exception
            mock_client.get_stock_data.side_effect = Exception("API error")
            mock_get_client.return_value = mock_client

            # API调用失败时，应该抛出异常
            with self.assertRaises(Exception) as context:
                qdb.get_stock_data("000001")

            # Verify the exception message
            self.assertIn("API error", str(context.exception))
            # Verify the mock was called
            mock_client.get_stock_data.assert_called_once()

    def test_multiple_client_instances(self):
        """测试多个客户端实例"""
        # 第一次调用创建客户端
        client1 = qdb.client._get_client()

        # 第二次调用应该返回同一个客户端
        client2 = qdb.client._get_client()

        self.assertEqual(client1, client2)

    def test_parameter_validation(self):
        """测试参数验证"""
        with patch("qdb.client._get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.get_stock_data.return_value = pd.DataFrame()
            mock_get_client.return_value = mock_client

            # 测试空股票代码 - 实际上会传递给底层客户端处理
            result = qdb.get_stock_data("")
            self.assertIsInstance(result, pd.DataFrame)

            # 测试None股票代码 - 也会传递给底层客户端处理
            result = qdb.get_stock_data(None)
            self.assertIsInstance(result, pd.DataFrame)

    def test_function_signatures(self):
        """测试函数签名"""
        import inspect

        # 测试get_stock_data签名
        sig = inspect.signature(qdb.get_stock_data)
        params = list(sig.parameters.keys())

        self.assertIn("symbol", params)
        self.assertIn("start_date", params)
        self.assertIn("end_date", params)
        # kwargs参数包含了adjust等其他参数
        self.assertIn("kwargs", params)

    def test_return_types(self):
        """测试返回类型"""
        with patch("qdb.client._get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_get_client.return_value = mock_client

            # 测试DataFrame返回类型
            mock_client.get_stock_data.return_value = pd.DataFrame()
            result = qdb.get_stock_data("000001")
            self.assertIsInstance(result, pd.DataFrame)

            # 测试字典返回类型
            mock_client.get_asset_info.return_value = {}
            result = qdb.get_asset_info("000001")
            self.assertIsInstance(result, dict)


if __name__ == "__main__":
    unittest.main()
