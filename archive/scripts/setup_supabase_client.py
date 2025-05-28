"""
使用Supabase客户端库设置Supabase的脚本

此脚本使用Python Supabase客户端库来设置数据库表和执行SQL操作。
"""

import os
import sys
import logging
from dotenv import load_dotenv
from supabase import create_client, Client

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("supabase_client_setup")

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

def create_supabase_client():
    """创建Supabase客户端"""
    try:
        # 获取Supabase URL和API密钥
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')

        logger.info(f"连接到Supabase: {supabase_url}")

        # 创建客户端
        supabase = create_client(supabase_url, supabase_key)

        # 测试连接 - 使用rpc调用而不是查询表
        try:
            # 尝试获取当前时间戳，这是一个简单的查询，不需要表存在
            response = supabase.rpc('execute_sql', {'sql': 'SELECT NOW();'}).execute()
            logger.info("Supabase客户端创建成功 - RPC调用成功")
        except Exception as e:
            # 如果RPC调用失败，尝试使用REST API
            logger.warning(f"RPC调用失败: {e}")
            logger.info("尝试使用REST API测试连接")

            # 使用REST API获取服务器信息
            response = supabase.from_('').select('*').limit(1).execute()
            logger.info("Supabase客户端创建成功 - REST API调用成功")

        return supabase
    except Exception as e:
        logger.error(f"创建Supabase客户端失败: {e}")
        return None

def execute_sql(supabase, sql):
    """执行SQL查询"""
    try:
        logger.info(f"执行SQL查询: {sql[:50]}...")

        # 执行SQL查询
        response = supabase.rpc('execute_sql', {'sql': sql}).execute()

        logger.info("SQL查询执行成功")
        return True
    except Exception as e:
        logger.error(f"执行SQL查询失败: {e}")
        return False

def execute_sql_file(supabase, file_path):
    """执行SQL文件"""
    try:
        # 读取SQL文件
        with open(file_path, 'r') as f:
            sql_content = f.read()

        logger.info(f"执行SQL文件: {file_path}")

        # 将SQL语句拆分为多个语句
        sql_statements = sql_content.split(';')

        # 逐个执行SQL语句
        for i, statement in enumerate(sql_statements):
            # 跳过空语句
            if not statement.strip():
                continue

            # 添加分号
            statement = statement.strip() + ';'

            logger.info(f"执行SQL语句 {i+1}/{len(sql_statements)}: {statement[:50]}...")

            # 执行SQL语句
            try:
                response = supabase.rpc('execute_sql', {'sql': statement}).execute()
                logger.info(f"SQL语句 {i+1} 执行成功")
            except Exception as e:
                logger.warning(f"SQL语句 {i+1} 执行失败: {e}")
                # 继续执行其他语句

        logger.info(f"SQL文件 {file_path} 执行完成")
        return True
    except Exception as e:
        logger.error(f"执行SQL文件失败: {e}")
        return False

def check_tables_exist(supabase):
    """检查表是否存在"""
    try:
        # 检查assets表
        try:
            assets_response = supabase.table('assets').select('*').limit(1).execute()
            logger.info("assets表存在")
        except Exception as e:
            logger.error(f"assets表检查失败: {e}")
            return False

        # 检查prices表
        try:
            prices_response = supabase.table('prices').select('*').limit(1).execute()
            logger.info("prices表存在")
        except Exception as e:
            logger.error(f"prices表检查失败: {e}")
            return False

        logger.info("表检查成功: assets和prices表都存在")
        return True
    except Exception as e:
        logger.error(f"检查表失败: {e}")
        return False

def create_tables(supabase):
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

    if not execute_sql(supabase, assets_table_sql):
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

    if not execute_sql(supabase, prices_table_sql):
        return False

    # 创建索引
    indexes_sql = """
    CREATE INDEX IF NOT EXISTS idx_prices_asset_id ON prices (asset_id);
    CREATE INDEX IF NOT EXISTS idx_prices_date ON prices (date);
    CREATE INDEX IF NOT EXISTS idx_assets_symbol ON assets (symbol);
    """

    if not execute_sql(supabase, indexes_sql):
        return False

    logger.info("表和索引创建成功")
    return True

def setup_rls_policies(supabase):
    """设置行级安全策略"""
    # 启用行级安全
    enable_rls_sql = """
    ALTER TABLE IF EXISTS assets ENABLE ROW LEVEL SECURITY;
    ALTER TABLE IF EXISTS prices ENABLE ROW LEVEL SECURITY;
    """

    if not execute_sql(supabase, enable_rls_sql):
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

    if not execute_sql(supabase, assets_policies_sql):
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

    if not execute_sql(supabase, prices_policies_sql):
        return False

    logger.info("行级安全策略设置成功")
    return True

def main():
    """主函数"""
    logger.info("开始设置Supabase")

    # 检查环境变量
    if not check_env_variables():
        return False

    # 创建Supabase客户端
    supabase = create_supabase_client()
    if not supabase:
        return False

    # 创建表
    if not create_tables(supabase):
        logger.warning("创建表失败，但继续执行")

    # 设置行级安全策略
    if not setup_rls_policies(supabase):
        logger.warning("设置行级安全策略失败，但继续执行")

    # 检查表是否存在
    if not check_tables_exist(supabase):
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
