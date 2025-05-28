"""
自动设置Supabase数据库的脚本

此脚本使用psycopg2直接连接到Supabase PostgreSQL数据库，并执行SQL脚本创建必要的表和索引。
"""

import os
import sys
import logging
import psycopg2
from dotenv import load_dotenv

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("supabase_setup")

# 从.env文件加载环境变量
load_dotenv()

def parse_db_url(database_url):
    """解析数据库URL"""
    if database_url.startswith('postgresql://'):
        # 解析PostgreSQL URL
        parts = database_url.replace('postgresql://', '').split('@')
        user_pass = parts[0].split(':')
        host_db = parts[1].split('/')
        
        user = user_pass[0]
        password = user_pass[1]
        host_port = host_db[0].split(':')
        host = host_port[0]
        port = int(host_port[1]) if len(host_port) > 1 else 5432
        dbname = host_db[1]
        
        return {
            'dbname': dbname,
            'user': user,
            'password': password,
            'host': host,
            'port': port
        }
    else:
        raise ValueError(f"不支持的数据库URL格式: {database_url}")

def execute_sql_script(conn, script_path):
    """执行SQL脚本文件"""
    try:
        # 读取SQL脚本
        with open(script_path, 'r') as f:
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

def setup_rls_policies(conn):
    """设置行级安全策略"""
    try:
        # 创建游标
        cur = conn.cursor()
        
        # 启用行级安全
        cur.execute("ALTER TABLE IF EXISTS assets ENABLE ROW LEVEL SECURITY;")
        cur.execute("ALTER TABLE IF EXISTS prices ENABLE ROW LEVEL SECURITY;")
        
        # 创建策略
        # Assets表策略
        # 允许任何人读取assets
        cur.execute("""
        CREATE POLICY IF NOT EXISTS "Allow public read access to assets" ON assets
            FOR SELECT
            USING (true);
        """)
        
        # 允许只有具有admin角色的认证用户插入/更新/删除assets
        cur.execute("""
        CREATE POLICY IF NOT EXISTS "Allow admin insert access to assets" ON assets
            FOR INSERT
            TO authenticated
            WITH CHECK (auth.jwt() ? 'role' AND auth.jwt()->>'role' = 'admin');
        """)
        
        cur.execute("""
        CREATE POLICY IF NOT EXISTS "Allow admin update access to assets" ON assets
            FOR UPDATE
            TO authenticated
            USING (auth.jwt() ? 'role' AND auth.jwt()->>'role' = 'admin')
            WITH CHECK (auth.jwt() ? 'role' AND auth.jwt()->>'role' = 'admin');
        """)
        
        cur.execute("""
        CREATE POLICY IF NOT EXISTS "Allow admin delete access to assets" ON assets
            FOR DELETE
            TO authenticated
            USING (auth.jwt() ? 'role' AND auth.jwt()->>'role' = 'admin');
        """)
        
        # Prices表策略
        # 允许任何人读取prices
        cur.execute("""
        CREATE POLICY IF NOT EXISTS "Allow public read access to prices" ON prices
            FOR SELECT
            USING (true);
        """)
        
        # 允许只有具有admin角色的认证用户插入/更新/删除prices
        cur.execute("""
        CREATE POLICY IF NOT EXISTS "Allow admin insert access to prices" ON prices
            FOR INSERT
            TO authenticated
            WITH CHECK (auth.jwt() ? 'role' AND auth.jwt()->>'role' = 'admin');
        """)
        
        cur.execute("""
        CREATE POLICY IF NOT EXISTS "Allow admin update access to prices" ON prices
            FOR UPDATE
            TO authenticated
            USING (auth.jwt() ? 'role' AND auth.jwt()->>'role' = 'admin')
            WITH CHECK (auth.jwt() ? 'role' AND auth.jwt()->>'role' = 'admin');
        """)
        
        cur.execute("""
        CREATE POLICY IF NOT EXISTS "Allow admin delete access to prices" ON prices
            FOR DELETE
            TO authenticated
            USING (auth.jwt() ? 'role' AND auth.jwt()->>'role' = 'admin');
        """)
        
        # 提交事务
        conn.commit()
        
        # 关闭游标
        cur.close()
        
        logger.info("行级安全策略设置成功")
        return True
    except Exception as e:
        logger.error(f"设置行级安全策略失败: {e}")
        conn.rollback()
        return False

def setup_triggers(conn):
    """设置触发器"""
    try:
        # 创建游标
        cur = conn.cursor()
        
        # 创建更新时间戳函数
        cur.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """)
        
        # 创建触发器
        cur.execute("""
        DROP TRIGGER IF EXISTS update_assets_updated_at ON assets;
        CREATE TRIGGER update_assets_updated_at
        BEFORE UPDATE ON assets
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
        """)
        
        cur.execute("""
        DROP TRIGGER IF EXISTS update_prices_updated_at ON prices;
        CREATE TRIGGER update_prices_updated_at
        BEFORE UPDATE ON prices
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
        """)
        
        # 提交事务
        conn.commit()
        
        # 关闭游标
        cur.close()
        
        logger.info("触发器设置成功")
        return True
    except Exception as e:
        logger.error(f"设置触发器失败: {e}")
        conn.rollback()
        return False

def setup_permissions(conn):
    """设置权限"""
    try:
        # 创建游标
        cur = conn.cursor()
        
        # 设置权限
        cur.execute("GRANT SELECT ON assets TO anon, authenticated;")
        cur.execute("GRANT SELECT ON prices TO anon, authenticated;")
        
        # 为service_role设置权限
        cur.execute("GRANT ALL ON assets TO service_role;")
        cur.execute("GRANT ALL ON prices TO service_role;")
        cur.execute("GRANT USAGE, SELECT ON SEQUENCE assets_asset_id_seq TO service_role;")
        cur.execute("GRANT USAGE, SELECT ON SEQUENCE prices_price_id_seq TO service_role;")
        
        # 提交事务
        conn.commit()
        
        # 关闭游标
        cur.close()
        
        logger.info("权限设置成功")
        return True
    except Exception as e:
        logger.error(f"设置权限失败: {e}")
        conn.rollback()
        return False

def main():
    """主函数"""
    try:
        # 获取数据库URL
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            logger.error("未找到DATABASE_URL环境变量")
            return False
        
        # 解析数据库URL
        db_params = parse_db_url(database_url)
        
        # 打印连接信息（隐藏密码）
        logger.info(f"连接到PostgreSQL数据库: {db_params['host']}:{db_params['port']}/{db_params['dbname']} (用户: {db_params['user']})")
        
        # 连接到数据库
        conn = psycopg2.connect(
            dbname=db_params['dbname'],
            user=db_params['user'],
            password=db_params['password'],
            host=db_params['host'],
            port=db_params['port']
        )
        
        logger.info("数据库连接成功")
        
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
        
        # 设置行级安全策略
        if not setup_rls_policies(conn):
            logger.error("设置行级安全策略失败")
            conn.close()
            return False
        
        # 设置触发器
        if not setup_triggers(conn):
            logger.error("设置触发器失败")
            conn.close()
            return False
        
        # 设置权限
        if not setup_permissions(conn):
            logger.error("设置权限失败")
            conn.close()
            return False
        
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
