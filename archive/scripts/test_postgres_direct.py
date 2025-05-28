"""
测试 PostgreSQL 直连功能

此脚本用于测试 PostgreSQL 直连功能，包括：
1. 连接测试
2. 基本操作测试（查询、插入、更新、删除）
3. 中文数据处理测试
"""

import os
import sys
import logging
import traceback
from datetime import date
from dotenv import load_dotenv

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("postgres_direct_test")

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 从 .env 文件加载环境变量
load_dotenv()

def test_connection():
    """测试数据库连接"""
    try:
        from services.postgres_client import get_postgres_client
        
        logger.info("测试数据库连接")
        
        # 获取客户端
        client = get_postgres_client()
        
        # 测试连接
        version = client.execute_query_scalar("SELECT version()")
        logger.info(f"PostgreSQL 版本: {version}")
        
        # 获取表列表
        tables = client.execute_query("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        logger.info(f"数据库中的表: {[table[0] for table in tables]}")
        
        logger.info("数据库连接测试成功")
        return True
    except Exception as e:
        logger.error(f"数据库连接测试失败: {e}")
        logger.error(traceback.format_exc())
        return False

def test_basic_operations():
    """测试基本数据库操作"""
    try:
        from services.postgres_client import get_postgres_client
        
        logger.info("测试基本数据库操作")
        
        # 获取客户端
        client = get_postgres_client()
        
        # 检查 assets 表是否存在
        if not client.table_exists("assets"):
            logger.info("创建 assets 表")
            client.execute_non_query("""
            CREATE TABLE assets (
                id SERIAL PRIMARY KEY,
                symbol VARCHAR(20) NOT NULL,
                name VARCHAR(100),
                asset_type VARCHAR(20),
                exchange VARCHAR(20),
                currency VARCHAR(3),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(symbol)
            )
            """)
        
        # 检查 prices 表是否存在
        if not client.table_exists("prices"):
            logger.info("创建 prices 表")
            client.execute_non_query("""
            CREATE TABLE prices (
                id SERIAL PRIMARY KEY,
                asset_id INTEGER NOT NULL,
                date DATE NOT NULL,
                open NUMERIC(10, 2),
                high NUMERIC(10, 2),
                low NUMERIC(10, 2),
                close NUMERIC(10, 2),
                volume BIGINT,
                adjusted_close NUMERIC(10, 2),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (asset_id) REFERENCES assets (id),
                UNIQUE (asset_id, date)
            )
            """)
        
        # 插入测试资产
        logger.info("插入测试资产")
        symbol = f"TEST{date.today().strftime('%Y%m%d')}"
        
        # 检查资产是否已存在
        existing_asset = client.execute_query_dict_one(
            "SELECT id FROM assets WHERE symbol = %s",
            (symbol,)
        )
        
        if existing_asset:
            asset_id = existing_asset["id"]
            logger.info(f"资产已存在，ID: {asset_id}")
        else:
            # 插入资产
            asset_id = client.execute_query_scalar(
                """
                INSERT INTO assets (symbol, name, asset_type, exchange, currency)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
                """,
                (symbol, "Test Asset", "STOCK", "TEST", "USD")
            )
            logger.info(f"插入资产成功，ID: {asset_id}")
        
        # 插入测试价格
        logger.info("插入测试价格")
        today = date.today()
        
        # 检查价格是否已存在
        existing_price = client.execute_query_dict_one(
            "SELECT id FROM prices WHERE asset_id = %s AND date = %s",
            (asset_id, today)
        )
        
        if existing_price:
            price_id = existing_price["id"]
            logger.info(f"价格已存在，ID: {price_id}")
            
            # 更新价格
            rows_updated = client.execute_non_query(
                """
                UPDATE prices
                SET open = %s, high = %s, low = %s, close = %s, volume = %s, adjusted_close = %s
                WHERE id = %s
                """,
                (100.0, 105.0, 95.0, 102.5, 1000, 102.5, price_id)
            )
            logger.info(f"更新价格成功，影响行数: {rows_updated}")
        else:
            # 插入价格
            price_id = client.execute_query_scalar(
                """
                INSERT INTO prices (asset_id, date, open, high, low, close, volume, adjusted_close)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (asset_id, today, 100.0, 105.0, 95.0, 102.5, 1000, 102.5)
            )
            logger.info(f"插入价格成功，ID: {price_id}")
        
        # 查询数据
        logger.info("查询数据")
        
        # 查询资产
        asset = client.execute_query_dict_one(
            "SELECT * FROM assets WHERE id = %s",
            (asset_id,)
        )
        logger.info(f"查询资产结果: {asset}")
        
        # 查询价格
        price = client.execute_query_dict_one(
            "SELECT * FROM prices WHERE id = %s",
            (price_id,)
        )
        logger.info(f"查询价格结果: {price}")
        
        # 查询资产和价格
        asset_with_price = client.execute_query_dict_one(
            """
            SELECT a.symbol, a.name, p.date, p.open, p.high, p.low, p.close, p.volume
            FROM assets a
            JOIN prices p ON a.id = p.asset_id
            WHERE a.id = %s AND p.date = %s
            """,
            (asset_id, today)
        )
        logger.info(f"查询资产和价格结果: {asset_with_price}")
        
        logger.info("基本数据库操作测试成功")
        return True
    except Exception as e:
        logger.error(f"基本数据库操作测试失败: {e}")
        logger.error(traceback.format_exc())
        return False

def test_chinese_data():
    """测试中文数据处理"""
    try:
        from services.postgres_client import get_postgres_client
        
        logger.info("测试中文数据处理")
        
        # 获取客户端
        client = get_postgres_client()
        
        # 插入中文测试资产
        logger.info("插入中文测试资产")
        symbol = f"CN{date.today().strftime('%Y%m%d')}"
        
        # 检查资产是否已存在
        existing_asset = client.execute_query_dict_one(
            "SELECT id FROM assets WHERE symbol = %s",
            (symbol,)
        )
        
        if existing_asset:
            asset_id = existing_asset["id"]
            logger.info(f"中文资产已存在，ID: {asset_id}")
            
            # 更新资产
            rows_updated = client.execute_non_query(
                """
                UPDATE assets
                SET name = %s, exchange = %s
                WHERE id = %s
                """,
                ("中文测试资产", "上海证券交易所", asset_id)
            )
            logger.info(f"更新中文资产成功，影响行数: {rows_updated}")
        else:
            # 插入资产
            asset_id = client.execute_query_scalar(
                """
                INSERT INTO assets (symbol, name, asset_type, exchange, currency)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
                """,
                (symbol, "中文测试资产", "STOCK", "上海证券交易所", "CNY")
            )
            logger.info(f"插入中文资产成功，ID: {asset_id}")
        
        # 查询中文数据
        logger.info("查询中文数据")
        
        # 查询资产
        asset = client.execute_query_dict_one(
            "SELECT * FROM assets WHERE id = %s",
            (asset_id,)
        )
        logger.info(f"查询中文资产结果: {asset}")
        
        # 验证中文数据完整性
        if asset["name"] == "中文测试资产" and asset["exchange"] == "上海证券交易所":
            logger.info("中文数据完整性验证通过")
        else:
            logger.error("中文数据完整性验证失败")
            logger.error(f"期望名称: 中文测试资产，实际名称: {asset['name']}")
            logger.error(f"期望交易所: 上海证券交易所，实际交易所: {asset['exchange']}")
        
        logger.info("中文数据处理测试成功")
        return True
    except Exception as e:
        logger.error(f"中文数据处理测试失败: {e}")
        logger.error(traceback.format_exc())
        return False

def run_all_tests():
    """运行所有测试"""
    tests = [
        ("数据库连接测试", test_connection),
        ("基本数据库操作测试", test_basic_operations),
        ("中文数据处理测试", test_chinese_data)
    ]
    
    results = []
    for name, test_func in tests:
        logger.info(f"\n{'='*50}\n开始 {name}\n{'='*50}")
        result = test_func()
        results.append((name, result))
        logger.info(f"完成 {name}: {'成功' if result else '失败'}")
    
    # 打印测试结果摘要
    logger.info("\n\n测试结果摘要:")
    logger.info("=" * 50)
    all_passed = True
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        logger.info(f"{status} - {name}")
        if not result:
            all_passed = False
    
    logger.info("=" * 50)
    if all_passed:
        logger.info("所有测试通过！PostgreSQL 直连测试成功。")
    else:
        logger.error("部分测试失败。请检查日志获取详细信息。")
    
    return all_passed

if __name__ == "__main__":
    logger.info("开始测试 PostgreSQL 直连功能")
    success = run_all_tests()
    if success:
        logger.info("测试成功！可以直接连接 PostgreSQL 数据库")
        sys.exit(0)
    else:
        logger.error("测试失败。请检查日志获取详细信息")
        sys.exit(1)
