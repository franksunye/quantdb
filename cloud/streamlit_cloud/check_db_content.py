#!/usr/bin/env python3
"""
Check database content and structure
"""
import sqlite3
import os
from pathlib import Path

def check_database_content():
    """Check database content"""
    current_dir = Path(__file__).parent
    db_path = current_dir / "database" / "stock_data.db"
    
    print(f"🔍 Checking database: {db_path}")
    print(f"File exists: {db_path.exists()}")
    
    if not db_path.exists():
        print("❌ Database file does not exist!")
        return False
    
    print(f"File size: {db_path.stat().st_size} bytes")
    
    try:
        # Connect to database
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Check tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print(f"\n📋 Tables found: {len(tables)}")
        for table in tables:
            table_name = table[0]
            print(f"  - {table_name}")
            
            # Count records in each table
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                print(f"    Records: {count}")
            except Exception as e:
                print(f"    Error counting records: {e}")
        
        # Check specific tables
        expected_tables = ['assets', 'daily_stock_data', 'intraday_stock_data', 'request_logs', 'data_coverage', 'system_metrics']
        
        print(f"\n✅ Expected tables check:")
        for expected_table in expected_tables:
            if any(expected_table == table[0] for table in tables):
                print(f"  ✅ {expected_table}")
            else:
                print(f"  ❌ {expected_table} - MISSING")
        
        # If assets table exists, show sample data
        if any('assets' == table[0] for table in tables):
            print(f"\n📊 Sample assets data:")
            cursor.execute("SELECT symbol, name FROM assets LIMIT 5")
            assets = cursor.fetchall()
            for asset in assets:
                print(f"  - {asset[0]}: {asset[1]}")
        
        conn.close()
        return len(tables) > 0
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def recreate_database():
    """Recreate database with proper structure"""
    print("\n🔧 Recreating database...")
    
    current_dir = Path(__file__).parent
    db_path = current_dir / "database" / "stock_data.db"
    
    # Remove existing file
    if db_path.exists():
        os.remove(db_path)
        print("🗑️  Removed existing database file")
    
    # Add src to path
    import sys
    src_dir = current_dir / "src"
    sys.path.insert(0, str(src_dir))
    
    try:
        # Import and create database
        from api.database import engine, Base
        from api.models import Asset, DailyStockData, IntradayStockData, RequestLog, DataCoverage, SystemMetrics
        
        print("📋 Creating database tables...")
        Base.metadata.create_all(bind=engine)
        
        print("✅ Database tables created successfully!")
        
        # Verify creation
        return check_database_content()
        
    except Exception as e:
        print(f"❌ Database creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def populate_sample_data():
    """Populate with sample data"""
    print("\n📊 Populating sample data...")
    
    current_dir = Path(__file__).parent
    src_dir = current_dir / "src"
    sys.path.insert(0, str(src_dir))
    
    try:
        from api.database import SessionLocal
        from api.models import Asset
        from datetime import datetime
        
        db_session = SessionLocal()
        
        # Sample assets
        sample_assets = [
            {
                'symbol': '600000',
                'name': '浦发银行',
                'isin': 'CNE000001Z29',
                'asset_type': 'stock',
                'exchange': 'SSE',
                'currency': 'CNY',
                'industry': '银行',
                'concept': '银行股',
                'pe_ratio': 4.5,
                'pb_ratio': 0.6,
                'roe': 12.5
            },
            {
                'symbol': '000001',
                'name': '平安银行',
                'isin': 'CNE000001307',
                'asset_type': 'stock',
                'exchange': 'SZSE',
                'currency': 'CNY',
                'industry': '银行',
                'concept': '银行股',
                'pe_ratio': 5.2,
                'pb_ratio': 0.8,
                'roe': 11.8
            },
            {
                'symbol': '600519',
                'name': '贵州茅台',
                'isin': 'CNE000001315',
                'asset_type': 'stock',
                'exchange': 'SSE',
                'currency': 'CNY',
                'industry': '食品饮料',
                'concept': '白酒概念',
                'pe_ratio': 28.5,
                'pb_ratio': 12.8,
                'roe': 25.2
            }
        ]
        
        for asset_data in sample_assets:
            asset = Asset(**asset_data)
            db_session.add(asset)
            print(f"  ✅ Added {asset_data['symbol']} - {asset_data['name']}")
        
        db_session.commit()
        db_session.close()
        
        print("✅ Sample data populated successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Sample data population failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function"""
    print("🚀 Database Content Check and Repair")
    print("=" * 50)
    
    # Check current content
    has_content = check_database_content()
    
    if not has_content:
        print("\n🔧 Database appears to be empty or corrupted. Recreating...")
        
        # Recreate database
        if recreate_database():
            # Populate with sample data
            populate_sample_data()
            
            # Final check
            print("\n🔍 Final verification:")
            check_database_content()
        else:
            print("❌ Failed to recreate database")
    else:
        print("\n✅ Database appears to be working correctly")
    
    print("\n" + "=" * 50)
    print("Database check completed!")

if __name__ == "__main__":
    main()
