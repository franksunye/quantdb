# tests/api/test_version_api.py
"""
测试API版本控制功能

这个测试模块验证API版本控制功能是否正确工作。
"""

import os
import sys
import unittest
from fastapi.testclient import TestClient

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.api.main import app
from src.api.version import APIVersion, get_all_versions, get_latest_version_info
from src.logger_unified import get_logger

# 设置测试日志记录器
logger = get_logger("test_version_api")

class TestVersionAPI(unittest.TestCase):
    """测试API版本控制功能"""

    def setUp(self):
        """设置测试环境"""
        self.client = TestClient(app)
        logger.info("设置TestVersionAPI测试环境")

    def test_get_all_versions(self):
        """测试获取所有API版本信息"""
        logger.info("测试获取所有API版本信息")
        
        # 发送请求到版本端点
        response = self.client.get("/api/v1/version/")
        
        # 验证响应状态码
        self.assertEqual(response.status_code, 200, "版本端点应返回200状态码")
        
        # 验证响应内容类型
        self.assertEqual(response.headers["content-type"], "application/json", 
                         "版本端点应返回JSON内容")
        
        # 验证响应结构
        data = response.json()
        self.assertIn("versions", data, "响应应包含'versions'字段")
        self.assertIn("latest", data, "响应应包含'latest'字段")
        self.assertIn("current", data, "响应应包含'current'字段")
        
        # 验证版本信息
        versions = data["versions"]
        self.assertIn("v1", versions, "应包含v1版本信息")
        self.assertIn("v2", versions, "应包含v2版本信息")
        
        # 验证最新版本
        self.assertEqual(data["latest"], "v2", "最新版本应为v2")
        
        logger.info("获取所有API版本信息测试通过")

    def test_get_latest_version(self):
        """测试获取最新API版本信息"""
        logger.info("测试获取最新API版本信息")
        
        # 发送请求到最新版本端点
        response = self.client.get("/api/v1/version/latest")
        
        # 验证响应状态码
        self.assertEqual(response.status_code, 200, "最新版本端点应返回200状态码")
        
        # 验证响应内容类型
        self.assertEqual(response.headers["content-type"], "application/json", 
                         "最新版本端点应返回JSON内容")
        
        # 验证响应结构
        data = response.json()
        self.assertIn("version", data, "响应应包含'version'字段")
        self.assertIn("api_version", data, "响应应包含'api_version'字段")
        self.assertIn("release_date", data, "响应应包含'release_date'字段")
        self.assertIn("deprecated", data, "响应应包含'deprecated'字段")
        self.assertIn("description", data, "响应应包含'description'字段")
        
        # 验证最新版本信息
        latest_info = get_latest_version_info()
        self.assertEqual(data["version"], latest_info.version, 
                         f"版本应为{latest_info.version}")
        self.assertEqual(data["api_version"], latest_info.api_version, 
                         f"API版本应为{latest_info.api_version}")
        
        logger.info("获取最新API版本信息测试通过")

    def test_get_specific_version(self):
        """测试获取特定API版本信息"""
        logger.info("测试获取特定API版本信息")
        
        # 发送请求到特定版本端点
        response = self.client.get("/api/v1/version/v1")
        
        # 验证响应状态码
        self.assertEqual(response.status_code, 200, "特定版本端点应返回200状态码")
        
        # 验证响应内容类型
        self.assertEqual(response.headers["content-type"], "application/json", 
                         "特定版本端点应返回JSON内容")
        
        # 验证响应结构
        data = response.json()
        self.assertIn("version", data, "响应应包含'version'字段")
        self.assertIn("api_version", data, "响应应包含'api_version'字段")
        self.assertEqual(data["api_version"], "v1", "API版本应为v1")
        
        logger.info("获取特定API版本信息测试通过")

    def test_invalid_version(self):
        """测试获取无效API版本信息"""
        logger.info("测试获取无效API版本信息")
        
        # 发送请求到无效版本端点
        response = self.client.get("/api/v1/version/v3")
        
        # 验证响应状态码
        self.assertEqual(response.status_code, 404, "无效版本端点应返回404状态码")
        
        logger.info("获取无效API版本信息测试通过")

    def test_v2_version_endpoint(self):
        """测试v2版本的版本端点"""
        logger.info("测试v2版本的版本端点")
        
        # 发送请求到v2版本端点
        response = self.client.get("/api/v2/version/")
        
        # 验证响应状态码
        self.assertEqual(response.status_code, 200, "v2版本端点应返回200状态码")
        
        # 验证响应内容类型
        self.assertEqual(response.headers["content-type"], "application/json", 
                         "v2版本端点应返回JSON内容")
        
        # 验证响应结构
        data = response.json()
        self.assertIn("versions", data, "响应应包含'versions'字段")
        self.assertIn("latest", data, "响应应包含'latest'字段")
        self.assertIn("current", data, "响应应包含'current'字段")
        
        logger.info("v2版本的版本端点测试通过")

    def test_health_check_v2(self):
        """测试v2版本的健康检查端点"""
        logger.info("测试v2版本的健康检查端点")
        
        # 发送请求到v2健康检查端点
        response = self.client.get("/api/v2/health")
        
        # 验证响应状态码
        self.assertEqual(response.status_code, 200, "v2健康检查端点应返回200状态码")
        
        # 验证响应内容类型
        self.assertEqual(response.headers["content-type"], "application/json", 
                         "v2健康检查端点应返回JSON内容")
        
        # 验证响应结构
        data = response.json()
        self.assertIn("status", data, "响应应包含'status'字段")
        self.assertIn("version", data, "响应应包含'version'字段")
        self.assertIn("api_version", data, "响应应包含'api_version'字段")
        self.assertIn("timestamp", data, "响应应包含'timestamp'字段")
        
        # 验证响应值
        self.assertEqual(data["status"], "ok", "健康状态应为'ok'")
        self.assertEqual(data["api_version"], "v2", "API版本应为'v2'")
        
        logger.info("v2版本的健康检查端点测试通过")

if __name__ == "__main__":
    unittest.main()
