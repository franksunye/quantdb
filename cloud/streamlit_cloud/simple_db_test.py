#!/usr/bin/env python3
"""
Simple database test
"""
import os
import sys
from pathlib import Path

# Add src directory to Python path
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

def test_config():
    """Test configuration"""
    print("🔍 Testing configuration...")
    
    try:
        from config import DATABASE_URL, DATABASE_PATH, DB_TYPE
        print(f"DATABASE_URL: {DATABASE_URL}")
        print(f"DATABASE_PATH: {DATABASE_PATH}")
        print(f"DB_TYPE: {DB_TYPE}")
        
        # Check if database file exists
        db_exists = os.path.exists(DATABASE_PATH)
        print(f"Database file exists: {db_exists}")
        
        if db_exists:
            size = os.path.getsize(DATABASE_PATH)
            print(f"Database size: {size} bytes")
        
        return True
        
    except Exception as e:
        print(f"❌ Config test failed: {e}")
        return False

def test_engine():
    """Test SQLAlchemy engine"""
    print("\n🔍 Testing SQLAlchemy engine...")
    
    try:
        from api.database import engine
        print(f"Engine: {engine}")
        print(f"Engine URL: {engine.url}")
        
        # Test connection
        with engine.connect() as conn:
            from sqlalchemy import text
            result = conn.execute(text("SELECT 1"))
            print("✅ Engine connection successful")
            return True
            
    except Exception as e:
        print(f"❌ Engine test failed: {e}")
        return False

def test_models():
    """Test model imports"""
    print("\n🔍 Testing model imports...")
    
    try:
        from api.models import Asset, DailyStockData, IntradayStockData, RequestLog, DataCoverage, SystemMetrics
        print("✅ All models imported successfully")
        return True
        
    except Exception as e:
        print(f"❌ Model import failed: {e}")
        return False

def test_table_creation():
    """Test table creation"""
    print("\n🔍 Testing table creation...")
    
    try:
        from api.database import engine, Base
        from api.models import Asset, DailyStockData, IntradayStockData, RequestLog, DataCoverage, SystemMetrics
        
        # Create tables
        Base.metadata.create_all(bind=engine)
        print("✅ Table creation command executed")
        
        # Check if tables exist
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        print(f"Tables found: {tables}")
        
        expected_tables = ['assets', 'daily_stock_data', 'intraday_stock_data', 'request_logs', 'data_coverage', 'system_metrics']
        
        for table in expected_tables:
            if table in tables:
                print(f"  ✅ {table}")
            else:
                print(f"  ❌ {table} - MISSING")
        
        return len(tables) > 0
        
    except Exception as e:
        print(f"❌ Table creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_direct_sqlite():
    """Test direct SQLite connection"""
    print("\n🔍 Testing direct SQLite connection...")
    
    try:
        import sqlite3
        from config import DATABASE_PATH
        
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Check tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print(f"Direct SQLite tables: {[table[0] for table in tables]}")
        
        conn.close()
        return len(tables) > 0
        
    except Exception as e:
        print(f"❌ Direct SQLite test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Simple Database Test")
    print("=" * 40)
    
    tests = [
        ("Configuration", test_config),
        ("SQLAlchemy Engine", test_engine),
        ("Model Imports", test_models),
        ("Table Creation", test_table_creation),
        ("Direct SQLite", test_direct_sqlite)
    ]
    
    passed = 0
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 30)
        
        try:
            if test_func():
                print(f"✅ {test_name} PASSED")
                passed += 1
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} CRASHED: {e}")
    
    print("\n" + "=" * 40)
    print(f"📊 Results: {passed}/{len(tests)} tests passed")
    
    return passed == len(tests)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
