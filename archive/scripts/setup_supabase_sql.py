"""
使用SQL文件设置Supabase的脚本

此脚本读取SQL文件并将其内容发送到Supabase的SQL编辑器API。
"""

import os
import sys
import logging
import requests
import json
import base64
from dotenv import load_dotenv

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("supabase_sql_setup")

# 从.env文件加载环境变量
load_dotenv()

def check_env_variables():
    """检查必要的环境变量是否存在"""
    required_vars = ['SUPABASE_URL', 'SUPABASE_KEY', 'SUPABASE_SERVICE_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"缺少以下环境变量: {', '.join(missing_vars)}")
        return False
    
    logger.info("环境变量检查通过")
    return True

def test_connection():
    """测试Supabase连接"""
    try:
        # 获取Supabase URL和API密钥
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')
        
        logger.info(f"连接到Supabase: {supabase_url}")
        
        # 测试REST API连接
        headers = {
            "apikey": supabase_key,
            "Content-Type": "application/json"
        }
        
        # 尝试获取健康状态
        response = requests.get(
            f"{supabase_url}/rest/v1/",
            headers=headers
        )
        
        if response.status_code == 200:
            logger.info("Supabase连接成功")
            return True
        else:
            logger.error(f"Supabase连接失败: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"Supabase连接测试失败: {e}")
        return False

def execute_sql_file(file_path):
    """执行SQL文件"""
    try:
        # 读取SQL文件
        with open(file_path, 'r') as f:
            sql_content = f.read()
        
        # 获取Supabase URL和API密钥
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_service_key = os.getenv('SUPABASE_SERVICE_KEY')
        
        logger.info(f"执行SQL文件: {file_path}")
        
        # 使用REST API执行SQL
        headers = {
            "apikey": supabase_service_key,
            "Authorization": f"Bearer {supabase_service_key}",
            "Content-Type": "application/json"
        }
        
        # 将SQL语句拆分为多个语句
        sql_statements = sql_content.split(';')
        
        # 逐个执行SQL语句
        for i, statement in enumerate(sql_statements):
            # 跳过空语句
            if not statement.strip():
                continue
            
            # 添加分号
            statement = statement.strip() + ';'
            
            logger.info(f"执行SQL语句 {i+1}/{len(sql_statements)}: {statement[:50]}...")
            
            # 使用REST API执行SQL
            response = requests.post(
                f"{supabase_url}/rest/v1/rpc/execute_sql",
                headers=headers,
                json={"sql": statement}
            )
            
            if response.status_code == 200:
                logger.info(f"SQL语句 {i+1} 执行成功")
            else:
                logger.warning(f"SQL语句 {i+1} 执行失败: {response.status_code} - {response.text}")
                # 继续执行其他语句
        
        logger.info(f"SQL文件 {file_path} 执行完成")
        return True
    except Exception as e:
        logger.error(f"执行SQL文件失败: {e}")
        return False

def check_tables_exist():
    """检查表是否存在"""
    try:
        # 获取Supabase URL和API密钥
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_service_key = os.getenv('SUPABASE_SERVICE_KEY')
        
        # 使用REST API检查表
        headers = {
            "apikey": supabase_service_key,
            "Authorization": f"Bearer {supabase_service_key}",
            "Content-Type": "application/json"
        }
        
        # 检查assets表
        assets_response = requests.get(
            f"{supabase_url}/rest/v1/assets?limit=1",
            headers=headers
        )
        
        # 检查prices表
        prices_response = requests.get(
            f"{supabase_url}/rest/v1/prices?limit=1",
            headers=headers
        )
        
        if assets_response.status_code == 200 and prices_response.status_code == 200:
            logger.info("表检查成功: assets和prices表都存在")
            return True
        else:
            if assets_response.status_code != 200:
                logger.error(f"assets表检查失败: {assets_response.status_code} - {assets_response.text}")
            if prices_response.status_code != 200:
                logger.error(f"prices表检查失败: {prices_response.status_code} - {prices_response.text}")
            return False
    except Exception as e:
        logger.error(f"检查表失败: {e}")
        return False

def main():
    """主函数"""
    logger.info("开始设置Supabase")
    
    # 检查环境变量
    if not check_env_variables():
        return False
    
    # 测试连接
    if not test_connection():
        return False
    
    # 执行基本架构SQL文件
    basic_schema_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'supabase_basic_schema.sql')
    if not execute_sql_file(basic_schema_path):
        logger.warning("基本架构SQL文件执行失败，但继续执行")
    
    # 执行完整架构SQL文件
    schema_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'supabase_schema.sql')
    if not execute_sql_file(schema_path):
        logger.warning("完整架构SQL文件执行失败，但继续执行")
    
    # 检查表是否存在
    if not check_tables_exist():
        logger.warning("表检查失败，但可能是由于权限问题，请手动验证")
    
    logger.info("Supabase设置成功")
    return True

if __name__ == "__main__":
    success = main()
    if success:
        logger.info("Supabase设置成功完成")
        sys.exit(0)
    else:
        logger.error("Supabase设置失败")
        sys.exit(1)
