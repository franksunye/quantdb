"""
前端API客户端测试

测试API客户端的功能和错误处理。
"""

import unittest
from unittest.mock import patch, MagicMock
import requests
import sys
import os

# 添加项目路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from utils.api_client import QuantDBClient, QuantDBAPIError, format_date_for_api, parse_api_date, test_api_connection
from utils.config import config
from datetime import date, datetime

class TestQuantDBClient(unittest.TestCase):
    """测试QuantDB API客户端"""
    
    def setUp(self):
        """设置测试环境"""
        self.client = QuantDBClient()
        self.test_symbol = "600000"
        self.test_start_date = "20240101"
        self.test_end_date = "20240131"
    
    def test_client_initialization(self):
        """测试客户端初始化"""
        self.assertEqual(self.client.base_url, config.API_BASE_URL)
        self.assertEqual(self.client.api_prefix, config.API_PREFIX)
        self.assertEqual(self.client.timeout, config.API_TIMEOUT)
        self.assertIsNotNone(self.client.session)
    
    def test_get_url(self):
        """测试URL构建"""
        endpoint = "/health"
        expected_url = f"{config.API_BASE_URL}{config.API_PREFIX}{endpoint}"
        actual_url = self.client._get_url(endpoint)
        self.assertEqual(actual_url, expected_url)
    
    @patch('requests.Session.request')
    def test_make_request_success(self, mock_request):
        """测试成功的API请求"""
        # 模拟成功响应
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "ok"}
        mock_request.return_value = mock_response
        
        result = self.client._make_request("GET", "/health")
        
        self.assertEqual(result, {"status": "ok"})
        mock_request.assert_called_once()
    
    @patch('requests.Session.request')
    def test_make_request_404_error(self, mock_request):
        """测试404错误处理"""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_request.return_value = mock_response
        
        with self.assertRaises(QuantDBAPIError) as context:
            self.client._make_request("GET", "/nonexistent")
        
        self.assertIn("数据未找到", str(context.exception))
    
    @patch('requests.Session.request')
    def test_make_request_connection_error(self, mock_request):
        """测试连接错误处理"""
        mock_request.side_effect = requests.exceptions.ConnectionError()
        
        with self.assertRaises(QuantDBAPIError) as context:
            self.client._make_request("GET", "/health")
        
        self.assertIn("无法连接到后端API服务", str(context.exception))
    
    @patch('requests.Session.request')
    def test_make_request_timeout_error(self, mock_request):
        """测试超时错误处理"""
        mock_request.side_effect = requests.exceptions.Timeout()
        
        with self.assertRaises(QuantDBAPIError) as context:
            self.client._make_request("GET", "/health")
        
        self.assertIn("请求超时", str(context.exception))
    
    @patch.object(QuantDBClient, '_make_request')
    def test_get_health(self, mock_make_request):
        """测试健康检查API"""
        expected_response = {
            "status": "ok",
            "version": "0.8.0",
            "timestamp": "2024-01-01T00:00:00"
        }
        mock_make_request.return_value = expected_response
        
        result = self.client.get_health()
        
        self.assertEqual(result, expected_response)
        mock_make_request.assert_called_once_with("GET", "/health")
    
    @patch.object(QuantDBClient, '_make_request')
    def test_get_stock_data(self, mock_make_request):
        """测试股票数据获取API"""
        expected_response = {
            "data": [
                {"date": "2024-01-01", "close": 10.0},
                {"date": "2024-01-02", "close": 10.5}
            ],
            "metadata": {"cache_hit": True}
        }
        mock_make_request.return_value = expected_response
        
        result = self.client.get_stock_data(
            self.test_symbol, 
            self.test_start_date, 
            self.test_end_date
        )
        
        self.assertEqual(result, expected_response)
        mock_make_request.assert_called_once_with(
            "GET",
            f"/historical/stock/{self.test_symbol}",
            params={
                "start_date": self.test_start_date,
                "end_date": self.test_end_date
            }
        )
    
    def test_get_stock_data_invalid_symbol(self):
        """测试无效股票代码"""
        with self.assertRaises(QuantDBAPIError) as context:
            self.client.get_stock_data("invalid", self.test_start_date, self.test_end_date)
        
        self.assertIn("股票代码格式错误", str(context.exception))
    
    @patch.object(QuantDBClient, '_make_request')
    def test_get_asset_info(self, mock_make_request):
        """测试资产信息获取API"""
        expected_response = {
            "symbol": "600000",
            "name": "浦发银行",
            "industry": "银行",
            "pe_ratio": 5.2
        }
        mock_make_request.return_value = expected_response
        
        result = self.client.get_asset_info(self.test_symbol)
        
        self.assertEqual(result, expected_response)
        mock_make_request.assert_called_once_with("GET", f"/assets/symbol/{self.test_symbol}")
    
    @patch.object(QuantDBClient, '_make_request')
    def test_get_assets_list(self, mock_make_request):
        """测试资产列表获取API"""
        expected_response = [
            {"symbol": "600000", "name": "浦发银行"},
            {"symbol": "000001", "name": "平安银行"}
        ]
        mock_make_request.return_value = expected_response
        
        result = self.client.get_assets_list(limit=10)
        
        self.assertEqual(result, expected_response)
        mock_make_request.assert_called_once_with(
            "GET", 
            "/assets",
            params={"skip": 0, "limit": 10}
        )
    
    @patch.object(QuantDBClient, '_make_request')
    def test_get_cache_status(self, mock_make_request):
        """测试缓存状态获取API"""
        expected_response = {
            "database_size_mb": 15.5,
            "total_records": 1000,
            "cache_hit_rate": 95.5
        }
        mock_make_request.return_value = expected_response
        
        result = self.client.get_cache_status()
        
        self.assertEqual(result, expected_response)
        mock_make_request.assert_called_once_with("GET", "/cache/status")

