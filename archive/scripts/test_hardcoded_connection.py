"""
测试使用硬编码参数连接 Supabase PostgreSQL 数据库

此脚本用于测试使用硬编码参数连接 Supabase PostgreSQL 数据库，以解决编码问题。
"""

import sys
import logging
import traceback
from datetime import date

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("hardcoded_connection_test")

# 硬编码的数据库连接参数
DB_HOST = "db.dvusiqfijdmjcsubyapw.supabase.co"
DB_PORT = 5432
DB_NAME = "postgres"
DB_USER = "postgres"
DB_PASSWORD = "sd4UI5aiKpDn5Vd2"  # 直接使用密码，避免从环境变量读取

def test_psycopg2_hardcoded():
    """测试使用硬编码参数通过 psycopg2 连接"""
    try:
        import psycopg2
        
        logger.info(f"使用硬编码参数通过 psycopg2 连接到数据库: {DB_HOST}:{DB_PORT}/{DB_NAME} (用户: {DB_USER})")
        
        # 连接到数据库
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
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
        
        logger.info("psycopg2 硬编码参数连接测试成功")
        return True
    except Exception as e:
        logger.error(f"psycopg2 硬编码参数连接测试失败: {e}")
        logger.error(traceback.format_exc())
        return False

def test_sqlalchemy_hardcoded():
    """测试使用硬编码参数通过 SQLAlchemy 连接"""
    try:
        from sqlalchemy import create_engine, text
        
        # 构建数据库 URL
        database_url = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        
        logger.info(f"使用硬编码参数通过 SQLAlchemy 连接到数据库: {DB_HOST}:{DB_PORT}/{DB_NAME} (用户: {DB_USER})")
        
        # 创建数据库引擎
        engine = create_engine(database_url)
        
        # 测试连接
        with engine.connect() as conn:
            # 执行简单查询
            result = conn.execute(text("SELECT 1"))
            logger.info(f"查询结果: {result.scalar()}")
            
            # 获取版本信息
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            logger.info(f"PostgreSQL 版本: {version}")
            
            logger.info("SQLAlchemy 硬编码参数连接测试成功")
            return True
    except Exception as e:
        logger.error(f"SQLAlchemy 硬编码参数连接测试失败: {e}")
        logger.error(traceback.format_exc())
        return False

def test_pg8000_hardcoded():
    """测试使用硬编码参数通过 pg8000 连接"""
    try:
        import pg8000
        
        logger.info(f"使用硬编码参数通过 pg8000 连接到数据库: {DB_HOST}:{DB_PORT}/{DB_NAME} (用户: {DB_USER})")
        
        # 连接到数据库
        conn = pg8000.connect(
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        
        # 测试连接
        cursor = conn.cursor()
        cursor.execute("SELECT version()")
        version = cursor.fetchone()
        
        logger.info(f"PostgreSQL 版本: {version[0]}")
        
        # 获取表列表
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        tables = [row[0] for row in cursor.fetchall()]
        
        logger.info(f"数据库中的表: {tables}")
        
        # 关闭连接
        cursor.close()
        conn.close()
        
        logger.info("pg8000 硬编码参数连接测试成功")
        return True
    except Exception as e:
        logger.error(f"pg8000 硬编码参数连接测试失败: {e}")
        logger.error(traceback.format_exc())
        return False

def test_chinese_data_hardcoded():
    """测试使用硬编码参数处理中文数据"""
    try:
        import psycopg2
        
        logger.info(f"测试使用硬编码参数处理中文数据...")
        
        # 连接到数据库
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        
        # 设置客户端编码
        conn.set_client_encoding('UTF8')
        
        # 开始事务
        conn.autocommit = False
        cursor = conn.cursor()
        
        # 创建临时表
        cursor.execute("""
        CREATE TEMPORARY TABLE chinese_test_hardcoded (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100),
            description TEXT
        )
        """)
        
        # 插入中文数据
        chinese_name = "测试资产"
        chinese_description = "这是一个包含中文字符的测试描述，用于测试硬编码参数对中文的支持。"
        
        cursor.execute(
            "INSERT INTO chinese_test_hardcoded (name, description) VALUES (%s, %s) RETURNING id",
            (chinese_name, chinese_description)
        )
        
        # 获取插入的 ID
        row_id = cursor.fetchone()[0]
        logger.info(f"插入中文数据，ID: {row_id}")
        
        # 查询插入的数据
        cursor.execute("SELECT name, description FROM chinese_test_hardcoded WHERE id = %s", (row_id,))
        result = cursor.fetchone()
        
        retrieved_name, retrieved_description = result
        
        logger.info(f"查询结果 - 名称: {retrieved_name}")
        logger.info(f"查询结果 - 描述: {retrieved_description}")
        
        # 验证数据完整性
        if retrieved_name == chinese_name and retrieved_description == chinese_description:
            logger.info("中文数据完整性验证通过")
        else:
            logger.error("中文数据完整性验证失败")
            logger.error(f"原始名称: {chinese_name}")
            logger.error(f"检索名称: {retrieved_name}")
            logger.error(f"原始描述: {chinese_description}")
            logger.error(f"检索描述: {retrieved_description}")
            
            # 打印字符编码信息
            logger.info(f"原始名称编码: {[ord(c) for c in chinese_name]}")
            logger.info(f"检索名称编码: {[ord(c) for c in retrieved_name]}")
        
        # 回滚事务
        conn.rollback()
        
        # 关闭连接
        cursor.close()
        conn.close()
        
        logger.info("硬编码参数中文数据处理测试完成")
        return True
    except Exception as e:
        logger.error(f"硬编码参数中文数据处理测试失败: {e}")
        logger.error(traceback.format_exc())
        return False

def run_all_tests():
    """运行所有测试"""
    tests = [
        ("psycopg2 硬编码参数连接测试", test_psycopg2_hardcoded),
        ("SQLAlchemy 硬编码参数连接测试", test_sqlalchemy_hardcoded),
        ("pg8000 硬编码参数连接测试", test_pg8000_hardcoded),
        ("硬编码参数中文数据处理测试", test_chinese_data_hardcoded)
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
        logger.info("所有测试通过！硬编码参数连接测试成功。")
    else:
        logger.error("部分测试失败。请检查日志获取详细信息。")
    
    return all_passed

if __name__ == "__main__":
    logger.info("开始测试使用硬编码参数连接 Supabase PostgreSQL 数据库")
    success = run_all_tests()
    if success:
        logger.info("测试成功！可以使用硬编码参数连接 Supabase PostgreSQL 数据库")
        sys.exit(0)
    else:
        logger.error("测试失败。请检查日志获取详细信息")
        sys.exit(1)
