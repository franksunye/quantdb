"""
E2E测试配置文件

定义E2E测试的配置参数，包括测试数据库、服务器设置等
"""

import os
import tempfile
from pathlib import Path

class E2ETestConfig:
    """E2E测试配置类"""
    
    def __init__(self):
        # 测试服务器配置
        self.SERVER_HOST = "127.0.0.1"
        self.SERVER_PORT = 18000  # 使用不同端口避免与开发服务器冲突
        self.BASE_URL = f"http://{self.SERVER_HOST}:{self.SERVER_PORT}"
        self.API_PREFIX = "/api/v1"
        
        # 测试数据库配置
        self.TEST_DB_DIR = Path(tempfile.gettempdir()) / "quantdb_e2e_tests"
        self.TEST_DB_DIR.mkdir(exist_ok=True)
        self.TEST_DB_PATH = self.TEST_DB_DIR / "test_stock_data.db"
        self.TEST_DB_URL = f"sqlite:///{self.TEST_DB_PATH}"
        
        # 测试数据配置
        self.TEST_SYMBOLS = ["000001", "600519"]  # 平安银行, 贵州茅台
        self.TEST_START_DATE = "20240101"
        self.TEST_END_DATE = "20240105"
        
        # 服务器启动配置
        self.SERVER_STARTUP_TIMEOUT = 30  # 秒
        self.SERVER_SHUTDOWN_TIMEOUT = 10  # 秒
        self.REQUEST_TIMEOUT = 30  # 秒
        
        # 日志配置
        self.LOG_LEVEL = "INFO"
        self.ENABLE_DETAILED_LOGGING = True
        
    def get_env_vars(self):
        """获取E2E测试需要的环境变量"""
        return {
            "DATABASE_URL": self.TEST_DB_URL,
            "ENVIRONMENT": "test",
            "LOG_LEVEL": self.LOG_LEVEL,
            # 确保使用测试数据库
            "QUANTDB_DB_PATH": str(self.TEST_DB_PATH),
        }
    
    def cleanup(self):
        """清理测试环境"""
        try:
            if self.TEST_DB_PATH.exists():
                self.TEST_DB_PATH.unlink()
            if self.TEST_DB_DIR.exists() and not any(self.TEST_DB_DIR.iterdir()):
                self.TEST_DB_DIR.rmdir()
        except Exception as e:
            print(f"清理测试环境时出错: {e}")

# 全局配置实例
e2e_config = E2ETestConfig()
