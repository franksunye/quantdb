"""
运行 Supabase 部署测试的主脚本

此脚本用于运行所有 Supabase 部署相关的测试，包括连接测试、API 测试和数据迁移测试。
"""

import os
import sys
import logging
import importlib
import argparse
from datetime import datetime

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"supabase_tests_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)
logger = logging.getLogger("supabase_tests")

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

def check_env_variables():
    """检查必要的环境变量是否存在"""
    required_vars = ['DATABASE_URL', 'SUPABASE_URL', 'SUPABASE_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"缺少以下环境变量: {', '.join(missing_vars)}")
        logger.error("请确保在 .env 文件中设置了这些变量，或者在环境中设置了这些变量。")
        return False
    
    logger.info("环境变量检查通过")
    return True

def run_test_module(module_name):
    """运行指定的测试模块"""
    try:
        logger.info(f"开始运行测试模块: {module_name}")
        
        # 导入测试模块
        module = importlib.import_module(f"tests.deployment.{module_name}")
        
        # 运行测试
        if hasattr(module, 'run_all_tests'):
            success = module.run_all_tests()
        elif hasattr(module, 'run_migration_test'):
            success = module.run_migration_test()
        else:
            logger.error(f"模块 {module_name} 没有可运行的测试函数")
            return False
        
        if success:
            logger.info(f"测试模块 {module_name} 运行成功")
        else:
            logger.error(f"测试模块 {module_name} 运行失败")
        
        return success
    except Exception as e:
        logger.error(f"运行测试模块 {module_name} 时出错: {e}")
        return False

def run_all_tests():
    """运行所有测试"""
    # 检查环境变量
    if not check_env_variables():
        return False
    
    # 定义测试模块
    test_modules = [
        "test_supabase_connection",
        "test_supabase_api",
        "test_data_migration"
    ]
    
    # 运行测试
    results = []
    for module in test_modules:
        logger.info(f"\n{'='*50}\n运行测试模块: {module}\n{'='*50}")
        success = run_test_module(module)
        results.append((module, success))
    
    # 打印测试结果摘要
    logger.info("\n\n测试结果摘要:")
    logger.info("=" * 50)
    all_passed = True
    for module, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        logger.info(f"{status} - {module}")
        if not result:
            all_passed = False
    
    logger.info("=" * 50)
    if all_passed:
        logger.info("所有测试通过！Supabase 部署测试成功。")
    else:
        logger.error("部分测试失败。请检查日志获取详细信息。")
    
    return all_passed

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='运行 Supabase 部署测试')
    parser.add_argument('--module', type=str, help='要运行的特定测试模块')
    parser.add_argument('--list', action='store_true', help='列出可用的测试模块')
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_arguments()
    
    if args.list:
        logger.info("可用的测试模块:")
        logger.info("- test_supabase_connection: 测试与 Supabase 数据库的连接")
        logger.info("- test_supabase_api: 测试 Supabase API 功能")
        logger.info("- test_data_migration: 测试数据迁移功能")
        sys.exit(0)
    
    if args.module:
        logger.info(f"运行特定测试模块: {args.module}")
        success = run_test_module(args.module)
    else:
        logger.info("运行所有测试模块")
        success = run_all_tests()
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)
