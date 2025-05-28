"""
测试使用 Supabase REST API 访问数据库

此脚本用于测试使用 Supabase REST API 访问数据库，避免直接连接 PostgreSQL 数据库。
"""

import os
import sys
import json
import logging
import requests
import traceback
from datetime import date
from dotenv import load_dotenv

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("supabase_rest_api_test")

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 从 .env 文件加载环境变量
load_dotenv()

def test_rest_api_connection():
    """测试 Supabase REST API 连接"""
    try:
        # 获取 Supabase URL 和 API 密钥
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')
        
        if not supabase_url or not supabase_key:
            logger.error("未找到 SUPABASE_URL 或 SUPABASE_KEY 环境变量")
            return False
        
        logger.info(f"测试 Supabase REST API 连接: {supabase_url}")
        
        # 设置请求头
        headers = {
            "apikey": supabase_key,
            "Content-Type": "application/json"
        }
        
        # 测试连接
        response = requests.get(
            f"{supabase_url}/rest/v1/",
            headers=headers
        )
        
        if response.status_code == 200:
            logger.info("Supabase REST API 连接成功")
            return True
        else:
            logger.error(f"Supabase REST API 连接失败: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"Supabase REST API 连接测试失败: {e}")
        logger.error(traceback.format_exc())
        return False

def test_rest_api_query():
    """测试 Supabase REST API 查询"""
    try:
        # 获取 Supabase URL 和 API 密钥
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')
        
        if not supabase_url or not supabase_key:
            logger.error("未找到 SUPABASE_URL 或 SUPABASE_KEY 环境变量")
            return False
        
        logger.info(f"测试 Supabase REST API 查询")
        
        # 设置请求头
        headers = {
            "apikey": supabase_key,
            "Content-Type": "application/json"
        }
        
        # 查询表列表
        response = requests.get(
            f"{supabase_url}/rest/v1/",
            headers=headers
        )
        
        if response.status_code == 200:
            logger.info(f"表列表: {response.text}")
        else:
            logger.error(f"查询表列表失败: {response.status_code} - {response.text}")
            return False
        
        # 查询 assets 表
        response = requests.get(
            f"{supabase_url}/rest/v1/assets?select=*&limit=5",
            headers=headers
        )
        
        if response.status_code == 200:
            assets = response.json()
            logger.info(f"查询 assets 表成功，返回 {len(assets)} 条记录")
            if assets:
                logger.info(f"第一条记录: {json.dumps(assets[0], ensure_ascii=False, indent=2)}")
        else:
            logger.error(f"查询 assets 表失败: {response.status_code} - {response.text}")
            return False
        
        logger.info("Supabase REST API 查询测试成功")
        return True
    except Exception as e:
        logger.error(f"Supabase REST API 查询测试失败: {e}")
        logger.error(traceback.format_exc())
        return False

def test_rest_api_insert():
    """测试 Supabase REST API 插入"""
    try:
        # 获取 Supabase URL 和 API 密钥
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_SERVICE_KEY')  # 使用 service_role 密钥
        
        if not supabase_url or not supabase_key:
            logger.error("未找到 SUPABASE_URL 或 SUPABASE_SERVICE_KEY 环境变量")
            return False
        
        logger.info(f"测试 Supabase REST API 插入")
        
        # 设置请求头
        headers = {
            "apikey": supabase_key,
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }
        
        # 创建测试资产
        test_asset = {
            "symbol": f"TEST{date.today().strftime('%Y%m%d')}",
            "name": "测试资产",
            "asset_type": "STOCK",
            "exchange": "TEST",
            "currency": "CNY",
            "isin": f"CN{date.today().strftime('%Y%m%d')}"
        }
        
        # 插入测试资产
        response = requests.post(
            f"{supabase_url}/rest/v1/assets",
            headers=headers,
            json=test_asset
        )
        
        if response.status_code in (200, 201):
            inserted_asset = response.json()[0] if isinstance(response.json(), list) else response.json()
            asset_id = inserted_asset.get("asset_id")
            logger.info(f"插入测试资产成功，ID: {asset_id}")
            
            # 创建测试价格
            test_price = {
                "asset_id": asset_id,
                "date": date.today().isoformat(),
                "open": 100.0,
                "high": 105.0,
                "low": 95.0,
                "close": 102.5,
                "volume": 1000,
                "adjusted_close": 102.5
            }
            
            # 插入测试价格
            response = requests.post(
                f"{supabase_url}/rest/v1/prices",
                headers=headers,
                json=test_price
            )
            
            if response.status_code in (200, 201):
                inserted_price = response.json()[0] if isinstance(response.json(), list) else response.json()
                price_id = inserted_price.get("price_id")
                logger.info(f"插入测试价格成功，ID: {price_id}")
                
                # 查询插入的资产
                response = requests.get(
                    f"{supabase_url}/rest/v1/assets?asset_id=eq.{asset_id}",
                    headers=headers
                )
                
                if response.status_code == 200:
                    assets = response.json()
                    logger.info(f"查询插入的资产成功: {json.dumps(assets[0], ensure_ascii=False, indent=2)}")
                else:
                    logger.error(f"查询插入的资产失败: {response.status_code} - {response.text}")
                
                # 查询插入的价格
                response = requests.get(
                    f"{supabase_url}/rest/v1/prices?price_id=eq.{price_id}",
                    headers=headers
                )
                
                if response.status_code == 200:
                    prices = response.json()
                    logger.info(f"查询插入的价格成功: {json.dumps(prices[0], ensure_ascii=False, indent=2)}")
                else:
                    logger.error(f"查询插入的价格失败: {response.status_code} - {response.text}")
                
                # 删除测试数据
                response = requests.delete(
                    f"{supabase_url}/rest/v1/prices?price_id=eq.{price_id}",
                    headers=headers
                )
                
                if response.status_code == 204:
                    logger.info(f"删除测试价格成功")
                else:
                    logger.error(f"删除测试价格失败: {response.status_code} - {response.text}")
                
                response = requests.delete(
                    f"{supabase_url}/rest/v1/assets?asset_id=eq.{asset_id}",
                    headers=headers
                )
                
                if response.status_code == 204:
                    logger.info(f"删除测试资产成功")
                else:
                    logger.error(f"删除测试资产失败: {response.status_code} - {response.text}")
                
                logger.info("Supabase REST API 插入测试成功")
                return True
            else:
                logger.error(f"插入测试价格失败: {response.status_code} - {response.text}")
                
                # 删除测试资产
                response = requests.delete(
                    f"{supabase_url}/rest/v1/assets?asset_id=eq.{asset_id}",
                    headers=headers
                )
                
                return False
        else:
            logger.error(f"插入测试资产失败: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"Supabase REST API 插入测试失败: {e}")
        logger.error(traceback.format_exc())
        return False

def test_rest_api_chinese():
    """测试 Supabase REST API 中文处理"""
    try:
        # 获取 Supabase URL 和 API 密钥
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_SERVICE_KEY')  # 使用 service_role 密钥
        
        if not supabase_url or not supabase_key:
            logger.error("未找到 SUPABASE_URL 或 SUPABASE_SERVICE_KEY 环境变量")
            return False
        
        logger.info(f"测试 Supabase REST API 中文处理")
        
        # 设置请求头
        headers = {
            "apikey": supabase_key,
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }
        
        # 创建测试资产（包含中文）
        test_asset = {
            "symbol": f"CN{date.today().strftime('%Y%m%d')}",
            "name": "中文测试资产",
            "asset_type": "STOCK",
            "exchange": "上海证券交易所",
            "currency": "CNY",
            "isin": f"CN{date.today().strftime('%Y%m%d')}"
        }
        
        # 插入测试资产
        response = requests.post(
            f"{supabase_url}/rest/v1/assets",
            headers=headers,
            json=test_asset
        )
        
        if response.status_code in (200, 201):
            inserted_asset = response.json()[0] if isinstance(response.json(), list) else response.json()
            asset_id = inserted_asset.get("asset_id")
            logger.info(f"插入中文测试资产成功，ID: {asset_id}")
            
            # 查询插入的资产
            response = requests.get(
                f"{supabase_url}/rest/v1/assets?asset_id=eq.{asset_id}",
                headers=headers
            )
            
            if response.status_code == 200:
                assets = response.json()
                retrieved_asset = assets[0]
                logger.info(f"查询中文测试资产成功: {json.dumps(retrieved_asset, ensure_ascii=False, indent=2)}")
                
                # 验证中文数据完整性
                if retrieved_asset.get("name") == test_asset["name"] and retrieved_asset.get("exchange") == test_asset["exchange"]:
                    logger.info("中文数据完整性验证通过")
                else:
                    logger.error("中文数据完整性验证失败")
                    logger.error(f"原始名称: {test_asset['name']}")
                    logger.error(f"检索名称: {retrieved_asset.get('name')}")
                    logger.error(f"原始交易所: {test_asset['exchange']}")
                    logger.error(f"检索交易所: {retrieved_asset.get('exchange')}")
            else:
                logger.error(f"查询中文测试资产失败: {response.status_code} - {response.text}")
            
            # 删除测试资产
            response = requests.delete(
                f"{supabase_url}/rest/v1/assets?asset_id=eq.{asset_id}",
                headers=headers
            )
            
            if response.status_code == 204:
                logger.info(f"删除中文测试资产成功")
            else:
                logger.error(f"删除中文测试资产失败: {response.status_code} - {response.text}")
            
            logger.info("Supabase REST API 中文处理测试成功")
            return True
        else:
            logger.error(f"插入中文测试资产失败: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"Supabase REST API 中文处理测试失败: {e}")
        logger.error(traceback.format_exc())
        return False

def run_all_tests():
    """运行所有测试"""
    tests = [
        ("Supabase REST API 连接测试", test_rest_api_connection),
        ("Supabase REST API 查询测试", test_rest_api_query),
        ("Supabase REST API 插入测试", test_rest_api_insert),
        ("Supabase REST API 中文处理测试", test_rest_api_chinese)
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
        logger.info("所有测试通过！Supabase REST API 测试成功。")
    else:
        logger.error("部分测试失败。请检查日志获取详细信息。")
    
    return all_passed

if __name__ == "__main__":
    logger.info("开始测试使用 Supabase REST API 访问数据库")
    success = run_all_tests()
    if success:
        logger.info("测试成功！可以使用 Supabase REST API 访问数据库")
        sys.exit(0)
    else:
        logger.error("测试失败。请检查日志获取详细信息")
        sys.exit(1)
