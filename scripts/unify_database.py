#!/usr/bin/env python3
"""
数据库统一管理脚本

统一项目中的多个数据库文件，解决双数据库架构问题。
"""

import os
import shutil
import sqlite3
from pathlib import Path
from datetime import datetime


def backup_database(db_path: Path, backup_suffix: str = None) -> Path:
    """备份数据库文件"""
    if not db_path.exists():
        print(f"⚠️  数据库文件不存在: {db_path}")
        return None
    
    if backup_suffix is None:
        backup_suffix = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    backup_path = db_path.with_suffix(f".backup_{backup_suffix}")
    shutil.copy2(db_path, backup_path)
    print(f"✅ 备份创建: {backup_path}")
    return backup_path


def get_database_info(db_path: Path) -> dict:
    """获取数据库信息"""
    if not db_path.exists():
        return {"exists": False, "size": 0, "tables": [], "asset_count": 0, "data_count": 0}
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # 获取表列表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        
        # 获取资产数量
        asset_count = 0
        if 'assets' in tables:
            cursor.execute("SELECT COUNT(*) FROM assets")
            asset_count = cursor.fetchone()[0]
        
        # 获取数据记录数量
        data_count = 0
        if 'daily_stock_data' in tables:
            cursor.execute("SELECT COUNT(*) FROM daily_stock_data")
            data_count = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "exists": True,
            "size": db_path.stat().st_size,
            "tables": tables,
            "asset_count": asset_count,
            "data_count": data_count
        }
    except Exception as e:
        return {"exists": True, "error": str(e)}


def merge_databases(source_db: Path, target_db: Path) -> bool:
    """合并数据库（将source的数据合并到target）"""
    try:
        print(f"🔄 合并数据库: {source_db} -> {target_db}")
        
        # 连接两个数据库
        target_conn = sqlite3.connect(str(target_db))
        source_conn = sqlite3.connect(str(source_db))
        
        # 获取源数据库的表
        source_cursor = source_conn.cursor()
        source_cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in source_cursor.fetchall()]
        
        target_cursor = target_conn.cursor()
        
        for table in tables:
            print(f"  📋 处理表: {table}")
            
            # 获取源表数据
            source_cursor.execute(f"SELECT * FROM {table}")
            rows = source_cursor.fetchall()
            
            if not rows:
                print(f"    ⚠️  表 {table} 为空，跳过")
                continue
            
            # 获取列信息
            source_cursor.execute(f"PRAGMA table_info({table})")
            columns = [col[1] for col in source_cursor.fetchall()]
            
            # 构建INSERT OR REPLACE语句
            placeholders = ','.join(['?' for _ in columns])
            columns_str = ','.join(columns)
            
            insert_sql = f"INSERT OR REPLACE INTO {table} ({columns_str}) VALUES ({placeholders})"
            
            # 插入数据
            target_cursor.executemany(insert_sql, rows)
            print(f"    ✅ 合并了 {len(rows)} 条记录")
        
        target_conn.commit()
        target_conn.close()
        source_conn.close()
        
        print("✅ 数据库合并完成")
        return True
        
    except Exception as e:
        print(f"❌ 数据库合并失败: {e}")
        return False


