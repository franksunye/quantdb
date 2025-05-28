"""
使用psycopg2直接测试Supabase PostgreSQL连接
"""

import os
import sys
import logging
import psycopg2
from dotenv import load_dotenv

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("supabase_direct_test")

# 从.env文件加载环境变量
load_dotenv()

def test_connection():
    """测试数据库连接"""
    try:
        # 获取数据库URL
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            logger.error("未找到DATABASE_URL环境变量")
            return False
        
        # 解析数据库URL
        if database_url.startswith('postgresql://'):
            # 解析PostgreSQL URL
            parts = database_url.replace('postgresql://', '').split('@')
            user_pass = parts[0].split(':')
            host_db = parts[1].split('/')
            
            user = user_pass[0]
            password = user_pass[1]
            host_port = host_db[0].split(':')
            host = host_port[0]
            port = int(host_port[1]) if len(host_port) > 1 else 5432
            dbname = host_db[1]
            
            logger.info(f"连接到PostgreSQL数据库: {host}:{port}/{dbname} (用户: {user})")
            
            # 连接到数据库
            conn = psycopg2.connect(
                dbname=dbname,
                user=user,
                password=password,
                host=host,
                port=port
            )
            
            # 创建游标
            cur = conn.cursor()
            
            # 执行简单查询
            cur.execute("SELECT 1")
            result = cur.fetchone()
            logger.info(f"查询结果: {result}")
            
            # 获取表列表
            cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
            tables = [row[0] for row in cur.fetchall()]
            logger.info(f"数据库中的表: {tables}")
            
            # 检查是否存在我们的表
            expected_tables = ['assets', 'prices']
            missing_tables = [table for table in expected_tables if table not in tables]
            
            if missing_tables:
                logger.warning(f"缺少以下表: {missing_tables}")
                logger.info("请确保已执行SQL脚本创建表")
            else:
                logger.info("所有预期的表都存在")
                
                # 检查表结构
                for table in expected_tables:
                    cur.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table}'")
                    columns = [row[0] for row in cur.fetchall()]
                    logger.info(f"表 {table} 的列: {columns}")
            
            # 关闭连接
            cur.close()
            conn.close()
            
            logger.info("数据库连接测试成功")
            return True
        else:
            logger.error(f"不支持的数据库URL格式: {database_url}")
            return False
    except Exception as e:
        logger.error(f"数据库连接测试失败: {e}")
        return False

if __name__ == "__main__":
    logger.info("开始Supabase数据库直接连接测试")
    success = test_connection()
    if success:
        logger.info("测试成功！Supabase数据库连接正常")
        sys.exit(0)
    else:
        logger.error("测试失败。请检查日志获取详细信息")
        sys.exit(1)
