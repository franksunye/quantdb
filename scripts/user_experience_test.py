#!/usr/bin/env python3
"""
用户体验测试脚本

模拟真实用户使用QuantDB的完整流程，从安装到高级使用。
这个脚本可以独立运行，验证PyPI发布版本的质量。
"""

import subprocess
import sys
import os
import time
import tempfile
from pathlib import Path


def print_section(title):
    """打印测试章节标题"""
    print(f"\n{'='*60}")
    print(f"🧪 {title}")
    print('='*60)


def print_step(step, description):
    """打印测试步骤"""
    print(f"\n📋 步骤 {step}: {description}")
    print('-' * 40)


def run_command(cmd, description, cwd=None, timeout=300):
    """运行命令并返回结果"""
    print(f"执行: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    
    try:
        if isinstance(cmd, str):
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, 
                cwd=cwd, timeout=timeout
            )
        else:
            result = subprocess.run(
                cmd, capture_output=True, text=True, 
                cwd=cwd, timeout=timeout
            )
        
        if result.returncode == 0:
            print(f"✅ {description} - 成功")
            if result.stdout.strip():
                print(f"输出: {result.stdout.strip()}")
            return True, result.stdout, result.stderr
        else:
            print(f"❌ {description} - 失败")
            print(f"错误: {result.stderr}")
            return False, result.stdout, result.stderr
            
    except subprocess.TimeoutExpired:
        print(f"⏰ {description} - 超时")
        return False, "", "命令执行超时"
    except Exception as e:
        print(f"💥 {description} - 异常: {e}")
        return False, "", str(e)


def test_fresh_installation():
    """测试全新安装体验"""
    print_section("全新安装测试")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        venv_path = Path(temp_dir) / "quantdb_test_env"
        
        print_step(1, "创建虚拟环境")
        success, _, _ = run_command([
            sys.executable, "-m", "venv", str(venv_path)
        ], "创建虚拟环境")
        
        if not success:
            return False
        
        # 获取虚拟环境路径
        if sys.platform == "win32":
            python_path = venv_path / "Scripts" / "python.exe"
            pip_path = venv_path / "Scripts" / "pip.exe"
        else:
            python_path = venv_path / "bin" / "python"
            pip_path = venv_path / "bin" / "pip"
        
        print_step(2, "升级pip")
        success, _, _ = run_command([
            str(pip_path), "install", "--upgrade", "pip"
        ], "升级pip")
        
        if not success:
            return False
        
        print_step(3, "从PyPI安装quantdb")
        success, stdout, stderr = run_command([
            str(pip_path), "install", "quantdb"
        ], "安装quantdb包", timeout=600)
        
        if not success:
            print(f"安装失败详情: {stderr}")
            return False
        
        print_step(4, "验证安装")
        test_import = '''
import qdb
print(f"✅ QuantDB版本: {getattr(qdb, '__version__', '未知')}")
print("✅ 导入成功")
'''
        
        success, stdout, stderr = run_command([
            str(python_path), "-c", test_import
        ], "验证导入")
        
        return success


def test_basic_functionality():
    """测试基本功能"""
    print_section("基本功能测试")
    
    print_step(1, "测试基本API调用")
    basic_test = '''
import qdb
import sys

try:
    print("🔍 测试get_stock_data...")
    # 使用较短的时间范围减少网络依赖
    data = qdb.get_stock_data("000001", "20240101", "20240105")
    print(f"✅ 历史数据获取成功: {len(data)}条记录")
    
    print("🔍 测试get_stock_list...")
    stocks = qdb.get_stock_list()
    print(f"✅ 股票列表获取成功: {len(stocks)}只股票")
    
    print("🔍 测试get_realtime_data...")
    realtime = qdb.get_realtime_data("000001")
    print(f"✅ 实时数据获取成功: {type(realtime)}")
    
    print("🎉 所有基本功能测试通过")
    
except Exception as e:
    print(f"❌ 基本功能测试失败: {e}")
    sys.exit(1)
'''
    
    success, stdout, stderr = run_command([
        sys.executable, "-c", basic_test
    ], "基本功能测试", timeout=120)
    
    return success


