"""
测试直接连接 Supabase PostgreSQL 数据库

此脚本用于测试直接连接 Supabase PostgreSQL 数据库，包括：
1. 使用 SQLAlchemy 连接
2. 使用 psycopg2 直接连接
3. 测试基本的数据库操作
4. 测试与现有模型的兼容性
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
logger = logging.getLogger("direct_postgres_test")

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 从 .env 文件加载环境变量
load_dotenv()

def test_sqlalchemy_connection():
    """测试使用 SQLAlchemy 连接 Supabase PostgreSQL 数据库"""
    try:
        from sqlalchemy import create_engine, text, inspect
        
        # 获取数据库 URL
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            logger.error("未找到 DATABASE_URL 环境变量")
            return False
        
        # 打印数据库 URL（隐藏密码）
        if '@' in database_url:
            parts = database_url.split('@')
            masked_url = f"{parts[0].split(':')[0]}:***@{parts[1]}"
        else:
            masked_url = database_url
        
        logger.info(f"使用 SQLAlchemy 连接到数据库: {masked_url}")
        
        # 创建数据库引擎
        engine = create_engine(database_url)
        
        # 测试连接
        with engine.connect() as conn:
            # 执行简单查询
            result = conn.execute(text("SELECT 1"))
            logger.info(f"查询结果: {result.scalar()}")
            
            # 获取表列表
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            logger.info(f"数据库中的表: {tables}")
            
            # 检查是否存在我们的表
            expected_tables = ['assets', 'prices']
            missing_tables = [table for table in expected_tables if table not in tables]
            
            if missing_tables:
                logger.warning(f"缺少以下表: {missing_tables}")
                logger.info("请确保已执行SQL脚本创建表")
            else:
                logger.info("所有预期的表都存在")
                
                # 检查表结构
                for table in expected_tables:
                    columns = inspector.get_columns(table)
                    logger.info(f"表 {table} 的列: {[col['name'] for col in columns]}")
            
            logger.info("SQLAlchemy 连接测试成功")
            return True
    except Exception as e:
        logger.error(f"SQLAlchemy 连接测试失败: {e}")
        logger.error(traceback.format_exc())
        return False

def test_psycopg2_connection():
    """测试使用 psycopg2 直接连接 Supabase PostgreSQL 数据库"""
    try:
        import psycopg2
        
        # 获取数据库 URL
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            logger.error("未找到 DATABASE_URL 环境变量")
            return False
        
        # 解析数据库 URL
        if database_url.startswith('postgresql://'):
            # 解析 PostgreSQL URL
            parts = database_url.replace('postgresql://', '').split('@')
            user_pass = parts[0].split(':')
            host_db = parts[1].split('/')
            
            user = user_pass[0]
            password = user_pass[1]
            host_port = host_db[0].split(':')
            host = host_port[0]
            port = int(host_port[1]) if len(host_port) > 1 else 5432
            dbname = host_db[1]
            
            logger.info(f"使用 psycopg2 连接到 PostgreSQL 数据库: {host}:{port}/{dbname} (用户: {user})")
            
            # 连接到数据库
            conn = psycopg2.connect(
                dbname=dbname,
                user=user,
                password=password,
                host=host,
                port=port
            )
            
            # 测试连接
            cur = conn.cursor()
            cur.execute("SELECT version()")
            version = cur.fetchone()
            
            logger.info(f"PostgreSQL 版本: {version[0]}")
            
            # 获取表列表
            cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
            tables = [row[0] for row in cur.fetchall()]
            
            logger.info(f"数据库中的表: {tables}")
            
            # 关闭连接
            cur.close()
            conn.close()
            
            logger.info("psycopg2 连接测试成功")
            return True
        else:
            logger.error(f"不支持的数据库 URL 格式: {database_url}")
            return False
    except Exception as e:
        logger.error(f"psycopg2 连接测试失败: {e}")
        logger.error(traceback.format_exc())
        return False

def test_basic_operations():
    """测试基本的数据库操作"""
    try:
        from sqlalchemy import create_engine, text
        
        # 获取数据库 URL
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            logger.error("未找到 DATABASE_URL 环境变量")
            return False
        
        logger.info("测试基本的数据库操作...")
        
        # 创建数据库引擎
        engine = create_engine(database_url)
        
        # 测试插入、查询和删除操作
        with engine.connect() as conn:
            # 开始事务
            with conn.begin():
                # 插入测试资产
                asset_result = conn.execute(
                    text("""
                    INSERT INTO assets (symbol, name, asset_type, exchange, currency, isin)
                    VALUES (:symbol, :name, :asset_type, :exchange, :currency, :isin)
                    RETURNING asset_id
                    """),
                    {
                        "symbol": "TEST001",
                        "name": "Test Asset",
                        "asset_type": "STOCK",
                        "exchange": "TEST",
                        "currency": "USD",
                        "isin": "US0000000001"
                    }
                )
                
                asset_id = asset_result.scalar()
                logger.info(f"插入测试资产，ID: {asset_id}")
                
                # 插入测试价格
                price_result = conn.execute(
                    text("""
                    INSERT INTO prices (asset_id, date, open, high, low, close, volume, adjusted_close)
                    VALUES (:asset_id, :date, :open, :high, :low, :close, :volume, :adjusted_close)
                    RETURNING price_id
                    """),
                    {
                        "asset_id": asset_id,
                        "date": date.today(),
                        "open": 100.0,
                        "high": 105.0,
                        "low": 95.0,
                        "close": 102.5,
                        "volume": 1000,
                        "adjusted_close": 102.5
                    }
                )
                
                price_id = price_result.scalar()
                logger.info(f"插入测试价格，ID: {price_id}")
                
                # 查询插入的数据
                asset_query = conn.execute(
                    text("SELECT * FROM assets WHERE asset_id = :asset_id"),
                    {"asset_id": asset_id}
                )
                asset = asset_query.fetchone()
                logger.info(f"查询资产结果: {asset}")
                
                price_query = conn.execute(
                    text("SELECT * FROM prices WHERE price_id = :price_id"),
                    {"price_id": price_id}
                )
                price = price_query.fetchone()
                logger.info(f"查询价格结果: {price}")
                
                # 删除测试数据
                conn.execute(
                    text("DELETE FROM prices WHERE price_id = :price_id"),
                    {"price_id": price_id}
                )
                logger.info(f"删除测试价格，ID: {price_id}")
                
                conn.execute(
                    text("DELETE FROM assets WHERE asset_id = :asset_id"),
                    {"asset_id": asset_id}
                )
                logger.info(f"删除测试资产，ID: {asset_id}")
                
                # 回滚事务，确保不影响实际数据
                raise Exception("测试完成，回滚事务")
    except Exception as e:
        if "测试完成，回滚事务" in str(e):
            logger.info("基本数据库操作测试成功")
            return True
        else:
            logger.error(f"基本数据库操作测试失败: {e}")
            logger.error(traceback.format_exc())
            return False

def test_sqlalchemy_models():
    """测试使用 SQLAlchemy 模型"""
    try:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        
        # 导入模型
        from src.api.models import Base, Asset, Price
        
        # 获取数据库 URL
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            logger.error("未找到 DATABASE_URL 环境变量")
            return False
        
        logger.info("测试使用 SQLAlchemy 模型...")
        
        # 创建数据库引擎
        engine = create_engine(database_url)
        
        # 创建会话
        Session = sessionmaker(bind=engine)
        session = Session()
        
        try:
            # 创建测试资产
            test_asset = Asset(
                symbol="TEST002",
                name="Test Asset Model",
                isin="US0000000002",
                asset_type="STOCK",
                exchange="TEST",
                currency="USD"
            )
            
            # 添加到会话
            session.add(test_asset)
            session.flush()
            
            asset_id = test_asset.asset_id
            logger.info(f"创建测试资产，ID: {asset_id}")
            
            # 创建测试价格
            test_price = Price(
                asset_id=asset_id,
                date=date.today(),
                open=100.0,
                high=105.0,
                low=95.0,
                close=102.5,
                volume=1000,
                adjusted_close=102.5
            )
            
            # 添加到会话
            session.add(test_price)
            session.flush()
            
            price_id = test_price.price_id
            logger.info(f"创建测试价格，ID: {price_id}")
            
            # 查询插入的数据
            asset = session.query(Asset).filter(Asset.asset_id == asset_id).first()
            logger.info(f"查询资产结果: {asset.symbol} - {asset.name}")
            
            price = session.query(Price).filter(Price.price_id == price_id).first()
            logger.info(f"查询价格结果: {price.date} - {price.close}")
            
            # 回滚会话，确保不影响实际数据
            session.rollback()
            logger.info("SQLAlchemy 模型测试成功")
            return True
        finally:
            # 关闭会话
            session.close()
    except Exception as e:
        logger.error(f"SQLAlchemy 模型测试失败: {e}")
        logger.error(traceback.format_exc())
        return False

def run_all_tests():
    """运行所有测试"""
    tests = [
        ("SQLAlchemy 连接测试", test_sqlalchemy_connection),
        ("psycopg2 连接测试", test_psycopg2_connection),
        ("基本数据库操作测试", test_basic_operations),
        ("SQLAlchemy 模型测试", test_sqlalchemy_models)
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
        logger.info("所有测试通过！直接连接 Supabase PostgreSQL 数据库测试成功。")
    else:
        logger.error("部分测试失败。请检查日志获取详细信息。")
    
    return all_passed

if __name__ == "__main__":
    logger.info("开始测试直接连接 Supabase PostgreSQL 数据库")
    success = run_all_tests()
    if success:
        logger.info("测试成功！可以直接连接 Supabase PostgreSQL 数据库")
        sys.exit(0)
    else:
        logger.error("测试失败。请检查日志获取详细信息")
        sys.exit(1)
