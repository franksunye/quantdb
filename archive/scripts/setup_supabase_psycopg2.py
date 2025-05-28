"""
使用psycopg2设置Supabase的脚本

此脚本使用psycopg2直接连接到Supabase PostgreSQL数据库，并执行SQL脚本创建必要的表和索引。
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
logger = logging.getLogger("supabase_psycopg2_setup")

# 从.env文件加载环境变量
load_dotenv()

def parse_db_url(database_url):
    """解析数据库URL"""
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
        
        return {
            'dbname': dbname,
            'user': user,
            'password': password,
            'host': host,
            'port': port
        }
    else:
        raise ValueError(f"不支持的数据库URL格式: {database_url}")

def execute_sql_script(conn, script_path):
    """执行SQL脚本文件"""
    try:
        # 读取SQL脚本
        with open(script_path, 'r') as f:
            sql_script = f.read()
        
        logger.info(f"执行SQL脚本: {script_path}")
        
        # 创建游标
        cur = conn.cursor()
        
        # 执行SQL脚本
        cur.execute(sql_script)
        
        # 提交事务
        conn.commit()
        
        # 关闭游标
        cur.close()
        
        logger.info(f"SQL脚本执行成功: {script_path}")
        return True
    except Exception as e:
        logger.error(f"执行SQL脚本失败: {e}")
        conn.rollback()
        return False

def check_tables_exist(conn, expected_tables):
    """检查表是否存在"""
    try:
        # 创建游标
        cur = conn.cursor()
        
        # 获取表列表
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        tables = [row[0] for row in cur.fetchall()]
        
        logger.info(f"数据库中的表: {tables}")
        
        # 检查是否存在预期的表
        missing_tables = [table for table in expected_tables if table not in tables]
        
        if missing_tables:
            logger.warning(f"缺少以下表: {missing_tables}")
            return False
        
        logger.info("所有预期的表都存在")
        
        # 检查表结构
        for table in expected_tables:
            cur.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table}'")
            columns = [row[0] for row in cur.fetchall()]
            logger.info(f"表 {table} 的列: {columns}")
        
        # 关闭游标
        cur.close()
        
        return True
    except Exception as e:
        logger.error(f"检查表失败: {e}")
        return False

def main():
    """主函数"""
    try:
        # 获取数据库URL
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            logger.error("未找到DATABASE_URL环境变量")
            return False
        
        # 解析数据库URL
        db_params = parse_db_url(database_url)
        
        # 打印连接信息（隐藏密码）
        logger.info(f"连接到PostgreSQL数据库: {db_params['host']}:{db_params['port']}/{db_params['dbname']} (用户: {db_params['user']})")
        
        # 连接到数据库
        conn = psycopg2.connect(
            dbname=db_params['dbname'],
            user=db_params['user'],
            password=db_params['password'],
            host=db_params['host'],
            port=db_params['port']
        )
        
        logger.info("数据库连接成功")
        
        # 执行基本架构SQL脚本
        basic_schema_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'supabase_basic_schema.sql')
        if not execute_sql_script(conn, basic_schema_path):
            logger.error("执行基本架构SQL脚本失败")
            conn.close()
            return False
        
        # 检查表是否存在
        expected_tables = ['assets', 'prices']
        if not check_tables_exist(conn, expected_tables):
            logger.error("表创建失败")
            conn.close()
            return False
        
        # 执行完整架构SQL脚本
        schema_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'supabase_schema.sql')
        if not execute_sql_script(conn, schema_path):
            logger.warning("执行完整架构SQL脚本失败，但继续执行")
        
        # 关闭连接
        conn.close()
        
        logger.info("Supabase数据库设置成功")
        return True
    except Exception as e:
        logger.error(f"Supabase数据库设置失败: {e}")
        return False

if __name__ == "__main__":
    logger.info("开始设置Supabase数据库")
    success = main()
    if success:
        logger.info("Supabase数据库设置成功")
        sys.exit(0)
    else:
        logger.error("Supabase数据库设置失败")
        sys.exit(1)
