#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
验证Supabase部署脚本
用于验证QuantDB是否成功部署到Supabase
"""

import os
import sys
import json
import logging
import argparse
import requests
from dotenv import load_dotenv

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("supabase_deployment_verifier")

# 从.env文件加载环境变量
load_dotenv()

def verify_database_connection():
    """验证数据库连接"""
    logger.info("验证Supabase数据库连接...")
    
    try:
        # 导入Supabase适配器
        from src.db.supabase_adapter import SupabaseAdapter
        
        # 创建适配器实例
        adapter = SupabaseAdapter()
        
        # 连接到数据库
        if not adapter.connect():
            logger.error("无法连接到Supabase数据库")
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

def verify_database_schema():
    """验证数据库架构"""
    logger.info("验证数据库架构...")
    
    try:
        # 导入Supabase适配器
        from src.db.supabase_adapter import SupabaseAdapter
        
        # 创建适配器实例
        adapter = SupabaseAdapter()
        
        # 连接到数据库
        if not adapter.connect():
            logger.error("无法连接到Supabase数据库")
            return False
        
        # 检查必要的表是否存在
        tables_query = """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        """
        tables_result = adapter.execute_query(tables_query)
        
        if not tables_result:
            logger.error("无法获取表列表")
            adapter.disconnect()
            return False
        
        # 提取表名
        table_names = [table['table_name'] for table in tables_result]
        
        # 检查必要的表
        required_tables = ['assets', 'daily_stock_data']
        missing_tables = [table for table in required_tables if table not in table_names]
        
        if missing_tables:
            logger.error(f"缺少以下表: {', '.join(missing_tables)}")
            adapter.disconnect()
            return False
        
        logger.info(f"检测到以下表: {', '.join(table_names)}")
        
        # 检查assets表的列
        assets_columns_query = """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'assets'
        """
        assets_columns_result = adapter.execute_query(assets_columns_query)
        
        if not assets_columns_result:
            logger.error("无法获取assets表的列")
            adapter.disconnect()
            return False
        
        # 提取列名
        assets_column_names = [column['column_name'] for column in assets_columns_result]
        
        # 检查必要的列
        required_assets_columns = ['asset_id', 'symbol', 'name', 'asset_type', 'exchange', 'currency']
        missing_assets_columns = [column for column in required_assets_columns if column not in assets_column_names]
        
        if missing_assets_columns:
            logger.error(f"assets表缺少以下列: {', '.join(missing_assets_columns)}")
            adapter.disconnect()
            return False
        
        logger.info("数据库架构验证成功")
        adapter.disconnect()
        return True
    except Exception as e:
        logger.error(f"验证数据库架构时出错: {e}")
        return False

def verify_data_migration():
    """验证数据迁移"""
    logger.info("验证数据迁移...")
    
    try:
        # 导入Supabase适配器
        from src.db.supabase_adapter import SupabaseAdapter
        
        # 创建适配器实例
        adapter = SupabaseAdapter()
        
        # 连接到数据库
        if not adapter.connect():
            logger.error("无法连接到Supabase数据库")
            return False
        
        # 检查assets表中的记录数
        assets_count_query = "SELECT COUNT(*) as count FROM assets"
        assets_count_result = adapter.execute_query(assets_count_query)
        
        if not assets_count_result:
            logger.error("无法获取assets表的记录数")
            adapter.disconnect()
            return False
        
        assets_count = assets_count_result[0]['count']
        
        # 检查daily_stock_data表中的记录数
        stock_data_count_query = "SELECT COUNT(*) as count FROM daily_stock_data"
        stock_data_count_result = adapter.execute_query(stock_data_count_query)
        
        if not stock_data_count_result:
            logger.error("无法获取daily_stock_data表的记录数")
            adapter.disconnect()
            return False
        
        stock_data_count = stock_data_count_result[0]['count']
        
        logger.info(f"assets表中有 {assets_count} 条记录")
        logger.info(f"daily_stock_data表中有 {stock_data_count} 条记录")
        
        # 检查是否有足够的数据
        if assets_count == 0:
            logger.warning("assets表中没有记录，数据迁移可能失败")
            adapter.disconnect()
            return False
        
        if stock_data_count == 0:
            logger.warning("daily_stock_data表中没有记录，数据迁移可能失败")
            adapter.disconnect()
            return False
        
        logger.info("数据迁移验证成功")
        adapter.disconnect()
        return True
    except Exception as e:
        logger.error(f"验证数据迁移时出错: {e}")
        return False

def verify_api_connection(api_url=None):
    """验证API连接"""
    logger.info("验证API连接...")
    
    # 如果没有提供API URL，使用默认值
    if not api_url:
        api_url = "http://localhost:8000"
    
    try:
        # 检查API健康状态
        health_url = f"{api_url}/api/v1/health"
        logger.info(f"检查API健康状态: {health_url}")
        
        response = requests.get(health_url)
        
        if response.status_code != 200:
            logger.error(f"API健康检查失败: {response.status_code} - {response.text}")
            return False
        
        logger.info(f"API健康检查成功: {response.text}")
        
        # 检查API版本
        version_url = f"{api_url}/api/v1/version"
        logger.info(f"检查API版本: {version_url}")
        
        response = requests.get(version_url)
        
        if response.status_code != 200:
            logger.error(f"API版本检查失败: {response.status_code} - {response.text}")
            return False
        
        logger.info(f"API版本检查成功: {response.text}")
        
        # 检查API文档
        docs_url = f"{api_url}/api/v1/docs"
        logger.info(f"检查API文档: {docs_url}")
        
        response = requests.get(docs_url)
        
        if response.status_code != 200:
            logger.error(f"API文档检查失败: {response.status_code}")
            return False
        
        logger.info("API文档检查成功")
        
        logger.info("API连接验证成功")
        return True
    except Exception as e:
        logger.error(f"验证API连接时出错: {e}")
        return False

def verify_api_functionality(api_url=None):
    """验证API功能"""
    logger.info("验证API功能...")
    
    # 如果没有提供API URL，使用默认值
    if not api_url:
        api_url = "http://localhost:8000"
    
    try:
        # 检查股票数据API
        stock_url = f"{api_url}/api/v1/stocks/000001/prices?start_date=20250101&end_date=20250110"
        logger.info(f"检查股票数据API: {stock_url}")
        
        response = requests.get(stock_url)
        
        if response.status_code != 200:
            logger.error(f"股票数据API检查失败: {response.status_code} - {response.text}")
            return False
        
        data = response.json()
        
        if not data or 'prices' not in data:
            logger.error(f"股票数据API返回格式不正确: {data}")
            return False
        
        logger.info(f"股票数据API检查成功，返回了 {len(data['prices'])} 条记录")
        
        logger.info("API功能验证成功")
        return True
    except Exception as e:
        logger.error(f"验证API功能时出错: {e}")
        return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='验证Supabase部署脚本')
    parser.add_argument('--api-url', help='API URL，默认为http://localhost:8000')
    parser.add_argument('--skip-db-connection', action='store_true', help='跳过数据库连接验证')
    parser.add_argument('--skip-db-schema', action='store_true', help='跳过数据库架构验证')
    parser.add_argument('--skip-data-migration', action='store_true', help='跳过数据迁移验证')
    parser.add_argument('--skip-api-connection', action='store_true', help='跳过API连接验证')
    parser.add_argument('--skip-api-functionality', action='store_true', help='跳过API功能验证')
    
    args = parser.parse_args()
    
    # 验证数据库连接
    if not args.skip_db_connection and not verify_database_connection():
        logger.error("数据库连接验证失败")
        return False
    
    # 验证数据库架构
    if not args.skip_db_schema and not verify_database_schema():
        logger.error("数据库架构验证失败")
        return False
    
    # 验证数据迁移
    if not args.skip_data_migration and not verify_data_migration():
        logger.error("数据迁移验证失败")
        return False
    
    # 验证API连接
    if not args.skip_api_connection and not verify_api_connection(args.api_url):
        logger.error("API连接验证失败")
        return False
    
    # 验证API功能
    if not args.skip_api_functionality and not verify_api_functionality(args.api_url):
        logger.error("API功能验证失败")
        return False
    
    logger.info("所有验证通过，Supabase部署成功！")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
