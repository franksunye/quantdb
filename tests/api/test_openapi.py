# tests/api/test_openapi.py
"""
测试OpenAPI文档功能

这个测试模块验证OpenAPI文档是否正确加载和提供。
"""

import json
import os
import sys
import unittest

from fastapi.testclient import TestClient

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from api.main import app
from core.utils.logger import get_logger

# 设置测试日志记录器
logger = get_logger("test_openapi")

class TestOpenAPI(unittest.TestCase):
    """测试OpenAPI文档功能"""

    def setUp(self):
        """设置测试环境"""
        self.client = TestClient(app)
        logger.info("设置TestOpenAPI测试环境")

    def test_openapi_json_endpoint(self):
        """测试OpenAPI JSON端点是否返回有效的OpenAPI规范"""
        logger.info("测试OpenAPI JSON端点")

        # 发送请求到OpenAPI JSON端点
        response = self.client.get("/api/v2/openapi.json")

        # 验证响应状态码
        self.assertEqual(response.status_code, 200, "OpenAPI JSON端点应返回200状态码")

        # 验证响应内容类型
        self.assertEqual(response.headers["content-type"], "application/json",
                         "OpenAPI JSON端点应返回JSON内容")

        # 验证响应是有效的JSON
        try:
            openapi_spec = response.json()
            logger.info("成功解析OpenAPI规范JSON")
        except json.JSONDecodeError:
            self.fail("OpenAPI JSON端点返回的内容不是有效的JSON")

        # 验证OpenAPI规范的基本结构
        self.assertIn("openapi", openapi_spec, "OpenAPI规范应包含'openapi'字段")
        self.assertIn("info", openapi_spec, "OpenAPI规范应包含'info'字段")
        self.assertIn("paths", openapi_spec, "OpenAPI规范应包含'paths'字段")

        # 验证API信息
        self.assertEqual(openapi_spec["info"]["title"], "QuantDB API",
                         "API标题应为'QuantDB API'")
        self.assertEqual(openapi_spec["info"]["version"], "2.1.0",
                         "API版本应为'2.1.0'")

        # 验证是否包含关键路径
        paths = openapi_spec["paths"]
        self.assertIn("/api/v1/historical/stock/{symbol}", paths,
                      "OpenAPI规范应包含历史股票数据路径")
        self.assertIn("/api/v1/historical/database/cache/status", paths,
                      "OpenAPI规范应包含缓存状态路径")

        logger.info("OpenAPI JSON端点测试通过")

    def test_swagger_ui_endpoint(self):
        """测试Swagger UI端点是否可访问"""
        logger.info("测试Swagger UI端点")

        # 发送请求到Swagger UI端点
        response = self.client.get("/api/v2/docs")

        # 验证响应状态码
        self.assertEqual(response.status_code, 200, "Swagger UI端点应返回200状态码")

        # 验证响应内容类型
        self.assertEqual(response.headers["content-type"], "text/html; charset=utf-8",
                         "Swagger UI端点应返回HTML内容")

        # 验证响应内容包含Swagger UI的关键元素
        content = response.content.decode("utf-8")
        self.assertIn("swagger-ui", content, "Swagger UI页面应包含'swagger-ui'元素")
        self.assertIn("QuantDB API", content, "Swagger UI页面应包含API标题")

        logger.info("Swagger UI端点测试通过")

    def test_health_endpoint(self):
        """测试健康检查端点是否返回正确格式的响应"""
        logger.info("测试健康检查端点")

        # 发送请求到健康检查端点
        response = self.client.get("/api/v1/health")

        # 验证响应状态码
        self.assertEqual(response.status_code, 200, "健康检查端点应返回200状态码")

        # 验证响应内容类型
        self.assertEqual(response.headers["content-type"], "application/json",
                         "健康检查端点应返回JSON内容")

        # 验证响应结构
        data = response.json()
        self.assertIn("status", data, "健康检查响应应包含'status'字段")
        self.assertIn("version", data, "健康检查响应应包含'version'字段")
        self.assertIn("timestamp", data, "健康检查响应应包含'timestamp'字段")

        # 验证响应值
        self.assertEqual(data["status"], "ok", "健康状态应为'ok'")
        # 健康检查端点返回"ok"，与OpenAPI规范一致

        logger.info("健康检查端点测试通过")

if __name__ == "__main__":
    unittest.main()
