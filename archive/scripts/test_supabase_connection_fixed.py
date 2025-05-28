"""
测试Supabase连接的脚本（修复版）

此脚本直接使用硬编码的连接参数测试与Supabase的连接，避免环境变量解析问题。
"""

import os
import sys
import logging
import traceback
import requests
import psycopg2

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("supabase_connection_test")

def test_rest_api():
    """测试Supabase REST API连接"""
    try:
        # 直接使用硬编码的URL和密钥
        supabase_url = "https://dvusiqfijdmjcsubyapw.supabase.co"
        supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImR2dXNpcWZpamRtamNzdWJ5YXB3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDE3Njk2MjAsImV4cCI6MjA1NzM0NTYyMH0.hSjh0aIhUE2N_R4WY5-zOrDIq2Gpz2w1vyTInAdasoI"
        
        logger.info(f"测试REST API连接: {supabase_url}")
        
        # 设置请求头
        headers = {
            "apikey": supabase_key,
            "Content-Type": "application/json"
        }
        
        # 发送请求
        response = requests.get(
            f"{supabase_url}/rest/v1/",
            headers=headers
        )
        
        # 检查响应
        if response.status_code == 200:
            logger.info("REST API连接成功")
            logger.info(f"响应状态码: {response.status_code}")
            logger.info(f"响应内容: {response.text[:100]}...")
            return True
        else:
            logger.error(f"REST API连接失败: {response.status_code}")
            logger.error(f"响应内容: {response.text}")
            return False
    except Exception as e:
        logger.error(f"REST API连接测试失败: {e}")
        logger.error(traceback.format_exc())
        return False

def test_database_connection():
    """测试PostgreSQL数据库连接"""
    try:
        # 直接使用硬编码的连接参数
        db_params = {
            "dbname": "postgres",
            "user": "postgres",
            "password": "sd4UI5aiKpDn5Vd2",
            "host": "db.dvusiqfijdmjcsubyapw.supabase.co",
            "port": 5432
        }
        
        logger.info(f"测试数据库连接: {db_params['host']}:{db_params['port']}/{db_params['dbname']} (用户: {db_params['user']})")
        
        # 尝试连接
        logger.info("尝试连接到数据库...")
        conn = psycopg2.connect(
            dbname=db_params["dbname"],
            user=db_params["user"],
            password=db_params["password"],
            host=db_params["host"],
            port=db_params["port"]
        )
        
        # 测试连接
        cur = conn.cursor()
        cur.execute("SELECT version()")
        version = cur.fetchone()
        
        logger.info(f"数据库连接成功")
        logger.info(f"PostgreSQL版本: {version[0]}")
        
        # 获取表列表
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        tables = [row[0] for row in cur.fetchall()]
        
        logger.info(f"数据库中的表: {tables}")
        
        # 关闭连接
        cur.close()
        conn.close()
        
        return True
    except Exception as e:
        logger.error(f"数据库连接测试失败: {e}")
        logger.error(f"错误类型: {type(e).__name__}")
        logger.error(traceback.format_exc())
        return False

def create_tables():
    """创建表"""
    try:
        # 直接使用硬编码的连接参数
        db_params = {
            "dbname": "postgres",
            "user": "postgres",
            "password": "sd4UI5aiKpDn5Vd2",
            "host": "db.dvusiqfijdmjcsubyapw.supabase.co",
            "port": 5432
        }
        
        logger.info("尝试创建表...")
        
        # 连接到数据库
        conn = psycopg2.connect(
            dbname=db_params["dbname"],
            user=db_params["user"],
            password=db_params["password"],
            host=db_params["host"],
            port=db_params["port"]
        )
        
        # 创建游标
        cur = conn.cursor()
        
        # 创建assets表
        logger.info("创建assets表...")
        cur.execute("""
        CREATE TABLE IF NOT EXISTS assets (
            asset_id SERIAL PRIMARY KEY,
            symbol VARCHAR(20) NOT NULL,
            name VARCHAR(100),
            isin VARCHAR(12),
            asset_type VARCHAR(20),
            exchange VARCHAR(20),
            currency VARCHAR(3),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(symbol)
        )
        """)
        
        # 创建prices表
        logger.info("创建prices表...")
        cur.execute("""
        CREATE TABLE IF NOT EXISTS prices (
            price_id SERIAL PRIMARY KEY,
            asset_id INTEGER NOT NULL,
            date DATE NOT NULL,
            open NUMERIC(10, 2),
            high NUMERIC(10, 2),
            low NUMERIC(10, 2),
            close NUMERIC(10, 2),
            volume BIGINT,
            adjusted_close NUMERIC(10, 2),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (asset_id) REFERENCES assets (asset_id),
            UNIQUE (asset_id, date)
        )
        """)
        
        # 创建索引
        logger.info("创建索引...")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_prices_asset_id ON prices (asset_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_prices_date ON prices (date)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_assets_symbol ON assets (symbol)")
        
        # 提交事务
        conn.commit()
        
        # 验证表是否创建成功
        logger.info("验证表是否创建成功...")
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        tables = [row[0] for row in cur.fetchall()]
        
        logger.info(f"数据库中的表: {tables}")
        
        # 关闭连接
        cur.close()
        conn.close()
        
        logger.info("表创建成功")
        return True
    except Exception as e:
        logger.error(f"创建表失败: {e}")
        logger.error(traceback.format_exc())
        return False

def main():
    """主函数"""
    logger.info("开始测试Supabase连接")
    
    # 测试REST API连接
    if not test_rest_api():
        logger.error("REST API连接测试失败")
        return False
    
    # 测试数据库连接
    if not test_database_connection():
        logger.error("数据库连接测试失败")
        return False
    
    # 创建表
    if not create_tables():
        logger.error("创建表失败")
        return False
    
    logger.info("Supabase连接测试成功")
    return True

if __name__ == "__main__":
    success = main()
    if success:
        logger.info("所有测试通过")
        sys.exit(0)
    else:
        logger.error("测试失败")
        sys.exit(1)
