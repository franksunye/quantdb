"""
Supabase 设置脚本

此脚本用于设置 Supabase 项目，包括创建数据库表、设置 RLS 策略等。
"""

import os
import sys
import logging
import requests
from dotenv import load_dotenv

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("supabase_setup")

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 从 .env 文件加载环境变量
load_dotenv()

def check_env_variables():
    """检查必要的环境变量是否存在"""
    required_vars = ['SUPABASE_URL', 'SUPABASE_KEY', 'SUPABASE_SERVICE_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        logger.error(f"缺少以下环境变量: {', '.join(missing_vars)}")
        logger.error("请确保在 .env 文件中设置了这些变量，或者在环境中设置了这些变量。")
        return False

    logger.info("环境变量检查通过")
    return True

def test_supabase_connection():
    """测试 Supabase 连接"""
    try:
        # 获取 Supabase URL 和 API 密钥
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')

        logger.info(f"正在连接到 Supabase: {supabase_url}")

        # 测试 REST API 连接
        headers = {
            "apikey": supabase_key,
            "Content-Type": "application/json"
        }

        # 尝试获取健康状态
        response = requests.get(
            f"{supabase_url}/rest/v1/",
            headers=headers
        )

        if response.status_code == 200:
            logger.info("Supabase 连接成功")
            return True
        else:
            logger.error(f"Supabase 连接失败: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"Supabase 连接测试失败: {e}")
        return False

def execute_sql_script():
    """执行 SQL 脚本"""
    try:
        # 获取 Supabase URL 和 API 密钥
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_service_key = os.getenv('SUPABASE_SERVICE_KEY')

        # 读取 SQL 脚本
        script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'supabase_schema.sql')
        with open(script_path, 'r') as f:
            sql_script = f.read()

        logger.info("正在准备执行 SQL 脚本...")

        # 由于Supabase REST API不直接支持执行SQL脚本，我们需要使用SQL编辑器
        logger.info("Supabase REST API不直接支持执行SQL脚本")
        logger.info("请按照以下步骤手动设置 Supabase:")
        logger.info("1. 登录 Supabase 控制台: https://app.supabase.com")
        logger.info("2. 选择您的项目")
        logger.info("3. 点击 'SQL 编辑器'")
        logger.info("4. 创建新查询")
        logger.info("5. 复制以下SQL脚本并粘贴到查询编辑器中:")
        logger.info("-" * 50)
        logger.info(sql_script[:200] + "..." if len(sql_script) > 200 else sql_script)
        logger.info("-" * 50)
        logger.info("6. 执行查询")

        # 尝试检查表是否已存在，作为验证
        headers = {
            "apikey": supabase_service_key,
            "Authorization": f"Bearer {supabase_service_key}",
            "Content-Type": "application/json"
        }

        # 尝试获取表信息
        response = requests.get(
            f"{supabase_url}/rest/v1/",
            headers=headers
        )

        if response.status_code == 200:
            logger.info("Supabase API 连接成功，请手动执行SQL脚本")
            return False  # 返回False以便显示手动执行的说明
        else:
            logger.error(f"Supabase API 连接失败: {response.status_code} - {response.text}")
            logger.info("请手动在 Supabase SQL 编辑器中执行脚本")
            return False
    except Exception as e:
        logger.error(f"执行 SQL 脚本失败: {e}")
        logger.info("请手动在 Supabase SQL 编辑器中执行脚本")
        return False

def main():
    """主函数"""
    logger.info("开始设置 Supabase...")

    # 打印环境变量（隐藏敏感信息）
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    supabase_service_key = os.getenv('SUPABASE_SERVICE_KEY')

    logger.info(f"SUPABASE_URL: {supabase_url}")
    logger.info(f"SUPABASE_KEY: {'已设置' if supabase_key else '未设置'}")
    logger.info(f"SUPABASE_SERVICE_KEY: {'已设置' if supabase_service_key else '未设置'}")

    # 检查环境变量
    if not check_env_variables():
        return False

    # 测试连接
    if not test_supabase_connection():
        return False

    # 检查SQL脚本文件是否存在
    script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'supabase_schema.sql')
    if not os.path.exists(script_path):
        logger.error(f"SQL脚本文件不存在: {script_path}")
        return False

    logger.info(f"SQL脚本文件存在: {script_path}")

    # 执行 SQL 脚本
    if not execute_sql_script():
        logger.info("请按照以下步骤手动设置 Supabase:")
        logger.info("1. 登录 Supabase 控制台: https://app.supabase.com")
        logger.info("2. 选择您的项目")
        logger.info("3. 点击 'SQL 编辑器'")
        logger.info("4. 创建新查询")
        logger.info("5. 复制 database/supabase_schema.sql 文件中的内容")
        logger.info("6. 执行查询")
        return False

    logger.info("Supabase 设置完成")
    return True

if __name__ == "__main__":
    success = main()
    if success:
        sys.exit(0)
    else:
        sys.exit(1)
