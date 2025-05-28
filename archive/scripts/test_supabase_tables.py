"""
测试Supabase表是否存在的脚本

此脚本使用Supabase REST API测试表是否存在。
"""

import os
import sys
import logging
import requests
from dotenv import load_dotenv

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("supabase_tables_test")

# 从.env文件加载环境变量
load_dotenv()

def test_connection():
    """测试Supabase连接"""
    try:
        # 获取Supabase URL和API密钥
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')
        
        if not supabase_url or not supabase_key:
            logger.error("未找到必要的Supabase环境变量")
            return False
        
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

def check_tables_exist():
    """检查表是否存在"""
    try:
        # 获取Supabase URL和API密钥
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')
        
        if not supabase_url or not supabase_key:
            logger.error("未找到必要的Supabase环境变量")
            return False
        
        # 使用REST API检查表
        headers = {
            "apikey": supabase_key,
            "Content-Type": "application/json"
        }
        
        # 检查assets表
        assets_response = requests.get(
            f"{supabase_url}/rest/v1/assets?limit=1",
            headers=headers
        )
        
        if assets_response.status_code == 200:
            logger.info("assets表存在")
        else:
            logger.error(f"assets表不存在: {assets_response.status_code} - {assets_response.text}")
        
        # 检查prices表
        prices_response = requests.get(
            f"{supabase_url}/rest/v1/prices?limit=1",
            headers=headers
        )
        
        if prices_response.status_code == 200:
            logger.info("prices表存在")
        else:
            logger.error(f"prices表不存在: {prices_response.status_code} - {prices_response.text}")
        
        # 如果两个表都存在，返回True
        if assets_response.status_code == 200 and prices_response.status_code == 200:
            logger.info("所有表都存在")
            return True
        else:
            logger.error("部分表不存在")
            return False
    except Exception as e:
        logger.error(f"检查表失败: {e}")
        return False

def main():
    """主函数"""
    logger.info("开始测试Supabase表")
    
    # 测试连接
    if not test_connection():
        return False
    
    # 检查表是否存在
    if not check_tables_exist():
        logger.error("表不存在，请确保已创建表")
        return False
    
    logger.info("Supabase表测试成功")
    return True

if __name__ == "__main__":
    success = main()
    if success:
        logger.info("Supabase表测试成功完成")
        sys.exit(0)
    else:
        logger.error("Supabase表测试失败")
        sys.exit(1)
