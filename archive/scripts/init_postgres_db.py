"""
初始化 PostgreSQL 数据库

此脚本用于初始化 PostgreSQL 数据库，创建必要的表和索引。
"""

import os
import sys
import logging
import traceback
from dotenv import load_dotenv

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("init_postgres_db")

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 从 .env 文件加载环境变量
load_dotenv()

def init_database():
    """初始化数据库"""
    try:
        from services.postgres_client import get_postgres_client
        
        logger.info("初始化 PostgreSQL 数据库")
        
        # 获取客户端
        client = get_postgres_client()
        
        # 读取 SQL 文件
        sql_file_path = os.path.join(os.path.dirname(__file__), '..', 'database', 'postgres_init.sql')
        with open(sql_file_path, 'r', encoding='utf-8') as f:
            sql = f.read()
        
        # 分割 SQL 命令
        sql_commands = sql.split(';')
        
        # 执行每个 SQL 命令
        for command in sql_commands:
            command = command.strip()
            if command:
                logger.info(f"执行 SQL 命令: {command[:100]}...")
                try:
                    client.execute_non_query(command)
                    logger.info("SQL 命令执行成功")
                except Exception as e:
                    logger.error(f"SQL 命令执行失败: {e}")
        
        # 验证表是否创建成功
        tables = client.execute_query("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        table_names = [table[0] for table in tables]
        
        logger.info(f"数据库中的表: {table_names}")
        
        if 'assets' in table_names and 'prices' in table_names:
            logger.info("数据库初始化成功")
            return True
        else:
            logger.error("数据库初始化失败，缺少必要的表")
            return False
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        logger.error(traceback.format_exc())
        return False

def main():
    """主函数"""
    logger.info("开始初始化 PostgreSQL 数据库")
    
    # 初始化数据库
    if not init_database():
        logger.error("数据库初始化失败")
        return False
    
    logger.info("数据库初始化成功")
    return True

if __name__ == "__main__":
    success = main()
    if success:
        logger.info("脚本执行成功")
        sys.exit(0)
    else:
        logger.error("脚本执行失败")
        sys.exit(1)
