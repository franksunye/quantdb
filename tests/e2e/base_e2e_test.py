"""
E2E测试基类

提供E2E测试的基础设施，包括服务器管理、数据库清理等
"""

import unittest
import requests
import time
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from tests.e2e.config import e2e_config
from tests.e2e.server_manager import server_manager
from src.logger import setup_logger

logger = setup_logger("e2e_base_test")

class BaseE2ETest(unittest.TestCase):
    """E2E测试基类"""
    
    @classmethod
    def setUpClass(cls):
        """设置测试类 - 启动服务器"""
        logger.info("=" * 60)
        logger.info("开始E2E测试")
        logger.info("=" * 60)
        
        cls.config = e2e_config
        cls.server_manager = server_manager
        
        # 启动服务器
        if not cls.server_manager.start_server():
            raise Exception("无法启动E2E测试服务器")
        
        # 设置基础URL
        cls.base_url = cls.config.BASE_URL
        cls.api_prefix = cls.config.API_PREFIX
        
        logger.info(f"E2E测试环境已准备就绪: {cls.base_url}")
    
    @classmethod
    def tearDownClass(cls):
        """清理测试类 - 停止服务器"""
        logger.info("清理E2E测试环境...")
        cls.server_manager.stop_server()
        cls.config.cleanup()
        logger.info("E2E测试完成")
        logger.info("=" * 60)
    
    def setUp(self):
        """每个测试前的设置"""
        # 清理测试数据
        self._cleanup_test_data()
        
        # 验证服务器状态
        if not self.server_manager.is_running():
            self.fail("测试服务器未运行")
    
    def tearDown(self):
        """每个测试后的清理"""
        # 可以在这里添加测试后的清理逻辑
        pass
    
    def _cleanup_test_data(self):
        """清理测试数据"""
        try:
            # 清理所有测试符号的缓存数据
            for symbol in self.config.TEST_SYMBOLS:
                response = requests.delete(
                    f"{self.base_url}{self.api_prefix}/cache/clear/symbol/{symbol}",
                    timeout=self.config.REQUEST_TIMEOUT
                )
                if response.status_code == 200:
                    logger.debug(f"已清理 {symbol} 的缓存数据")
                    
        except requests.exceptions.RequestException as e:
            logger.warning(f"清理测试数据时出错: {e}")
    
    def make_request(self, method, endpoint, **kwargs):
        """发送HTTP请求的辅助方法"""
        url = f"{self.base_url}{self.api_prefix}{endpoint}"
        
        # 设置默认超时
        if 'timeout' not in kwargs:
            kwargs['timeout'] = self.config.REQUEST_TIMEOUT
        
        try:
            response = requests.request(method, url, **kwargs)
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"请求失败: {method} {url}, 错误: {e}")
            raise
    
    def get(self, endpoint, **kwargs):
        """GET请求的便捷方法"""
        return self.make_request('GET', endpoint, **kwargs)
    
    def post(self, endpoint, **kwargs):
        """POST请求的便捷方法"""
        return self.make_request('POST', endpoint, **kwargs)
    
    def delete(self, endpoint, **kwargs):
        """DELETE请求的便捷方法"""
        return self.make_request('DELETE', endpoint, **kwargs)
    
    def assert_api_success(self, response, expected_status=200):
        """断言API调用成功"""
        self.assertEqual(
            response.status_code, 
            expected_status,
            f"API调用失败: {response.status_code}, 响应: {response.text}"
        )
    
    def assert_api_error(self, response, expected_status):
        """断言API调用返回预期错误"""
        self.assertEqual(
            response.status_code,
            expected_status,
            f"API错误状态码不匹配: 期望 {expected_status}, 实际 {response.status_code}"
        )
    
    def wait_for_condition(self, condition_func, timeout=10, interval=0.5):
        """等待条件满足"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if condition_func():
                return True
            time.sleep(interval)
        return False
    
    def measure_request_time(self, request_func):
        """测量请求执行时间"""
        start_time = time.time()
        result = request_func()
        end_time = time.time()
        return result, end_time - start_time
