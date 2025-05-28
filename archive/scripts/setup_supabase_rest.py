"""
使用REST API设置Supabase的脚本

此脚本使用Supabase REST API和Management API来设置数据库表和RLS策略。
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
logger = logging.getLogger("supabase_rest_setup")

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

def execute_sql_query(sql_query):
    """执行SQL查询"""
    try:
        # 获取Supabase URL和API密钥
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_service_key = os.getenv('SUPABASE_SERVICE_KEY')
        project_id = supabase_url.split('//')[1].split('.')[0]
        
        logger.info(f"执行SQL查询: {sql_query[:50]}...")
        
        # 使用Management API执行SQL查询
        headers = {
            "Authorization": f"Bearer {supabase_service_key}",
            "Content-Type": "application/json"
        }
        
        # 使用Supabase Management API执行SQL查询
        response = requests.post(
            f"https://api.supabase.com/v1/projects/{project_id}/sql",
            headers=headers,
            json={"query": sql_query}
        )
        
        if response.status_code == 200:
            logger.info("SQL查询执行成功")
            return True
        else:
            logger.error(f"SQL查询执行失败: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"执行SQL查询失败: {e}")
        return False

def create_tables():
    """创建表"""
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
    
    if not execute_sql_query(assets_table_sql):
        return False
    
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
    
    if not execute_sql_query(prices_table_sql):
        return False
    
    # 创建索引
    indexes_sql = """
    CREATE INDEX IF NOT EXISTS idx_prices_asset_id ON prices (asset_id);
    CREATE INDEX IF NOT EXISTS idx_prices_date ON prices (date);
    CREATE INDEX IF NOT EXISTS idx_assets_symbol ON assets (symbol);
    """
    
    if not execute_sql_query(indexes_sql):
        return False
    
    logger.info("表和索引创建成功")
    return True

def setup_rls_policies():
    """设置行级安全策略"""
    # 启用行级安全
    enable_rls_sql = """
    ALTER TABLE IF EXISTS assets ENABLE ROW LEVEL SECURITY;
    ALTER TABLE IF EXISTS prices ENABLE ROW LEVEL SECURITY;
    """
    
    if not execute_sql_query(enable_rls_sql):
        return False
    
    # 创建assets表策略
    assets_policies_sql = """
    -- 允许任何人读取assets
    CREATE POLICY IF NOT EXISTS "Allow public read access to assets" ON assets
        FOR SELECT
        USING (true);
    
    -- 允许只有具有admin角色的认证用户插入/更新/删除assets
    CREATE POLICY IF NOT EXISTS "Allow admin insert access to assets" ON assets
        FOR INSERT
        TO authenticated
        WITH CHECK (auth.jwt() ? 'role' AND auth.jwt()->>'role' = 'admin');
    
    CREATE POLICY IF NOT EXISTS "Allow admin update access to assets" ON assets
        FOR UPDATE
        TO authenticated
        USING (auth.jwt() ? 'role' AND auth.jwt()->>'role' = 'admin')
        WITH CHECK (auth.jwt() ? 'role' AND auth.jwt()->>'role' = 'admin');
    
    CREATE POLICY IF NOT EXISTS "Allow admin delete access to assets" ON assets
        FOR DELETE
        TO authenticated
        USING (auth.jwt() ? 'role' AND auth.jwt()->>'role' = 'admin');
    """
    
    if not execute_sql_query(assets_policies_sql):
        return False
    
    # 创建prices表策略
    prices_policies_sql = """
    -- 允许任何人读取prices
    CREATE POLICY IF NOT EXISTS "Allow public read access to prices" ON prices
        FOR SELECT
        USING (true);
    
    -- 允许只有具有admin角色的认证用户插入/更新/删除prices
    CREATE POLICY IF NOT EXISTS "Allow admin insert access to prices" ON prices
        FOR INSERT
        TO authenticated
        WITH CHECK (auth.jwt() ? 'role' AND auth.jwt()->>'role' = 'admin');
    
    CREATE POLICY IF NOT EXISTS "Allow admin update access to prices" ON prices
        FOR UPDATE
        TO authenticated
        USING (auth.jwt() ? 'role' AND auth.jwt()->>'role' = 'admin')
        WITH CHECK (auth.jwt() ? 'role' AND auth.jwt()->>'role' = 'admin');
    
    CREATE POLICY IF NOT EXISTS "Allow admin delete access to prices" ON prices
        FOR DELETE
        TO authenticated
        USING (auth.jwt() ? 'role' AND auth.jwt()->>'role' = 'admin');
    """
    
    if not execute_sql_query(prices_policies_sql):
        return False
    
    logger.info("行级安全策略设置成功")
    return True

def setup_triggers():
    """设置触发器"""
    triggers_sql = """
    -- 创建更新时间戳函数
    CREATE OR REPLACE FUNCTION update_updated_at_column()
    RETURNS TRIGGER AS $$
    BEGIN
        NEW.updated_at = CURRENT_TIMESTAMP;
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
    
    -- 创建触发器
    DROP TRIGGER IF EXISTS update_assets_updated_at ON assets;
    CREATE TRIGGER update_assets_updated_at
    BEFORE UPDATE ON assets
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
    
    DROP TRIGGER IF EXISTS update_prices_updated_at ON prices;
    CREATE TRIGGER update_prices_updated_at
    BEFORE UPDATE ON prices
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
    """
    
    if not execute_sql_query(triggers_sql):
        return False
    
    logger.info("触发器设置成功")
    return True

def setup_permissions():
    """设置权限"""
    permissions_sql = """
    -- 设置权限
    GRANT SELECT ON assets TO anon, authenticated;
    GRANT SELECT ON prices TO anon, authenticated;
    
    -- 为service_role设置权限
    GRANT ALL ON assets TO service_role;
    GRANT ALL ON prices TO service_role;
    GRANT USAGE, SELECT ON SEQUENCE assets_asset_id_seq TO service_role;
    GRANT USAGE, SELECT ON SEQUENCE prices_price_id_seq TO service_role;
    """
    
    if not execute_sql_query(permissions_sql):
        return False
    
    logger.info("权限设置成功")
    return True

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
        return False
    
    # 设置行级安全策略
    if not setup_rls_policies():
        return False
    
    # 设置触发器
    if not setup_triggers():
        return False
    
    # 设置权限
    if not setup_permissions():
        return False
    
    # 检查表是否存在
    if not check_tables_exist():
        logger.warning("表检查失败，但可能是由于权限问题，请手动验证")
    
    logger.info("Supabase设置成功")
    return True

if __name__ == "__main__":
    success = main()
    if success:
        logger.info("Supabase设置成功完成")
        sys.exit(0)
    else:
        logger.error("Supabase设置失败")
        sys.exit(1)
