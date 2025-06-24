#!/usr/bin/env python3
"""
调试06660资产查询问题

分析为什么Stock Data页面能找到06660，但Asset Info页面找不到
"""

import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def debug_06660_issue():
    """调试06660资产查询问题"""
    
    print("=" * 70)
    print("调试06660资产查询问题")
    print("=" * 70)
    
    try:
        # 导入必要的模块
        from core.database import get_db
        from core.services.asset_info_service import AssetInfoService
        from core.models.asset import Asset
        
        # 获取数据库会话
        db_session = next(get_db())
        
        print(f"\n调试开始时间: {datetime.now()}")
        
        # 1. 直接查询数据库中的06660
        print("\n" + "=" * 40)
        print("1. 直接查询数据库中的06660")
        print("=" * 40)
        
        # 查询所有可能的06660变体
        symbol_variants = ['06660', '6660', 'HK06660', 'hk06660']
        
        for variant in symbol_variants:
            assets = db_session.query(Asset).filter(Asset.symbol == variant).all()
            print(f"查询 symbol='{variant}': 找到 {len(assets)} 条记录")
            for asset in assets:
                print(f"  - ID: {asset.asset_id}, Symbol: {asset.symbol}, Name: {asset.name}, Exchange: {asset.exchange}")
        
        # 2. 查询所有港股
        print("\n" + "=" * 40)
        print("2. 查询所有港股（HKEX）")
        print("=" * 40)
        
        hk_assets = db_session.query(Asset).filter(Asset.exchange == 'HKEX').all()
        print(f"总共找到 {len(hk_assets)} 只港股")
        
        # 查找包含6660的港股
        matching_hk_assets = [asset for asset in hk_assets if '6660' in asset.symbol]
        print(f"包含'6660'的港股: {len(matching_hk_assets)} 只")
        for asset in matching_hk_assets:
            print(f"  - ID: {asset.asset_id}, Symbol: {asset.symbol}, Name: {asset.name}")
        
        # 3. 测试AssetInfoService的查询逻辑
        print("\n" + "=" * 40)
        print("3. 测试AssetInfoService的查询逻辑")
        print("=" * 40)
        
        asset_service = AssetInfoService(db_session)
        print(f"只读模式: {asset_service._is_readonly}")
        
        # 测试_standardize_symbol方法
        test_symbols = ['06660', '6660', 'HK06660', 'hk06660']
        for symbol in test_symbols:
            standardized = asset_service._standardize_symbol(symbol)
            print(f"标准化 '{symbol}' -> '{standardized}'")
        
        # 4. 模拟get_or_create_asset的查询逻辑
        print("\n" + "=" * 40)
        print("4. 模拟get_or_create_asset的查询逻辑")
        print("=" * 40)
        
        test_symbol = '06660'
        standardized_symbol = asset_service._standardize_symbol(test_symbol)
        print(f"原始符号: {test_symbol}")
        print(f"标准化后: {standardized_symbol}")
        
        # 直接查询数据库
        asset = db_session.query(Asset).filter(Asset.symbol == standardized_symbol).first()
        if asset:
            print(f"✅ 找到资产: ID={asset.asset_id}, Symbol={asset.symbol}, Name={asset.name}")
        else:
            print(f"❌ 未找到资产")
        
        # 5. 测试市场检测
        print("\n" + "=" * 40)
        print("5. 测试市场检测")
        print("=" * 40)
        
        market = asset_service._detect_market(standardized_symbol)
        print(f"检测到的市场类型: {market}")
        
        # 6. 测试完整的get_or_create_asset流程
        print("\n" + "=" * 40)
        print("6. 测试完整的get_or_create_asset流程")
        print("=" * 40)
        
        try:
            result = asset_service.get_or_create_asset(test_symbol)
            if isinstance(result, tuple):
                asset_obj, metadata = result
            else:
                asset_obj = result
                metadata = {}
            
            print(f"✅ get_or_create_asset成功")
            print(f"  - Asset ID: {getattr(asset_obj, 'asset_id', 'None')}")
            print(f"  - Symbol: {asset_obj.symbol}")
            print(f"  - Name: {asset_obj.name}")
            print(f"  - Exchange: {asset_obj.exchange}")
            print(f"  - Data Source: {asset_obj.data_source}")
            
            cache_info = metadata.get('cache_info', {})
            print(f"  - Cache Hit: {cache_info.get('cache_hit', False)}")
            print(f"  - AKShare Called: {cache_info.get('akshare_called', False)}")
            
        except Exception as e:
            print(f"❌ get_or_create_asset失败: {e}")
            import traceback
            traceback.print_exc()
        
        # 7. 检查数据库连接和事务状态
        print("\n" + "=" * 40)
        print("7. 检查数据库连接和事务状态")
        print("=" * 40)
        
        try:
            # 测试简单查询
            count = db_session.query(Asset).count()
            print(f"数据库连接正常，总资产数: {count}")
            
            # 测试写操作
            from sqlalchemy import text
            db_session.execute(text("CREATE TEMP TABLE test_write (id INTEGER)"))
            db_session.execute(text("DROP TABLE test_write"))
            db_session.rollback()
            print("数据库写权限正常")
            
        except Exception as e:
            print(f"数据库操作异常: {e}")
        
    except Exception as e:
        print(f"调试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        try:
            db_session.close()
        except:
            pass
    
    print(f"\n调试结束时间: {datetime.now()}")
    print("=" * 70)

if __name__ == "__main__":
    debug_06660_issue()
