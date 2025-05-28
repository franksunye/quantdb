#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试Supabase数据库管理能力
这个脚本测试使用REST API和psql命令行工具管理Supabase数据库的能力
"""

import os
import sys
import json
import time
import logging
import subprocess
import requests
from dotenv import load_dotenv

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("supabase_management_test")

# 从.env文件加载环境变量
load_dotenv()

# 获取Supabase配置
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')
SUPABASE_DB_PASSWORD = os.getenv('SUPABASE_DB_PASSWORD')

# 测试表名
TEST_TABLE_NAME = "test_management_table"

def execute_psql_query(query):
    """执行psql查询并返回结果"""
    try:
        # 构建psql命令
        cmd = [
            "psql",
            "-h", "aws-0-us-west-1.pooler.supabase.com",
            "-p", "6543",
            "-d", "postgres",
            "-U", "postgres.dvusiqfijdmjcsubyapw",
            "-c", query
        ]
        
        # 设置环境变量
        env = os.environ.copy()
        env["PGPASSWORD"] = SUPABASE_DB_PASSWORD
        
        # 执行命令
        logger.info(f"执行psql查询: {query}")
        result = subprocess.run(cmd, capture_output=True, text=True, env=env)
        
        if result.returncode != 0:
            logger.error(f"psql查询失败: {result.stderr}")
            return None
        
        logger.info("psql查询成功")
        return result.stdout
    except Exception as e:
        logger.error(f"执行psql查询时出错: {e}")
        return None

def create_rpc_function():
    """创建用于管理表的RPC函数"""
    try:
        # 构建SQL函数，用于创建和删除测试表
        sql_function = f"""
        CREATE OR REPLACE FUNCTION create_test_table()
        RETURNS void AS $$
        BEGIN
          CREATE TABLE IF NOT EXISTS {TEST_TABLE_NAME} (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            value INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
          );
        END;
        $$ LANGUAGE plpgsql;
        
        CREATE OR REPLACE FUNCTION drop_test_table()
        RETURNS void AS $$
        BEGIN
          DROP TABLE IF EXISTS {TEST_TABLE_NAME};
        END;
        $$ LANGUAGE plpgsql;
        """
        
        # 使用psql执行SQL函数定义
        result = execute_psql_query(sql_function)
        if not result:
            logger.error("创建RPC函数失败")
            return False
        
        logger.info("成功创建RPC函数")
        return True
    except Exception as e:
        logger.error(f"创建RPC函数时出错: {e}")
        return False

def call_rpc_function(function_name, params=None):
    """调用RPC函数"""
    try:
        # 构建请求URL
        url = f"{SUPABASE_URL}/rest/v1/rpc/{function_name}"
        
        # 设置请求头
        headers = {
            "apikey": SUPABASE_SERVICE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
            "Content-Type": "application/json"
        }
        
        # 发送请求
        logger.info(f"调用RPC函数: {function_name}")
        response = requests.post(url, headers=headers, json=params or {})
        
        # 检查响应
        if response.status_code == 200:
            logger.info(f"RPC函数调用成功: {function_name}")
            return True
        else:
            logger.error(f"RPC函数调用失败: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"调用RPC函数时出错: {e}")
        return False

def insert_test_data():
    """插入测试数据"""
    try:
        # 构建请求URL
        url = f"{SUPABASE_URL}/rest/v1/{TEST_TABLE_NAME}"
        
        # 设置请求头
        headers = {
            "apikey": SUPABASE_SERVICE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }
        
        # 准备测试数据
        test_data = [
            {"name": "测试项目1", "value": 100},
            {"name": "测试项目2", "value": 200},
            {"name": "测试项目3", "value": 300}
        ]
        
        # 发送请求
        logger.info(f"插入测试数据: {json.dumps(test_data, ensure_ascii=False)}")
        response = requests.post(url, headers=headers, json=test_data)
        
        # 检查响应
        if response.status_code in [200, 201]:
            logger.info(f"测试数据插入成功: {response.status_code}")
            return True
        else:
            logger.error(f"测试数据插入失败: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"插入测试数据时出错: {e}")
        return False

def query_test_data():
    """使用psql查询测试数据"""
    query = f"SELECT * FROM {TEST_TABLE_NAME} ORDER BY id;"
    result = execute_psql_query(query)
    
    if result:
        logger.info(f"查询结果:\n{result}")
        return True
    else:
        logger.error("查询测试数据失败")
        return False

def run_test():
    """运行完整测试流程"""
    logger.info("开始测试Supabase数据库管理能力")
    
    # 步骤1: 测试psql连接
    logger.info("步骤1: 测试psql连接")
    result = execute_psql_query("SELECT version();")
    if not result:
        logger.error("psql连接测试失败，终止测试")
        return False
    
    # 步骤2: 创建RPC函数
    logger.info("步骤2: 创建RPC函数")
    if not create_rpc_function():
        logger.error("创建RPC函数失败，终止测试")
        return False
    
    # 步骤3: 调用RPC函数创建测试表
    logger.info("步骤3: 调用RPC函数创建测试表")
    if not call_rpc_function("create_test_table"):
        logger.error("创建测试表失败，终止测试")
        return False
    
    # 等待表创建完成
    logger.info("等待表创建完成...")
    time.sleep(2)
    
    # 步骤4: 插入测试数据
    logger.info("步骤4: 插入测试数据")
    if not insert_test_data():
        logger.error("插入测试数据失败，继续测试")
    
    # 步骤5: 查询测试数据
    logger.info("步骤5: 查询测试数据")
    if not query_test_data():
        logger.error("查询测试数据失败，继续测试")
    
    # 步骤6: 调用RPC函数删除测试表
    logger.info("步骤6: 调用RPC函数删除测试表")
    if not call_rpc_function("drop_test_table"):
        logger.error("删除测试表失败，继续测试")
    
    logger.info("测试完成")
    return True

if __name__ == "__main__":
    success = run_test()
    if success:
        logger.info("Supabase数据库管理能力测试成功")
        sys.exit(0)
    else:
        logger.error("Supabase数据库管理能力测试失败")
        sys.exit(1)
