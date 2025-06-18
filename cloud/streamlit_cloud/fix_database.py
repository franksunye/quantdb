#!/usr/bin/env python3
"""
Fix database issues for cloud deployment
"""
import os
import sys
import shutil
from pathlib import Path

# Add src directory to Python path
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

def backup_current_database():
    """Backup current database"""
    db_path = current_dir / "database" / "stock_data.db"
    backup_path = current_dir / "database" / "stock_data.db.backup"
    
    if db_path.exists():
        shutil.copy2(db_path, backup_path)
        print(f"✅ Database backed up to {backup_path}")
        return True
    return False

def create_fresh_database():
    """Create a fresh database with proper structure"""
    print("🔧 Creating fresh database...")
    
    db_path = current_dir / "database" / "stock_data.db"
    
    # Remove existing database
    if db_path.exists():
        os.remove(db_path)
        print("🗑️  Removed existing database")
    
    try:
        # Import database components
        from api.database import engine, Base, SessionLocal
        from api.models import Asset, DailyStockData, IntradayStockData, RequestLog, DataCoverage, SystemMetrics
        
        # Create all tables
        print("📋 Creating database tables...")
        Base.metadata.create_all(bind=engine)
        
        # Verify tables were created
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        expected_tables = ['assets', 'daily_stock_data', 'intraday_stock_data', 'request_logs', 'data_coverage', 'system_metrics']
        
        print("✅ Tables created:")
        for table in expected_tables:
            if table in tables:
                print(f"  ✅ {table}")
            else:
                print(f"  ❌ {table} - MISSING")
        
        return len(tables) >= len(expected_tables)
        
    except Exception as e:
        print(f"❌ Database creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def populate_essential_data():
    """Populate essential sample data"""
    print("📊 Populating essential data...")
    
    try:
        from api.database import SessionLocal
        from api.models import Asset
        from datetime import datetime
        
        db_session = SessionLocal()
        
        # Essential sample assets
        essential_assets = [
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
        
        for asset_data in essential_assets:
            # Check if asset already exists
            existing = db_session.query(Asset).filter(Asset.symbol == asset_data['symbol']).first()
            if not existing:
                asset = Asset(**asset_data)
                db_session.add(asset)
                print(f"  ✅ Added {asset_data['symbol']} - {asset_data['name']}")
            else:
                print(f"  ⏭️  {asset_data['symbol']} already exists")
        
        db_session.commit()
        
        # Verify data
        asset_count = db_session.query(Asset).count()
        print(f"✅ Total assets in database: {asset_count}")
        
        db_session.close()
        return asset_count > 0
        
    except Exception as e:
        print(f"❌ Data population failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_database_functionality():
    """Test database functionality"""
    print("🧪 Testing database functionality...")
    
    try:
        from api.database import SessionLocal
        from api.models import Asset
        
        db_session = SessionLocal()
        
        # Test basic query
        assets = db_session.query(Asset).limit(3).all()
        print(f"✅ Query test passed - found {len(assets)} assets")
        
        for asset in assets:
            print(f"  - {asset.symbol}: {asset.name}")
        
        db_session.close()
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def main():
    """Main repair function"""
    print("🚀 Database Repair Tool for Cloud Deployment")
    print("=" * 60)
    
    # Step 1: Backup current database
    print("\n📋 Step 1: Backup current database")
    backup_current_database()
    
    # Step 2: Create fresh database
    print("\n📋 Step 2: Create fresh database")
    if not create_fresh_database():
        print("❌ Failed to create database. Exiting.")
        return False
    
    # Step 3: Populate essential data
    print("\n📋 Step 3: Populate essential data")
    if not populate_essential_data():
        print("❌ Failed to populate data. Exiting.")
        return False
    
    # Step 4: Test functionality
    print("\n📋 Step 4: Test functionality")
    if not test_database_functionality():
        print("❌ Database test failed. Exiting.")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 Database repair completed successfully!")
    print("📁 Database file ready for cloud deployment")
    
    # Show file info
    db_path = current_dir / "database" / "stock_data.db"
    if db_path.exists():
        size_kb = db_path.stat().st_size / 1024
        print(f"📊 Database size: {size_kb:.1f} KB")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
