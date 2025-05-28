#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试使用psql命令连接Supabase
"""

import os
import sys
import logging
import subprocess
from dotenv import load_dotenv

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("psql_connection_test")

# 从.env文件加载环境变量
load_dotenv()

def test_psql_connection():
    """使用psql命令测试连接"""
    logger.info("使用psql命令测试连接...")

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
            # 构建psql命令（与PowerShell脚本完全相同）
            conn_string = f"sslmode=verify-full sslrootcert={ssl_cert} host={db_host} port={db_port} dbname={db_name} user={db_user}"

            # 使用与PowerShell脚本相同的方式执行命令
            cmd = ['psql', conn_string]

            # 执行命令
            logger.info(f"执行命令: {' '.join(cmd)}")

            # 使用交互式方式执行命令
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # 发送SQL命令
            stdout, stderr = process.communicate("SELECT 1 as test;\n\\q\n")

            # 检查结果
            if process.returncode == 0:
                logger.info(f"命令执行成功: {stdout}")
                return True
            else:
                logger.error(f"命令执行失败: {stderr}")
                return False
        finally:
            # 恢复原始环境变量
            os.environ['PGPASSWORD'] = old_pgpassword
    except Exception as e:
        logger.error(f"测试连接时出错: {e}")
        return False

def main():
    """主函数"""
    logger.info("开始测试psql连接...")

    # 测试psql连接
    success = test_psql_connection()

    # 显示结果
    logger.info(f"测试结果: {'成功' if success else '失败'}")

    # 返回结果
    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main())