class TestUtilityFunctions(unittest.TestCase):
    """测试工具函数"""
    
    def test_format_date_for_api(self):
        """测试日期格式化"""
        test_date = date(2024, 1, 15)
        result = format_date_for_api(test_date)
        self.assertEqual(result, "20240115")
    
    def test_parse_api_date(self):
        """测试API日期解析"""
        # 测试标准格式
        result1 = parse_api_date("2024-01-15")
        expected1 = datetime(2024, 1, 15)
        self.assertEqual(result1, expected1)
        
        # 测试紧凑格式
        result2 = parse_api_date("20240115")
        expected2 = datetime(2024, 1, 15)
        self.assertEqual(result2, expected2)
        
        # 测试无效格式
        with self.assertRaises(ValueError):
            parse_api_date("invalid-date")
    
    @patch('utils.api_client.get_api_client')
    def test_test_api_connection_success(self, mock_get_client):
        """测试API连接测试 - 成功"""
        mock_client = MagicMock()
        mock_client.get_health.return_value = {"status": "ok"}
        mock_get_client.return_value = mock_client

        result = test_api_connection()
        self.assertTrue(result)
    
    @patch('requests.get')
    def test_test_api_connection_failure(self, mock_get):
        """测试API连接测试 - 失败"""
        mock_get.side_effect = requests.exceptions.ConnectionError()
        
        result = test_api_connection()
        self.assertFalse(result)

class TestConfigValidation(unittest.TestCase):
    """测试配置验证"""
    
    def test_validate_symbol_valid(self):
        """测试有效股票代码验证"""
        valid_symbols = ["600000", "000001", "300001"]
        for symbol in valid_symbols:
            self.assertTrue(config.validate_symbol(symbol))
    
    def test_validate_symbol_invalid(self):
        """测试无效股票代码验证"""
        invalid_symbols = ["", "12345", "1234567", "abc123", None]
        for symbol in invalid_symbols:
            self.assertFalse(config.validate_symbol(symbol))
    
    def test_normalize_symbol(self):
        """测试股票代码标准化"""
        test_cases = [
            ("600000", "600000"),
            ("sh600000", "600000"),
            ("SZ000001", "000001"),
            ("600000.SH", "600000"),
            ("1", "000001"),  # 补零
        ]
        
        for input_symbol, expected in test_cases:
            result = config.normalize_symbol(input_symbol)
            self.assertEqual(result, expected, f"Failed for input: {input_symbol}")

if __name__ == '__main__':
    unittest.main()
