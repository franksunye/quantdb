#!/usr/bin/env python3
"""
测试数据保存功能的脚本
验证股票数据是否正确保存到数据库
"""

import sys
import os
import requests
import json
from datetime import datetime, date

# 添加项目路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

def test_data_saving():
    """测试数据保存功能"""
    print("🔍 测试数据保存功能...")
    
    # 测试一个新的股票代码
    test_symbol = "600001"  # 邯郸钢铁
    start_date = "20240601"
    end_date = "20240630"
    
    print(f"测试股票: {test_symbol}")
    print(f"日期范围: {start_date} - {end_date}")
    
    try:
        # 第一次查询 - 应该从AKShare获取数据并保存到数据库
        print("\n第一次查询 (应该从AKShare获取)...")
        response1 = requests.get(
            f"http://localhost:8000/api/v1/historical/stock/{test_symbol}?start_date={start_date}&end_date={end_date}",
            timeout=30
        )
        
        if response1.status_code == 200:
            data1 = response1.json()
            print(f"✅ 第一次查询成功")
            print(f"   数据条数: {len(data1.get('data', []))}")
            
            cache_info1 = data1.get('metadata', {}).get('cache_info', {})
            print(f"   缓存命中: {cache_info1.get('cache_hit', 'N/A')}")
            print(f"   AKShare调用: {cache_info1.get('akshare_called', 'N/A')}")
            print(f"   缓存命中率: {cache_info1.get('cache_hit_ratio', 'N/A')}")
            
            # 等待一下确保数据保存完成
            import time
            time.sleep(2)
            
            # 第二次查询 - 应该从数据库缓存获取
            print("\n第二次查询 (应该从缓存获取)...")
            response2 = requests.get(
                f"http://localhost:8000/api/v1/historical/stock/{test_symbol}?start_date={start_date}&end_date={end_date}",
                timeout=10
            )
            
            if response2.status_code == 200:
                data2 = response2.json()
                print(f"✅ 第二次查询成功")
                print(f"   数据条数: {len(data2.get('data', []))}")
                
                cache_info2 = data2.get('metadata', {}).get('cache_info', {})
                print(f"   缓存命中: {cache_info2.get('cache_hit', 'N/A')}")
                print(f"   AKShare调用: {cache_info2.get('akshare_called', 'N/A')}")
                print(f"   缓存命中率: {cache_info2.get('cache_hit_ratio', 'N/A')}")
                
                # 分析结果
                if cache_info2.get('cache_hit'):
                    print("🎉 缓存功能正常工作！")
                else:
                    print("⚠️ 缓存功能可能有问题")
                    
                # 检查数据一致性
                if len(data1.get('data', [])) == len(data2.get('data', [])):
                    print("✅ 数据一致性检查通过")
                else:
                    print("❌ 数据一致性检查失败")
                    
            else:
                print(f"❌ 第二次查询失败: {response2.status_code}")
                print(response2.text)
                
        else:
            print(f"❌ 第一次查询失败: {response1.status_code}")
            print(response1.text)
            
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")

def check_database_status():
    """检查数据库状态"""
    print("\n🔍 检查数据库状态...")
    
    try:
        response = requests.get("http://localhost:8000/api/v1/cache/status", timeout=5)
        if response.status_code == 200:
            cache_data = response.json()
            database_info = cache_data.get('database', {})
            
            print("数据库状态:")
            print(f"   资产数量: {database_info.get('assets_count', 'N/A')}")
            print(f"   日数据记录数: {database_info.get('daily_data_count', 'N/A')}")
            print(f"   最新数据日期: {database_info.get('latest_data_date', 'N/A')}")
            print(f"   数据库大小: {database_info.get('database_size_bytes', 'N/A')} bytes")
            
        else:
            print(f"❌ 获取数据库状态失败: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 检查数据库状态失败: {str(e)}")

def test_asset_creation():
    """测试资产创建功能"""
    print("\n🔍 测试资产创建功能...")
    
    test_symbol = "600001"
    
    try:
        response = requests.get(f"http://localhost:8000/api/v1/assets/symbol/{test_symbol}", timeout=10)
        if response.status_code == 200:
            asset_data = response.json()
            print(f"✅ 资产信息获取成功")
            print(f"   股票名称: {asset_data.get('name', 'N/A')}")
            print(f"   总股本: {asset_data.get('total_shares', 'N/A')}")
            print(f"   流通股本: {asset_data.get('circulating_shares', 'N/A')}")
            print(f"   ROE: {asset_data.get('roe', 'N/A')}")
            print(f"   PE比率: {asset_data.get('pe_ratio', 'N/A')}")
            print(f"   PB比率: {asset_data.get('pb_ratio', 'N/A')}")
            print(f"   最后更新: {asset_data.get('last_updated', 'N/A')}")
            
        else:
            print(f"❌ 获取资产信息失败: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ 测试资产创建失败: {str(e)}")

def main():
    """主测试函数"""
    print("🚀 开始测试数据保存和缓存功能...")
    print("=" * 60)
    
    # 检查后端API状态
    try:
        response = requests.get("http://localhost:8000/api/v1/health", timeout=5)
        if response.status_code == 200:
            print("✅ 后端API正常运行")
        else:
            print("❌ 后端API异常")
            return
    except:
        print("❌ 无法连接后端API")
        return
    
    # 检查数据库状态
    check_database_status()
    
    # 测试资产创建
    test_asset_creation()
    
    # 测试数据保存
    test_data_saving()
    
    print("\n" + "=" * 60)
    print("🎯 测试完成！")

if __name__ == "__main__":
    main()
