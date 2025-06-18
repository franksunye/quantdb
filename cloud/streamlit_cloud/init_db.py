#!/usr/bin/env python3
"""
Database initialization script for QuantDB Cloud Edition
"""
import os
import sys
from pathlib import Path

# Add src directory to Python path
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

def init_database():
    """Initialize database tables"""
    try:
        print("🔧 Initializing QuantDB database...")
        
        # Import database components
        from api.database import engine, Base
        from api.models import Asset, DailyStockData, IntradayStockData, RequestLog, DataCoverage, SystemMetrics
        
        print("📋 Creating database tables...")
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        print("✅ Database tables created successfully!")
        
        # Verify tables exist
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        expected_tables = [
            'assets',
            'daily_stock_data',
            'intraday_stock_data',
            'request_logs',
            'data_coverage',
            'system_metrics'
        ]
        
        print("📊 Verifying tables:")
        for table in expected_tables:
            if table in tables:
                print(f"  ✅ {table}")
            else:
                print(f"  ❌ {table} - MISSING")
        
        print(f"\n🎯 Total tables created: {len(tables)}")
        print("🚀 Database initialization complete!")
        
        return True
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

def test_database():
    """Test database connectivity"""
    try:
        print("\n🧪 Testing database connectivity...")
        
        from api.database import SessionLocal
        from api.models import Asset
        
        # Test session creation
        db_session = SessionLocal()
        
        try:
            # Test query
            count = db_session.query(Asset).count()
            print(f"✅ Database query successful - Asset count: {count}")
            
        finally:
            db_session.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 QuantDB Database Initialization")
    print("=" * 50)
    
    # Initialize database
    if init_database():
        # Test database
        if test_database():
            print("\n🎉 Database setup completed successfully!")
            sys.exit(0)
        else:
            print("\n❌ Database test failed!")
            sys.exit(1)
    else:
        print("\n❌ Database initialization failed!")
        sys.exit(1)
