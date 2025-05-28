#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试Supabase连接
"""

import os
import sys
import logging
import psycopg2
from dotenv import load_dotenv

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("supabase_connection_test")

# 从.env文件加载环境变量
load_dotenv()

def test_connection_with_params():
    """使用连接参数测试连接"""
    logger.info("使用连接参数测试连接...")

    # 获取Supabase配置
    db_host = os.getenv('SUPABASE_DB_HOST', 'aws-0-us-west-1.pooler.supabase.com')
    db_port = os.getenv('SUPABASE_DB_PORT', '6543')
    db_name = os.getenv('SUPABASE_DB_NAME', 'postgres')
    db_user = os.getenv('SUPABASE_DB_USER', 'postgres.dvusiqfijdmjcsubyapw')
    db_password = os.getenv('SUPABASE_DB_PASSWORD')
    ssl_cert = os.getenv('SUPABASE_SSL_CERT', 'prod-ca-2021.crt')

    # 显示连接信息
    logger.info(f"主机: {db_host}")
    logger.info(f"端口: {db_port}")
    logger.info(f"数据库: {db_name}")
    logger.info(f"用户: {db_user}")
    logger.info(f"SSL证书: {ssl_cert}")
    logger.info(f"密码长度: {len(db_password) if db_password else 0}")

    try:
        # 构建连接参数
        conn_params = {
            'host': db_host,
            'port': db_port,
            'dbname': db_name,
            'user': db_user,
            'password': db_password,
            'sslmode': 'verify-full',
            'sslrootcert': ssl_cert
        }

        # 连接到数据库
        conn = psycopg2.connect(**conn_params)
        logger.info("使用连接参数连接成功")

        # 执行简单查询
        cursor = conn.cursor()
        cursor.execute("SELECT 1 as test")
        result = cursor.fetchone()
        logger.info(f"查询结果: {result}")

        # 关闭连接
        cursor.close()
        conn.close()
        logger.info("连接已关闭")

        return True
    except Exception as e:
        logger.error(f"使用连接参数连接失败: {e}")
        return False

def test_connection_with_env_var():
    """使用环境变量测试连接"""
    logger.info("使用环境变量测试连接...")

    # 获取Supabase配置
    db_host = os.getenv('SUPABASE_DB_HOST', 'aws-0-us-west-1.pooler.supabase.com')
    db_port = os.getenv('SUPABASE_DB_PORT', '6543')
    db_name = os.getenv('SUPABASE_DB_NAME', 'postgres')
    db_user = os.getenv('SUPABASE_DB_USER', 'postgres.dvusiqfijdmjcsubyapw')
    db_password = os.getenv('SUPABASE_DB_PASSWORD')
    ssl_cert = os.getenv('SUPABASE_SSL_CERT', 'prod-ca-2021.crt')

    # 显示连接信息
    logger.info(f"主机: {db_host}")
    logger.info(f"端口: {db_port}")
    logger.info(f"数据库: {db_name}")
    logger.info(f"用户: {db_user}")
    logger.info(f"SSL证书: {ssl_cert}")
    logger.info(f"密码长度: {len(db_password) if db_password else 0}")

    try:
        # 保存原始环境变量
        old_pgpassword = os.environ.get('PGPASSWORD', '')

        # 设置环境变量
        os.environ['PGPASSWORD'] = db_password

        try:
            # 构建连接字符串
            conn_string = f"host={db_host} port={db_port} dbname={db_name} user={db_user} sslmode=verify-full sslrootcert={ssl_cert}"

            # 连接到数据库
            conn = psycopg2.connect(conn_string)
            logger.info("使用环境变量连接成功")

            # 执行简单查询
            cursor = conn.cursor()
            cursor.execute("SELECT 1 as test")
            result = cursor.fetchone()
            logger.info(f"查询结果: {result}")

            # 关闭连接
            cursor.close()
            conn.close()
            logger.info("连接已关闭")

            return True
        finally:
            # 恢复原始环境变量
            os.environ['PGPASSWORD'] = old_pgpassword
    except Exception as e:
        logger.error(f"使用环境变量连接失败: {e}")
        return False

def test_connection_with_url():
    """使用URL测试连接"""
    logger.info("使用URL测试连接...")

    # 构建数据库URL
    db_host = os.getenv('SUPABASE_DB_HOST', 'aws-0-us-west-1.pooler.supabase.com')
    db_port = os.getenv('SUPABASE_DB_PORT', '6543')
    db_name = os.getenv('SUPABASE_DB_NAME', 'postgres')
    db_user = os.getenv('SUPABASE_DB_USER', 'postgres.dvusiqfijdmjcsubyapw')
    db_password = os.getenv('SUPABASE_DB_PASSWORD')
    ssl_cert = os.getenv('SUPABASE_SSL_CERT', 'prod-ca-2021.crt')

    database_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}?sslmode=verify-full&sslrootcert={ssl_cert}"

    # 显示连接信息（隐藏密码）
    masked_url = database_url.replace(db_password, '********')
    logger.info(f"数据库URL: {masked_url}")

    try:
        # 连接到数据库
        conn = psycopg2.connect(database_url)
        logger.info("使用URL连接成功")

        # 执行简单查询
        cursor = conn.cursor()
        cursor.execute("SELECT 1 as test")
        result = cursor.fetchone()
        logger.info(f"查询结果: {result}")

        # 关闭连接
        cursor.close()
        conn.close()
        logger.info("连接已关闭")

        return True
    except Exception as e:
        logger.error(f"使用URL连接失败: {e}")
        return False

def main():
    """主函数"""
    logger.info("开始测试Supabase连接...")

    # 测试使用连接参数
    params_result = test_connection_with_params()

    # 测试使用环境变量
    env_var_result = test_connection_with_env_var()

    # 测试使用URL
    url_result = test_connection_with_url()

    # 显示结果
    logger.info("测试结果:")
    logger.info(f"使用连接参数: {'成功' if params_result else '失败'}")
    logger.info(f"使用环境变量: {'成功' if env_var_result else '失败'}")
    logger.info(f"使用URL: {'成功' if url_result else '失败'}")

    # 返回结果
    return params_result or env_var_result or url_result

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
