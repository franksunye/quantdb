"""
测试数据迁移的脚本

此脚本用于测试从 SQLite 数据库迁移数据到 Supabase PostgreSQL 数据库的功能。
"""

import os
import sys
import logging
import sqlite3
import pandas as pd
import tempfile
from datetime import date, datetime, timedelta
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, inspect

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("data_migration_test")

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# 从 .env 文件加载环境变量
load_dotenv()

def create_test_sqlite_db():
    """创建测试用的 SQLite 数据库"""
    try:
        # 创建临时 SQLite 数据库
        temp_dir = tempfile.gettempdir()
        db_path = os.path.join(temp_dir, "test_stock_data.db")
        logger.info(f"创建测试 SQLite 数据库: {db_path}")
        
        # 连接到 SQLite 数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 创建资产表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS assets (
            asset_id INTEGER PRIMARY KEY,
            symbol TEXT NOT NULL,
            name TEXT,
            isin TEXT,
            asset_type TEXT,
            exchange TEXT,
            currency TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # 创建价格表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS prices (
            price_id INTEGER PRIMARY KEY,
            asset_id INTEGER,
            date TEXT NOT NULL,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume INTEGER,
            adjusted_close REAL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (asset_id) REFERENCES assets (asset_id),
            UNIQUE (asset_id, date)
        )
        ''')
        
        # 插入测试数据
        # 插入资产
        assets = [
            (1, "000001", "平安银行", "CNE000000040", "STOCK", "SZSE", "CNY", datetime.now().isoformat(), datetime.now().isoformat()),
            (2, "600519", "贵州茅台", "CNE0000018R8", "STOCK", "SSE", "CNY", datetime.now().isoformat(), datetime.now().isoformat()),
            (3, "AAPL", "Apple Inc.", "US0378331005", "STOCK", "NASDAQ", "USD", datetime.now().isoformat(), datetime.now().isoformat())
        ]
        
        cursor.executemany('''
        INSERT INTO assets (asset_id, symbol, name, isin, asset_type, exchange, currency, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', assets)
        
        # 插入价格数据
        today = date.today()
        prices = []
        
        # 为每个资产生成 10 天的价格数据
        for asset_id in range(1, 4):
            base_price = 100.0 * asset_id
            for i in range(10):
                day = today - timedelta(days=i)
                price_id = asset_id * 100 + i
                open_price = base_price + i
                high_price = open_price + 5
                low_price = open_price - 5
                close_price = open_price + 2
                volume = 1000000 + i * 10000
                adjusted_close = close_price
                
                prices.append((
                    price_id, asset_id, day.isoformat(), open_price, high_price, low_price, close_price,
                    volume, adjusted_close, datetime.now().isoformat(), datetime.now().isoformat()
                ))
        
        cursor.executemany('''
        INSERT INTO prices (price_id, asset_id, date, open, high, low, close, volume, adjusted_close, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', prices)
        
        # 提交事务
        conn.commit()
        
        # 验证数据
        cursor.execute("SELECT COUNT(*) FROM assets")
        asset_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM prices")
        price_count = cursor.fetchone()[0]
        
        logger.info(f"测试数据库创建成功: {asset_count} 个资产, {price_count} 条价格记录")
        
        # 关闭连接
        conn.close()
        
        return db_path
    except Exception as e:
        logger.error(f"创建测试 SQLite 数据库失败: {e}")
        return None

def export_data_to_csv(db_path):
    """将 SQLite 数据导出到 CSV 文件"""
    try:
        # 创建导出目录
        export_dir = os.path.join(tempfile.gettempdir(), "export")
        os.makedirs(export_dir, exist_ok=True)
        
        # 连接到 SQLite 数据库
        conn = sqlite3.connect(db_path)
        
        # 导出资产表
        assets_df = pd.read_sql_query("SELECT * FROM assets", conn)
        assets_csv_path = os.path.join(export_dir, "assets.csv")
        assets_df.to_csv(assets_csv_path, index=False)
        logger.info(f"资产数据导出到: {assets_csv_path}")
        
        # 导出价格表
        prices_df = pd.read_sql_query("SELECT * FROM prices", conn)
        prices_csv_path = os.path.join(export_dir, "prices.csv")
        prices_df.to_csv(prices_csv_path, index=False)
        logger.info(f"价格数据导出到: {prices_csv_path}")
        
        # 关闭连接
        conn.close()
        
        return export_dir
    except Exception as e:
        logger.error(f"导出数据到 CSV 失败: {e}")
        return None

def import_data_to_postgres(export_dir):
    """将 CSV 数据导入到 PostgreSQL 数据库"""
    try:
        # 获取数据库 URL
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            logger.error("未找到 DATABASE_URL 环境变量")
            return False
        
        # 创建数据库引擎
        engine = create_engine(database_url)
        
        # 读取 CSV 文件
        assets_csv_path = os.path.join(export_dir, "assets.csv")
        prices_csv_path = os.path.join(export_dir, "prices.csv")
        
        assets_df = pd.read_csv(assets_csv_path)
        prices_df = pd.read_csv(prices_csv_path)
        
        # 连接到数据库
        with engine.connect() as conn:
            # 开始事务
            with conn.begin():
                # 清理现有测试数据（如果有）
                conn.execute(text("DELETE FROM prices WHERE asset_id IN (SELECT asset_id FROM assets WHERE symbol IN ('000001', '600519', 'AAPL'))"))
                conn.execute(text("DELETE FROM assets WHERE symbol IN ('000001', '600519', 'AAPL')"))
                
                # 导入资产数据
                for _, row in assets_df.iterrows():
                    conn.execute(
                        text("""
                        INSERT INTO assets (asset_id, symbol, name, isin, asset_type, exchange, currency, created_at, updated_at)
                        VALUES (:asset_id, :symbol, :name, :isin, :asset_type, :exchange, :currency, :created_at, :updated_at)
                        ON CONFLICT (asset_id) DO UPDATE SET
                            symbol = EXCLUDED.symbol,
                            name = EXCLUDED.name,
                            isin = EXCLUDED.isin,
                            asset_type = EXCLUDED.asset_type,
                            exchange = EXCLUDED.exchange,
                            currency = EXCLUDED.currency,
                            updated_at = CURRENT_TIMESTAMP
                        """),
                        {
                            "asset_id": row["asset_id"],
                            "symbol": row["symbol"],
                            "name": row["name"],
                            "isin": row["isin"],
                            "asset_type": row["asset_type"],
                            "exchange": row["exchange"],
                            "currency": row["currency"],
                            "created_at": row["created_at"],
                            "updated_at": row["updated_at"]
                        }
                    )
                
                # 导入价格数据
                for _, row in prices_df.iterrows():
                    conn.execute(
                        text("""
                        INSERT INTO prices (price_id, asset_id, date, open, high, low, close, volume, adjusted_close, created_at, updated_at)
                        VALUES (:price_id, :asset_id, :date, :open, :high, :low, :close, :volume, :adjusted_close, :created_at, :updated_at)
                        ON CONFLICT (asset_id, date) DO UPDATE SET
                            open = EXCLUDED.open,
                            high = EXCLUDED.high,
                            low = EXCLUDED.low,
                            close = EXCLUDED.close,
                            volume = EXCLUDED.volume,
                            adjusted_close = EXCLUDED.adjusted_close,
                            updated_at = CURRENT_TIMESTAMP
                        """),
                        {
                            "price_id": row["price_id"],
                            "asset_id": row["asset_id"],
                            "date": row["date"],
                            "open": row["open"],
                            "high": row["high"],
                            "low": row["low"],
                            "close": row["close"],
                            "volume": row["volume"],
                            "adjusted_close": row["adjusted_close"],
                            "created_at": row["created_at"],
                            "updated_at": row["updated_at"]
                        }
                    )
                
                # 重置序列（如果需要）
                conn.execute(text("SELECT setval('assets_asset_id_seq', (SELECT MAX(asset_id) FROM assets))"))
                conn.execute(text("SELECT setval('prices_price_id_seq', (SELECT MAX(price_id) FROM prices))"))
        
        # 验证导入
        with engine.connect() as conn:
            # 检查资产数据
            result = conn.execute(text("SELECT COUNT(*) FROM assets WHERE symbol IN ('000001', '600519', 'AAPL')"))
            asset_count = result.scalar()
            
            # 检查价格数据
            result = conn.execute(text("SELECT COUNT(*) FROM prices WHERE asset_id IN (1, 2, 3)"))
            price_count = result.scalar()
            
            logger.info(f"数据导入验证: {asset_count} 个资产, {price_count} 条价格记录")
            
            if asset_count != 3 or price_count != 30:
                logger.error(f"数据导入验证失败: 预期 3 个资产和 30 条价格记录，实际 {asset_count} 个资产和 {price_count} 条价格记录")
                return False
        
        logger.info("数据成功导入到 PostgreSQL")
        return True
    except Exception as e:
        logger.error(f"导入数据到 PostgreSQL 失败: {e}")
        return False

def cleanup_test_data():
    """清理测试数据"""
    try:
        # 获取数据库 URL
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            logger.error("未找到 DATABASE_URL 环境变量")
            return False
        
        # 创建数据库引擎
        engine = create_engine(database_url)
        
        # 连接到数据库
        with engine.connect() as conn:
            # 开始事务
            with conn.begin():
                # 清理测试数据
                conn.execute(text("DELETE FROM prices WHERE asset_id IN (1, 2, 3)"))
                conn.execute(text("DELETE FROM assets WHERE asset_id IN (1, 2, 3)"))
        
        logger.info("测试数据清理完成")
        return True
    except Exception as e:
        logger.error(f"清理测试数据失败: {e}")
        return False

def run_migration_test():
    """运行数据迁移测试"""
    try:
        # 创建测试 SQLite 数据库
        db_path = create_test_sqlite_db()
        if not db_path:
            return False
        
        # 导出数据到 CSV
        export_dir = export_data_to_csv(db_path)
        if not export_dir:
            return False
        
        # 导入数据到 PostgreSQL
        import_success = import_data_to_postgres(export_dir)
        if not import_success:
            return False
        
        # 清理测试数据
        cleanup_success = cleanup_test_data()
        if not cleanup_success:
            logger.warning("测试数据清理失败，但迁移测试已成功完成")
        
        return True
    except Exception as e:
        logger.error(f"数据迁移测试失败: {e}")
        return False

if __name__ == "__main__":
    logger.info("开始数据迁移测试")
    success = run_migration_test()
    if success:
        logger.info("数据迁移测试成功！")
        sys.exit(0)
    else:
        logger.error("数据迁移测试失败。请检查日志获取详细信息。")
        sys.exit(1)
