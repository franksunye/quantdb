"""
测试Supabase连接并处理编码问题的脚本

此脚本专门处理中文Windows环境下的编码问题，确保与Supabase的连接正常。
"""

import os
import sys
import logging
import requests
import json
import locale
from dotenv import load_dotenv

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("supabase_encoding_test")

# 从.env文件加载环境变量
load_dotenv()

# 显示系统编码信息
system_encoding = locale.getpreferredencoding()
logger.info(f"系统默认编码: {system_encoding}")
logger.info(f"Python默认编码: {sys.getdefaultencoding()}")
logger.info(f"文件系统编码: {sys.getfilesystemencoding()}")

def test_connection():
    """测试Supabase连接"""
    try:
        # 获取Supabase URL和API密钥
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')
        
        if not supabase_url or not supabase_key:
            logger.error("未找到必要的Supabase环境变量")
            return False
        
        # 打印环境变量（隐藏敏感信息）
        logger.info(f"SUPABASE_URL: {supabase_url}")
        logger.info(f"SUPABASE_KEY: {'已设置' if supabase_key else '未设置'}")
        
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
            logger.info("Supabase REST API连接成功")
            return True
        else:
            logger.error(f"Supabase REST API连接失败: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"Supabase连接测试失败: {e}")
        return False

def test_database_connection():
    """测试数据库连接"""
    try:
        # 获取数据库URL
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            logger.error("未找到DATABASE_URL环境变量")
            return False
        
        # 打印数据库URL（隐藏密码）
        if '@' in database_url:
            parts = database_url.split('@')
            user_part = parts[0].split(':')[0]
            host_part = parts[1]
            masked_url = f"{user_part}:***@{host_part}"
        else:
            masked_url = database_url
        
        logger.info(f"DATABASE_URL: {masked_url}")
        
        # 解析数据库URL
        try:
            # 尝试解析URL
            if database_url.startswith('postgresql://'):
                # 手动解析URL，避免编码问题
                parts = database_url.replace('postgresql://', '').split('@')
                user_pass = parts[0].split(':')
                host_db = parts[1].split('/')
                
                user = user_pass[0]
                # 密码可能包含特殊字符，导致编码问题
                password = user_pass[1]
                host_port = host_db[0].split(':')
                host = host_port[0]
                port = int(host_port[1]) if len(host_port) > 1 else 5432
                dbname = host_db[1]
                
                logger.info(f"解析数据库URL成功: {host}:{port}/{dbname} (用户: {user})")
            else:
                logger.error(f"不支持的数据库URL格式: {database_url}")
                return False
        except Exception as e:
            logger.error(f"解析数据库URL失败: {e}")
            return False
        
        # 尝试使用psycopg2连接
        try:
            import psycopg2
            
            logger.info("尝试使用psycopg2连接数据库...")
            
            # 使用解析后的参数连接
            conn = psycopg2.connect(
                dbname=dbname,
                user=user,
                password=password,
                host=host,
                port=port
            )
            
            # 测试连接
            cur = conn.cursor()
            cur.execute("SELECT 1")
            result = cur.fetchone()
            
            logger.info(f"psycopg2连接成功，查询结果: {result}")
            
            # 关闭连接
            cur.close()
            conn.close()
            
            return True
        except Exception as e:
            logger.error(f"psycopg2连接失败: {e}")
            
            # 尝试使用不同的编码方式
            try:
                logger.info("尝试使用不同编码方式连接...")
                
                # 尝试使用系统默认编码
                password_bytes = password.encode(system_encoding)
                password_utf8 = password_bytes.decode('utf-8')
                
                conn = psycopg2.connect(
                    dbname=dbname,
                    user=user,
                    password=password_utf8,
                    host=host,
                    port=port
                )
                
                logger.info("使用系统编码转换后连接成功")
                conn.close()
                return True
            except Exception as e2:
                logger.error(f"使用系统编码转换后连接仍然失败: {e2}")
                return False
    except Exception as e:
        logger.error(f"数据库连接测试失败: {e}")
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
    logger.info("开始测试Supabase编码问题")
    
    # 测试REST API连接
    if not test_connection():
        return False
    
    # 测试数据库连接
    if not test_database_connection():
        logger.warning("数据库连接测试失败，但继续执行")
    
    # 检查表是否存在
    if not check_tables_exist():
        logger.error("表不存在，请确保已创建表")
        return False
    
    logger.info("Supabase编码测试完成")
    return True

if __name__ == "__main__":
    success = main()
    if success:
        logger.info("Supabase编码测试成功完成")
        sys.exit(0)
    else:
        logger.error("Supabase编码测试失败")
        sys.exit(1)
