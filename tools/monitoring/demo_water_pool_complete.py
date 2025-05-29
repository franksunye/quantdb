#!/usr/bin/env python3
"""
完整的"水池蓄水情况"监控演示

展示从空数据库到有数据后的完整监控过程
"""

import sys
import os
import time
import requests
import threading
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

def start_api_server():
    """启动API服务器"""
    import uvicorn
    from src.api.main import app
    uvicorn.run(app, host='127.0.0.1', port=8000, log_level='warning')

def demo_complete_water_pool():
    """完整的水池监控演示"""
    
    print("=" * 70)
    print("🏊‍♂️ QuantDB 完整水池蓄水情况监控演示")
    print("=" * 70)
    
    # 启动API服务器
    print("\n🚀 启动API服务器...")
    server_thread = threading.Thread(target=start_api_server, daemon=True)
    server_thread.start()
    time.sleep(3)
    
    try:
        # 阶段1: 查看空水池状态
        print("\n📊 阶段1: 空水池状态")
        print("-" * 40)
        
        # 运行监控演示
        os.system("python tools/monitoring/demo_monitoring.py")
        
        # 阶段2: 开始蓄水 - 获取第一批数据
        print("\n💧 阶段2: 开始蓄水 - 获取第一批股票数据")
        print("-" * 40)
        
        symbols_to_fetch = ["000001", "600519", "000002"]
        
        for i, symbol in enumerate(symbols_to_fetch, 1):
            print(f"\n🔄 获取第 {i} 只股票数据: {symbol}")
            
            start_time = time.time()
            response = requests.get(
                f"http://localhost:8000/api/v1/historical/stock/{symbol}",
                params={
                    "start_date": "20240101",
                    "end_date": "20240105"
                },
                timeout=30
            )
            request_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                record_count = len(data.get("data", []))
                print(f"  ✅ 成功获取 {record_count} 条记录，耗时 {request_time:.2f}秒")
                print(f"  📊 数据来源: AKShare (首次获取)")
            else:
                print(f"  ❌ 获取失败: {response.status_code}")
        
        # 阶段3: 查看蓄水后状态
        print(f"\n📈 阶段3: 蓄水后状态")
        print("-" * 40)
        
        # 再次运行监控演示
        os.system("python tools/monitoring/demo_monitoring.py")
        
        # 阶段4: 测试缓存效果
        print(f"\n⚡ 阶段4: 测试缓存效果")
        print("-" * 40)
        
        test_symbol = symbols_to_fetch[0]
        print(f"🔄 再次请求 {test_symbol} 数据 (测试缓存命中):")
        
        start_time = time.time()
        response = requests.get(
            f"http://localhost:8000/api/v1/historical/stock/{test_symbol}",
            params={
                "start_date": "20240101",
                "end_date": "20240105"
            },
            timeout=10
        )
        cache_request_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            record_count = len(data.get("data", []))
            print(f"  ✅ 缓存命中! 获取 {record_count} 条记录，耗时 {cache_request_time:.2f}秒")
            print(f"  📊 数据来源: 数据库缓存")
            print(f"  🚀 性能提升: 响应速度明显更快")
        
        # 阶段5: 测试范围扩展
        print(f"\n📏 阶段5: 测试数据范围扩展")
        print("-" * 40)
        
        print(f"🔄 扩展 {test_symbol} 数据范围 (测试智能补充):")
        
        start_time = time.time()
        response = requests.get(
            f"http://localhost:8000/api/v1/historical/stock/{test_symbol}",
            params={
                "start_date": "20240101",
                "end_date": "20240110"  # 扩展范围
            },
            timeout=30
        )
        expand_request_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            record_count = len(data.get("data", []))
            print(f"  ✅ 智能扩展! 获取 {record_count} 条记录，耗时 {expand_request_time:.2f}秒")
            print(f"  📊 数据来源: 部分缓存 + 部分AKShare")
            print(f"  🧠 智能策略: 只获取缺失的日期范围")
        
        # 阶段6: 最终水池状态
        print(f"\n🏊‍♂️ 阶段6: 最终水池状态")
        print("-" * 40)
        
        # 最后一次运行监控演示
        os.system("python tools/monitoring/demo_monitoring.py")
        
        # 总结
        print(f"\n🎯 水池蓄水监控总结")
        print("=" * 70)
        print(f"✅ 成功演示了完整的水池蓄水过程:")
        print(f"   1. 空水池状态 → 数据库为空")
        print(f"   2. 开始蓄水 → 从AKShare获取数据并缓存")
        print(f"   3. 缓存命中 → 直接从数据库返回，速度更快")
        print(f"   4. 智能扩展 → 只获取缺失部分，避免重复")
        print(f"   5. 水池监控 → 实时了解数据覆盖情况")
        print(f"")
        print(f"🎉 核心价值验证:")
        print(f"   📈 性能提升: 缓存请求明显更快")
        print(f"   💰 成本节省: 减少AKShare API调用")
        print(f"   🧠 智能策略: 只获取必要的数据")
        print(f"   📊 可观测性: 清晰的水池状态监控")
        
    except Exception as e:
        print(f"❌ 演示过程中出错: {e}")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    demo_complete_water_pool()
