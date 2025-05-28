"""
测试 Supabase PostgreSQL 数据库性能

此脚本用于测试 Supabase PostgreSQL 数据库的性能，包括：
1. 批量插入数据
2. 批量查询数据
3. 复杂查询性能
4. 与 SQLite 性能对比
"""

import os
import sys
import time
import logging
import random
from datetime import date, timedelta
from dotenv import load_dotenv

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("postgres_performance_test")

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 从 .env 文件加载环境变量
load_dotenv()

def get_postgres_engine():
    """获取 PostgreSQL 数据库引擎"""
    from sqlalchemy import create_engine
    
    # 获取数据库 URL
    database_url = os.getenv('DATABASE_URL')
    if not database_url or not database_url.startswith('postgresql://'):
        logger.error("未找到有效的 PostgreSQL DATABASE_URL 环境变量")
        return None
    
    # 创建数据库引擎
    engine = create_engine(database_url)
    return engine

def get_sqlite_engine():
    """获取 SQLite 数据库引擎"""
    from sqlalchemy import create_engine
    
    # 使用项目中的 SQLite 数据库
    sqlite_url = 'sqlite:///./database/stock_data.db'
    
    # 创建数据库引擎
    engine = create_engine(sqlite_url)
    return engine

def test_bulk_insert(engine, num_records=1000):
    """测试批量插入性能"""
    from sqlalchemy.orm import sessionmaker
    from src.api.models import Asset, Price
    
    if engine is None:
        logger.error("数据库引擎为空")
        return False
    
    # 创建会话
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # 创建测试资产
        test_asset = Asset(
            symbol=f"PERF{int(time.time())}",
            name="Performance Test Asset",
            isin=f"US{int(time.time())}",
            asset_type="STOCK",
            exchange="TEST",
            currency="USD"
        )
        
        # 添加到会话
        session.add(test_asset)
        session.flush()
        
        asset_id = test_asset.asset_id
        logger.info(f"创建测试资产，ID: {asset_id}")
        
        # 生成测试价格数据
        start_date = date.today() - timedelta(days=num_records)
        prices = []
        
        logger.info(f"开始生成 {num_records} 条价格记录...")
        
        for i in range(num_records):
            current_date = start_date + timedelta(days=i)
            base_price = 100.0 + random.uniform(-20.0, 20.0)
            
            price = Price(
                asset_id=asset_id,
                date=current_date,
                open=base_price,
                high=base_price * (1 + random.uniform(0, 0.05)),
                low=base_price * (1 - random.uniform(0, 0.05)),
                close=base_price * (1 + random.uniform(-0.03, 0.03)),
                volume=int(random.uniform(1000, 10000)),
                adjusted_close=base_price * (1 + random.uniform(-0.03, 0.03))
            )
            
            prices.append(price)
        
        # 记录开始时间
        start_time = time.time()
        
        # 批量插入
        session.bulk_save_objects(prices)
        session.flush()
        
        # 记录结束时间
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        logger.info(f"批量插入 {num_records} 条记录耗时: {elapsed_time:.4f} 秒")
        logger.info(f"平均每条记录插入时间: {(elapsed_time / num_records) * 1000:.4f} 毫秒")
        
        # 回滚会话，确保不影响实际数据
        session.rollback()
        logger.info("批量插入测试完成")
        
        return {
            "records": num_records,
            "total_time": elapsed_time,
            "avg_time_ms": (elapsed_time / num_records) * 1000
        }
    except Exception as e:
        logger.error(f"批量插入测试失败: {e}")
        session.rollback()
        return False
    finally:
        # 关闭会话
        session.close()

