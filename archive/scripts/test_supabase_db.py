"""
简单的Supabase数据库连接测试脚本
"""

import os
import sys
import logging
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, inspect

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("supabase_simple_test")

# 从.env文件加载环境变量
load_dotenv()

def test_connection():
    """测试数据库连接"""
    try:
        # 获取数据库URL
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            logger.error("未找到DATABASE_URL环境变量")
            return False
        
        # 打印数据库URL（隐藏密码）
        if '@' in database_url:
            parts = database_url.split('@')
            masked_url = f"{parts[0].split(':')[0]}:***@{parts[1]}"
        else:
            masked_url = database_url
        
        logger.info(f"连接到数据库: {masked_url}")
        
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
            
            logger.info("数据库连接测试成功")
            return True
    except Exception as e:
        logger.error(f"数据库连接测试失败: {e}")
        return False

if __name__ == "__main__":
    logger.info("开始Supabase数据库连接测试")
    success = test_connection()
    if success:
        logger.info("测试成功！Supabase数据库连接正常")
        sys.exit(0)
    else:
        logger.error("测试失败。请检查日志获取详细信息")
        sys.exit(1)
