"""
测试 Supabase API 的脚本

此脚本用于测试 Supabase API 的功能，包括认证、数据访问和行级安全策略。
"""

import os
import sys
import logging
import json
from datetime import date
import requests
from dotenv import load_dotenv

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("supabase_api_test")

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# 从 .env 文件加载环境变量
load_dotenv()

def test_supabase_api_connection():
    """测试 Supabase API 连接"""
    try:
        # 获取 Supabase URL 和 API 密钥
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')
        
        if not supabase_url or not supabase_key:
            logger.error("未找到 SUPABASE_URL 或 SUPABASE_KEY 环境变量")
            return False
        
        logger.info(f"正在连接到 Supabase API: {supabase_url}")
        
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
            logger.info("Supabase API 连接成功")
            return True
        else:
            logger.error(f"Supabase API 连接失败: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"Supabase API 连接测试失败: {e}")
        return False

def test_supabase_data_access():
    """测试 Supabase 数据访问"""
    try:
        # 获取 Supabase URL 和 API 密钥
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')
        
        if not supabase_url or not supabase_key:
            logger.error("未找到 SUPABASE_URL 或 SUPABASE_KEY 环境变量")
            return False
        
        # 设置 API 请求头
        headers = {
            "apikey": supabase_key,
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }
        
        # 测试插入数据
        test_asset = {
            "symbol": "TEST002",
            "name": "Test Asset API",
            "asset_type": "STOCK",
            "exchange": "TEST",
            "currency": "USD"
        }
        
        insert_response = requests.post(
            f"{supabase_url}/rest/v1/assets",
            headers=headers,
            json=test_asset
        )
        
        if insert_response.status_code not in (201, 200):
            logger.error(f"插入数据失败: {insert_response.status_code} - {insert_response.text}")
            return False
        
        inserted_asset = insert_response.json()[0] if isinstance(insert_response.json(), list) else insert_response.json()
        asset_id = inserted_asset.get("asset_id")
        logger.info(f"成功插入资产，ID: {asset_id}")
        
        # 测试查询数据
        query_response = requests.get(
            f"{supabase_url}/rest/v1/assets?asset_id=eq.{asset_id}",
            headers=headers
        )
        
        if query_response.status_code != 200:
            logger.error(f"查询数据失败: {query_response.status_code} - {query_response.text}")
            # 清理插入的测试数据
            delete_response = requests.delete(
                f"{supabase_url}/rest/v1/assets?asset_id=eq.{asset_id}",
                headers=headers
            )
            return False
        
        queried_asset = query_response.json()[0] if query_response.json() else None
        if not queried_asset or queried_asset.get("asset_id") != asset_id:
            logger.error(f"查询结果不匹配: {queried_asset}")
            # 清理插入的测试数据
            delete_response = requests.delete(
                f"{supabase_url}/rest/v1/assets?asset_id=eq.{asset_id}",
                headers=headers
            )
            return False
        
        logger.info(f"成功查询资产: {queried_asset}")
        
        # 测试更新数据
        update_data = {"name": "Updated Test Asset API"}
        update_response = requests.patch(
            f"{supabase_url}/rest/v1/assets?asset_id=eq.{asset_id}",
            headers=headers,
            json=update_data
        )
        
        if update_response.status_code != 204:
            logger.error(f"更新数据失败: {update_response.status_code} - {update_response.text}")
            # 清理插入的测试数据
            delete_response = requests.delete(
                f"{supabase_url}/rest/v1/assets?asset_id=eq.{asset_id}",
                headers=headers
            )
            return False
        
        # 验证更新
        query_updated_response = requests.get(
            f"{supabase_url}/rest/v1/assets?asset_id=eq.{asset_id}",
            headers=headers
        )
        
        updated_asset = query_updated_response.json()[0] if query_updated_response.json() else None
        if not updated_asset or updated_asset.get("name") != "Updated Test Asset API":
            logger.error(f"更新结果不匹配: {updated_asset}")
            # 清理插入的测试数据
            delete_response = requests.delete(
                f"{supabase_url}/rest/v1/assets?asset_id=eq.{asset_id}",
                headers=headers
            )
            return False
        
        logger.info(f"成功更新资产: {updated_asset}")
        
        # 测试删除数据
        delete_response = requests.delete(
            f"{supabase_url}/rest/v1/assets?asset_id=eq.{asset_id}",
            headers=headers
        )
        
        if delete_response.status_code != 204:
            logger.error(f"删除数据失败: {delete_response.status_code} - {delete_response.text}")
            return False
        
        # 验证删除
        query_deleted_response = requests.get(
            f"{supabase_url}/rest/v1/assets?asset_id=eq.{asset_id}",
            headers=headers
        )
        
        if query_deleted_response.json():
            logger.error(f"删除验证失败，资产仍然存在: {query_deleted_response.json()}")
            return False
        
        logger.info("成功删除资产")
        logger.info("数据访问测试成功")
        return True
    except Exception as e:
        logger.error(f"数据访问测试失败: {e}")
        return False

def test_row_level_security_policies():
    """测试行级安全策略"""
    try:
        # 获取 Supabase URL 和 API 密钥
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')  # 这是 anon 密钥
        supabase_service_key = os.getenv('SUPABASE_SERVICE_KEY')  # 这是 service_role 密钥
        
        if not supabase_url or not supabase_key or not supabase_service_key:
            logger.error("未找到必要的 Supabase 环境变量")
            return False
        
        # 使用 service_role 密钥插入测试数据
        service_headers = {
            "apikey": supabase_service_key,
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }
        
        test_asset = {
            "symbol": "TEST003",
            "name": "Test RLS Asset",
            "asset_type": "STOCK",
            "exchange": "TEST",
            "currency": "USD"
        }
        
        # 插入测试资产
        insert_response = requests.post(
            f"{supabase_url}/rest/v1/assets",
            headers=service_headers,
            json=test_asset
        )
        
        if insert_response.status_code not in (201, 200):
            logger.error(f"插入测试数据失败: {insert_response.status_code} - {insert_response.text}")
            return False
        
        inserted_asset = insert_response.json()[0] if isinstance(insert_response.json(), list) else insert_response.json()
        asset_id = inserted_asset.get("asset_id")
        logger.info(f"成功插入测试资产，ID: {asset_id}")
        
        # 使用 anon 密钥尝试读取数据（应该成功，因为我们设置了公共读取策略）
        anon_headers = {
            "apikey": supabase_key,
            "Content-Type": "application/json"
        }
        
        read_response = requests.get(
            f"{supabase_url}/rest/v1/assets?asset_id=eq.{asset_id}",
            headers=anon_headers
        )
        
        if read_response.status_code != 200 or not read_response.json():
            logger.error(f"使用 anon 密钥读取数据失败: {read_response.status_code} - {read_response.text}")
            # 清理测试数据
            delete_response = requests.delete(
                f"{supabase_url}/rest/v1/assets?asset_id=eq.{asset_id}",
                headers=service_headers
            )
            return False
        
        logger.info("使用 anon 密钥成功读取数据")
        
        # 使用 anon 密钥尝试更新数据（应该失败，因为我们只允许管理员更新）
        update_data = {"name": "Updated RLS Test"}
        update_response = requests.patch(
            f"{supabase_url}/rest/v1/assets?asset_id=eq.{asset_id}",
            headers=anon_headers,
            json=update_data
        )
        
        # 应该返回 401 或 403 错误
        if update_response.status_code not in (401, 403, 404):
            logger.error(f"使用 anon 密钥更新数据应该失败，但返回了: {update_response.status_code} - {update_response.text}")
            # 清理测试数据
            delete_response = requests.delete(
                f"{supabase_url}/rest/v1/assets?asset_id=eq.{asset_id}",
                headers=service_headers
            )
            return False
        
        logger.info("使用 anon 密钥更新数据正确地被拒绝")
        
        # 使用 service_role 密钥清理测试数据
        delete_response = requests.delete(
            f"{supabase_url}/rest/v1/assets?asset_id=eq.{asset_id}",
            headers=service_headers
        )
        
        if delete_response.status_code != 204:
            logger.error(f"清理测试数据失败: {delete_response.status_code} - {delete_response.text}")
            return False
        
        logger.info("行级安全策略测试成功")
        return True
    except Exception as e:
        logger.error(f"行级安全策略测试失败: {e}")
        return False

def run_all_tests():
    """运行所有测试"""
    tests = [
        ("Supabase API 连接测试", test_supabase_api_connection),
        ("Supabase 数据访问测试", test_supabase_data_access),
        ("行级安全策略测试", test_row_level_security_policies)
    ]
    
    results = []
    for name, test_func in tests:
        logger.info(f"开始 {name}")
        result = test_func()
        results.append((name, result))
        logger.info(f"完成 {name}: {'成功' if result else '失败'}")
    
    # 打印测试结果摘要
    logger.info("\n测试结果摘要:")
    all_passed = True
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        logger.info(f"{status} - {name}")
        if not result:
            all_passed = False
    
    return all_passed

if __name__ == "__main__":
    logger.info("开始 Supabase API 测试")
    success = run_all_tests()
    if success:
        logger.info("所有测试通过！Supabase API 功能正常。")
        sys.exit(0)
    else:
        logger.error("部分测试失败。请检查日志获取详细信息。")
        sys.exit(1)