def test_bulk_query(engine, num_records=1000):
    """测试批量查询性能"""
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import text
    
    if engine is None:
        logger.error("数据库引擎为空")
        return False
    
    # 创建会话
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # 创建测试资产
        with session.begin():
            result = session.execute(
                text("""
                INSERT INTO assets (symbol, name, asset_type, exchange, currency, isin)
                VALUES (:symbol, :name, :asset_type, :exchange, :currency, :isin)
                RETURNING asset_id
                """),
                {
                    "symbol": f"QPERF{int(time.time())}",
                    "name": "Query Performance Test Asset",
                    "asset_type": "STOCK",
                    "exchange": "TEST",
                    "currency": "USD",
                    "isin": f"US{int(time.time())}"
                }
            )
            
            asset_id = result.scalar()
            logger.info(f"创建测试资产，ID: {asset_id}")
            
            # 生成测试价格数据
            start_date = date.today() - timedelta(days=num_records)
            
            # 批量插入价格数据
            for i in range(num_records):
                current_date = start_date + timedelta(days=i)
                base_price = 100.0 + random.uniform(-20.0, 20.0)
                
                session.execute(
                    text("""
                    INSERT INTO prices (asset_id, date, open, high, low, close, volume, adjusted_close)
                    VALUES (:asset_id, :date, :open, :high, :low, :close, :volume, :adjusted_close)
                    """),
                    {
                        "asset_id": asset_id,
                        "date": current_date,
                        "open": base_price,
                        "high": base_price * (1 + random.uniform(0, 0.05)),
                        "low": base_price * (1 - random.uniform(0, 0.05)),
                        "close": base_price * (1 + random.uniform(-0.03, 0.03)),
                        "volume": int(random.uniform(1000, 10000)),
                        "adjusted_close": base_price * (1 + random.uniform(-0.03, 0.03))
                    }
                )
            
            logger.info(f"插入 {num_records} 条测试价格记录")
            
            # 记录开始时间
            start_time = time.time()
            
            # 批量查询
            result = session.execute(
                text("""
                SELECT * FROM prices
                WHERE asset_id = :asset_id
                ORDER BY date
                """),
                {"asset_id": asset_id}
            )
            
            # 获取所有结果
            records = result.fetchall()
            
            # 记录结束时间
            end_time = time.time()
            elapsed_time = end_time - start_time
            
            logger.info(f"查询 {len(records)} 条记录耗时: {elapsed_time:.4f} 秒")
            logger.info(f"平均每条记录查询时间: {(elapsed_time / len(records)) * 1000:.4f} 毫秒")
            
            # 测试复杂查询
            start_time = time.time()
            
            # 执行复杂查询
            result = session.execute(
                text("""
                SELECT 
                    a.symbol,
                    a.name,
                    p.date,
                    p.open,
                    p.high,
                    p.low,
                    p.close,
                    p.volume
                FROM 
                    prices p
                JOIN 
                    assets a ON p.asset_id = a.asset_id
                WHERE 
                    p.asset_id = :asset_id
                    AND p.date BETWEEN :start_date AND :end_date
                ORDER BY 
                    p.date
                """),
                {
                    "asset_id": asset_id,
                    "start_date": start_date + timedelta(days=int(num_records * 0.3)),
                    "end_date": start_date + timedelta(days=int(num_records * 0.7))
                }
            )
            
            # 获取所有结果
            complex_records = result.fetchall()
            
            # 记录结束时间
            end_time = time.time()
            complex_elapsed_time = end_time - start_time
            
            logger.info(f"复杂查询 {len(complex_records)} 条记录耗时: {complex_elapsed_time:.4f} 秒")
            
            # 删除测试数据
            session.execute(
                text("DELETE FROM prices WHERE asset_id = :asset_id"),
                {"asset_id": asset_id}
            )
            
            session.execute(
                text("DELETE FROM assets WHERE asset_id = :asset_id"),
                {"asset_id": asset_id}
            )
            
            # 回滚会话，确保不影响实际数据
            raise Exception("测试完成，回滚事务")
    except Exception as e:
        if "测试完成，回滚事务" in str(e):
            logger.info("批量查询测试完成")
            return {
                "records": len(records),
                "total_time": elapsed_time,
                "avg_time_ms": (elapsed_time / len(records)) * 1000,
                "complex_query_time": complex_elapsed_time,
                "complex_records": len(complex_records)
            }
        else:
            logger.error(f"批量查询测试失败: {e}")
            return False
    finally:
        # 关闭会话
        session.close()

def run_performance_tests():
    """运行性能测试"""
    # 获取数据库引擎
    postgres_engine = get_postgres_engine()
    sqlite_engine = get_sqlite_engine()
    
    if postgres_engine is None:
        logger.error("无法创建 PostgreSQL 数据库引擎")
        return False
    
    # 测试批量插入
    logger.info("\n" + "="*50 + "\n测试 PostgreSQL 批量插入性能\n" + "="*50)
    pg_insert_result = test_bulk_insert(postgres_engine, num_records=100)
    
    if sqlite_engine is not None:
        logger.info("\n" + "="*50 + "\n测试 SQLite 批量插入性能\n" + "="*50)
        sqlite_insert_result = test_bulk_insert(sqlite_engine, num_records=100)
    else:
        logger.warning("SQLite 数据库引擎不可用，跳过 SQLite 测试")
        sqlite_insert_result = None
    
    # 测试批量查询
    logger.info("\n" + "="*50 + "\n测试 PostgreSQL 批量查询性能\n" + "="*50)
    pg_query_result = test_bulk_query(postgres_engine, num_records=100)
    
    if sqlite_engine is not None:
        logger.info("\n" + "="*50 + "\n测试 SQLite 批量查询性能\n" + "="*50)
        sqlite_query_result = test_bulk_query(sqlite_engine, num_records=100)
    else:
        logger.warning("SQLite 数据库引擎不可用，跳过 SQLite 测试")
        sqlite_query_result = None
    
    # 打印性能对比结果
    logger.info("\n\n性能测试结果对比:")
    logger.info("=" * 50)
    
    if pg_insert_result and sqlite_insert_result:
        logger.info("批量插入性能对比:")
        logger.info(f"PostgreSQL: {pg_insert_result['avg_time_ms']:.4f} 毫秒/记录")
        logger.info(f"SQLite: {sqlite_insert_result['avg_time_ms']:.4f} 毫秒/记录")
        logger.info(f"性能比: {sqlite_insert_result['avg_time_ms'] / pg_insert_result['avg_time_ms']:.2f}x")
    
    if pg_query_result and sqlite_query_result:
        logger.info("\n批量查询性能对比:")
        logger.info(f"PostgreSQL: {pg_query_result['avg_time_ms']:.4f} 毫秒/记录")
        logger.info(f"SQLite: {sqlite_query_result['avg_time_ms']:.4f} 毫秒/记录")
        logger.info(f"性能比: {sqlite_query_result['avg_time_ms'] / pg_query_result['avg_time_ms']:.2f}x")
        
        logger.info("\n复杂查询性能对比:")
        logger.info(f"PostgreSQL: {pg_query_result['complex_query_time']:.4f} 秒")
        logger.info(f"SQLite: {sqlite_query_result['complex_query_time']:.4f} 秒")
        logger.info(f"性能比: {sqlite_query_result['complex_query_time'] / pg_query_result['complex_query_time']:.2f}x")
    
    logger.info("=" * 50)
    
    return True

if __name__ == "__main__":
    logger.info("开始 Supabase PostgreSQL 数据库性能测试")
    success = run_performance_tests()
    if success:
        logger.info("性能测试完成")
        sys.exit(0)
    else:
        logger.error("性能测试失败")
        sys.exit(1)
