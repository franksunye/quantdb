#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
基本测试Supabase REST API功能
这个脚本测试使用Supabase REST API进行基本的数据操作
"""

import os
import sys
import json
import logging
import requests
from dotenv import load_dotenv

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("supabase_basic_test")

# 从.env文件加载环境变量
load_dotenv()

# 获取Supabase配置
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')

def test_rest_api_connection():
    """测试REST API连接"""
    try:
        # 构建请求URL
        url = f"{SUPABASE_URL}/rest/v1/"
        
        # 设置请求头
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}"
        }
        
        # 发送请求
        logger.info(f"测试REST API连接: {url}")
        response = requests.get(url, headers=headers)
        
        # 检查响应
        if response.status_code == 200:
            logger.info(f"REST API连接成功: {response.status_code}")
            return True
        else:
            logger.error(f"REST API连接失败: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"测试REST API连接时出错: {e}")
        return False

def get_tables():
    """获取数据库中的表列表"""
    try:
        # 构建请求URL - 查询information_schema.tables
        url = f"{SUPABASE_URL}/rest/v1/information_schema/tables?select=table_name&table_schema=eq.public"
        
        # 设置请求头
        headers = {
            "apikey": SUPABASE_SERVICE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}"
        }
        
        # 发送请求
        logger.info(f"获取表列表: {url}")
        response = requests.get(url, headers=headers)
        
        # 检查响应
        if response.status_code == 200:
            tables = response.json()
            logger.info(f"成功获取表列表，共 {len(tables)} 个表")
            for table in tables:
                logger.info(f"表名: {table.get('table_name')}")
            return tables
        else:
            logger.error(f"获取表列表失败: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"获取表列表时出错: {e}")
        return None

def create_table_via_migration():
    """通过迁移API创建表"""
    try:
        # 构建请求URL
        url = f"{SUPABASE_URL}/rest/v1/migrations"
        
        # 设置请求头
        headers = {
            "apikey": SUPABASE_SERVICE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
            "Content-Type": "application/json"
        }
        
        # 准备迁移数据
        migration_data = {
            "name": "create_test_table",
            "sql": """
            CREATE TABLE IF NOT EXISTS test_table (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                value INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        }
        
        # 发送请求
        logger.info(f"创建表: {migration_data['sql']}")
        response = requests.post(url, headers=headers, json=migration_data)
        
        # 检查响应
        if response.status_code in [200, 201]:
            logger.info(f"表创建成功: {response.status_code}")
            return True
        else:
            logger.error(f"表创建失败: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"创建表时出错: {e}")
        return False

def test_psql_connection():
    """测试psql连接"""
    try:
        import subprocess
        
        # 构建psql命令
        cmd = [
            "psql",
            "-h", "aws-0-us-west-1.pooler.supabase.com",
            "-p", "6543",
            "-d", "postgres",
            "-U", "postgres.dvusiqfijdmjcsubyapw",
            "-c", "SELECT version();"
        ]
        
        # 设置环境变量
        env = os.environ.copy()
        env["PGPASSWORD"] = os.getenv('SUPABASE_DB_PASSWORD')
        
        # 执行命令
        logger.info("测试psql连接...")
        result = subprocess.run(cmd, capture_output=True, text=True, env=env)
        
        # 检查结果
        if result.returncode == 0:
            logger.info(f"psql连接成功: {result.stdout}")
            return True
        else:
            logger.error(f"psql连接失败: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"测试psql连接时出错: {e}")
        return False

def run_test():
    """运行完整测试流程"""
    logger.info("开始测试Supabase基本功能")
    
    # 步骤1: 测试REST API连接
    logger.info("步骤1: 测试REST API连接")
    if not test_rest_api_connection():
        logger.error("REST API连接测试失败，终止测试")
        return False
    
    # 步骤2: 获取表列表
    logger.info("步骤2: 获取表列表")
    tables = get_tables()
    if tables is None:
        logger.warning("获取表列表失败，继续测试")
    
    # 步骤3: 测试psql连接
    logger.info("步骤3: 测试psql连接")
    if not test_psql_connection():
        logger.warning("psql连接测试失败，继续测试")
    
    logger.info("测试完成")
    return True

if __name__ == "__main__":
    success = run_test()
    if success:
        logger.info("Supabase基本功能测试成功")
        sys.exit(0)
    else:
        logger.error("Supabase基本功能测试失败")
        sys.exit(1)
