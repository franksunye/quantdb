#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
API部署脚本
用于部署QuantDB API服务
"""

import os
import sys
import argparse
import logging
import subprocess
from dotenv import load_dotenv

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("api_deployer")

# 从.env文件加载环境变量
load_dotenv()

def check_prerequisites():
    """检查前提条件"""
    logger.info("检查前提条件...")
    
    # 检查环境变量
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        logger.error("缺少DATABASE_URL环境变量")
        return False
    
    # 检查数据库类型
    if database_url.startswith('postgresql'):
        # 检查Supabase配置
        required_vars = [
            'SUPABASE_DB_HOST',
            'SUPABASE_DB_PORT',
            'SUPABASE_DB_NAME',
            'SUPABASE_DB_USER',
            'SUPABASE_DB_PASSWORD',
            'SUPABASE_SSL_CERT'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            logger.error(f"缺少以下Supabase环境变量: {', '.join(missing_vars)}")
            return False
        
        # 检查SSL证书
        ssl_cert = os.getenv('SUPABASE_SSL_CERT')
        if not os.path.exists(ssl_cert):
            logger.error(f"SSL证书文件不存在: {ssl_cert}")
            return False
    
    # 检查uvicorn是否可用
    try:
        result = subprocess.run(['uvicorn', '--version'], capture_output=True, text=True)
        if result.returncode != 0:
            logger.error("uvicorn命令不可用，请确保已安装FastAPI和uvicorn")
            return False
        logger.info(f"检测到uvicorn: {result.stdout.strip()}")
    except FileNotFoundError:
        logger.error("uvicorn命令不可用，请确保已安装FastAPI和uvicorn")
        return False
    
    logger.info("前提条件检查通过")
    return True

def verify_database_connection():
    """验证数据库连接"""
    logger.info("验证数据库连接...")
    
    try:
        # 导入数据库适配器
        from src.db.adapter_factory import create_db_adapter
        
        # 创建适配器实例
        adapter = create_db_adapter()
        
        # 连接到数据库
        if not adapter.connect():
            logger.error("无法连接到数据库")
            return False
        
        # 执行简单查询
        result = adapter.execute_query("SELECT 1 as test")
        if not result or result[0]['test'] != 1:
            logger.error("数据库查询测试失败")
            adapter.disconnect()
            return False
        
        logger.info("数据库连接验证成功")
        adapter.disconnect()
        return True
    except Exception as e:
        logger.error(f"验证数据库连接时出错: {e}")
        return False

def start_api_service(host, port, reload):
    """启动API服务"""
    logger.info(f"启动API服务: {host}:{port}")
    
    # 构建命令
    cmd = ['uvicorn', 'src.api.main:app', '--host', host, '--port', str(port)]
    if reload:
        cmd.append('--reload')
    
    # 启动服务
    try:
        logger.info(f"执行命令: {' '.join(cmd)}")
        process = subprocess.Popen(cmd)
        logger.info(f"API服务已启动，进程ID: {process.pid}")
        return process
    except Exception as e:
        logger.error(f"启动API服务时出错: {e}")
        return None

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='API部署脚本')
    parser.add_argument('--host', default='0.0.0.0', help='API服务主机地址')
    parser.add_argument('--port', type=int, default=8000, help='API服务端口')
    parser.add_argument('--reload', action='store_true', help='启用自动重载')
    parser.add_argument('--skip-checks', action='store_true', help='跳过前提条件检查')
    
    args = parser.parse_args()
    
    # 检查前提条件
    if not args.skip_checks:
        if not check_prerequisites():
            logger.error("前提条件检查失败，终止部署")
            return 1
        
        if not verify_database_connection():
            logger.error("数据库连接验证失败，终止部署")
            return 1
    
    # 启动API服务
    process = start_api_service(args.host, args.port, args.reload)
    if not process:
        logger.error("API服务启动失败")
        return 1
    
    # 等待服务结束
    try:
        process.wait()
    except KeyboardInterrupt:
        logger.info("收到中断信号，停止API服务")
        process.terminate()
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
