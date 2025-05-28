"""
使用HTTP请求设置Supabase的脚本

此脚本使用直接的HTTP请求来设置Supabase数据库表和RLS策略。
"""

import os
import sys
import logging
import requests
import json
from dotenv import load_dotenv

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("supabase_http_setup")

# 从.env文件加载环境变量
load_dotenv()

def check_env_variables():
    """检查必要的环境变量是否存在"""
    required_vars = ['SUPABASE_URL', 'SUPABASE_KEY', 'SUPABASE_SERVICE_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"缺少以下环境变量: {', '.join(missing_vars)}")
        return False
    
    logger.info("环境变量检查通过")
    return True

def test_connection():
    """测试Supabase连接"""
    try:
        # 获取Supabase URL和API密钥
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')
        
        logger.info(f"连接到Supabase: {supabase_url}")
        
        # 测试REST API连接
        headers = {
            "apikey": supabase_key,
            "Content-Type": "application/json"
        }
        
        # 尝试获取健康状态
        response = requests.get(
            f"{supabase_url}/rest/v1/",
            headers=headers
        )
        
        if response.status_code == 200:
            logger.info("Supabase连接成功")
            return True
        else:
            logger.error(f"Supabase连接失败: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"Supabase连接测试失败: {e}")
        return False

def create_tables():
    """创建表"""
    try:
        # 获取Supabase URL和API密钥
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_service_key = os.getenv('SUPABASE_SERVICE_KEY')
        
        # 设置请求头
        headers = {
            "apikey": supabase_service_key,
            "Authorization": f"Bearer {supabase_service_key}",
            "Content-Type": "application/json"
        }
        
        # 创建assets表
        assets_table_sql = """
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
        );
        """
        
        # 使用PostgreSQL REST API创建表
        # 注意：这里我们使用SQL查询，但是通过REST API发送
        # 我们需要使用Supabase的SQL API，这通常是通过管理API提供的
        # 但是我们可以尝试使用pgrest的rpc功能
        
        # 尝试使用pgrest的rpc功能
        try:
            # 创建一个SQL执行函数
            create_function_sql = """
            CREATE OR REPLACE FUNCTION execute_sql(sql text) RETURNS void AS $$
            BEGIN
                EXECUTE sql;
            END;
            $$ LANGUAGE plpgsql SECURITY DEFINER;
            """
            
            # 发送请求创建函数
            response = requests.post(
                f"{supabase_url}/rest/v1/rpc/execute_sql",
                headers=headers,
                json={"sql": create_function_sql}
            )
            
            if response.status_code == 200:
                logger.info("SQL执行函数创建成功")
            else:
                logger.warning(f"SQL执行函数创建失败: {response.status_code} - {response.text}")
                logger.info("尝试直接创建表")
        except Exception as e:
            logger.warning(f"创建SQL执行函数失败: {e}")
            logger.info("尝试直接创建表")
        
        # 直接使用SQL API创建表
        # 注意：这需要Supabase项目有SQL API权限
        try:
            # 创建assets表
            response = requests.post(
                f"{supabase_url}/rest/v1/",
                headers=headers,
                json={"query": assets_table_sql}
            )
            
            if response.status_code == 200:
                logger.info("assets表创建成功")
            else:
                logger.warning(f"assets表创建失败: {response.status_code} - {response.text}")
        except Exception as e:
            logger.warning(f"创建assets表失败: {e}")
        
        # 创建prices表
        prices_table_sql = """
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
        );
        """
        
        try:
            # 创建prices表
            response = requests.post(
                f"{supabase_url}/rest/v1/",
                headers=headers,
                json={"query": prices_table_sql}
            )
            
            if response.status_code == 200:
                logger.info("prices表创建成功")
            else:
                logger.warning(f"prices表创建失败: {response.status_code} - {response.text}")
        except Exception as e:
            logger.warning(f"创建prices表失败: {e}")
        
        # 创建索引
        indexes_sql = """
        CREATE INDEX IF NOT EXISTS idx_prices_asset_id ON prices (asset_id);
        CREATE INDEX IF NOT EXISTS idx_prices_date ON prices (date);
        CREATE INDEX IF NOT EXISTS idx_assets_symbol ON assets (symbol);
        """
        
        try:
            # 创建索引
            response = requests.post(
                f"{supabase_url}/rest/v1/",
                headers=headers,
                json={"query": indexes_sql}
            )
            
            if response.status_code == 200:
                logger.info("索引创建成功")
            else:
                logger.warning(f"索引创建失败: {response.status_code} - {response.text}")
        except Exception as e:
            logger.warning(f"创建索引失败: {e}")
        
        logger.info("表和索引创建尝试完成")
        return True
    except Exception as e:
        logger.error(f"创建表失败: {e}")
        return False

def check_tables_exist():
    """检查表是否存在"""
    try:
        # 获取Supabase URL和API密钥
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_service_key = os.getenv('SUPABASE_SERVICE_KEY')
        
        # 使用REST API检查表
        headers = {
            "apikey": supabase_service_key,
            "Authorization": f"Bearer {supabase_service_key}",
            "Content-Type": "application/json"
        }
        
        # 检查assets表
        assets_response = requests.get(
            f"{supabase_url}/rest/v1/assets?limit=1",
            headers=headers
        )
        
        # 检查prices表
        prices_response = requests.get(
            f"{supabase_url}/rest/v1/prices?limit=1",
            headers=headers
        )
        
        if assets_response.status_code == 200 and prices_response.status_code == 200:
            logger.info("表检查成功: assets和prices表都存在")
            return True
        else:
            if assets_response.status_code != 200:
                logger.error(f"assets表检查失败: {assets_response.status_code} - {assets_response.text}")
            if prices_response.status_code != 200:
                logger.error(f"prices表检查失败: {prices_response.status_code} - {prices_response.text}")
            return False
    except Exception as e:
        logger.error(f"检查表失败: {e}")
        return False

def main():
    """主函数"""
    logger.info("开始设置Supabase")
    
    # 检查环境变量
    if not check_env_variables():
        return False
    
    # 测试连接
    if not test_connection():
        return False
    
    # 创建表
    if not create_tables():
        logger.warning("创建表失败，但继续执行")
    
    # 检查表是否存在
    if not check_tables_exist():
        logger.warning("表检查失败，但可能是由于权限问题，请手动验证")
    
    logger.info("Supabase设置尝试完成")
    return True

if __name__ == "__main__":
    success = main()
    if success:
        logger.info("Supabase设置尝试完成")
        sys.exit(0)
    else:
        logger.error("Supabase设置失败")
        sys.exit(1)
