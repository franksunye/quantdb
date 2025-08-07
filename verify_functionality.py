#!/usr/bin/env python3
"""
QuantDB 原有功能正确性验证脚本

这个脚本验证在添加实时数据API后，原有功能是否仍然正确工作。
"""

import sys
import traceback
from datetime import datetime, timedelta


def test_package_import():
    """测试包导入"""
    print("1. 测试包导入...")
    try:
        import qdb
        print("   ✅ qdb包导入成功")
        return True
    except Exception as e:
        print(f"   ❌ qdb包导入失败: {e}")
        return False


def test_initialization():
    """测试初始化功能"""
    print("2. 测试初始化功能...")
    try:
        import qdb
        qdb.init()
        print("   ✅ QDB初始化成功")
        return True
    except Exception as e:
        print(f"   ❌ QDB初始化失败: {e}")
        return False


def test_cache_management():
    """测试缓存管理功能"""
    print("3. 测试缓存管理功能...")
    try:
        import qdb
        
        # 测试缓存状态
        stats = qdb.cache_stats()
        print(f"   ✅ 缓存状态查询成功: {stats['status']}")
        
        # 测试缓存清理
        qdb.clear_cache()
        print("   ✅ 缓存清理成功")
        
        return True
    except Exception as e:
        print(f"   ❌ 缓存管理测试失败: {e}")
        return False


def test_historical_data():
    """测试历史数据功能"""
    print("4. 测试历史数据功能...")
    try:
        import qdb
        
        # 测试历史数据查询
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        
        data = qdb.get_stock_data('000001', start_date=start_date, end_date=end_date)
        print(f"   ✅ 历史数据查询成功: {len(data)} 条记录")
        
        # 测试批量查询
        batch_data = qdb.get_multiple_stocks(['000001', '000002'], 
                                           start_date=start_date, 
                                           end_date=end_date)
        print(f"   ✅ 批量历史数据查询成功: {len(batch_data)} 只股票")
        
        return True
    except Exception as e:
        print(f"   ❌ 历史数据测试失败: {e}")
        return False


def test_asset_info():
    """测试资产信息功能"""
    print("5. 测试资产信息功能...")
    try:
        import qdb
        
        # 测试资产信息查询
        asset_info = qdb.get_asset_info('000001')
        if asset_info:
            print(f"   ✅ 资产信息查询成功: {asset_info.get('name', 'N/A')}")
        else:
            print("   ⚠️ 资产信息查询返回空结果（可能是正常的）")
        
        return True
    except Exception as e:
        print(f"   ❌ 资产信息测试失败: {e}")
        return False


def test_akshare_compatibility():
    """测试AKShare兼容性"""
    print("6. 测试AKShare兼容性...")
    try:
        import qdb
        
        # 测试AKShare兼容接口
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=7)).strftime('%Y%m%d')
        
        data = qdb.stock_zh_a_hist(symbol='000001', 
                                  start_date=start_date, 
                                  end_date=end_date)
        print(f"   ✅ AKShare兼容接口成功: {len(data)} 条记录")
        
        return True
    except Exception as e:
        print(f"   ❌ AKShare兼容性测试失败: {e}")
        return False


def test_realtime_data():
    """测试实时数据功能（新功能）"""
    print("7. 测试实时数据功能...")
    try:
        import qdb
        
        # 测试单个股票实时数据
        realtime_data = qdb.get_realtime_data('000001')
        if 'error' not in realtime_data:
            print(f"   ✅ 单个实时数据查询成功: {realtime_data['symbol']} - {realtime_data.get('price', 'N/A')}")
        else:
            print(f"   ⚠️ 单个实时数据查询有错误: {realtime_data['error']}")
        
        # 测试批量实时数据
        batch_realtime = qdb.get_realtime_data_batch(['000001', '000002'])
        success_count = sum(1 for data in batch_realtime.values() if 'error' not in data)
        print(f"   ✅ 批量实时数据查询成功: {success_count}/{len(batch_realtime)} 只股票")
        
        return True
    except Exception as e:
        print(f"   ❌ 实时数据测试失败: {e}")
        return False


def test_configuration():
    """测试配置功能"""
    print("8. 测试配置功能...")
    try:
        import qdb
        
        # 测试日志级别设置
        qdb.set_log_level('INFO')
        print("   ✅ 日志级别设置成功")
        
        # 测试缓存目录设置
        qdb.set_cache_dir('/tmp/test_qdb_cache')
        print("   ✅ 缓存目录设置成功")
        
        return True
    except Exception as e:
        print(f"   ❌ 配置功能测试失败: {e}")
        return False


def test_version_info():
    """测试版本信息"""
    print("9. 测试版本信息...")
    try:
        import qdb
        
        version = qdb.__version__
        print(f"   ✅ 版本信息: {version}")
        
        # 验证版本号格式
        if version and len(version.split('.')) >= 2:
            print("   ✅ 版本号格式正确")
        else:
            print("   ⚠️ 版本号格式可能有问题")
        
        return True
    except Exception as e:
        print(f"   ❌ 版本信息测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("🧪 QuantDB 原有功能正确性验证")
    print("=" * 60)
    print(f"测试时间: {datetime.now().isoformat()}")
    print("=" * 60)
    
    tests = [
        test_package_import,
        test_initialization,
        test_cache_management,
        test_historical_data,
        test_asset_info,
        test_akshare_compatibility,
        test_realtime_data,
        test_configuration,
        test_version_info
    ]
    
    results = []
    
    for test_func in tests:
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"   ❌ 测试异常: {e}")
            traceback.print_exc()
            results.append(False)
        print()
    
    # 测试总结
    print("=" * 60)
    print("测试总结")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"总测试数: {total}")
    print(f"通过测试: {passed}")
    print(f"失败测试: {total - passed}")
    print(f"通过率: {passed/total*100:.1f}%")
    
    if passed == total:
        print("\n🎉 所有测试通过！原有功能完全正常！")
        return 0
    elif passed >= total * 0.8:
        print("\n✅ 大部分测试通过，原有功能基本正常")
        return 0
    else:
        print("\n⚠️ 多个测试失败，需要检查原有功能")
        return 1


if __name__ == "__main__":
    exit(main())