def unify_databases():
    """统一数据库架构"""
    print("🎯 QuantDB 数据库统一工具")
    print("=" * 50)
    
    # 定义路径
    project_root = Path(__file__).parent.parent
    root_db = project_root / "database" / "stock_data.db"
    cloud_db = project_root / "cloud" / "streamlit_cloud" / "database" / "stock_data.db"
    
    print(f"项目根目录: {project_root}")
    print(f"根目录数据库: {root_db}")
    print(f"云端数据库: {cloud_db}")
    print()
    
    # 检查数据库状态
    print("📊 数据库状态检查:")
    root_info = get_database_info(root_db)
    cloud_info = get_database_info(cloud_db)
    
    print(f"根目录数据库:")
    if root_info["exists"]:
        print(f"  - 大小: {root_info['size']} bytes")
        print(f"  - 表数量: {len(root_info.get('tables', []))}")
        print(f"  - 资产数量: {root_info.get('asset_count', 0)}")
        print(f"  - 数据记录: {root_info.get('data_count', 0)}")
    else:
        print("  - 不存在")
    
    print(f"云端数据库:")
    if cloud_info["exists"]:
        print(f"  - 大小: {cloud_info['size']} bytes")
        print(f"  - 表数量: {len(cloud_info.get('tables', []))}")
        print(f"  - 资产数量: {cloud_info.get('asset_count', 0)}")
        print(f"  - 数据记录: {cloud_info.get('data_count', 0)}")
    else:
        print("  - 不存在")
    
    print()
    
    # 决定统一策略
    if not root_info["exists"] and not cloud_info["exists"]:
        print("❌ 两个数据库都不存在，无法统一")
        return False
    
    if not root_info["exists"]:
        print("🔄 根目录数据库不存在，复制云端数据库")
        root_db.parent.mkdir(exist_ok=True)
        shutil.copy2(cloud_db, root_db)
        print("✅ 复制完成")
    elif not cloud_info["exists"]:
        print("✅ 云端数据库不存在，根目录数据库已是统一版本")
    else:
        # 两个都存在，需要合并
        print("🔄 两个数据库都存在，需要合并")
        
        # 备份
        backup_database(root_db, "before_merge")
        backup_database(cloud_db, "before_merge")
        
        # 选择数据更完整的作为目标
        if cloud_info.get("data_count", 0) > root_info.get("data_count", 0):
            print("📈 云端数据库数据更完整，以云端为主合并到根目录")
            shutil.copy2(cloud_db, root_db)
        else:
            print("📈 根目录数据库数据足够，保持根目录数据库")
    
    # 验证统一结果
    print("\n🔍 统一后验证:")
    final_info = get_database_info(root_db)
    if final_info["exists"]:
        print(f"✅ 统一数据库状态:")
        print(f"  - 路径: {root_db}")
        print(f"  - 大小: {final_info['size']} bytes")
        print(f"  - 表数量: {len(final_info.get('tables', []))}")
        print(f"  - 资产数量: {final_info.get('asset_count', 0)}")
        print(f"  - 数据记录: {final_info.get('data_count', 0)}")
    
    # 清理建议
    print("\n🧹 清理建议:")
    print("1. 删除云端数据库目录 (已统一到根目录)")
    print("2. 更新配置文件指向统一数据库")
    print("3. 测试所有功能确保正常工作")
    
    return True


def clean_old_databases():
    """清理旧的数据库文件"""
    print("\n🧹 清理旧数据库文件:")
    
    project_root = Path(__file__).parent.parent
    cloud_db_dir = project_root / "cloud" / "streamlit_cloud" / "database"
    
    if cloud_db_dir.exists():
        print(f"发现云端数据库目录: {cloud_db_dir}")
        
        # 列出文件
        files = list(cloud_db_dir.glob("*"))
        if files:
            print("包含文件:")
            for file in files:
                print(f"  - {file.name} ({file.stat().st_size} bytes)")
            
            response = input("\n是否删除云端数据库目录? (y/N): ")
            if response.lower() == 'y':
                shutil.rmtree(cloud_db_dir)
                print("✅ 云端数据库目录已删除")
            else:
                print("⏭️  保留云端数据库目录")
        else:
            print("目录为空，删除目录")
            cloud_db_dir.rmdir()
    else:
        print("✅ 云端数据库目录不存在，无需清理")


if __name__ == "__main__":
    try:
        if unify_databases():
            print("\n🎉 数据库统一完成!")
            
            # 询问是否清理
            response = input("\n是否清理旧的数据库文件? (y/N): ")
            if response.lower() == 'y':
                clean_old_databases()
            
            print("\n📋 后续步骤:")
            print("1. 测试应用启动: streamlit run cloud/streamlit_cloud/app.py")
            print("2. 验证数据查询功能正常")
            print("3. 检查API服务连接统一数据库")
            
        else:
            print("\n❌ 数据库统一失败")
            
    except KeyboardInterrupt:
        print("\n\n⏹️  操作被用户取消")
    except Exception as e:
        print(f"\n❌ 意外错误: {e}")