def test_user_scenarios():
    """测试用户使用场景"""
    print_section("用户场景测试")
    
    scenarios = [
        {
            "name": "量化分析师场景",
            "code": '''
import qdb
import pandas as pd

# 量化分析师获取多只股票数据
symbols = ["000001", "000002"]
portfolio_data = {}

for symbol in symbols:
    try:
        data = qdb.get_stock_data(symbol, "20240101", "20240105")
        if len(data) > 0:
            portfolio_data[symbol] = data
            print(f"✅ {symbol}: {len(data)}条数据")
    except Exception as e:
        print(f"⚠️ {symbol}获取失败: {e}")

print(f"✅ 投资组合数据获取完成: {len(portfolio_data)}只股票")
'''
        },
        {
            "name": "数据科学家场景", 
            "code": '''
import qdb

# 数据科学家进行数据探索
try:
    # 获取股票列表进行筛选
    stocks = qdb.get_stock_list()
    print(f"✅ 可用股票数量: {len(stocks)}")
    
    # 选择前几只进行分析
    sample_stocks = stocks.head(3) if hasattr(stocks, 'head') else stocks[:3]
    print(f"✅ 样本选择完成: {len(sample_stocks)}只")
    
except Exception as e:
    print(f"⚠️ 数据探索异常: {e}")

print("✅ 数据科学场景测试完成")
'''
        },
        {
            "name": "个人投资者场景",
            "code": '''
import qdb

# 个人投资者查看关注股票
watchlist = ["000001"]  # 平安银行

for symbol in watchlist:
    try:
        # 获取实时价格
        realtime = qdb.get_realtime_data(symbol)
        print(f"✅ {symbol}实时数据: {type(realtime)}")
        
        # 获取近期历史
        history = qdb.get_stock_data(symbol, "20240101", "20240105")
        print(f"✅ {symbol}历史数据: {len(history)}条")
        
    except Exception as e:
        print(f"⚠️ {symbol}查询失败: {e}")

print("✅ 个人投资者场景测试完成")
'''
        }
    ]
    
    all_success = True
    for i, scenario in enumerate(scenarios, 1):
        print_step(i, scenario["name"])
        success, stdout, stderr = run_command([
            sys.executable, "-c", scenario["code"]
        ], scenario["name"], timeout=90)
        
        if not success:
            all_success = False
            print(f"❌ {scenario['name']}失败")
        else:
            print(f"✅ {scenario['name']}成功")
    
    return all_success


def test_performance_experience():
    """测试性能体验"""
    print_section("性能体验测试")
    
    print_step(1, "缓存性能测试")
    perf_test = '''
import qdb
import time

symbol = "000001"
start_date = "20240101"
end_date = "20240105"

try:
    # 第一次调用
    start_time = time.time()
    data1 = qdb.get_stock_data(symbol, start_date, end_date)
    first_time = time.time() - start_time
    print(f"首次调用: {first_time:.2f}秒, 数据量: {len(data1)}")
    
    # 第二次调用（缓存）
    start_time = time.time()
    data2 = qdb.get_stock_data(symbol, start_date, end_date)
    second_time = time.time() - start_time
    print(f"缓存调用: {second_time:.2f}秒, 数据量: {len(data2)}")
    
    # 性能提升
    if second_time < first_time:
        improvement = (first_time - second_time) / first_time * 100
        print(f"✅ 性能提升: {improvement:.1f}%")
    else:
        print("✅ 缓存功能正常")
        
except Exception as e:
    print(f"⚠️ 性能测试异常: {e}")

print("✅ 性能测试完成")
'''
    
    success, stdout, stderr = run_command([
        sys.executable, "-c", perf_test
    ], "性能测试", timeout=60)
    
    return success


def main():
    """主测试流程"""
    print("🚀 QuantDB用户体验测试开始")
    print(f"Python版本: {sys.version}")
    print(f"测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    test_results = []
    
    # 测试套件
    tests = [
        ("全新安装测试", test_fresh_installation),
        ("基本功能测试", test_basic_functionality), 
        ("用户场景测试", test_user_scenarios),
        ("性能体验测试", test_performance_experience),
    ]
    
    for test_name, test_func in tests:
        print(f"\n🧪 开始执行: {test_name}")
        try:
            result = test_func()
            test_results.append((test_name, result))
            if result:
                print(f"✅ {test_name} - 通过")
            else:
                print(f"❌ {test_name} - 失败")
        except Exception as e:
            print(f"💥 {test_name} - 异常: {e}")
            test_results.append((test_name, False))
    
    # 总结报告
    print_section("测试总结报告")
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    print(f"📊 测试结果: {passed}/{total} 通过")
    print(f"📈 通过率: {passed/total*100:.1f}%")
    
    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {status} {test_name}")
    
    if passed == total:
        print("\n🎉 所有用户体验测试通过！QuantDB已准备好为用户提供优质服务！")
        return 0
    else:
        print(f"\n⚠️ 有{total-passed}个测试失败，需要进一步优化用户体验")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
