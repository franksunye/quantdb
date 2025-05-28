#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
QuantDB Supabase部署脚本
用于在Supabase上部署QuantDB的MVP版本
"""

import os
import sys
import logging
import argparse
import psycopg2
from dotenv import load_dotenv

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("supabase_deployment")

# 从.env文件加载环境变量
load_dotenv()

# 获取Supabase配置
SUPABASE_DB_HOST = os.getenv('SUPABASE_DB_HOST', 'aws-0-us-west-1.pooler.supabase.com')
SUPABASE_DB_PORT = os.getenv('SUPABASE_DB_PORT', '6543')  # Transaction Pooler端口
SUPABASE_DB_NAME = os.getenv('SUPABASE_DB_NAME', 'postgres')
SUPABASE_DB_USER = os.getenv('SUPABASE_DB_USER', 'postgres.dvusiqfijdmjcsubyapw')
SUPABASE_DB_PASSWORD = os.getenv('SUPABASE_DB_PASSWORD')
SUPABASE_SSL_CERT = os.getenv('SUPABASE_SSL_CERT', 'prod-ca-2021.crt')

def connect_to_supabase():
    """连接到Supabase PostgreSQL数据库"""
    try:
        # 打印连接信息（不包括密码）
        logger.info(f"连接到Supabase PostgreSQL数据库...")
        logger.info(f"主机: {SUPABASE_DB_HOST}")
        logger.info(f"端口: {SUPABASE_DB_PORT}")
        logger.info(f"数据库: {SUPABASE_DB_NAME}")
        logger.info(f"用户: {SUPABASE_DB_USER}")
        logger.info(f"SSL证书: {SUPABASE_SSL_CERT}")
        logger.info(f"密码长度: {len(SUPABASE_DB_PASSWORD) if SUPABASE_DB_PASSWORD else 0}")

        # 使用环境变量设置密码
        old_pgpassword = os.environ.get('PGPASSWORD', '')
        os.environ['PGPASSWORD'] = SUPABASE_DB_PASSWORD

        try:
            # 构建连接字符串
            conn_string = f"host={SUPABASE_DB_HOST} port={SUPABASE_DB_PORT} dbname={SUPABASE_DB_NAME} user={SUPABASE_DB_USER} sslmode=verify-full sslrootcert={SUPABASE_SSL_CERT}"

            # 连接到数据库
            conn = psycopg2.connect(conn_string)
            logger.info(f"成功连接到Supabase PostgreSQL数据库: {SUPABASE_DB_HOST}")
            return conn
        finally:
            # 恢复原始环境变量
            os.environ['PGPASSWORD'] = old_pgpassword
    except Exception as e:
        logger.error(f"连接Supabase数据库失败: {e}")
        sys.exit(1)

def execute_sql_script(conn, script_path):
    """执行SQL脚本"""
    try:
        # 读取SQL脚本
        with open(script_path, 'r', encoding='utf-8') as f:
            sql_script = f.read()

        # 执行SQL脚本
        cursor = conn.cursor()
        cursor.execute(sql_script)
        conn.commit()
        cursor.close()

        logger.info(f"成功执行SQL脚本: {script_path}")
        return True
    except Exception as e:
        logger.error(f"执行SQL脚本失败: {e}")
        conn.rollback()
        return False

def check_database_state(conn):
    """检查数据库状态"""
    try:
        cursor = conn.cursor()

        # 检查表是否存在
        cursor.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        """)
        tables = cursor.fetchall()

        logger.info("数据库中的表:")
        for table in tables:
            logger.info(f"- {table[0]}")

        # 检查assets表中的记录数
        cursor.execute("SELECT COUNT(*) FROM assets")
        asset_count = cursor.fetchone()[0]
        logger.info(f"assets表中有 {asset_count} 条记录")

        # 检查daily_stock_data表中的记录数
        cursor.execute("SELECT COUNT(*) FROM daily_stock_data")
        stock_data_count = cursor.fetchone()[0]
        logger.info(f"daily_stock_data表中有 {stock_data_count} 条记录")

        cursor.close()
        return True
    except Exception as e:
        logger.error(f"检查数据库状态失败: {e}")
        return False

def run_data_migration():
    """运行数据迁移脚本"""
    try:
        logger.info("开始运行数据迁移脚本...")

        # 导入并运行迁移脚本
        sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
        from migrate_to_supabase import main as migrate_main

        migrate_main()
        logger.info("数据迁移完成")
        return True
    except Exception as e:
        logger.error(f"运行数据迁移脚本失败: {e}")
        return False

def deploy(args):
    """部署QuantDB到Supabase"""
    logger.info("开始部署QuantDB到Supabase...")

    # 连接到Supabase
    conn = connect_to_supabase()

    try:
        # 初始化数据库
        if args.init_db:
            logger.info("初始化数据库...")
            schema_path = os.path.join(os.path.dirname(__file__), '..', 'database', 'supabase_schema.sql')
            if not execute_sql_script(conn, schema_path):
                logger.error("初始化数据库失败，终止部署")
                return False

        # 迁移数据
        if args.migrate_data:
            logger.info("迁移数据...")
            if not run_data_migration():
                logger.error("数据迁移失败，终止部署")
                return False

        # 检查部署状态
        logger.info("检查部署状态...")
        if not check_database_state(conn):
            logger.error("检查部署状态失败")
            return False

        logger.info("QuantDB成功部署到Supabase")
        return True
    finally:
        conn.close()

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='QuantDB Supabase部署工具')
    parser.add_argument('--init-db', action='store_true', help='初始化数据库')
    parser.add_argument('--migrate-data', action='store_true', help='迁移数据')
    parser.add_argument('--all', action='store_true', help='执行所有部署步骤')

    args = parser.parse_args()

    # 如果指定了--all，则执行所有步骤
    if args.all:
        args.init_db = True
        args.migrate_data = True

    # 如果没有指定任何参数，显示帮助信息
    if not (args.init_db or args.migrate_data):
        parser.print_help()
        return

    # 执行部署
    success = deploy(args)

    if success:
        logger.info("部署成功完成")
        sys.exit(0)
    else:
        logger.error("部署失败")
        sys.exit(1)

if __name__ == "__main__":
    main()
