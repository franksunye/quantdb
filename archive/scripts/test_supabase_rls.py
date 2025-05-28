"""
测试Supabase行级安全策略的脚本

此脚本测试Supabase的行级安全策略是否正确配置。
"""

import os
import sys
import requests
from dotenv import load_dotenv

def test_rls():
    """测试行级安全策略"""
    try:
        # 加载环境变量
        load_dotenv()
        
        # 获取Supabase URL和API密钥
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')
        supabase_service_key = os.getenv('SUPABASE_SERVICE_KEY')
        
        if not supabase_url or not supabase_key or not supabase_service_key:
            print("未找到必要的Supabase环境变量")
            return False
        
        print(f"连接到Supabase: {supabase_url}")
        
        # 测试匿名访问
        print("测试匿名访问...")
        
        # 设置请求头
        anon_headers = {
            "apikey": supabase_key,
            "Content-Type": "application/json"
        }
        
        # 尝试读取assets表
        print("尝试读取assets表...")
        assets_response = requests.get(
            f"{supabase_url}/rest/v1/assets?limit=10",
            headers=anon_headers
        )
        
        if assets_response.status_code == 200:
            print("匿名用户可以读取assets表")
            print(f"assets表数据: {assets_response.json()}")
        else:
            print(f"匿名用户无法读取assets表: {assets_response.status_code} - {assets_response.text}")
        
        # 尝试读取prices表
        print("尝试读取prices表...")
        prices_response = requests.get(
            f"{supabase_url}/rest/v1/prices?limit=10",
            headers=anon_headers
        )
        
        if prices_response.status_code == 200:
            print("匿名用户可以读取prices表")
            print(f"prices表数据: {prices_response.json()}")
        else:
            print(f"匿名用户无法读取prices表: {prices_response.status_code} - {prices_response.text}")
        
        # 尝试插入数据到assets表
        print("尝试插入数据到assets表...")
        assets_insert_response = requests.post(
            f"{supabase_url}/rest/v1/assets",
            headers=anon_headers,
            json={
                "symbol": "TEST",
                "name": "Test Asset",
                "asset_type": "stock",
                "exchange": "TEST",
                "currency": "USD"
            }
        )
        
        if assets_insert_response.status_code == 201:
            print("匿名用户可以插入数据到assets表")
            print(f"插入的数据: {assets_insert_response.json()}")
        else:
            print(f"匿名用户无法插入数据到assets表: {assets_insert_response.status_code} - {assets_insert_response.text}")
        
        # 测试服务角色访问
        print("测试服务角色访问...")
        
        # 设置请求头
        service_headers = {
            "apikey": supabase_service_key,
            "Authorization": f"Bearer {supabase_service_key}",
            "Content-Type": "application/json"
        }
        
        # 尝试插入数据到assets表
        print("尝试使用服务角色插入数据到assets表...")
        service_assets_insert_response = requests.post(
            f"{supabase_url}/rest/v1/assets",
            headers=service_headers,
            json={
                "symbol": "TEST2",
                "name": "Test Asset 2",
                "asset_type": "stock",
                "exchange": "TEST",
                "currency": "USD"
            }
        )
        
        if service_assets_insert_response.status_code == 201:
            print("服务角色可以插入数据到assets表")
            print(f"插入的数据: {service_assets_insert_response.json()}")
            
            # 获取插入的数据的ID
            asset_id = service_assets_insert_response.json().get("asset_id")
            
            if asset_id:
                # 尝试插入数据到prices表
                print("尝试使用服务角色插入数据到prices表...")
                service_prices_insert_response = requests.post(
                    f"{supabase_url}/rest/v1/prices",
                    headers=service_headers,
                    json={
                        "asset_id": asset_id,
                        "date": "2025-05-17",
                        "open": 100.0,
                        "high": 110.0,
                        "low": 90.0,
                        "close": 105.0,
                        "volume": 1000,
                        "adjusted_close": 105.0
                    }
                )
                
                if service_prices_insert_response.status_code == 201:
                    print("服务角色可以插入数据到prices表")
                    print(f"插入的数据: {service_prices_insert_response.json()}")
                else:
                    print(f"服务角色无法插入数据到prices表: {service_prices_insert_response.status_code} - {service_prices_insert_response.text}")
        else:
            print(f"服务角色无法插入数据到assets表: {service_assets_insert_response.status_code} - {service_assets_insert_response.text}")
        
        print("行级安全策略测试完成")
        return True
    except Exception as e:
        print(f"测试行级安全策略失败: {e}")
        return False

def main():
    """主函数"""
    print("开始测试Supabase行级安全策略")
    
    # 测试行级安全策略
    if not test_rls():
        print("测试行级安全策略失败")
        return False
    
    print("Supabase行级安全策略测试成功")
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("脚本执行成功")
        sys.exit(0)
    else:
        print("脚本执行失败")
        sys.exit(1)
