"""
仅使用REST API测试Supabase的脚本

此脚本仅使用REST API测试与Supabase的连接，避免PostgreSQL连接问题。
"""

import sys
import logging
import requests

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("supabase_rest_test")

def test_rest_api():
    """测试Supabase REST API连接"""
    try:
        # 直接使用硬编码的URL和密钥
        supabase_url = "https://dvusiqfijdmjcsubyapw.supabase.co"
        supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImR2dXNpcWZpamRtamNzdWJ5YXB3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDE3Njk2MjAsImV4cCI6MjA1NzM0NTYyMH0.hSjh0aIhUE2N_R4WY5-zOrDIq2Gpz2w1vyTInAdasoI"
        
        print(f"测试REST API连接: {supabase_url}")
        
        # 设置请求头
        headers = {
            "apikey": supabase_key,
            "Content-Type": "application/json"
        }
        
        # 发送请求
        print("发送请求...")
        response = requests.get(
            f"{supabase_url}/rest/v1/",
            headers=headers
        )
        
        # 检查响应
        print(f"响应状态码: {response.status_code}")
        if response.status_code == 200:
            print("REST API连接成功")
            print(f"响应内容: {response.text[:100]}...")
            return True
        else:
            print(f"REST API连接失败: {response.status_code}")
            print(f"响应内容: {response.text}")
            return False
    except Exception as e:
        print(f"REST API连接测试失败: {e}")
        return False

def check_tables():
    """检查表是否存在"""
    try:
        # 直接使用硬编码的URL和密钥
        supabase_url = "https://dvusiqfijdmjcsubyapw.supabase.co"
        supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImR2dXNpcWZpamRtamNzdWJ5YXB3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDE3Njk2MjAsImV4cCI6MjA1NzM0NTYyMH0.hSjh0aIhUE2N_R4WY5-zOrDIq2Gpz2w1vyTInAdasoI"
        
        print("检查表是否存在...")
        
        # 设置请求头
        headers = {
            "apikey": supabase_key,
            "Content-Type": "application/json"
        }
        
        # 检查assets表
        print("检查assets表...")
        assets_response = requests.get(
            f"{supabase_url}/rest/v1/assets?limit=1",
            headers=headers
        )
        
        if assets_response.status_code == 200:
            print("assets表存在")
            print(f"assets表数据: {assets_response.json()}")
        else:
            print(f"assets表不存在: {assets_response.status_code} - {assets_response.text}")
        
        # 检查prices表
        print("检查prices表...")
        prices_response = requests.get(
            f"{supabase_url}/rest/v1/prices?limit=1",
            headers=headers
        )
        
        if prices_response.status_code == 200:
            print("prices表存在")
            print(f"prices表数据: {prices_response.json()}")
        else:
            print(f"prices表不存在: {prices_response.status_code} - {prices_response.text}")
        
        return True
    except Exception as e:
        print(f"检查表失败: {e}")
        return False

def main():
    """主函数"""
    print("开始测试Supabase REST API")
    
    # 测试REST API连接
    if not test_rest_api():
        print("REST API连接测试失败")
        return False
    
    # 检查表是否存在
    if not check_tables():
        print("检查表失败")
        return False
    
    print("Supabase REST API测试成功")
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("所有测试通过")
        sys.exit(0)
    else:
        print("测试失败")
        sys.exit(1)
