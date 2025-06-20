#!/usr/bin/env python3
"""
云端前端测试运行器

运行所有测试并生成测试报告。
"""

import unittest
import sys
import os
from io import StringIO

# 添加项目路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

def run_all_tests():
    """运行所有测试"""
    
    print("=" * 60)
    print("QuantDB 云端前端测试套件")
    print("=" * 60)
    
    # 发现并运行所有测试
    loader = unittest.TestLoader()
    start_dir = os.path.dirname(os.path.abspath(__file__))
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    # 创建测试运行器
    stream = StringIO()
    runner = unittest.TextTestRunner(
        stream=stream,
        verbosity=2,
        buffer=True
    )
    
    # 运行测试
    result = runner.run(suite)
    
    # 输出结果
    output = stream.getvalue()
    print(output)
    
    # 生成测试报告
    print("\n" + "=" * 60)
    print("测试报告")
    print("=" * 60)
    
    print(f"总测试数: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    print(f"跳过: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
    
    # 显示失败和错误详情
    if result.failures:
        print("\n失败的测试:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback.split('AssertionError:')[-1].strip()}")
    
    if result.errors:
        print("\n错误的测试:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback.split('Exception:')[-1].strip()}")
    
    # 计算成功率
    success_rate = ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100) if result.testsRun > 0 else 0
    print(f"\n测试成功率: {success_rate:.1f}%")
    
    if success_rate >= 90:
        print("✅ 测试质量: 优秀")
    elif success_rate >= 80:
        print("⚠️ 测试质量: 良好")
    else:
        print("❌ 测试质量: 需要改进")
    
    return result.wasSuccessful()

def run_specific_test(test_module):
    """运行特定测试模块"""
    
    print(f"运行测试模块: {test_module}")
    print("-" * 40)
    
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromName(test_module)
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

def main():
    """主函数"""
    
    if len(sys.argv) > 1:
        # 运行特定测试
        test_module = sys.argv[1]
        success = run_specific_test(test_module)
    else:
        # 运行所有测试
        success = run_all_tests()
    
    # 退出码
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
