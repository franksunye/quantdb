"""
E2E测试服务器管理器

负责启动、停止和管理E2E测试用的API服务器
"""

import os
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

import requests

# 添加项目根目录到路径
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine

from core.models import Base
from core.utils.logger import get_logger
from tests.e2e.config import e2e_config

logger = get_logger("e2e_server_manager")


class E2EServerManager:
    """E2E测试服务器管理器"""

    def __init__(self):
        self.server_process = None
        self.config = e2e_config

    def start_server(self):
        """启动测试服务器"""
        logger.info("启动E2E测试服务器...")

        # 初始化测试数据库
        self._initialize_test_database()

        # 设置环境变量
        env = os.environ.copy()
        env.update(self.config.get_env_vars())

        # 启动服务器进程
        cmd = [
            sys.executable,
            "-m",
            "uvicorn",
            "api.main:app",
            "--host",
            self.config.SERVER_HOST,
            "--port",
            str(self.config.SERVER_PORT),
            "--log-level",
            "warning",  # 减少日志输出
        ]

        try:
            self.server_process = subprocess.Popen(
                cmd,
                env=env,
                cwd=str(project_root),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid,  # 创建新的进程组
            )

            # 等待服务器启动
            if self._wait_for_server():
                logger.info(f"E2E测试服务器已启动: {self.config.BASE_URL}")
                return True
            else:
                logger.error("E2E测试服务器启动失败")
                self.stop_server()
                return False

        except Exception as e:
            logger.error(f"启动E2E测试服务器时出错: {e}")
            return False

    def _wait_for_server(self):
        """等待服务器启动并响应"""
        logger.info("等待服务器响应...")

        for attempt in range(self.config.SERVER_STARTUP_TIMEOUT):
            try:
                response = requests.get(
                    f"{self.config.BASE_URL}{self.config.API_PREFIX}/health", timeout=2
                )
                if response.status_code == 200:
                    logger.info("服务器响应正常")
                    return True
            except requests.exceptions.RequestException:
                pass

            time.sleep(1)

        return False

    def _initialize_test_database(self):
        """初始化测试数据库"""
        logger.info("初始化E2E测试数据库...")

        try:
            # 确保测试数据库目录存在
            self.config.TEST_DB_DIR.mkdir(exist_ok=True)

            # 删除现有的测试数据库文件
            if self.config.TEST_DB_PATH.exists():
                self.config.TEST_DB_PATH.unlink()

            # 创建数据库引擎并创建所有表
            engine = create_engine(self.config.TEST_DB_URL)
            Base.metadata.create_all(engine)
            engine.dispose()

            logger.info("E2E测试数据库初始化完成")

        except Exception as e:
            logger.error(f"初始化E2E测试数据库时出错: {e}")
            raise

    def stop_server(self):
        """停止测试服务器"""
        if self.server_process:
            logger.info("停止E2E测试服务器...")

            try:
                # 发送SIGTERM信号给整个进程组
                os.killpg(os.getpgid(self.server_process.pid), signal.SIGTERM)

                # 等待进程结束
                try:
                    self.server_process.wait(
                        timeout=self.config.SERVER_SHUTDOWN_TIMEOUT
                    )
                except subprocess.TimeoutExpired:
                    # 如果进程没有在超时时间内结束，强制杀死
                    logger.warning("服务器未在超时时间内停止，强制终止")
                    os.killpg(os.getpgid(self.server_process.pid), signal.SIGKILL)
                    self.server_process.wait()

                logger.info("E2E测试服务器已停止")

            except Exception as e:
                logger.error(f"停止E2E测试服务器时出错: {e}")

            finally:
                self.server_process = None

    def is_running(self):
        """检查服务器是否正在运行"""
        if not self.server_process:
            return False

        # 检查进程是否还活着
        if self.server_process.poll() is not None:
            return False

        # 检查服务器是否响应
        try:
            response = requests.get(
                f"{self.config.BASE_URL}{self.config.API_PREFIX}/health", timeout=2
            )
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    def __enter__(self):
        """上下文管理器入口"""
        if self.start_server():
            return self
        else:
            raise Exception("无法启动E2E测试服务器")

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.stop_server()
        self.config.cleanup()


# 全局服务器管理器实例
server_manager = E2EServerManager()
