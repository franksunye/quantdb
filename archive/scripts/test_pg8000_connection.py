"""
测试使用 pg8000 连接 Supabase PostgreSQL 数据库

pg8000 是一个纯 Python 实现的 PostgreSQL 驱动，可能对于中文编码问题有更好的支持。
此脚本用于测试使用 pg8000 连接 Supabase PostgreSQL 数据库，包括：
1. 基本连接测试
2. 中文数据处理测试
3. 与 psycopg2 的对比
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
logger = logging.getLogger("pg8000_test")

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 从 .env 文件加载环境变量
load_dotenv()

def parse_db_url(database_url):
    """解析数据库 URL"""
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
        
        return {
            'dbname': dbname,
            'user': user,
            'password': password,
            'host': host,
            'port': port
        }
    else:
        raise ValueError(f"不支持的数据库 URL 格式: {database_url}")

def test_pg8000_connection():
    """测试使用 pg8000 连接 Supabase PostgreSQL 数据库"""
    try:
        import pg8000
        
        # 获取数据库 URL
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            logger.error("未找到 DATABASE_URL 环境变量")
            return False
        
        # 解析数据库 URL
        try:
            db_params = parse_db_url(database_url)
            
            logger.info(f"使用 pg8000 连接到 PostgreSQL 数据库: {db_params['host']}:{db_params['port']}/{db_params['dbname']} (用户: {db_params['user']})")
            
            # 连接到数据库
            conn = pg8000.connect(
                database=db_params['dbname'],
                user=db_params['user'],
                password=db_params['password'],
                host=db_params['host'],
                port=db_params['port']
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
            
            logger.info("pg8000 连接测试成功")
            return True
        except Exception as e:
            logger.error(f"解析数据库 URL 或连接失败: {e}")
            logger.error(traceback.format_exc())
            return False
    except ImportError:
        logger.error("pg8000 未安装，请使用 pip install pg8000 安装")
        return False

def test_chinese_data():
    """测试中文数据处理"""
    try:
        import pg8000
        
        # 获取数据库 URL
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            logger.error("未找到 DATABASE_URL 环境变量")
            return False
        
        # 解析数据库 URL
        try:
            db_params = parse_db_url(database_url)
            
            logger.info(f"测试中文数据处理...")
            
            # 连接到数据库
            conn = pg8000.connect(
                database=db_params['dbname'],
                user=db_params['user'],
                password=db_params['password'],
                host=db_params['host'],
                port=db_params['port']
            )
            
            # 开始事务
            cursor = conn.cursor()
            
            # 创建临时表
            cursor.execute("""
            CREATE TEMPORARY TABLE chinese_test (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100),
                description TEXT
            )
            """)
            
            # 插入中文数据
            chinese_name = "测试资产"
            chinese_description = "这是一个包含中文字符的测试描述，用于测试 pg8000 对中文的支持。"
            
            cursor.execute(
                "INSERT INTO chinese_test (name, description) VALUES (%s, %s) RETURNING id",
                (chinese_name, chinese_description)
            )
            
            # 获取插入的 ID
            row_id = cursor.fetchone()[0]
            logger.info(f"插入中文数据，ID: {row_id}")
            
            # 查询插入的数据
            cursor.execute("SELECT name, description FROM chinese_test WHERE id = %s", (row_id,))
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
            
            logger.info("中文数据处理测试完成")
            return True
        except Exception as e:
            logger.error(f"中文数据处理测试失败: {e}")
            logger.error(traceback.format_exc())
            return False
    except ImportError:
        logger.error("pg8000 未安装，请使用 pip install pg8000 安装")
        return False

def test_psycopg2_chinese():
    """使用 psycopg2 测试中文数据处理"""
    try:
        import psycopg2
        
        # 获取数据库 URL
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            logger.error("未找到 DATABASE_URL 环境变量")
            return False
        
        # 解析数据库 URL
        try:
            db_params = parse_db_url(database_url)
            
            logger.info(f"使用 psycopg2 测试中文数据处理...")
            
            # 连接到数据库
            conn = psycopg2.connect(
                dbname=db_params['dbname'],
                user=db_params['user'],
                password=db_params['password'],
                host=db_params['host'],
                port=db_params['port']
            )
            
            # 开始事务
            conn.autocommit = False
            cursor = conn.cursor()
            
            # 创建临时表
            cursor.execute("""
            CREATE TEMPORARY TABLE chinese_test_psycopg2 (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100),
                description TEXT
            )
            """)
            
            # 插入中文数据
            chinese_name = "测试资产"
            chinese_description = "这是一个包含中文字符的测试描述，用于测试 psycopg2 对中文的支持。"
            
            cursor.execute(
                "INSERT INTO chinese_test_psycopg2 (name, description) VALUES (%s, %s) RETURNING id",
                (chinese_name, chinese_description)
            )
            
            # 获取插入的 ID
            row_id = cursor.fetchone()[0]
            logger.info(f"插入中文数据，ID: {row_id}")
            
            # 查询插入的数据
            cursor.execute("SELECT name, description FROM chinese_test_psycopg2 WHERE id = %s", (row_id,))
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
            
            logger.info("psycopg2 中文数据处理测试完成")
            return True
        except Exception as e:
            logger.error(f"psycopg2 中文数据处理测试失败: {e}")
            logger.error(traceback.format_exc())
            return False
    except ImportError:
        logger.error("psycopg2 未安装，请使用 pip install psycopg2 安装")
        return False

def run_all_tests():
    """运行所有测试"""
    tests = [
        ("pg8000 连接测试", test_pg8000_connection),
        ("pg8000 中文数据处理测试", test_chinese_data),
        ("psycopg2 中文数据处理测试", test_psycopg2_chinese)
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
        logger.info("所有测试通过！pg8000 连接测试成功。")
    else:
        logger.error("部分测试失败。请检查日志获取详细信息。")
    
    return all_passed

if __name__ == "__main__":
    logger.info("开始测试使用 pg8000 连接 Supabase PostgreSQL 数据库")
    success = run_all_tests()
    if success:
        logger.info("测试成功！可以使用 pg8000 连接 Supabase PostgreSQL 数据库")
        sys.exit(0)
    else:
        logger.error("测试失败。请检查日志获取详细信息")
        sys.exit(1)
