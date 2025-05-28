"""
使用psycopg2创建Supabase表的脚本

此脚本使用psycopg2直接连接到Supabase PostgreSQL数据库，并创建必要的表。
"""

import os
import sys
import psycopg2
from dotenv import load_dotenv

def create_tables():
    """创建表"""
    try:
        # 加载环境变量
        load_dotenv()
        
        # 获取数据库连接参数
        db_host = "db.dvusiqfijdmjcsubyapw.supabase.co"
        db_port = 5432
        db_name = "postgres"
        db_user = "postgres"
        db_password = os.getenv('SUPABASE_DB_PASSWORD')
        
        if not db_password:
            print("未找到SUPABASE_DB_PASSWORD环境变量")
            return False
        
        print(f"连接到PostgreSQL数据库: {db_host}:{db_port}/{db_name} (用户: {db_user})")
        
        # 连接到数据库
        conn = psycopg2.connect(
            dbname=db_name,
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port
        )
        
        print("数据库连接成功")
        
        # 创建游标
        cur = conn.cursor()
        
        # 创建assets表
        print("创建assets表...")
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
        print("创建prices表...")
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
        print("创建索引...")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_prices_asset_id ON prices (asset_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_prices_date ON prices (date)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_assets_symbol ON assets (symbol)")
        
        # 提交事务
        conn.commit()
        
        # 验证表是否创建成功
        print("验证表是否创建成功...")
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        tables = [row[0] for row in cur.fetchall()]
        
        print(f"数据库中的表: {tables}")
        
        # 检查是否存在预期的表
        expected_tables = ['assets', 'prices']
        missing_tables = [table for table in expected_tables if table not in tables]
        
        if missing_tables:
            print(f"缺少以下表: {missing_tables}")
        else:
            print("所有预期的表都存在")
            
            # 检查表结构
            for table in expected_tables:
                cur.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table}'")
                columns = [row[0] for row in cur.fetchall()]
                print(f"表 {table} 的列: {columns}")
        
        # 关闭连接
        cur.close()
        conn.close()
        
        print("表创建成功")
        return True
    except Exception as e:
        print(f"创建表失败: {e}")
        return False

def main():
    """主函数"""
    print("开始创建Supabase表")
    
    # 创建表
    if not create_tables():
        print("创建表失败")
        return False
    
    print("Supabase表创建成功")
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("脚本执行成功")
        sys.exit(0)
    else:
        print("脚本执行失败")
        sys.exit(1)
