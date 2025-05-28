#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
QuantDB Supabase部署执行脚本
用于按顺序执行Supabase部署的各个步骤
"""

import os
import sys
import time
import logging
import argparse
import subprocess
from dotenv import load_dotenv

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("supabase_deployment_runner")

# 从.env文件加载环境变量
load_dotenv()

def check_prerequisites():
    """检查前提条件"""
    logger.info("检查前提条件...")
    
    # 检查环境变量
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
        logger.error(f"缺少以下环境变量: {', '.join(missing_vars)}")
        return False
    
    # 检查SSL证书
    ssl_cert = os.getenv('SUPABASE_SSL_CERT')
    if not os.path.exists(ssl_cert):
        logger.error(f"SSL证书文件不存在: {ssl_cert}")
        return False
    
    # 检查psql是否可用
    try:
        result = subprocess.run(['psql', '--version'], capture_output=True, text=True)
        if result.returncode != 0:
            logger.error("psql命令不可用，请确保已安装PostgreSQL客户端工具")
            return False
        logger.info(f"检测到psql: {result.stdout.strip()}")
    except FileNotFoundError:
        logger.error("psql命令不可用，请确保已安装PostgreSQL客户端工具")
        return False
    
    # 检查Python依赖
    try:
        import psycopg2
        logger.info("检测到psycopg2")
    except ImportError:
        logger.error("未安装psycopg2，请运行: pip install psycopg2-binary")
        return False
    
    logger.info("前提条件检查通过")
    return True

def initialize_database():
    """初始化数据库"""
    logger.info("开始初始化数据库...")
    
    try:
        result = subprocess.run(
            ['python', 'scripts/deploy_to_supabase.py', '--init-db'],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            logger.error(f"初始化数据库失败: {result.stderr}")
            return False
        
        logger.info(result.stdout)
        logger.info("数据库初始化成功")
        return True
    except Exception as e:
        logger.error(f"初始化数据库时出错: {e}")
        return False

def migrate_data():
    """迁移数据"""
    logger.info("开始迁移数据...")
    
    try:
        result = subprocess.run(
            ['python', 'scripts/deploy_to_supabase.py', '--migrate-data'],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            logger.error(f"迁移数据失败: {result.stderr}")
            return False
        
        logger.info(result.stdout)
        logger.info("数据迁移成功")
        return True
    except Exception as e:
        logger.error(f"迁移数据时出错: {e}")
        return False

def test_supabase_adapter():
    """测试Supabase适配器"""
    logger.info("开始测试Supabase适配器...")
    
    try:
        result = subprocess.run(
            ['python', '-m', 'unittest', 'tests.test_supabase_adapter'],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            logger.error(f"Supabase适配器测试失败: {result.stderr}")
            return False
        
        logger.info(result.stdout)
        logger.info("Supabase适配器测试通过")
        return True
    except Exception as e:
        logger.error(f"测试Supabase适配器时出错: {e}")
        return False

def update_api_config():
    """更新API配置"""
    logger.info("开始更新API配置...")
    
    # 构建数据库URL
    db_host = os.getenv('SUPABASE_DB_HOST')
    db_port = os.getenv('SUPABASE_DB_PORT')
    db_name = os.getenv('SUPABASE_DB_NAME')
    db_user = os.getenv('SUPABASE_DB_USER')
    db_password = os.getenv('SUPABASE_DB_PASSWORD')
    ssl_cert = os.getenv('SUPABASE_SSL_CERT')
    
    db_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}?sslmode=verify-full&sslrootcert={ssl_cert}"
    
    # 更新.env文件
    try:
        with open('.env', 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        with open('.env', 'w', encoding='utf-8') as f:
            for line in lines:
                if line.startswith('DATABASE_URL=sqlite:'):
                    f.write(f"# {line}")  # 注释掉SQLite配置
                    f.write(f"DATABASE_URL={db_url}\n")  # 添加Supabase配置
                else:
                    f.write(line)
        
        logger.info("API配置更新成功")
        return True
    except Exception as e:
        logger.error(f"更新API配置时出错: {e}")
        return False

def start_api_service():
    """启动API服务"""
    logger.info("开始启动API服务...")
    
    try:
        # 使用非阻塞方式启动API服务
        process = subprocess.Popen(
            ['uvicorn', 'src.api.main:app', '--host', '0.0.0.0', '--port', '8000'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # 等待服务启动
        logger.info("等待API服务启动...")
        time.sleep(5)
        
        # 检查服务是否正常运行
        try:
            import requests
            response = requests.get('http://localhost:8000/api/v1/health')
            if response.status_code == 200:
                logger.info("API服务启动成功")
                return True, process
            else:
                logger.error(f"API服务健康检查失败: {response.status_code}")
                process.terminate()
                return False, None
        except Exception as e:
            logger.error(f"API服务健康检查出错: {e}")
            process.terminate()
            return False, None
    except Exception as e:
        logger.error(f"启动API服务时出错: {e}")
        return False, None

def run_end_to_end_tests():
    """运行端到端测试"""
    logger.info("开始运行端到端测试...")
    
    # 启动测试服务器
    try:
        test_server = subprocess.Popen(
            ['python', 'start_test_server.py', '--port', '8766'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # 等待测试服务器启动
        logger.info("等待测试服务器启动...")
        time.sleep(5)
        
        # 运行测试
        result = subprocess.run(
            ['python', '-m', 'unittest', 'tests.e2e.test_stock_data_http_api'],
            capture_output=True,
            text=True
        )
        
        # 停止测试服务器
        test_server.terminate()
        
        if result.returncode != 0:
            logger.error(f"端到端测试失败: {result.stderr}")
            return False
        
        logger.info(result.stdout)
        logger.info("端到端测试通过")
        return True
    except Exception as e:
        logger.error(f"运行端到端测试时出错: {e}")
        if 'test_server' in locals():
            test_server.terminate()
        return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='QuantDB Supabase部署执行脚本')
    parser.add_argument('--skip-prereq', action='store_true', help='跳过前提条件检查')
    parser.add_argument('--skip-init', action='store_true', help='跳过数据库初始化')
    parser.add_argument('--skip-migrate', action='store_true', help='跳过数据迁移')
    parser.add_argument('--skip-test-adapter', action='store_true', help='跳过Supabase适配器测试')
    parser.add_argument('--skip-update-config', action='store_true', help='跳过API配置更新')
    parser.add_argument('--skip-start-api', action='store_true', help='跳过API服务启动')
    parser.add_argument('--skip-e2e-tests', action='store_true', help='跳过端到端测试')
    
    args = parser.parse_args()
    
    # 检查前提条件
    if not args.skip_prereq and not check_prerequisites():
        logger.error("前提条件检查失败，终止部署")
        return False
    
    # 初始化数据库
    if not args.skip_init and not initialize_database():
        logger.error("数据库初始化失败，终止部署")
        return False
    
    # 迁移数据
    if not args.skip_migrate and not migrate_data():
        logger.error("数据迁移失败，终止部署")
        return False
    
    # 测试Supabase适配器
    if not args.skip_test_adapter and not test_supabase_adapter():
        logger.error("Supabase适配器测试失败，终止部署")
        return False
    
    # 更新API配置
    if not args.skip_update_config and not update_api_config():
        logger.error("API配置更新失败，终止部署")
        return False
    
    # 启动API服务
    api_process = None
    if not args.skip_start_api:
        success, api_process = start_api_service()
        if not success:
            logger.error("API服务启动失败，终止部署")
            return False
    
    # 运行端到端测试
    if not args.skip_e2e_tests and not run_end_to_end_tests():
        logger.error("端到端测试失败")
        if api_process:
            api_process.terminate()
        return False
    
    # 停止API服务
    if api_process:
        logger.info("停止API服务...")
        api_process.terminate()
    
    logger.info("QuantDB成功部署到Supabase")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
