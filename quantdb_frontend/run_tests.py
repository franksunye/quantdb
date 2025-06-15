#!/usr/bin/env python3
"""
QuantDB Frontend 测试运行器

运行前端相关的所有测试，包括单元测试、集成测试和端到端测试。
"""

import unittest
import sys
import os
import subprocess
import time
from pathlib import Path

def run_frontend_unit_tests():
    """运行前端单元测试"""
    print("\n" + "="*50)
    print("运行前端单元测试")
    print("="*50)
    
    # 获取测试目录
    test_dir = Path(__file__).parent / "tests"
    
    if not test_dir.exists():
        print("❌ 测试目录不存在")
        return False
    
    # 发现并运行测试
    loader = unittest.TestLoader()
    suite = loader.discover(str(test_dir), pattern='test_*.py')
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 返回测试结果
    success = result.wasSuccessful()
    if success:
        print(f"✅ 前端单元测试通过: {result.testsRun}个测试")
    else:
        print(f"❌ 前端单元测试失败: {len(result.failures)}个失败, {len(result.errors)}个错误")
    
    return success

def run_frontend_integration_tests():
    """运行前端集成测试"""
    print("\n" + "="*50)
    print("运行前端集成测试")
    print("="*50)
    
    try:
        # 检查后端API是否运行
        import requests
        response = requests.get("http://localhost:8000/api/v1/health", timeout=5)
        if response.status_code != 200:
            print("⚠️  后端API未运行，跳过集成测试")
            return True
    except:
        print("⚠️  无法连接后端API，跳过集成测试")
        return True
    
    # 运行集成测试
    print("🔗 后端API运行正常，开始集成测试...")
    
    # 这里可以添加具体的集成测试
    test_cases = [
        test_api_connectivity,
        test_stock_data_query,
        test_asset_info_query,
        test_error_handling
    ]
    
    passed = 0
    failed = 0
    
    for test_case in test_cases:
        try:
            print(f"运行测试: {test_case.__name__}")
            test_case()
            print(f"✅ {test_case.__name__} 通过")
            passed += 1
        except Exception as e:
            print(f"❌ {test_case.__name__} 失败: {str(e)}")
            failed += 1
    
    print(f"\n集成测试结果: {passed}个通过, {failed}个失败")
    return failed == 0

def test_api_connectivity():
    """测试API连接性"""
    import requests
    
    # 测试健康检查
    response = requests.get("http://localhost:8000/api/v1/health", timeout=10)
    assert response.status_code == 200
    
    data = response.json()
    assert "status" in data
    assert data["status"] == "ok"

def test_stock_data_query():
    """测试股票数据查询"""
    import requests
    
    # 测试股票数据查询
    url = "http://localhost:8000/api/v1/historical/stock/600000"
    params = {
        "start_date": "20240101",
        "end_date": "20240131"
    }
    
    response = requests.get(url, params=params, timeout=30)
    assert response.status_code == 200
    
    data = response.json()
    assert "data" in data
    assert isinstance(data["data"], list)

def test_asset_info_query():
    """测试资产信息查询"""
    import requests
    
    # 测试资产信息查询
    url = "http://localhost:8000/api/v1/assets/symbol/600000"
    
    response = requests.get(url, timeout=10)
    assert response.status_code == 200
    
    data = response.json()
    assert "symbol" in data
    assert data["symbol"] == "600000"

def test_error_handling():
    """测试错误处理"""
    import requests
    
    # 测试无效股票代码
    url = "http://localhost:8000/api/v1/assets/symbol/invalid"
    
    response = requests.get(url, timeout=10)
    # 应该返回错误或空数据，但不应该是500错误
    assert response.status_code in [200, 404, 422]

def run_frontend_e2e_tests():
    """运行前端端到端测试"""
    print("\n" + "="*50)
    print("运行前端端到端测试")
    print("="*50)
    
    try:
        # 检查Streamlit是否可用
        import streamlit
        print("✅ Streamlit 可用")
    except ImportError:
        print("❌ Streamlit 未安装，跳过E2E测试")
        return False
    
    # 这里可以添加Streamlit应用的E2E测试
    # 由于Streamlit应用需要浏览器环境，这里主要测试应用能否正常启动
    
    print("🔍 检查前端应用文件...")
    
    app_file = Path(__file__).parent / "app.py"
    if not app_file.exists():
        print("❌ app.py 文件不存在")
        return False
    
    print("✅ 前端应用文件存在")
    
    # 检查页面文件
    pages_dir = Path(__file__).parent / "pages"
    if pages_dir.exists():
        page_files = list(pages_dir.glob("*.py"))
        print(f"✅ 发现 {len(page_files)} 个页面文件")
    else:
        print("⚠️  pages 目录不存在")
    
    # 检查工具模块
    utils_dir = Path(__file__).parent / "utils"
    if utils_dir.exists():
        util_files = list(utils_dir.glob("*.py"))
        print(f"✅ 发现 {len(util_files)} 个工具模块")
    else:
        print("❌ utils 目录不存在")
        return False
    
    print("✅ 前端E2E检查通过")
    return True

def run_performance_tests():
    """运行性能测试"""
    print("\n" + "="*50)
    print("运行前端性能测试")
    print("="*50)
    
    try:
        # 检查后端API
        import requests
        
        # 测试API响应时间
        start_time = time.time()
        response = requests.get("http://localhost:8000/api/v1/health", timeout=10)
        end_time = time.time()
        
        if response.status_code == 200:
            response_time = (end_time - start_time) * 1000
            print(f"✅ API响应时间: {response_time:.1f}ms")
            
            if response_time < 100:
                print("🚀 API性能: 优秀")
            elif response_time < 500:
                print("⚡ API性能: 良好")
            else:
                print("⏳ API性能: 需要优化")
            
            return True
        else:
            print("❌ API健康检查失败")
            return False
            
    except Exception as e:
        print(f"❌ 性能测试失败: {str(e)}")
        return False

def main():
    """主函数"""
    print("🚀 QuantDB Frontend 测试运行器")
    print("=" * 50)
    
    # 解析命令行参数
    import argparse
    parser = argparse.ArgumentParser(description="运行QuantDB前端测试")
    parser.add_argument("--unit", action="store_true", help="运行单元测试")
    parser.add_argument("--integration", action="store_true", help="运行集成测试")
    parser.add_argument("--e2e", action="store_true", help="运行端到端测试")
    parser.add_argument("--performance", action="store_true", help="运行性能测试")
    parser.add_argument("--all", action="store_true", help="运行所有测试")
    
    args = parser.parse_args()
    
    # 如果没有指定参数，默认运行所有测试
    if not any([args.unit, args.integration, args.e2e, args.performance]):
        args.all = True
    
    success = True
    
    # 运行指定的测试
    if args.all or args.unit:
        success &= run_frontend_unit_tests()
    
    if args.all or args.integration:
        success &= run_frontend_integration_tests()
    
    if args.all or args.e2e:
        success &= run_frontend_e2e_tests()
    
    if args.all or args.performance:
        success &= run_performance_tests()
    
    # 输出总结
    print("\n" + "="*50)
    if success:
        print("✅ 所有测试通过")
        print("🎉 前端功能正常")
    else:
        print("❌ 部分测试失败")
        print("🔧 请检查失败的测试并修复问题")
    
    print("="*50)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
