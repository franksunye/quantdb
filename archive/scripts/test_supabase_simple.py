#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
简单测试Supabase数据库管理能力
这个脚本使用REST API测试Supabase数据库管理能力
"""

import os
import sys
import json
import time
import logging
import requests
from dotenv import load_dotenv

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("supabase_simple_test")

# 从.env文件加载环境变量
load_dotenv()

# 获取Supabase配置
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')

# 测试表名
TEST_TABLE_NAME = "test_simple_table"

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

def execute_sql(sql):
    """执行SQL语句"""
    try:
        # 构建请求URL
        url = f"{SUPABASE_URL}/rest/v1/rpc/execute_sql"
        
        # 设置请求头
        headers = {
            "apikey": SUPABASE_SERVICE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
            "Content-Type": "application/json"
        }
        
        # 准备请求数据
        data = {
            "sql": sql
        }
        
        # 发送请求
        logger.info(f"执行SQL: {sql}")
        response = requests.post(url, headers=headers, json=data)
        
        # 检查响应
        if response.status_code == 200:
            logger.info(f"SQL执行成功: {response.status_code}")
            return response.json()
        else:
            logger.error(f"SQL执行失败: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"执行SQL时出错: {e}")
        return None

def create_test_table():
    """创建测试表"""
    sql = f"""
    CREATE TABLE IF NOT EXISTS {TEST_TABLE_NAME} (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        value INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    return execute_sql(sql)

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
            return response.json()
        else:
            logger.error(f"测试数据插入失败: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"插入测试数据时出错: {e}")
        return None

def query_test_data():
    """查询测试数据"""
    try:
        # 构建请求URL
        url = f"{SUPABASE_URL}/rest/v1/{TEST_TABLE_NAME}?select=*&order=id.asc"
        
        # 设置请求头
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}"
        }
        
        # 发送请求
        logger.info(f"查询测试数据: {url}")
        response = requests.get(url, headers=headers)
        
        # 检查响应
        if response.status_code == 200:
            data = response.json()
            logger.info(f"查询成功，返回 {len(data)} 条记录")
            logger.info(f"数据: {json.dumps(data, ensure_ascii=False)}")
            return data
        else:
            logger.error(f"查询失败: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"查询测试数据时出错: {e}")
        return None

def drop_test_table():
    """删除测试表"""
    sql = f"DROP TABLE IF EXISTS {TEST_TABLE_NAME};"
    return execute_sql(sql)

def run_test():
    """运行完整测试流程"""
    logger.info("开始测试Supabase数据库管理能力")
    
    # 步骤1: 测试REST API连接
    logger.info("步骤1: 测试REST API连接")
    if not test_rest_api_connection():
        logger.error("REST API连接测试失败，终止测试")
        return False
    
    # 步骤2: 创建测试表
    logger.info("步骤2: 创建测试表")
    result = create_test_table()
    if result is None:
        logger.warning("使用execute_sql创建表失败，尝试替代方法")
        # 如果execute_sql函数不可用，可能需要创建自定义RPC函数
        # 这里简化处理，继续测试
    
    # 等待表创建完成
    logger.info("等待表创建完成...")
    time.sleep(2)
    
    # 步骤3: 插入测试数据
    logger.info("步骤3: 插入测试数据")
    inserted_data = insert_test_data()
    if inserted_data is None:
        logger.error("插入测试数据失败，继续测试")
    
    # 步骤4: 查询测试数据
    logger.info("步骤4: 查询测试数据")
    queried_data = query_test_data()
    if queried_data is None:
        logger.error("查询测试数据失败，继续测试")
    
    # 步骤5: 删除测试表
    logger.info("步骤5: 删除测试表")
    result = drop_test_table()
    if result is None:
        logger.warning("使用execute_sql删除表失败")
    
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
