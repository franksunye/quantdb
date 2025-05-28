#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
更新API配置脚本
用于将API配置从SQLite切换到Supabase
"""

import os
import sys
import logging
import argparse
from dotenv import load_dotenv

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("api_config_updater")

# 从.env文件加载环境变量
load_dotenv()

def update_env_file(use_supabase=True):
    """更新.env文件"""
    logger.info(f"开始更新.env文件，使用{'Supabase' if use_supabase else 'SQLite'}...")
    
    # 获取Supabase配置
    db_host = os.getenv('SUPABASE_DB_HOST', 'aws-0-us-west-1.pooler.supabase.com')
    db_port = os.getenv('SUPABASE_DB_PORT', '6543')
    db_name = os.getenv('SUPABASE_DB_NAME', 'postgres')
    db_user = os.getenv('SUPABASE_DB_USER', 'postgres.dvusiqfijdmjcsubyapw')
    db_password = os.getenv('SUPABASE_DB_PASSWORD')
    ssl_cert = os.getenv('SUPABASE_SSL_CERT', 'prod-ca-2021.crt')
    
    # 构建数据库URL
    sqlite_url = "sqlite:///./database/stock_data.db"
    supabase_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}?sslmode=verify-full&sslrootcert={ssl_cert}"
    
    # 读取.env文件
    try:
        with open('.env', 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 更新.env文件
        with open('.env', 'w', encoding='utf-8') as f:
            for line in lines:
                if line.startswith('DATABASE_URL='):
                    if use_supabase:
                        # 切换到Supabase
                        if line.startswith('DATABASE_URL=sqlite:'):
                            f.write(f"# {line}")  # 注释掉SQLite配置
                            f.write(f"DATABASE_URL={supabase_url}\n")  # 添加Supabase配置
                        elif line.startswith('DATABASE_URL=postgresql:'):
                            f.write(f"DATABASE_URL={supabase_url}\n")  # 更新Supabase配置
                        else:
                            f.write(line)
                    else:
                        # 切换到SQLite
                        if line.startswith('DATABASE_URL=postgresql:'):
                            f.write(f"# {line}")  # 注释掉Supabase配置
                            f.write(f"DATABASE_URL={sqlite_url}\n")  # 添加SQLite配置
                        elif line.startswith('# DATABASE_URL=sqlite:'):
                            f.write(line[2:])  # 取消注释SQLite配置
                        else:
                            f.write(line)
                else:
                    f.write(line)
        
        logger.info(f".env文件更新成功，现在使用{'Supabase' if use_supabase else 'SQLite'}")
        return True
    except Exception as e:
        logger.error(f"更新.env文件时出错: {e}")
        return False

def update_config_module():
    """更新config.py模块"""
    logger.info("重新加载配置模块...")
    
    try:
        # 导入config模块
        from src import config
        
        # 重新加载config模块
        import importlib
        importlib.reload(config)
        
        # 验证配置
        logger.info(f"当前数据库URL: {config.DATABASE_URL}")
        
        return True
    except Exception as e:
        logger.error(f"重新加载配置模块时出错: {e}")
        return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='更新API配置脚本')
    parser.add_argument('--use', choices=['supabase', 'sqlite'], required=True, help='使用哪种数据库')
    
    args = parser.parse_args()
    
    # 更新.env文件
    if not update_env_file(args.use == 'supabase'):
        logger.error("更新.env文件失败，终止操作")
        return False
    
    # 更新config模块
    if not update_config_module():
        logger.error("更新config模块失败，但.env文件已更新")
        return False
    
    logger.info(f"API配置已成功更新为使用{args.use.upper()}")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
