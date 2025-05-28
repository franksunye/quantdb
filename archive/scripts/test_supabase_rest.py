"""
使用REST API测试Supabase连接
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
logger = logging.getLogger("supabase_rest_test")

# 从.env文件加载环境变量
load_dotenv()

def test_supabase_rest_api():
    """测试Supabase REST API连接"""
    try:
        # 获取Supabase URL和API密钥
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')
        supabase_service_key = os.getenv('SUPABASE_SERVICE_KEY')
        
        if not supabase_url or not supabase_key or not supabase_service_key:
            logger.error("未找到必要的Supabase环境变量")
            return False
        
        logger.info(f"连接到Supabase: {supabase_url}")
        
        # 使用anon密钥测试REST API连接
        anon_headers = {
            "apikey": supabase_key,
            "Content-Type": "application/json"
        }
        
        # 尝试获取表信息
        anon_response = requests.get(
            f"{supabase_url}/rest/v1/",
            headers=anon_headers
        )
        
        if anon_response.status_code == 200:
            logger.info("使用anon密钥连接Supabase REST API成功")
        else:
            logger.error(f"使用anon密钥连接Supabase REST API失败: {anon_response.status_code} - {anon_response.text}")
            return False
        
        # 使用service_role密钥测试REST API连接
        service_headers = {
            "apikey": supabase_service_key,
            "Authorization": f"Bearer {supabase_service_key}",
            "Content-Type": "application/json"
        }
        
        # 尝试获取表信息
        service_response = requests.get(
            f"{supabase_url}/rest/v1/",
            headers=service_headers
        )
        
        if service_response.status_code == 200:
            logger.info("使用service_role密钥连接Supabase REST API成功")
        else:
            logger.error(f"使用service_role密钥连接Supabase REST API失败: {service_response.status_code} - {service_response.text}")
            return False
        
        # 检查assets表是否存在
        assets_response = requests.get(
            f"{supabase_url}/rest/v1/assets?limit=1",
            headers=service_headers
        )
        
        if assets_response.status_code == 200:
            logger.info("assets表存在")
            logger.info(f"assets表数据示例: {assets_response.json()}")
        elif assets_response.status_code == 404:
            logger.warning("assets表不存在，请确保已执行SQL脚本创建表")
        else:
            logger.error(f"检查assets表失败: {assets_response.status_code} - {assets_response.text}")
        
        # 检查prices表是否存在
        prices_response = requests.get(
            f"{supabase_url}/rest/v1/prices?limit=1",
            headers=service_headers
        )
        
        if prices_response.status_code == 200:
            logger.info("prices表存在")
            logger.info(f"prices表数据示例: {prices_response.json()}")
        elif prices_response.status_code == 404:
            logger.warning("prices表不存在，请确保已执行SQL脚本创建表")
        else:
            logger.error(f"检查prices表失败: {prices_response.status_code} - {prices_response.text}")
        
        logger.info("Supabase REST API测试成功")
        return True
    except Exception as e:
        logger.error(f"Supabase REST API测试失败: {e}")
        return False

if __name__ == "__main__":
    logger.info("开始Supabase REST API测试")
    success = test_supabase_rest_api()
    if success:
        logger.info("测试成功！Supabase REST API连接正常")
        sys.exit(0)
    else:
        logger.error("测试失败。请检查日志获取详细信息")
        sys.exit(1)
