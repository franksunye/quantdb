"""
创建 Supabase execute_sql 函数

此脚本用于创建 Supabase execute_sql 函数，使用 Supabase Management API。
"""

import os
import sys
import logging
import requests
import traceback
from dotenv import load_dotenv

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("create_execute_sql_function")

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 从 .env 文件加载环境变量
load_dotenv()

def create_execute_sql_function():
    """创建 execute_sql 函数"""
    try:
        # 获取 Supabase URL、项目 ID 和访问令牌
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_access_token = os.getenv('SUPABASE_ACCESS_TOKEN')
        
        if not supabase_url or not supabase_access_token:
            logger.error("未找到 SUPABASE_URL 或 SUPABASE_ACCESS_TOKEN 环境变量")
            return False
        
        # 从 URL 中提取项目 ID
        project_id = supabase_url.split('//')[1].split('.')[0]
        
        logger.info(f"使用 Supabase Management API 创建 execute_sql 函数，项目 ID: {project_id}")
        
        # 设置请求头
        headers = {
            "Authorization": f"Bearer {supabase_access_token}",
            "Content-Type": "application/json"
        }
        
        # SQL 函数定义
        sql = """
        CREATE OR REPLACE FUNCTION execute_sql(sql text)
        RETURNS text
        LANGUAGE plpgsql
        SECURITY DEFINER
        AS $$
        BEGIN
            EXECUTE sql;
            RETURN 'SQL executed successfully';
        EXCEPTION
            WHEN OTHERS THEN
                RETURN 'Error: ' || SQLERRM;
        END;
        $$;
        """
        
        # 使用 Supabase Management API 执行 SQL
        response = requests.post(
            f"https://api.supabase.com/v1/projects/{project_id}/sql",
            headers=headers,
            json={"query": sql}
        )
        
        if response.status_code in (200, 201):
            logger.info(f"execute_sql 函数创建成功: {response.text}")
            return True
        else:
            logger.error(f"execute_sql 函数创建失败: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"execute_sql 函数创建失败: {e}")
        logger.error(traceback.format_exc())
        return False

def main():
    """主函数"""
    logger.info("开始创建 Supabase execute_sql 函数")
    
    # 创建 execute_sql 函数
    if not create_execute_sql_function():
        logger.error("创建 execute_sql 函数失败")
        return False
    
    logger.info("Supabase execute_sql 函数创建成功")
    return True

if __name__ == "__main__":
    success = main()
    if success:
        logger.info("Supabase execute_sql 函数创建成功")
        sys.exit(0)
    else:
        logger.error("Supabase execute_sql 函数创建失败")
        sys.exit(1)
