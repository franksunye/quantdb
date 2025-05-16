"""
启动测试服务器脚本

此脚本用于启动一个用于端到端测试的API服务器。
使用专用端口8765，避免与开发服务器冲突。
"""

import uvicorn
import argparse
import sys
import os
import logging
import time
import socket
import requests
from contextlib import closing

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("test-server")

def is_port_in_use(port):
    """检查端口是否被占用"""
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        return s.connect_ex(('localhost', port)) == 0

def wait_for_server(host, port, max_retries=10, retry_delay=1):
    """等待服务器启动"""
    url = f"http://{host}:{port}/"

    for i in range(max_retries):
        try:
            logger.info(f"检查服务器是否启动 (尝试 {i+1}/{max_retries})...")
            response = requests.get(url)
            if response.status_code == 200 or response.status_code == 404:
                logger.info(f"服务器已启动 (状态码: {response.status_code})")
                return True
        except requests.exceptions.ConnectionError:
            pass

        time.sleep(retry_delay)

    logger.error(f"服务器启动超时")
    return False

def main():
    """启动测试服务器"""
    # 确保当前工作目录是项目根目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)  # 切换到脚本所在目录

    logger.info(f"当前工作目录: {os.getcwd()}")

    # 检查API模块是否可以导入
    try:
        from src.api.main import app
        logger.info("成功导入API模块")
    except ImportError as e:
        logger.error(f"导入API模块失败: {e}")
        logger.error("请确保您在项目根目录运行此脚本")
        sys.exit(1)

    parser = argparse.ArgumentParser(description='启动测试API服务器')
    parser.add_argument('--port', type=int, default=8765, help='服务器端口 (默认: 8765)')
    parser.add_argument('--host', type=str, default='127.0.0.1', help='服务器主机 (默认: 127.0.0.1)')
    args = parser.parse_args()

    # 检查端口是否被占用
    if is_port_in_use(args.port):
        logger.error(f"端口 {args.port} 已被占用，请尝试其他端口")
        sys.exit(1)

    logger.info(f"启动测试服务器在 {args.host}:{args.port}")
    logger.info("按 Ctrl+C 停止服务器")

    # 启动服务器
    try:
        # 使用线程启动服务器，这样可以在主线程中检查服务器是否启动成功
        import threading
        server_thread = threading.Thread(
            target=uvicorn.run,
            kwargs={
                "app": "src.api.main:app",
                "host": args.host,
                "port": args.port,
                "log_level": "info"
            }
        )
        server_thread.daemon = True
        server_thread.start()

        # 等待服务器启动
        if wait_for_server(args.host, args.port):
            logger.info(f"服务器已成功启动，可以开始运行测试")

            # 测试API端点
            test_url = f"http://{args.host}:{args.port}/api/v2/historical/stock/000001?start_date=20250421&end_date=20250425"
            logger.info(f"测试API端点: {test_url}")
            try:
                response = requests.get(test_url)
                logger.info(f"API测试结果: 状态码 {response.status_code}")
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"API返回数据: {len(data.get('data', []))} 条记录")
                else:
                    logger.warning(f"API返回非200状态码: {response.status_code}")
            except Exception as e:
                logger.error(f"API测试失败: {e}")

            # 保持主线程运行
            while True:
                time.sleep(1)
        else:
            logger.error("服务器启动失败")
            sys.exit(1)
    except KeyboardInterrupt:
        logger.info("收到中断信号，停止服务器")
    except Exception as e:
        logger.error(f"启动服务器时出错: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
