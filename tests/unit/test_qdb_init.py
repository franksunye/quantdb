"""
测试 qdb/__init__.py 模块的导入导出功能

测试覆盖：
- 所有公共API的导入
- 版本信息
- 异常类导入
- __all__ 列表完整性
"""

import types
import unittest
from unittest.mock import MagicMock, patch


class TestQDBInit(unittest.TestCase):
    """测试qdb包的初始化和导出"""

    def test_version_info(self):
        """测试版本信息"""
        import qdb

        # 测试版本信息存在
        self.assertTrue(hasattr(qdb, '__version__'))
        self.assertTrue(hasattr(qdb, '__author__'))
        self.assertTrue(hasattr(qdb, '__email__'))
        self.assertTrue(hasattr(qdb, '__description__'))
        
        # 测试版本格式
        self.assertIsInstance(qdb.__version__, str)
        self.assertRegex(qdb.__version__, r'^\d+\.\d+\.\d+.*$')
        
        # 测试作者信息
        self.assertEqual(qdb.__author__, "Ye Sun")
        self.assertEqual(qdb.__email__, "franksunye@hotmail.com")
        self.assertIn("caching", qdb.__description__.lower())

    def test_core_api_imports(self):
        """测试核心API函数导入"""
        import qdb

        # 核心功能
        core_functions = [
            'init', 'get_stock_data', 'get_multiple_stocks', 'get_asset_info'
        ]
        
        for func_name in core_functions:
            with self.subTest(function=func_name):
                self.assertTrue(hasattr(qdb, func_name))
                func = getattr(qdb, func_name)
                self.assertTrue(callable(func))

    def test_realtime_api_imports(self):
        """测试实时数据API导入"""
        import qdb
        
        realtime_functions = [
            'get_realtime_data', 'get_realtime_data_batch'
        ]
        
        for func_name in realtime_functions:
            with self.subTest(function=func_name):
                self.assertTrue(hasattr(qdb, func_name))
                func = getattr(qdb, func_name)
                self.assertTrue(callable(func))

    def test_stock_list_api_imports(self):
        """测试股票列表API导入"""
        import qdb
        
        self.assertTrue(hasattr(qdb, 'get_stock_list'))
        self.assertTrue(callable(qdb.get_stock_list))

    def test_index_api_imports(self):
        """测试指数数据API导入"""
        import qdb
        
        index_functions = [
            'get_index_data', 'get_index_realtime', 'get_index_list'
        ]
        
        for func_name in index_functions:
            with self.subTest(function=func_name):
                self.assertTrue(hasattr(qdb, func_name))
                func = getattr(qdb, func_name)
                self.assertTrue(callable(func))

    def test_financial_api_imports(self):
        """测试财务数据API导入"""
        import qdb
        
        financial_functions = [
            'get_financial_summary', 'get_financial_indicators'
        ]
        
        for func_name in financial_functions:
            with self.subTest(function=func_name):
                self.assertTrue(hasattr(qdb, func_name))
                func = getattr(qdb, func_name)
                self.assertTrue(callable(func))

    def test_cache_management_imports(self):
        """测试缓存管理API导入"""
        import qdb
        
        cache_functions = ['cache_stats', 'clear_cache']
        
        for func_name in cache_functions:
            with self.subTest(function=func_name):
                self.assertTrue(hasattr(qdb, func_name))
                func = getattr(qdb, func_name)
                self.assertTrue(callable(func))

    def test_akshare_compatibility_imports(self):
        """测试AKShare兼容性API导入"""
        import qdb
        
        self.assertTrue(hasattr(qdb, 'stock_zh_a_hist'))
        self.assertTrue(callable(qdb.stock_zh_a_hist))

    def test_configuration_imports(self):
        """测试配置API导入"""
        import qdb
        
        config_functions = ['set_cache_dir', 'set_log_level']
        
        for func_name in config_functions:
            with self.subTest(function=func_name):
                self.assertTrue(hasattr(qdb, func_name))
                func = getattr(qdb, func_name)
                self.assertTrue(callable(func))

    def test_exception_imports(self):
        """测试异常类导入"""
        import qdb
        
        exception_classes = [
            'QDBError', 'CacheError', 'DataError', 'NetworkError'
        ]
        
        for exc_name in exception_classes:
            with self.subTest(exception=exc_name):
                self.assertTrue(hasattr(qdb, exc_name))
                exc_class = getattr(qdb, exc_name)
                self.assertTrue(isinstance(exc_class, type))
                self.assertTrue(issubclass(exc_class, Exception))

    def test_all_list_completeness(self):
        """测试__all__列表的完整性"""
        import qdb

        # 检查__all__存在
        self.assertTrue(hasattr(qdb, '__all__'))
        self.assertIsInstance(qdb.__all__, list)
        
        # 检查__all__中的所有项目都可以导入
        for item in qdb.__all__:
            with self.subTest(item=item):
                self.assertTrue(hasattr(qdb, item))

    def test_all_list_no_duplicates(self):
        """测试__all__列表无重复项"""
        import qdb
        
        all_items = qdb.__all__
        unique_items = list(set(all_items))
        
        self.assertEqual(len(all_items), len(unique_items), 
                        "Found duplicate items in __all__")

    def test_module_docstring(self):
        """测试模块文档字符串"""
        import qdb
        
        self.assertIsNotNone(qdb.__doc__)
        self.assertIn("QDB", qdb.__doc__)
        self.assertIn("caching", qdb.__doc__.lower())

    def test_import_without_errors(self):
        """测试导入过程无错误"""
        try:
            import qdb

            # 测试基本属性访问不会引发错误
            _ = qdb.__version__
            _ = qdb.get_stock_data
            _ = qdb.QDBError
        except Exception as e:
            self.fail(f"Import failed with error: {e}")

    def test_lazy_import_behavior(self):
        """测试延迟导入行为"""
        # 重新导入以测试延迟加载
        import importlib
        import sys

        # 清除模块缓存
        modules_to_clear = [name for name in sys.modules.keys() if name.startswith('qdb')]
        for module_name in modules_to_clear:
            if module_name in sys.modules:
                del sys.modules[module_name]
        
        # 重新导入
        import qdb

        # 验证基本功能可用
        self.assertTrue(hasattr(qdb, 'get_stock_data'))
        self.assertTrue(callable(qdb.get_stock_data))


if __name__ == '__main__':
    unittest.main()
