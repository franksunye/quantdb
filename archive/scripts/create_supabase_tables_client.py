"""
使用 Supabase 客户端库创建表

此脚本使用 Supabase 客户端库创建必要的表。
"""

import os
import sys
import logging
import traceback
from dotenv import load_dotenv
from supabase import create_client, Client

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("create_supabase_tables_client")

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 从 .env 文件加载环境变量
load_dotenv()

def create_supabase_client():
    """创建 Supabase 客户端"""
    try:
        # 获取 Supabase URL 和 API 密钥
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')
        
        if not supabase_url or not supabase_key:
            logger.error("未找到 SUPABASE_URL 或 SUPABASE_KEY 环境变量")
            return None
        
        logger.info(f"连接到 Supabase: {supabase_url}")
        
        # 创建客户端
        supabase = create_client(supabase_url, supabase_key)
        
        return supabase
    except Exception as e:
        logger.error(f"创建 Supabase 客户端失败: {e}")
        logger.error(traceback.format_exc())
        return None

def create_execute_sql_function(supabase):
    """创建 execute_sql 函数"""
    try:
        logger.info("创建 execute_sql 函数")
        
        # SQL 函数定义
        sql = """
        CREATE OR REPLACE FUNCTION execute_sql(sql text)
        RETURNS text
        LANGUAGE plpgsql
        SECURITY DEFINER
        AS $$
        BEGIN
            EXECUTE sql;
            RETURN 'SQL executed successfully';
        EXCEPTION
            WHEN OTHERS THEN
                RETURN 'Error: ' || SQLERRM;
        END;
        $$;
        """
        
        # 执行 SQL
        response = supabase.rpc('execute_sql', {'sql': sql}).execute()
        
        logger.info(f"execute_sql 函数创建结果: {response}")
        return True
    except Exception as e:
        logger.error(f"创建 execute_sql 函数失败: {e}")
        logger.error(traceback.format_exc())
        return False

def create_assets_table(supabase):
    """创建 assets 表"""
    try:
        logger.info("创建 assets 表")
        
        # SQL 表定义
        sql = """
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
        
        # 执行 SQL
        response = supabase.rpc('execute_sql', {'sql': sql}).execute()
        
        logger.info(f"assets 表创建结果: {response}")
        return True
    except Exception as e:
        logger.error(f"创建 assets 表失败: {e}")
        logger.error(traceback.format_exc())
        return False

def create_prices_table(supabase):
    """创建 prices 表"""
    try:
        logger.info("创建 prices 表")
        
        # SQL 表定义
        sql = """
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
        
        # 执行 SQL
        response = supabase.rpc('execute_sql', {'sql': sql}).execute()
        
        logger.info(f"prices 表创建结果: {response}")
        return True
    except Exception as e:
        logger.error(f"创建 prices 表失败: {e}")
        logger.error(traceback.format_exc())
        return False

def create_indexes(supabase):
    """创建索引"""
    try:
        logger.info("创建索引")
        
        # SQL 索引定义
        sql = """
        CREATE INDEX IF NOT EXISTS idx_prices_asset_id ON prices (asset_id);
        CREATE INDEX IF NOT EXISTS idx_prices_date ON prices (date);
        CREATE INDEX IF NOT EXISTS idx_assets_symbol ON assets (symbol);
        """
        
        # 执行 SQL
        response = supabase.rpc('execute_sql', {'sql': sql}).execute()
        
        logger.info(f"索引创建结果: {response}")
        return True
    except Exception as e:
        logger.error(f"创建索引失败: {e}")
        logger.error(traceback.format_exc())
        return False

def create_rls_policies(supabase):
    """创建行级安全策略"""
    try:
        logger.info("创建行级安全策略")
        
        # SQL 策略定义
        sql = """
        -- 启用行级安全
        ALTER TABLE assets ENABLE ROW LEVEL SECURITY;
        ALTER TABLE prices ENABLE ROW LEVEL SECURITY;
        
        -- 创建策略
        CREATE POLICY "允许所有用户查看资产" ON assets
            FOR SELECT USING (true);
        
        CREATE POLICY "允许所有用户查看价格" ON prices
            FOR SELECT USING (true);
        
        CREATE POLICY "只允许管理员插入资产" ON assets
            FOR INSERT WITH CHECK (auth.role() = 'authenticated');
        
        CREATE POLICY "只允许管理员更新资产" ON assets
            FOR UPDATE USING (auth.role() = 'authenticated');
        
        CREATE POLICY "只允许管理员删除资产" ON assets
            FOR DELETE USING (auth.role() = 'authenticated');
        
        CREATE POLICY "只允许管理员插入价格" ON prices
            FOR INSERT WITH CHECK (auth.role() = 'authenticated');
        
        CREATE POLICY "只允许管理员更新价格" ON prices
            FOR UPDATE USING (auth.role() = 'authenticated');
        
        CREATE POLICY "只允许管理员删除价格" ON prices
            FOR DELETE USING (auth.role() = 'authenticated');
        """
        
        # 执行 SQL
        response = supabase.rpc('execute_sql', {'sql': sql}).execute()
        
        logger.info(f"行级安全策略创建结果: {response}")
        return True
    except Exception as e:
        logger.error(f"创建行级安全策略失败: {e}")
        logger.error(traceback.format_exc())
        return False

def check_tables_exist(supabase):
    """检查表是否存在"""
    try:
        logger.info("检查表是否存在")
        
        # 检查 assets 表
        try:
            response = supabase.from_('assets').select('*', count='exact').limit(1).execute()
            logger.info(f"assets 表存在，记录数: {response.count}")
        except Exception as e:
            logger.error(f"assets 表不存在或无法访问: {e}")
        
        # 检查 prices 表
        try:
            response = supabase.from_('prices').select('*', count='exact').limit(1).execute()
            logger.info(f"prices 表存在，记录数: {response.count}")
        except Exception as e:
            logger.error(f"prices 表不存在或无法访问: {e}")
        
        return True
    except Exception as e:
        logger.error(f"检查表是否存在失败: {e}")
        logger.error(traceback.format_exc())
        return False

def main():
    """主函数"""
    logger.info("开始创建 Supabase 表")
    
    # 创建 Supabase 客户端
    supabase = create_supabase_client()
    if not supabase:
        logger.error("创建 Supabase 客户端失败")
        return False
    
    # 创建 execute_sql 函数
    if not create_execute_sql_function(supabase):
        logger.warning("创建 execute_sql 函数失败，但继续执行")
    
    # 创建 assets 表
    if not create_assets_table(supabase):
        logger.error("创建 assets 表失败")
        return False
    
    # 创建 prices 表
    if not create_prices_table(supabase):
        logger.error("创建 prices 表失败")
        return False
    
    # 创建索引
    if not create_indexes(supabase):
        logger.warning("创建索引失败，但继续执行")
    
    # 创建行级安全策略
    if not create_rls_policies(supabase):
        logger.warning("创建行级安全策略失败，但继续执行")
    
    # 检查表是否存在
    if not check_tables_exist(supabase):
        logger.warning("检查表是否存在失败，但继续执行")
    
    logger.info("Supabase 表创建完成")
    return True

if __name__ == "__main__":
    success = main()
    if success:
        logger.info("脚本执行成功")
        sys.exit(0)
    else:
        logger.error("脚本执行失败")
        sys.exit(1)
