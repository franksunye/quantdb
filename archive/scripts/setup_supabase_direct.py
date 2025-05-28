"""
直接使用连接参数设置Supabase的脚本

此脚本直接使用连接参数连接到Supabase PostgreSQL数据库，避免解析URL导致的编码问题。
"""

import os
import sys
import logging
import psycopg2
import traceback
from dotenv import load_dotenv

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("supabase_direct_setup")

# 从.env文件加载环境变量
load_dotenv()

def execute_sql_script(conn, script_path):
    """执行SQL脚本文件"""
    try:
        # 读取SQL脚本
        with open(script_path, 'r', encoding='utf-8') as f:
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
        # 直接设置连接参数
        # 注意：这些参数应该在.env文件中设置
        db_host = "db.dvusiqfijdmjcsubyapw.supabase.co"
        db_port = 5432
        db_name = "postgres"
        db_user = "postgres"
        db_password = "sd4UI5aiKpDn5Vd2"  # 这里直接使用密码，避免解析URL导致的编码问题

        logger.info(f"连接到PostgreSQL数据库: {db_host}:{db_port}/{db_name} (用户: {db_user})")

        # 连接到数据库
        try:
            logger.info("尝试连接到数据库...")
            conn = psycopg2.connect(
                dbname=db_name,
                user=db_user,
                password=db_password,
                host=db_host,
                port=db_port
            )

            logger.info("数据库连接成功")
        except Exception as e:
            logger.error(f"数据库连接失败: {e}")
            logger.error(f"错误类型: {type(e).__name__}")
            logger.error(f"错误详情: {traceback.format_exc()}")
            return False

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
