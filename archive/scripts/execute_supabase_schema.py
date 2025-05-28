#!/usr/bin/env python
"""
执行Supabase架构SQL脚本

这个脚本使用Supabase REST API执行架构SQL脚本，避免编码问题。
"""

import os
import sys
import argparse
import logging
import requests
from dotenv import load_dotenv

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("execute-supabase-schema")

def execute_sql(supabase_url, supabase_service_key, sql):
    """
    使用Supabase REST API执行SQL
    
    Args:
        supabase_url: Supabase项目URL
        supabase_service_key: Supabase服务角色密钥
        sql: 要执行的SQL
    
    Returns:
        执行结果
    """
    url = f"{supabase_url}/rest/v1/rpc/exec_sql"
    headers = {
        "apikey": supabase_service_key,
        "Authorization": f"Bearer {supabase_service_key}",
        "Content-Type": "application/json"
    }
    data = {
        "query": sql
    }
    
    logger.info(f"执行SQL: {sql[:100]}...")
    
    try:
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 200:
            logger.info("SQL执行成功")
            return response.json()
        else:
            logger.error(f"SQL执行失败: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"执行SQL时发生错误: {str(e)}")
        return None

def read_sql_file(file_path):
    """
    读取SQL文件
    
    Args:
        file_path: SQL文件路径
    
    Returns:
        SQL语句列表
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 分割SQL语句
        statements = []
        current_statement = ""
        
        for line in content.split('\n'):
            # 跳过注释行
            if line.strip().startswith('--'):
                continue
            
            # 添加到当前语句
            current_statement += line + "\n"
            
            # 如果遇到语句结束符，添加到语句列表
            if line.strip().endswith(';'):
                statements.append(current_statement.strip())
                current_statement = ""
        
        # 添加最后一个语句（如果有）
        if current_statement.strip():
            statements.append(current_statement.strip())
        
        logger.info(f"从文件 {file_path} 中读取了 {len(statements)} 条SQL语句")
        return statements
    except Exception as e:
        logger.error(f"读取SQL文件时发生错误: {str(e)}")
        return []

def execute_schema(supabase_url, supabase_service_key, schema_file):
    """
    执行架构SQL脚本
    
    Args:
        supabase_url: Supabase项目URL
        supabase_service_key: Supabase服务角色密钥
        schema_file: 架构SQL文件路径
    
    Returns:
        是否成功
    """
    # 读取SQL文件
    statements = read_sql_file(schema_file)
    if not statements:
        logger.error("没有找到SQL语句")
        return False
    
    # 执行SQL语句
    success_count = 0
    error_count = 0
    
    for i, statement in enumerate(statements):
        logger.info(f"执行第 {i+1}/{len(statements)} 条SQL语句")
        result = execute_sql(supabase_url, supabase_service_key, statement)
        
        if result is not None:
            success_count += 1
        else:
            error_count += 1
    
    logger.info(f"执行完成: {success_count} 条成功, {error_count} 条失败")
    return error_count == 0

def main():
    """主入口点"""
    parser = argparse.ArgumentParser(description="执行Supabase架构SQL脚本")
    parser.add_argument("schema_file", help="架构SQL文件路径")
    parser.add_argument("--url", help="Supabase项目URL")
    parser.add_argument("--key", help="Supabase服务角色密钥")
    
    args = parser.parse_args()
    
    # 加载环境变量
    load_dotenv()
    
    # 获取Supabase配置
    supabase_url = args.url or os.getenv("SUPABASE_URL")
    supabase_service_key = args.key or os.getenv("SUPABASE_SERVICE_KEY")
    
    if not supabase_url or not supabase_service_key:
        logger.error("未提供Supabase URL或服务角色密钥")
        sys.exit(1)
    
    # 执行架构
    success = execute_schema(supabase_url, supabase_service_key, args.schema_file)
    
    if success:
        logger.info("架构执行成功")
        sys.exit(0)
    else:
        logger.error("架构执行失败")
        sys.exit(1)

if __name__ == "__main__":
    main()
