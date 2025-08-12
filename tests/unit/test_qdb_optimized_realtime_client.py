"""
DEPRECATED: 测试 qdb/optimized_realtime_client.py 模块的优化实时数据客户端功能

⚠️  DEPRECATED MODULE TEST ⚠️
This test file is for a deprecated module that no longer exists.
The optimized_realtime_client.py module has been replaced by the new lightweight architecture.

Current architecture:
- qdb/__init__.py: Module-level functions
- qdb/client.py: LightweightQDBClient class
- core/services/realtime_data_service.py: Realtime data business logic

This test file is kept for historical reference but all tests are skipped.
"""

import os
import shutil
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import MagicMock, call, patch

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from qdb.exceptions import CacheError, DataError, QDBError

# Skip all tests in this file since the module no longer exists
import pytest
pytestmark = pytest.mark.skip(reason="DEPRECATED: optimized_realtime_client module no longer exists")


class TestOptimizedRealtimeClient(unittest.TestCase):
    """测试OptimizedRealtimeClient类"""

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
        client = OptimizedRealtimeClient()
        
        # 检查默认缓存目录
        expected_dir = os.path.expanduser("~/.qdb_cache")
        self.assertEqual(client.cache_dir, expected_dir)
        
        # 检查目录是否创建
        self.assertTrue(os.path.exists(client.cache_dir))

    def test_init_custom_cache_dir(self):
        """测试自定义缓存目录初始化"""
        client = OptimizedRealtimeClient(self.cache_dir)
        
        self.assertEqual(client.cache_dir, self.cache_dir)
        self.assertTrue(os.path.exists(self.cache_dir))

    def test_realtime_cache_initialization(self):
        """测试实时缓存数据库初始化"""
        client = OptimizedRealtimeClient(self.cache_dir)
        
        # 检查实时缓存数据库文件
        db_path = os.path.join(self.cache_dir, "realtime_cache.db")
        self.assertTrue(os.path.exists(db_path))

    def test_memory_cache_configuration(self):
        """测试内存缓存配置"""
        client = OptimizedRealtimeClient(self.cache_dir)
        
        # 检查内存缓存初始化
        self.assertIsInstance(client.memory_cache, dict)
        self.assertEqual(len(client.memory_cache), 0)
        
        # 检查TTL配置
        self.assertEqual(client.cache_ttl, 60)  # 1分钟
        self.assertEqual(client.trading_hours_ttl, 30)  # 交易时间30秒
        self.assertEqual(client.batch_cache_ttl, 300)  # 批量缓存5分钟

    def test_batch_cache_initialization(self):
        """测试批量缓存初始化"""
        client = OptimizedRealtimeClient(self.cache_dir)
        
        self.assertIsInstance(client.batch_cache, dict)
        self.assertIsNone(client.batch_cache_time)

    def test_thread_safety_initialization(self):
        """测试线程安全初始化"""
        client = OptimizedRealtimeClient(self.cache_dir)
        
        # 检查线程锁
        self.assertIsNotNone(client._cache_lock)
        self.assertIsInstance(client._cache_lock, threading.Lock)

    @patch('qdb.optimized_realtime_client.ak')
    def test_get_realtime_data_single(self, mock_ak):
        """测试单个股票实时数据获取"""
        # 模拟AKShare返回数据
        mock_ak.stock_zh_a_spot_em.return_value = [
            ['000001', '平安银行', 10.50, 0.10, 0.96, 10.40, 10.60, 10.30, 10.45, 1000000]
        ]
        
        client = OptimizedRealtimeClient(self.cache_dir)
        
        result = client.get_realtime_data("000001")
        
        self.assertIsInstance(result, dict)
        self.assertIn('symbol', result)
        self.assertIn('current_price', result)
        self.assertEqual(result['symbol'], '000001')

    @patch('qdb.optimized_realtime_client.ak')
    def test_get_realtime_data_batch(self, mock_ak):
        """测试批量股票实时数据获取"""
        # 模拟AKShare返回数据
        mock_ak.stock_zh_a_spot_em.return_value = [
            ['000001', '平安银行', 10.50, 0.10, 0.96, 10.40, 10.60, 10.30, 10.45, 1000000],
            ['000002', '万科A', 20.30, -0.20, -0.98, 20.50, 20.60, 20.20, 20.35, 2000000]
        ]
        
        client = OptimizedRealtimeClient(self.cache_dir)
        
        result = client.get_realtime_data_batch(["000001", "000002"])
        
        self.assertIsInstance(result, dict)
        self.assertIn('000001', result)
        self.assertIn('000002', result)
        self.assertEqual(len(result), 2)

    def test_memory_cache_storage_and_retrieval(self):
        """测试内存缓存存储和检索"""
        client = OptimizedRealtimeClient(self.cache_dir)
        
        # 手动添加缓存数据
        test_data = {
            'symbol': '000001',
            'current_price': 10.50,
            'timestamp': time.time()
        }
        
        with client._cache_lock:
            client.memory_cache['000001'] = {
                'data': test_data,
                'timestamp': time.time()
            }
        
        # 验证缓存存在
        self.assertIn('000001', client.memory_cache)
        cached_data = client.memory_cache['000001']['data']
        self.assertEqual(cached_data['symbol'], '000001')
        self.assertEqual(cached_data['current_price'], 10.50)

    def test_cache_expiration(self):
        """测试缓存过期机制"""
        client = OptimizedRealtimeClient(self.cache_dir)
        
        # 添加过期的缓存数据
        expired_time = time.time() - client.cache_ttl - 1
        
        with client._cache_lock:
            client.memory_cache['000001'] = {
                'data': {'symbol': '000001', 'current_price': 10.50},
                'timestamp': expired_time
            }
        
        # 验证缓存已过期（需要实现_is_cache_valid方法）
        # 这里假设客户端有检查缓存有效性的方法
        self.assertTrue(time.time() - expired_time > client.cache_ttl)

    def test_batch_cache_mechanism(self):
        """测试批量缓存机制"""
        client = OptimizedRealtimeClient(self.cache_dir)
        
        # 模拟批量缓存数据
        batch_data = {
            '000001': {'current_price': 10.50},
            '000002': {'current_price': 20.30}
        }
        
        client.batch_cache = batch_data
        client.batch_cache_time = time.time()
        
        # 验证批量缓存
        self.assertEqual(len(client.batch_cache), 2)
        self.assertIn('000001', client.batch_cache)
        self.assertIn('000002', client.batch_cache)

    def test_batch_cache_expiration(self):
        """测试批量缓存过期"""
        client = OptimizedRealtimeClient(self.cache_dir)
        
        # 设置过期的批量缓存
        client.batch_cache_time = time.time() - client.batch_cache_ttl - 1
        
        # 验证批量缓存已过期
        time_diff = time.time() - client.batch_cache_time
        self.assertTrue(time_diff > client.batch_cache_ttl)

    def test_trading_hours_ttl_logic(self):
        """测试交易时间TTL逻辑"""
        client = OptimizedRealtimeClient(self.cache_dir)
        
        # 验证交易时间TTL配置
        self.assertEqual(client.trading_hours_ttl, 30)
        self.assertLess(client.trading_hours_ttl, client.cache_ttl)

    def test_thread_safety_concurrent_access(self):
        """测试线程安全的并发访问"""
        client = OptimizedRealtimeClient(self.cache_dir)
        
        results = []
        errors = []
        
        def worker():
            try:
                # 模拟并发缓存操作
                with client._cache_lock:
                    client.memory_cache[f'test_{threading.current_thread().ident}'] = {
                        'data': {'price': 10.0},
                        'timestamp': time.time()
                    }
                results.append(True)
            except Exception as e:
                errors.append(e)
        
        # 创建多个线程
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 验证没有错误
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(results), 5)

    def test_database_cache_integration(self):
        """测试数据库缓存集成"""
        client = OptimizedRealtimeClient(self.cache_dir)
        
        # 验证数据库文件存在
        db_path = client.db_path
        self.assertTrue(os.path.exists(db_path))

    def test_error_handling_akshare_failure(self):
        """测试AKShare失败的错误处理"""
        with patch('qdb.optimized_realtime_client.ak') as mock_ak:
            mock_ak.stock_zh_a_spot_em.side_effect = Exception("AKShare error")
            
            client = OptimizedRealtimeClient(self.cache_dir)
            
            with self.assertRaises(DataError):
                client.get_realtime_data("000001")

    def test_error_handling_invalid_symbol(self):
        """测试无效股票代码处理"""
        client = OptimizedRealtimeClient(self.cache_dir)
        
        with self.assertRaises(QDBError):
            client.get_realtime_data("")
        
        with self.assertRaises(QDBError):
            client.get_realtime_data(None)

    def test_cache_statistics(self):
        """测试缓存统计信息"""
        client = OptimizedRealtimeClient(self.cache_dir)
        
        # 添加一些缓存数据
        with client._cache_lock:
            client.memory_cache['000001'] = {
                'data': {'current_price': 10.50},
                'timestamp': time.time()
            }
            client.memory_cache['000002'] = {
                'data': {'current_price': 20.30},
                'timestamp': time.time()
            }
        
        # 验证缓存统计
        cache_count = len(client.memory_cache)
        self.assertEqual(cache_count, 2)

    def test_cache_cleanup(self):
        """测试缓存清理"""
        client = OptimizedRealtimeClient(self.cache_dir)
        
        # 添加缓存数据
        with client._cache_lock:
            client.memory_cache['000001'] = {
                'data': {'current_price': 10.50},
                'timestamp': time.time()
            }
        
        # 清理缓存
        with client._cache_lock:
            client.memory_cache.clear()
        
        # 验证缓存已清理
        self.assertEqual(len(client.memory_cache), 0)

    def test_performance_optimization_features(self):
        """测试性能优化特性"""
        client = OptimizedRealtimeClient(self.cache_dir)
        
        # 验证优化特性配置
        self.assertIsInstance(client.memory_cache, dict)  # 内存缓存
        self.assertIsInstance(client.batch_cache, dict)   # 批量缓存
        self.assertIsNotNone(client._cache_lock)          # 线程安全
        self.assertGreater(client.cache_ttl, 0)           # TTL配置
        self.assertGreater(client.batch_cache_ttl, 0)     # 批量TTL配置

    def test_cache_directory_permissions(self):
        """测试缓存目录权限"""
        # 创建只读目录
        readonly_dir = os.path.join(self.temp_dir, "readonly")
        os.makedirs(readonly_dir)
        os.chmod(readonly_dir, 0o444)  # 只读权限
        
        try:
            # 尝试在只读目录中创建缓存
            with self.assertRaises(QDBError):
                OptimizedRealtimeClient(readonly_dir)
        finally:
            # 恢复权限以便清理
            os.chmod(readonly_dir, 0o755)

    def test_multiple_client_instances(self):
        """测试多个客户端实例"""
        client1 = OptimizedRealtimeClient(self.cache_dir)
        client2 = OptimizedRealtimeClient(self.cache_dir)
        
        # 两个客户端应该有独立的内存缓存
        self.assertIsNot(client1.memory_cache, client2.memory_cache)
        
        # 但应该使用相同的数据库文件
        self.assertEqual(client1.db_path, client2.db_path)

    def test_configuration_parameters(self):
        """测试配置参数"""
        client = OptimizedRealtimeClient(self.cache_dir)
        
        # 验证所有配置参数都有合理的默认值
        self.assertIsInstance(client.cache_ttl, int)
        self.assertIsInstance(client.trading_hours_ttl, int)
        self.assertIsInstance(client.batch_cache_ttl, int)
        
        self.assertGreater(client.cache_ttl, 0)
        self.assertGreater(client.trading_hours_ttl, 0)
        self.assertGreater(client.batch_cache_ttl, 0)
        
        # 交易时间TTL应该小于普通TTL
        self.assertLess(client.trading_hours_ttl, client.cache_ttl)


if __name__ == '__main__':
    unittest.main()
