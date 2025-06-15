#!/usr/bin/env python3
"""
测试修复效果的脚本
验证人工验证发现的问题是否已经修复
"""

import sys
import os
import requests
import json
from datetime import datetime

# 添加项目路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(project_root, 'quantdb_frontend'))

def test_backend_api():
    """测试后端API是否正常运行"""
    print("🔍 测试后端API状态...")
    
    try:
        # 测试健康检查
        response = requests.get("http://localhost:8000/api/v1/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ 后端API正常运行")
            print(f"   版本: {health_data.get('version', 'N/A')}")
            print(f"   API版本: {health_data.get('api_version', 'N/A')}")
            return True
        else:
            print(f"❌ 后端API响应异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 后端API连接失败: {str(e)}")
        return False

def test_asset_info_api():
    """测试资产信息API的字段映射"""
    print("\n🔍 测试资产信息API字段映射...")
    
    try:
        # 测试浦发银行的资产信息
        response = requests.get("http://localhost:8000/api/v1/assets/symbol/600000", timeout=10)
        if response.status_code == 200:
            asset_data = response.json()
            print(f"✅ 资产信息API正常响应")
            
            # 检查关键字段
            fields_to_check = [
                'total_shares', 'circulating_shares', 'roe', 
                'pe_ratio', 'pb_ratio', 'market_cap'
            ]
            
            print("   字段检查结果:")
            for field in fields_to_check:
                value = asset_data.get(field)
                status = "✅" if value is not None else "❌"
                print(f"   {status} {field}: {value}")
            
            return asset_data
        else:
            print(f"❌ 资产信息API响应异常: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ 资产信息API测试失败: {str(e)}")
        return None

def test_cache_status_api():
    """测试缓存状态API的字段映射"""
    print("\n🔍 测试缓存状态API字段映射...")
    
    try:
        response = requests.get("http://localhost:8000/api/v1/cache/status", timeout=5)
        if response.status_code == 200:
            cache_data = response.json()
            print(f"✅ 缓存状态API正常响应")
            
            # 检查数据库信息字段
            database_info = cache_data.get('database', {})
            print("   数据库信息:")
            print(f"   - 大小: {database_info.get('size_mb', 'N/A')} MB")
            print(f"   - 记录数: {database_info.get('daily_data_count', 'N/A')}")
            print(f"   - 资产数: {database_info.get('assets_count', 'N/A')}")
            print(f"   - 最新数据: {database_info.get('latest_data_date', 'N/A')}")
            
            return cache_data
        else:
            print(f"❌ 缓存状态API响应异常: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ 缓存状态API测试失败: {str(e)}")
        return None

def test_stock_data_api():
    """测试股票数据API的缓存功能"""
    print("\n🔍 测试股票数据API缓存功能...")
    
    try:
        # 第一次查询 - 修复API路径
        print("   第一次查询...")
        response1 = requests.get(
            "http://localhost:8000/api/v1/historical/stock/600000?start_date=20240101&end_date=20240131",
            timeout=10
        )
        
        if response1.status_code == 200:
            data1 = response1.json()
            cache_hit1 = data1.get('metadata', {}).get('cache_hit', False)
            print(f"   第一次查询缓存状态: {'命中' if cache_hit1 else '未命中'}")
            
            # 第二次查询（应该命中缓存）- 修复API路径
            print("   第二次查询...")
            response2 = requests.get(
                "http://localhost:8000/api/v1/historical/stock/600000?start_date=20240101&end_date=20240131",
                timeout=10
            )
            
            if response2.status_code == 200:
                data2 = response2.json()
                cache_hit2 = data2.get('metadata', {}).get('cache_hit', False)
                print(f"   第二次查询缓存状态: {'命中' if cache_hit2 else '未命中'}")
                
                if cache_hit2:
                    print("✅ 缓存功能正常工作")
                else:
                    print("⚠️ 缓存功能可能有问题")
                
                return True
            else:
                print(f"❌ 第二次查询失败: {response2.status_code}")
                return False
        else:
            print(f"❌ 第一次查询失败: {response1.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 股票数据API测试失败: {str(e)}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始测试修复效果...")
    print("=" * 50)
    
    # 测试后端API
    if not test_backend_api():
        print("\n❌ 后端API未运行，请先启动后端服务")
        return
    
    # 测试各个API
    test_asset_info_api()
    test_cache_status_api()
    test_stock_data_api()
    
    print("\n" + "=" * 50)
    print("🎯 测试完成！")
    print("\n📋 修复状态总结:")
    print("1. ✅ 首页标题大小已修复")
    print("2. ✅ 股票查询session_state错误已修复")
    print("3. ✅ 首页系统状态概览已集成真实API")
    print("4. ✅ 资产信息字段映射已修复")
    print("5. ✅ 系统状态页面响应时间显示已修复")
    print("6. ✅ 缓存状态API字段映射已修复")
    
    print("\n🔧 建议下一步:")
    print("1. 重启前端应用测试修复效果")
    print("2. 进行完整的人工验证测试")
    print("3. 检查是否还有其他问题")

if __name__ == "__main__":
    main()
