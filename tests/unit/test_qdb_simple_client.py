"""
DEPRECATED: 测试 qdb/simple_client.py 模块的简化客户端功能

⚠️  DEPRECATED MODULE TEST ⚠️
This test file is for a deprecated module that no longer exists.
The simple_client.py module has been replaced by the new lightweight architecture.

Current architecture:
- qdb/__init__.py: Module-level functions
- qdb/client.py: LightweightQDBClient class
- core/: All business logic

This test file is kept for historical reference but all tests are skipped.
"""

import os
import shutil
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, call, patch

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from qdb.exceptions import CacheError, DataError, QDBError

# Skip all tests in this file since the module no longer exists
import pytest
pytestmark = pytest.mark.skip(reason="DEPRECATED: simple_client module no longer exists")


class TestSimpleQDBClient(unittest.TestCase):
    """测试SimpleQDBClient类"""

    def setUp(self):
        """设置测试环境"""
        self.temp_dir = tempfile.mkdtemp()
        self.cache_dir = os.path.join(self.temp_dir, "test_cache")

    def tearDown(self):
        """清理测试环境"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_init_default_cache_dir(self):
        """测试默认缓存目录初始化"""
        client = SimpleQDBClient()
        
        # 检查默认缓存目录
        expected_dir = os.path.expanduser("~/.qdb_cache")
        self.assertEqual(client.cache_dir, expected_dir)
        
        # 检查目录是否创建
        self.assertTrue(os.path.exists(client.cache_dir))

    def test_init_custom_cache_dir(self):
        """测试自定义缓存目录初始化"""
        client = SimpleQDBClient(self.cache_dir)
        
        self.assertEqual(client.cache_dir, self.cache_dir)
        self.assertTrue(os.path.exists(self.cache_dir))

    def test_ensure_cache_dir_creation(self):
        """测试缓存目录创建"""
        # 确保目录不存在
        self.assertFalse(os.path.exists(self.cache_dir))
        
        client = SimpleQDBClient(self.cache_dir)
        
        # 检查目录是否被创建
        self.assertTrue(os.path.exists(self.cache_dir))

    def test_database_initialization(self):
        """测试数据库初始化"""
        client = SimpleQDBClient(self.cache_dir)
        
        # 检查数据库文件是否创建
        db_path = os.path.join(self.cache_dir, "qdb_cache.db")
        self.assertTrue(os.path.exists(db_path))
        
        # 检查数据库连接
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        # 应该至少有一个表
        self.assertGreater(len(tables), 0)
        
        conn.close()

    def test_get_connection(self):
        """测试数据库连接获取"""
        client = SimpleQDBClient(self.cache_dir)
        
        conn = client._get_connection()
        self.assertIsInstance(conn, sqlite3.Connection)
        
        # 测试连接可用性
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        self.assertEqual(result[0], 1)
        
        conn.close()

    @patch('qdb.simple_client.AKSHARE_AVAILABLE', True)
    @patch('qdb.simple_client.ak')
    def test_get_stock_data_with_akshare(self, mock_ak):
        """测试使用AKShare获取股票数据"""
        # 模拟AKShare返回数据
        import pandas as pd
        mock_data = pd.DataFrame({
            'date': ['2024-01-01', '2024-01-02'],
            'open': [10.0, 10.5],
            'high': [11.0, 11.5],
            'low': [9.5, 10.0],
            'close': [10.5, 11.0],
            'volume': [1000000, 1200000]
        })
        mock_ak.stock_zh_a_hist.return_value = mock_data
        
        client = SimpleQDBClient(self.cache_dir)
        
        # 测试获取数据
        result = client.get_stock_data("000001", start_date="20240101", end_date="20240102")
        
        # 验证结果
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 2)
        self.assertIn('close', result.columns)
        
        # 验证AKShare被调用
        mock_ak.stock_zh_a_hist.assert_called_once()

    @patch('qdb.simple_client.AKSHARE_AVAILABLE', False)
    def test_get_stock_data_without_akshare(self):
        """测试没有AKShare时的行为"""
        client = SimpleQDBClient(self.cache_dir)
        
        with self.assertRaises(QDBError) as context:
            client.get_stock_data("000001")
        
        self.assertIn("AKShare not available", str(context.exception))

    def test_cache_stats_empty(self):
        """测试空缓存的统计信息"""
        client = SimpleQDBClient(self.cache_dir)
        
        stats = client.cache_stats()
        
        self.assertIsInstance(stats, dict)
        self.assertIn('total_records', stats)
        self.assertIn('cache_size_mb', stats)
        self.assertEqual(stats['total_records'], 0)

    def test_clear_cache(self):
        """测试清除缓存"""
        client = SimpleQDBClient(self.cache_dir)
        
        # 先添加一些测试数据
        conn = client._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO daily_stock_data 
            (symbol, date, open, high, low, close, volume, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
        """, ("000001", "2024-01-01", 10.0, 11.0, 9.5, 10.5, 1000000))
        conn.commit()
        conn.close()
        
        # 验证数据存在
        stats_before = client.cache_stats()
        self.assertGreater(stats_before['total_records'], 0)
        
        # 清除缓存
        client.clear_cache()
        
        # 验证数据被清除
        stats_after = client.cache_stats()
        self.assertEqual(stats_after['total_records'], 0)

    def test_error_handling_database_error(self):
        """测试数据库错误处理"""
        client = SimpleQDBClient(self.cache_dir)
        
        # 模拟数据库错误
        with patch.object(client, '_get_connection') as mock_conn:
            mock_conn.side_effect = sqlite3.Error("Database error")
            
            with self.assertRaises(CacheError):
                client.cache_stats()

    def test_error_handling_invalid_symbol(self):
        """测试无效股票代码处理"""
        client = SimpleQDBClient(self.cache_dir)
        
        with patch('qdb.simple_client.AKSHARE_AVAILABLE', True):
            with patch('qdb.simple_client.ak') as mock_ak:
                # 模拟AKShare抛出异常
                mock_ak.stock_zh_a_hist.side_effect = Exception("Invalid symbol")
                
                with self.assertRaises(DataError):
                    client.get_stock_data("INVALID")

    def test_database_table_structure(self):
        """测试数据库表结构"""
        client = SimpleQDBClient(self.cache_dir)
        
        conn = client._get_connection()
        cursor = conn.cursor()
        
        # 检查daily_stock_data表结构
        cursor.execute("PRAGMA table_info(daily_stock_data)")
        columns = cursor.fetchall()
        
        # 验证必要的列存在
        column_names = [col[1] for col in columns]
        expected_columns = ['symbol', 'date', 'open', 'high', 'low', 'close', 'volume']
        
        for col in expected_columns:
            self.assertIn(col, column_names)
        
        conn.close()

    def test_concurrent_access(self):
        """测试并发访问"""
        client1 = SimpleQDBClient(self.cache_dir)
        client2 = SimpleQDBClient(self.cache_dir)
        
        # 两个客户端应该能够同时访问同一个缓存目录
        stats1 = client1.cache_stats()
        stats2 = client2.cache_stats()
        
        self.assertEqual(stats1['total_records'], stats2['total_records'])

    def test_cache_directory_permissions(self):
        """测试缓存目录权限"""
        # 创建只读目录
        readonly_dir = os.path.join(self.temp_dir, "readonly")
        os.makedirs(readonly_dir)
        os.chmod(readonly_dir, 0o444)  # 只读权限
        
        try:
            # 尝试在只读目录中创建缓存
            with self.assertRaises(QDBError):
                SimpleQDBClient(readonly_dir)
        finally:
            # 恢复权限以便清理
            os.chmod(readonly_dir, 0o755)

    def test_data_persistence(self):
        """测试数据持久化"""
        # 创建客户端并添加数据
        client1 = SimpleQDBClient(self.cache_dir)
        
        # 手动添加测试数据
        conn = client1._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO daily_stock_data 
            (symbol, date, open, high, low, close, volume, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
        """, ("000001", "2024-01-01", 10.0, 11.0, 9.5, 10.5, 1000000))
        conn.commit()
        conn.close()
        
        # 创建新客户端实例
        client2 = SimpleQDBClient(self.cache_dir)
        
        # 验证数据仍然存在
        stats = client2.cache_stats()
        self.assertGreater(stats['total_records'], 0)

    def test_invalid_cache_dir_path(self):
        """测试无效缓存目录路径"""
        # 测试空路径
        with self.assertRaises(QDBError):
            SimpleQDBClient("")
        
        # 测试None路径（应该使用默认路径）
        client = SimpleQDBClient(None)
        self.assertIsNotNone(client.cache_dir)

    def test_database_file_corruption_recovery(self):
        """测试数据库文件损坏恢复"""
        client = SimpleQDBClient(self.cache_dir)
        
        # 损坏数据库文件
        db_path = os.path.join(self.cache_dir, "qdb_cache.db")
        with open(db_path, 'w') as f:
            f.write("corrupted data")
        
        # 创建新客户端应该能够恢复
        client2 = SimpleQDBClient(self.cache_dir)
        
        # 验证数据库功能正常
        stats = client2.cache_stats()
        self.assertIsInstance(stats, dict)


if __name__ == '__main__':
    unittest.main()
