"""
测试 qdb/exceptions.py 模块的异常处理功能

测试覆盖：
- 所有异常类的创建和继承
- 错误代码和消息处理
- 异常装饰器功能
- 用户友好的错误格式化
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from qdb.exceptions import (
    QDBError, CacheError, DataError, NetworkError, ConfigError, ValidationError,
    handle_qdb_errors, get_error_message, format_user_error, ERROR_CODES
)


class TestQDBExceptions(unittest.TestCase):
    """测试QDB异常类"""

    def test_qdb_error_base_class(self):
        """测试QDBError基类"""
        # 测试基本创建
        error = QDBError("Test message")
        self.assertEqual(str(error), "Test message")
        self.assertEqual(error.message, "Test message")
        self.assertIsNone(error.error_code)
        
        # 测试带错误代码的创建
        error_with_code = QDBError("Test message", "TEST_CODE")
        self.assertEqual(str(error_with_code), "[TEST_CODE] Test message")
        self.assertEqual(error_with_code.error_code, "TEST_CODE")
        
        # 测试继承关系
        self.assertIsInstance(error, Exception)

    def test_cache_error(self):
        """测试CacheError异常"""
        error = CacheError("Cache operation failed")
        
        self.assertIsInstance(error, QDBError)
        self.assertEqual(error.message, "Cache operation failed")
        self.assertEqual(error.error_code, "CACHE_ERROR")
        self.assertEqual(str(error), "[CACHE_ERROR] Cache operation failed")

    def test_data_error(self):
        """测试DataError异常"""
        error = DataError("Data acquisition failed")
        
        self.assertIsInstance(error, QDBError)
        self.assertEqual(error.message, "Data acquisition failed")
        self.assertEqual(error.error_code, "DATA_ERROR")
        self.assertEqual(str(error), "[DATA_ERROR] Data acquisition failed")

    def test_network_error(self):
        """测试NetworkError异常"""
        error = NetworkError("Network request failed")
        
        self.assertIsInstance(error, QDBError)
        self.assertEqual(error.message, "Network request failed")
        self.assertEqual(error.error_code, "NETWORK_ERROR")
        self.assertEqual(str(error), "[NETWORK_ERROR] Network request failed")

    def test_config_error(self):
        """测试ConfigError异常"""
        error = ConfigError("Configuration error")
        
        self.assertIsInstance(error, QDBError)
        self.assertEqual(error.message, "Configuration error")
        self.assertEqual(error.error_code, "CONFIG_ERROR")
        self.assertEqual(str(error), "[CONFIG_ERROR] Configuration error")

    def test_validation_error(self):
        """测试ValidationError异常"""
        error = ValidationError("Data validation failed")
        
        self.assertIsInstance(error, QDBError)
        self.assertEqual(error.message, "Data validation failed")
        self.assertEqual(error.error_code, "VALIDATION_ERROR")
        self.assertEqual(str(error), "[VALIDATION_ERROR] Data validation failed")

    def test_error_codes_constant(self):
        """测试ERROR_CODES常量"""
        self.assertIsInstance(ERROR_CODES, dict)
        
        expected_codes = [
            "CACHE_ERROR", "DATA_ERROR", "NETWORK_ERROR", 
            "CONFIG_ERROR", "VALIDATION_ERROR"
        ]
        
        for code in expected_codes:
            self.assertIn(code, ERROR_CODES)
            self.assertIsInstance(ERROR_CODES[code], str)

    def test_get_error_message(self):
        """测试get_error_message函数"""
        # 测试已知错误代码
        message = get_error_message("CACHE_ERROR")
        self.assertEqual(message, "Cache operation failed")
        
        # 测试未知错误代码
        unknown_message = get_error_message("UNKNOWN_CODE")
        self.assertEqual(unknown_message, "Unknown error")

    def test_format_user_error_qdb_error(self):
        """测试format_user_error函数 - QDB错误"""
        error = QDBError("Test error message")
        formatted = format_user_error(error)
        
        self.assertIn("❌ QDB Error:", formatted)
        self.assertIn("Test error message", formatted)

    def test_format_user_error_import_error(self):
        """测试format_user_error函数 - 导入错误"""
        error = ImportError("No module named 'test'")
        formatted = format_user_error(error)
        
        self.assertIn("❌ Dependency Error:", formatted)
        self.assertIn("pip install quantdb[full]", formatted)

    def test_format_user_error_file_not_found(self):
        """测试format_user_error函数 - 文件未找到错误"""
        error = FileNotFoundError("File not found")
        formatted = format_user_error(error)
        
        self.assertIn("❌ File Error:", formatted)
        self.assertIn("reinitialize cache", formatted)

    def test_format_user_error_permission_error(self):
        """测试format_user_error函数 - 权限错误"""
        error = PermissionError("Permission denied")
        formatted = format_user_error(error)
        
        self.assertIn("❌ Permission Error:", formatted)
        self.assertIn("directory permissions", formatted)

    def test_format_user_error_connection_error(self):
        """测试format_user_error函数 - 连接错误"""
        error = ConnectionError("Connection failed")
        formatted = format_user_error(error)
        
        self.assertIn("❌ Network Error:", formatted)
        self.assertIn("network connection", formatted)

    def test_handle_qdb_errors_decorator_success(self):
        """测试handle_qdb_errors装饰器 - 成功情况"""
        @handle_qdb_errors
        def successful_function():
            return "success"
        
        result = successful_function()
        self.assertEqual(result, "success")

    def test_handle_qdb_errors_decorator_qdb_error(self):
        """测试handle_qdb_errors装饰器 - QDB错误直接抛出"""
        @handle_qdb_errors
        def qdb_error_function():
            raise QDBError("QDB error")
        
        with self.assertRaises(QDBError) as context:
            qdb_error_function()
        
        self.assertEqual(str(context.exception), "QDB error")

    def test_handle_qdb_errors_decorator_import_error(self):
        """测试handle_qdb_errors装饰器 - 导入错误转换"""
        @handle_qdb_errors
        def import_error_function():
            raise ImportError("Missing module")
        
        with self.assertRaises(ConfigError) as context:
            import_error_function()
        
        self.assertIn("Missing required dependency", str(context.exception))

    def test_handle_qdb_errors_decorator_file_not_found(self):
        """测试handle_qdb_errors装饰器 - 文件未找到错误转换"""
        @handle_qdb_errors
        def file_error_function():
            raise FileNotFoundError("File not found")
        
        with self.assertRaises(CacheError) as context:
            file_error_function()
        
        self.assertIn("Cache file not found", str(context.exception))

    def test_handle_qdb_errors_decorator_permission_error(self):
        """测试handle_qdb_errors装饰器 - 权限错误转换"""
        @handle_qdb_errors
        def permission_error_function():
            raise PermissionError("Permission denied")
        
        with self.assertRaises(CacheError) as context:
            permission_error_function()
        
        self.assertIn("cache directory permissions", str(context.exception))

    def test_handle_qdb_errors_decorator_connection_error(self):
        """测试handle_qdb_errors装饰器 - 连接错误转换"""
        @handle_qdb_errors
        def connection_error_function():
            raise ConnectionError("Connection failed")
        
        with self.assertRaises(NetworkError) as context:
            connection_error_function()
        
        self.assertIn("Network connection failed", str(context.exception))

    def test_handle_qdb_errors_decorator_value_error(self):
        """测试handle_qdb_errors装饰器 - 值错误转换"""
        @handle_qdb_errors
        def value_error_function():
            raise ValueError("Invalid value")
        
        with self.assertRaises(ValidationError) as context:
            value_error_function()
        
        self.assertIn("Data validation failed", str(context.exception))

    def test_handle_qdb_errors_decorator_generic_error(self):
        """测试handle_qdb_errors装饰器 - 通用错误转换"""
        @handle_qdb_errors
        def generic_error_function():
            raise RuntimeError("Runtime error")
        
        with self.assertRaises(QDBError) as context:
            generic_error_function()
        
        self.assertIn("Unknown error", str(context.exception))

    def test_exception_inheritance_chain(self):
        """测试异常继承链"""
        # 所有QDB异常都应该继承自QDBError
        qdb_exceptions = [CacheError, DataError, NetworkError, ConfigError, ValidationError]
        
        for exc_class in qdb_exceptions:
            with self.subTest(exception_class=exc_class.__name__):
                self.assertTrue(issubclass(exc_class, QDBError))
                self.assertTrue(issubclass(exc_class, Exception))

    def test_exception_with_args_and_kwargs(self):
        """测试异常的参数传递"""
        # 测试位置参数
        error = QDBError("Message", "CODE")
        self.assertEqual(error.message, "Message")
        self.assertEqual(error.error_code, "CODE")
        
        # 测试关键字参数
        error2 = QDBError(message="Message2", error_code="CODE2")
        self.assertEqual(error2.message, "Message2")
        self.assertEqual(error2.error_code, "CODE2")


if __name__ == '__main__':
    unittest.main()
