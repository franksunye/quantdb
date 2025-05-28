#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
数据库切换脚本
用于在SQLite和Supabase之间切换数据库配置
"""

import os
import sys
import argparse
import logging
from dotenv import load_dotenv

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("db_switcher")

# 从.env文件加载环境变量
load_dotenv()

def update_env_file(db_type):
    """
    更新.env文件中的数据库配置
    
    Args:
        db_type: 数据库类型，'sqlite'或'supabase'
    
    Returns:
        是否成功更新
    """
    logger.info(f"更新数据库配置为: {db_type}")
    
    # 获取当前配置
    env_path = '.env'
    if not os.path.exists(env_path):
        logger.error(f"找不到.env文件: {env_path}")
        return False
    
    # 读取.env文件
    with open(env_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 构建数据库URL
    sqlite_url = "sqlite:///./database/stock_data.db"
    
    # 获取Supabase配置
    supabase_host = os.getenv('SUPABASE_DB_HOST', 'aws-0-us-west-1.pooler.supabase.com')
    supabase_port = os.getenv('SUPABASE_DB_PORT', '6543')
    supabase_name = os.getenv('SUPABASE_DB_NAME', 'postgres')
    supabase_user = os.getenv('SUPABASE_DB_USER', 'postgres.dvusiqfijdmjcsubyapw')
    supabase_password = os.getenv('SUPABASE_DB_PASSWORD')
    supabase_ssl_cert = os.getenv('SUPABASE_SSL_CERT', 'prod-ca-2021.crt')
    
    if db_type == 'supabase' and not supabase_password:
        logger.error("缺少Supabase数据库密码，请在.env文件中设置SUPABASE_DB_PASSWORD")
        return False
    
    supabase_url = f"postgresql://{supabase_user}:{supabase_password}@{supabase_host}:{supabase_port}/{supabase_name}?sslmode=verify-full&sslrootcert={supabase_ssl_cert}"
    
    # 更新.env文件
    updated = False
    with open(env_path, 'w', encoding='utf-8') as f:
        for line in lines:
            if line.strip().startswith('DATABASE_URL='):
                if db_type == 'sqlite':
                    f.write(f"DATABASE_URL={sqlite_url}\n")
                else:
                    f.write(f"DATABASE_URL={supabase_url}\n")
                updated = True
            else:
                f.write(line)
    
    if updated:
        logger.info(f"成功更新数据库配置为: {db_type}")
    else:
        logger.warning("未找到DATABASE_URL配置行，添加新配置")
        with open(env_path, 'a', encoding='utf-8') as f:
            if db_type == 'sqlite':
                f.write(f"\nDATABASE_URL={sqlite_url}\n")
            else:
                f.write(f"\nDATABASE_URL={supabase_url}\n")
    
    return True

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='数据库切换脚本')
    parser.add_argument('db_type', choices=['sqlite', 'supabase'], help='数据库类型')
    
    args = parser.parse_args()
    
    if update_env_file(args.db_type):
        logger.info(f"数据库已切换为: {args.db_type}")
        return 0
    else:
        logger.error("数据库切换失败")
        return 1

if __name__ == '__main__':
    sys.exit(main())
