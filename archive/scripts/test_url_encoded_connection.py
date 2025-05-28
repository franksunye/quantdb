"""
测试使用 URL 编码的密码连接 Supabase PostgreSQL 数据库

此脚本用于测试使用 URL 编码的密码连接 Supabase PostgreSQL 数据库，以解决编码问题。
"""

import os
import sys
import logging
import traceback
import urllib.parse
from datetime import date
from dotenv import load_dotenv

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("url_encoded_connection_test")

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 从 .env 文件加载环境变量
load_dotenv()

def test_sqlalchemy_url_encoded():
    """测试使用 URL 编码的密码通过 SQLAlchemy 连接"""
    try:
        from sqlalchemy import create_engine, text
        
        # 获取数据库连接参数
        db_host = "db.dvusiqfijdmjcsubyapw.supabase.co"
        db_port = 5432
        db_name = "postgres"
        db_user = "postgres"
        db_password = os.getenv('SUPABASE_DB_PASSWORD')
        
        if not db_password:
            logger.error("未找到 SUPABASE_DB_PASSWORD 环境变量")
            return False
        
        # URL 编码密码
        encoded_password = urllib.parse.quote_plus(db_password)
        
        # 构建数据库 URL
        database_url = f"postgresql://{db_user}:{encoded_password}@{db_host}:{db_port}/{db_name}"
        
        logger.info(f"使用 URL 编码的密码通过 SQLAlchemy 连接到数据库: {db_host}:{db_port}/{db_name} (用户: {db_user})")
        
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
            
            logger.info("SQLAlchemy URL 编码连接测试成功")
            return True
    except Exception as e:
        logger.error(f"SQLAlchemy URL 编码连接测试失败: {e}")
        logger.error(traceback.format_exc())
        return False

def test_psycopg2_url_encoded():
    """测试使用 URL 编码的密码通过 psycopg2 连接"""
    try:
        import psycopg2
        
        # 获取数据库连接参数
        db_host = "db.dvusiqfijdmjcsubyapw.supabase.co"
        db_port = 5432
        db_name = "postgres"
        db_user = "postgres"
        db_password = os.getenv('SUPABASE_DB_PASSWORD')
        
        if not db_password:
            logger.error("未找到 SUPABASE_DB_PASSWORD 环境变量")
            return False
        
        # URL 编码密码
        encoded_password = urllib.parse.quote_plus(db_password)
        
        logger.info(f"使用 URL 编码的密码通过 psycopg2 连接到数据库: {db_host}:{db_port}/{db_name} (用户: {db_user})")
        
        # 构建连接字符串
        dsn = f"dbname={db_name} user={db_user} password={encoded_password} host={db_host} port={db_port}"
        
        # 连接到数据库
        conn = psycopg2.connect(dsn)
        
        # 测试连接
        cur = conn.cursor()
        cur.execute("SELECT version()")
        version = cur.fetchone()
        
        logger.info(f"PostgreSQL 版本: {version[0]}")
        
        # 关闭连接
        cur.close()
        conn.close()
        
        logger.info("psycopg2 URL 编码连接测试成功")
        return True
    except Exception as e:
        logger.error(f"psycopg2 URL 编码连接测试失败: {e}")
        logger.error(traceback.format_exc())
        return False

def test_psycopg2_direct_params():
    """测试使用直接参数通过 psycopg2 连接"""
    try:
        import psycopg2
        
        # 获取数据库连接参数
        db_host = "db.dvusiqfijdmjcsubyapw.supabase.co"
        db_port = 5432
        db_name = "postgres"
        db_user = "postgres"
        db_password = os.getenv('SUPABASE_DB_PASSWORD')
        
        if not db_password:
            logger.error("未找到 SUPABASE_DB_PASSWORD 环境变量")
            return False
        
        logger.info(f"使用直接参数通过 psycopg2 连接到数据库: {db_host}:{db_port}/{db_name} (用户: {db_user})")
        
        # 连接到数据库
        conn = psycopg2.connect(
            dbname=db_name,
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port
        )
        
        # 测试连接
        cur = conn.cursor()
        cur.execute("SELECT version()")
        version = cur.fetchone()
        
        logger.info(f"PostgreSQL 版本: {version[0]}")
        
        # 关闭连接
        cur.close()
        conn.close()
        
        logger.info("psycopg2 直接参数连接测试成功")
        return True
    except Exception as e:
        logger.error(f"psycopg2 直接参数连接测试失败: {e}")
        logger.error(traceback.format_exc())
        return False

def test_chinese_data_url_encoded():
    """测试使用 URL 编码的密码处理中文数据"""
    try:
        import psycopg2
        
        # 获取数据库连接参数
        db_host = "db.dvusiqfijdmjcsubyapw.supabase.co"
        db_port = 5432
        db_name = "postgres"
        db_user = "postgres"
        db_password = os.getenv('SUPABASE_DB_PASSWORD')
        
        if not db_password:
            logger.error("未找到 SUPABASE_DB_PASSWORD 环境变量")
            return False
        
        # URL 编码密码
        encoded_password = urllib.parse.quote_plus(db_password)
        
        logger.info(f"测试使用 URL 编码的密码处理中文数据...")
        
        # 构建连接字符串
        dsn = f"dbname={db_name} user={db_user} password={encoded_password} host={db_host} port={db_port}"
        
        # 连接到数据库
        conn = psycopg2.connect(dsn)
        
        # 设置客户端编码
        conn.set_client_encoding('UTF8')
        
        # 开始事务
        conn.autocommit = False
        cursor = conn.cursor()
        
        # 创建临时表
        cursor.execute("""
        CREATE TEMPORARY TABLE chinese_test_encoded (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100),
            description TEXT
        )
        """)
        
        # 插入中文数据
        chinese_name = "测试资产"
        chinese_description = "这是一个包含中文字符的测试描述，用于测试 URL 编码密码对中文的支持。"
        
        cursor.execute(
            "INSERT INTO chinese_test_encoded (name, description) VALUES (%s, %s) RETURNING id",
            (chinese_name, chinese_description)
        )
        
        # 获取插入的 ID
        row_id = cursor.fetchone()[0]
        logger.info(f"插入中文数据，ID: {row_id}")
        
        # 查询插入的数据
        cursor.execute("SELECT name, description FROM chinese_test_encoded WHERE id = %s", (row_id,))
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
        
        logger.info("URL 编码密码中文数据处理测试完成")
        return True
    except Exception as e:
        logger.error(f"URL 编码密码中文数据处理测试失败: {e}")
        logger.error(traceback.format_exc())
        return False

def run_all_tests():
    """运行所有测试"""
    tests = [
        ("SQLAlchemy URL 编码连接测试", test_sqlalchemy_url_encoded),
        ("psycopg2 URL 编码连接测试", test_psycopg2_url_encoded),
        ("psycopg2 直接参数连接测试", test_psycopg2_direct_params),
        ("URL 编码密码中文数据处理测试", test_chinese_data_url_encoded)
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
        logger.info("所有测试通过！URL 编码密码连接测试成功。")
    else:
        logger.error("部分测试失败。请检查日志获取详细信息。")
    
    return all_passed

if __name__ == "__main__":
    logger.info("开始测试使用 URL 编码的密码连接 Supabase PostgreSQL 数据库")
    success = run_all_tests()
    if success:
        logger.info("测试成功！可以使用 URL 编码的密码连接 Supabase PostgreSQL 数据库")
        sys.exit(0)
    else:
        logger.error("测试失败。请检查日志获取详细信息")
        sys.exit(1)
