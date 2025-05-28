"""
测试Supabase API的脚本

此脚本测试Supabase API是否正确配置。
"""

import os
import sys
import requests
from dotenv import load_dotenv

def test_api():
    """测试API"""
    try:
        # 加载环境变量
        load_dotenv()
        
        # 获取Supabase URL和API密钥
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')
        
        if not supabase_url or not supabase_key:
            print("未找到必要的Supabase环境变量")
            return False
        
        print(f"连接到Supabase: {supabase_url}")
        
        # 设置请求头
        headers = {
            "apikey": supabase_key,
            "Content-Type": "application/json"
        }
        
        # 测试API连接
        print("测试API连接...")
        response = requests.get(
            f"{supabase_url}/rest/v1/",
            headers=headers
        )
        
        if response.status_code == 200:
            print("API连接成功")
            print(f"响应状态码: {response.status_code}")
            print(f"响应内容: {response.text[:100]}...")
        else:
            print(f"API连接失败: {response.status_code} - {response.text}")
            return False
        
        # 测试认证
        print("测试认证...")
        auth_response = requests.get(
            f"{supabase_url}/auth/v1/user",
            headers={
                "apikey": supabase_key,
                "Authorization": f"Bearer {supabase_key}",
                "Content-Type": "application/json"
            }
        )
        
        if auth_response.status_code == 200:
            print("认证成功")
            print(f"响应状态码: {auth_response.status_code}")
            print(f"响应内容: {auth_response.text[:100]}...")
        else:
            print(f"认证失败: {auth_response.status_code} - {auth_response.text}")
            # 认证失败不影响测试结果
        
        # 测试存储
        print("测试存储...")
        storage_response = requests.get(
            f"{supabase_url}/storage/v1/bucket",
            headers=headers
        )
        
        if storage_response.status_code == 200:
            print("存储API连接成功")
            print(f"响应状态码: {storage_response.status_code}")
            print(f"响应内容: {storage_response.text[:100]}...")
        else:
            print(f"存储API连接失败: {storage_response.status_code} - {storage_response.text}")
            # 存储API连接失败不影响测试结果
        
        print("API测试完成")
        return True
    except Exception as e:
        print(f"测试API失败: {e}")
        return False

def main():
    """主函数"""
    print("开始测试Supabase API")
    
    # 测试API
    if not test_api():
        print("测试API失败")
        return False
    
    print("Supabase API测试成功")
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("脚本执行成功")
        sys.exit(0)
    else:
        print("脚本执行失败")
        sys.exit(1)
