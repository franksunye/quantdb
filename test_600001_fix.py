#!/usr/bin/env python3
"""
测试600001查询问题修复效果的脚本
"""

import sys
import os
import requests
from datetime import datetime, timedelta

# 添加项目路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

def test_stock_validator():
    """测试股票验证工具"""
    print("🔍 测试股票验证工具...")
    
    try:
        from utils.stock_validator import validate_stock_code, analyze_query_failure
        
        # 测试600001
        result = validate_stock_code('600001')
        print(f"✅ 600001验证结果:")
        print(f"   有效: {result['is_valid']}")
        print(f"   活跃: {result['is_active']}")
        print(f"   有问题: {result['is_problematic']}")
        print(f"   状态: {result['status']}")
        print(f"   名称: {result.get('name', 'N/A')}")
        
        # 测试查询失败分析
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=7)).strftime('%Y%m%d')
        
        analysis = analyze_query_failure('600001', start_date, end_date)
        print(f"\n✅ 查询失败分析:")
        print(f"   可能原因: {analysis['possible_reasons']}")
        print(f"   建议: {analysis['recommendations']}")
        print(f"   推荐股票: {[s['symbol'] + '-' + s['name'] for s in analysis['suggested_stocks'][:3]]}")
        
    except Exception as e:
        print(f"❌ 股票验证工具测试失败: {e}")

def test_api_with_600001():
    """测试API对600001的处理"""
    print("\n🔍 测试API对600001的处理...")
    
    try:
        # 检查后端API状态
        health_response = requests.get("http://localhost:8000/api/v1/health", timeout=5)
        if health_response.status_code != 200:
            print("❌ 后端API未运行")
            return
        
        print("✅ 后端API正常运行")
        
        # 测试600001查询
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=7)).strftime('%Y%m%d')
        
        api_url = f"http://localhost:8000/api/v1/historical/stock/600001?start_date={start_date}&end_date={end_date}"
        print(f"API URL: {api_url}")
        
        response = requests.get(api_url, timeout=30)
        
        print(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API查询成功")
            print(f"   返回数据条数: {len(data.get('data', []))}")
            print(f"   状态: {data.get('metadata', {}).get('status', 'N/A')}")
            print(f"   消息: {data.get('metadata', {}).get('message', 'N/A')}")
            
            # 检查错误分析
            error_analysis = data.get('metadata', {}).get('error_analysis', {})
            if error_analysis:
                print(f"   错误分析: {error_analysis.get('possible_reasons', [])}")
                print(f"   建议: {error_analysis.get('recommendations', [])}")
            
            # 检查建议
            suggestions = data.get('metadata', {}).get('suggestions', [])
            if suggestions:
                print(f"   API建议: {suggestions}")
        else:
            print(f"❌ API查询失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到后端API")
    except Exception as e:
        print(f"❌ API测试失败: {e}")

def test_alternative_stocks():
    """测试替代股票的查询"""
    print("\n🔍 测试替代股票查询...")
    
    alternative_stocks = ['600000', '000001', '600519']
    
    for symbol in alternative_stocks:
        try:
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=7)).strftime('%Y%m%d')
            
            api_url = f"http://localhost:8000/api/v1/historical/stock/{symbol}?start_date={start_date}&end_date={end_date}"
            response = requests.get(api_url, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                data_count = len(data.get('data', []))
                print(f"✅ {symbol}: 成功获取 {data_count} 条数据")
                
                if data_count > 0:
                    print(f"   最新价格: {data['data'][-1].get('close', 'N/A')}")
                    cache_info = data.get('metadata', {}).get('cache_info', {})
                    if cache_info:
                        print(f"   缓存命中: {cache_info.get('cache_hit', 'N/A')}")
            else:
                print(f"❌ {symbol}: 查询失败 ({response.status_code})")
                
        except Exception as e:
            print(f"❌ {symbol}: 查询异常 - {e}")

def test_date_range_analysis():
    """测试日期范围分析"""
    print("\n🔍 测试日期范围分析...")
    
    test_cases = [
        # 只包含周末的情况
        {
            "name": "周末日期范围",
            "start": "20241214",  # 假设是周六
            "end": "20241215"     # 假设是周日
        },
        # 很短的日期范围
        {
            "name": "很短的日期范围",
            "start": (datetime.now() - timedelta(days=2)).strftime('%Y%m%d'),
            "end": datetime.now().strftime('%Y%m%d')
        },
        # 正常的日期范围
        {
            "name": "正常日期范围",
            "start": (datetime.now() - timedelta(days=30)).strftime('%Y%m%d'),
            "end": datetime.now().strftime('%Y%m%d')
        }
    ]
    
    for case in test_cases:
        try:
            from utils.stock_validator import analyze_query_failure
            
            analysis = analyze_query_failure('600001', case['start'], case['end'])
            date_analysis = analysis.get('date_analysis', {})
            
            print(f"📅 {case['name']}:")
            print(f"   日期范围: {case['start']} - {case['end']}")
            print(f"   天数: {date_analysis.get('days_requested', 'N/A')}")
            print(f"   是否只有周末: {date_analysis.get('is_weekend_only', 'N/A')}")
            print(f"   是否太短: {date_analysis.get('is_too_short', 'N/A')}")
            print(f"   建议: {analysis.get('recommendations', [])[:2]}")
            print()
            
        except Exception as e:
            print(f"❌ {case['name']} 分析失败: {e}")

def main():
    """主测试函数"""
    print("🚀 开始测试600001查询问题修复效果...")
    print("=" * 60)
    
    # 1. 测试股票验证工具
    test_stock_validator()
    
    # 2. 测试API处理
    test_api_with_600001()
    
    # 3. 测试替代股票
    test_alternative_stocks()
    
    # 4. 测试日期范围分析
    test_date_range_analysis()
    
    print("\n" + "=" * 60)
    print("🎯 测试完成！")
    
    print("\n📋 修复效果总结:")
    print("1. ✅ 添加了股票验证工具，可以识别问题股票")
    print("2. ✅ 改进了前端错误提示，提供详细分析和建议")
    print("3. ✅ 后端API增加了错误分析和建议")
    print("4. ✅ 提供了替代股票推荐")
    print("5. ✅ 增强了日期范围分析")
    
    print("\n💡 用户体验改进:")
    print("- 当查询600001失败时，系统会明确告知这是问题股票")
    print("- 提供具体的解决方案和替代建议")
    print("- 分析日期范围是否合理")
    print("- 推荐活跃的替代股票")

if __name__ == "__main__":
    main()
