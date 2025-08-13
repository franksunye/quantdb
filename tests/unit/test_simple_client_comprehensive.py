"""
SimpleQDBClient的全面测试，专门提升覆盖率

重点测试所有未覆盖的方法和代码路径
"""

import os
import shutil
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

import pandas as pd

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# from qdb.simple_client import SimpleQDBClient  # DEPRECATED: Module no longer exists
import pytest

# Import the replacement class to avoid flake8 errors
from qdb.client import LightweightQDBClient as SimpleQDBClient
from qdb.exceptions import CacheError, DataError, QDBError

pytestmark = pytest.mark.skip(reason="DEPRECATED: simple_client module no longer exists")


class TestSimpleClientComprehensive(unittest.TestCase):
    """SimpleQDBClient的全面测试"""

    def setUp(self):
        """设置测试环境"""
        self.temp_dir = tempfile.mkdtemp()
        self.cache_dir = os.path.join(self.temp_dir, "test_cache")

    def tearDown(self):
        """清理测试环境"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    @patch('qdb.simple_client.AKSHARE_AVAILABLE', True)
    @patch('qdb.simple_client.ak')
    def test_get_stock_list(self, mock_ak):
        """测试get_stock_list方法"""
        mock_ak.stock_info_a_code_name.return_value = pd.DataFrame({
            'code': ['000001', '000002'],
            'name': ['平安银行', '万科A']
        })
        
        client = SimpleQDBClient(self.cache_dir)
        result = client.get_stock_list()
        
        self.assertIsInstance(result, pd.DataFrame)
        mock_ak.stock_info_a_code_name.assert_called_once()

    @patch('qdb.simple_client.AKSHARE_AVAILABLE', True)
    @patch('qdb.simple_client.ak')
    def test_get_asset_info(self, mock_ak):
        """测试get_asset_info方法"""
        mock_ak.stock_info_a_code_name.return_value = pd.DataFrame({
            'code': ['000001'],
            'name': ['平安银行']
        })
        
        client = SimpleQDBClient(self.cache_dir)
        result = client.get_asset_info("000001")
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result['symbol'], '000001')
        self.assertEqual(result['name'], '平安银行')

    @patch('qdb.simple_client.AKSHARE_AVAILABLE', True)
    @patch('qdb.simple_client.ak')
    def test_get_multiple_stocks(self, mock_ak):
        """测试get_multiple_stocks方法"""
        mock_ak.stock_zh_a_hist.return_value = pd.DataFrame({
            'date': ['2024-01-01'],
            'close': [10.0]
        })
        
        client = SimpleQDBClient(self.cache_dir)
        result = client.get_multiple_stocks(['000001', '000002'], days=30)
        
        self.assertIsInstance(result, dict)
        self.assertIn('000001', result)
        self.assertIn('000002', result)

    @patch('qdb.simple_client.AKSHARE_AVAILABLE', True)
    @patch('qdb.simple_client.ak')
    def test_get_realtime_data(self, mock_ak):
        """测试get_realtime_data方法"""
        mock_ak.stock_zh_a_spot_em.return_value = [
            ['000001', '平安银行', 10.50, 0.10, 0.96, 10.40, 10.60, 10.30, 10.45, 1000000]
        ]
        
        client = SimpleQDBClient(self.cache_dir)
        result = client.get_realtime_data("000001")
        
        self.assertIsInstance(result, dict)
        self.assertIn('symbol', result)
        self.assertIn('current_price', result)

    @patch('qdb.simple_client.AKSHARE_AVAILABLE', True)
    @patch('qdb.simple_client.ak')
    def test_get_realtime_data_batch(self, mock_ak):
        """测试get_realtime_data_batch方法"""
        mock_ak.stock_zh_a_spot_em.return_value = [
            ['000001', '平安银行', 10.50, 0.10, 0.96, 10.40, 10.60, 10.30, 10.45, 1000000],
            ['000002', '万科A', 20.30, -0.20, -0.98, 20.50, 20.60, 20.20, 20.35, 2000000]
        ]
        
        client = SimpleQDBClient(self.cache_dir)
        result = client.get_realtime_data_batch(['000001', '000002'])
        
        self.assertIsInstance(result, dict)
        self.assertIn('000001', result)
        self.assertIn('000002', result)

    @patch('qdb.simple_client.AKSHARE_AVAILABLE', True)
    @patch('qdb.simple_client.ak')
    def test_get_index_data(self, mock_ak):
        """测试get_index_data方法"""
        mock_ak.stock_zh_index_daily.return_value = pd.DataFrame({
            'date': ['2024-01-01'],
            'close': [3000.0]
        })
        
        client = SimpleQDBClient(self.cache_dir)
        result = client.get_index_data("000001", "20240101", "20240201")
        
        self.assertIsInstance(result, pd.DataFrame)
        mock_ak.stock_zh_index_daily.assert_called()

    @patch('qdb.simple_client.AKSHARE_AVAILABLE', True)
    @patch('qdb.simple_client.ak')
    def test_get_index_realtime(self, mock_ak):
        """测试get_index_realtime方法"""
        mock_ak.stock_zh_index_spot.return_value = [
            ['000001', '上证指数', 3000.0, 10.0, 0.33]
        ]
        
        client = SimpleQDBClient(self.cache_dir)
        result = client.get_index_realtime("000001")
        
        self.assertIsInstance(result, dict)
        self.assertIn('symbol', result)
        self.assertIn('current', result)

    @patch('qdb.simple_client.AKSHARE_AVAILABLE', True)
    @patch('qdb.simple_client.ak')
    def test_get_index_list(self, mock_ak):
        """测试get_index_list方法"""
        mock_ak.stock_zh_index_spot.return_value = [
            ['000001', '上证指数', 3000.0, 10.0, 0.33],
            ['000300', '沪深300', 4000.0, 20.0, 0.50]
        ]
        
        client = SimpleQDBClient(self.cache_dir)
        result = client.get_index_list()
        
        self.assertIsInstance(result, pd.DataFrame)
        mock_ak.stock_zh_index_spot.assert_called_once()

    @patch('qdb.simple_client.AKSHARE_AVAILABLE', True)
    @patch('qdb.simple_client.ak')
    def test_get_financial_summary(self, mock_ak):
        """测试get_financial_summary方法"""
        mock_ak.stock_financial_abstract.return_value = pd.DataFrame({
            'period': ['2024Q1', '2023Q4'],
            'revenue': [1000, 950]
        })
        
        client = SimpleQDBClient(self.cache_dir)
        result = client.get_financial_summary("000001")
        
        self.assertIsInstance(result, dict)
        self.assertIn('quarters', result)

    @patch('qdb.simple_client.AKSHARE_AVAILABLE', True)
    @patch('qdb.simple_client.ak')
    def test_get_financial_indicators(self, mock_ak):
        """测试get_financial_indicators方法"""
        mock_ak.stock_financial_analysis_indicator.return_value = pd.DataFrame({
            'period': ['2024Q1'],
            'pe_ratio': [15.0]
        })
        
        client = SimpleQDBClient(self.cache_dir)
        result = client.get_financial_indicators("000001")
        
        self.assertIsInstance(result, pd.DataFrame)
        mock_ak.stock_financial_analysis_indicator.assert_called()

    def test_cache_operations(self):
        """测试缓存操作"""
        client = SimpleQDBClient(self.cache_dir)
        
        # 测试缓存统计
        stats = client.cache_stats()
        self.assertIsInstance(stats, dict)
        self.assertIn('total_records', stats)
        self.assertIn('cache_size_mb', stats)
        
        # 测试清除缓存
        client.clear_cache()
        
        # 再次检查统计
        stats_after = client.cache_stats()
        self.assertEqual(stats_after['total_records'], 0)

    def test_database_operations(self):
        """测试数据库操作"""
        client = SimpleQDBClient(self.cache_dir)
        
        # 测试数据库连接
        conn = client._get_connection()
        self.assertIsInstance(conn, sqlite3.Connection)
        
        # 测试表创建
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        self.assertGreater(len(tables), 0)
        
        conn.close()

    def test_error_handling_no_akshare(self):
        """测试没有AKShare时的错误处理"""
        with patch('qdb.simple_client.AKSHARE_AVAILABLE', False):
            client = SimpleQDBClient(self.cache_dir)
            
            with self.assertRaises(QDBError):
                client.get_stock_data("000001")

    def test_error_handling_akshare_exceptions(self):
        """测试AKShare异常处理"""
        with patch('qdb.simple_client.AKSHARE_AVAILABLE', True):
            with patch('qdb.simple_client.ak') as mock_ak:
                mock_ak.stock_zh_a_hist.side_effect = Exception("AKShare error")
                
                client = SimpleQDBClient(self.cache_dir)
                
                with self.assertRaises(DataError):
                    client.get_stock_data("000001")

    def test_date_parameter_handling(self):
        """测试日期参数处理"""
        with patch('qdb.simple_client.AKSHARE_AVAILABLE', True):
            with patch('qdb.simple_client.ak') as mock_ak:
                mock_ak.stock_zh_a_hist.return_value = pd.DataFrame({'close': [10.0]})
                
                client = SimpleQDBClient(self.cache_dir)
                
                # 测试不同的日期参数格式
                result1 = client.get_stock_data("000001", start_date="2024-01-01")
                result2 = client.get_stock_data("000001", start_date="20240101")
                result3 = client.get_stock_data("000001", days=30)
                
                self.assertIsInstance(result1, pd.DataFrame)
                self.assertIsInstance(result2, pd.DataFrame)
                self.assertIsInstance(result3, pd.DataFrame)

    def test_adjust_parameter_handling(self):
        """测试复权参数处理"""
        with patch('qdb.simple_client.AKSHARE_AVAILABLE', True):
            with patch('qdb.simple_client.ak') as mock_ak:
                mock_ak.stock_zh_a_hist.return_value = pd.DataFrame({'close': [10.0]})
                
                client = SimpleQDBClient(self.cache_dir)
                
                # 测试不同的复权参数
                result1 = client.get_stock_data("000001", adjust="qfq")
                result2 = client.get_stock_data("000001", adjust="hfq")
                result3 = client.get_stock_data("000001", adjust="")
                result4 = client.get_stock_data("000001", adjust=None)
                
                for result in [result1, result2, result3, result4]:
                    self.assertIsInstance(result, pd.DataFrame)

    def test_force_refresh_parameter(self):
        """测试force_refresh参数"""
        with patch('qdb.simple_client.AKSHARE_AVAILABLE', True):
            with patch('qdb.simple_client.ak') as mock_ak:
                mock_ak.stock_zh_a_hist.return_value = pd.DataFrame({'close': [10.0]})
                
                client = SimpleQDBClient(self.cache_dir)
                
                # 测试force_refresh参数
                result1 = client.get_stock_data("000001", force_refresh=True)
                result2 = client.get_stock_data("000001", force_refresh=False)
                
                self.assertIsInstance(result1, pd.DataFrame)
                self.assertIsInstance(result2, pd.DataFrame)

    def test_cache_directory_creation(self):
        """测试缓存目录创建"""
        nested_cache_dir = os.path.join(self.temp_dir, "nested", "cache")
        
        # 目录不存在时应该创建
        self.assertFalse(os.path.exists(nested_cache_dir))
        
        client = SimpleQDBClient(nested_cache_dir)
        
        # 目录应该被创建
        self.assertTrue(os.path.exists(nested_cache_dir))
        self.assertEqual(client.cache_dir, nested_cache_dir)

    def test_database_file_creation(self):
        """测试数据库文件创建"""
        client = SimpleQDBClient(self.cache_dir)
        
        db_path = os.path.join(self.cache_dir, "qdb_cache.db")
        self.assertTrue(os.path.exists(db_path))
        
        # 验证数据库可以连接
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        self.assertEqual(result[0], 1)
        conn.close()


if __name__ == '__main__':
    unittest.main()
