#!/usr/bin/env python3
"""
Debug database connection and data
"""
import os
import sys
from pathlib import Path

# Add src directory to Python path
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

def debug_database():
    """Debug database connection"""
    print("🔍 Debugging database connection...")
    
    # Check file paths
    print(f"Current directory: {current_dir}")
    print(f"Src directory: {src_dir}")
    
    # Check database file
    db_path = current_dir / "database" / "stock_data.db"
    print(f"Database path: {db_path}")
    print(f"Database exists: {db_path.exists()}")
    
    if db_path.exists():
        print(f"Database size: {db_path.stat().st_size} bytes")
    
    # Check config
    try:
        from config import DATABASE_URL, DATABASE_PATH, DB_TYPE
        print(f"DATABASE_URL: {DATABASE_URL}")
        print(f"DATABASE_PATH: {DATABASE_PATH}")
        print(f"DB_TYPE: {DB_TYPE}")
    except Exception as e:
        print(f"❌ Config import error: {e}")
        return False
    
    # Test database connection
    try:
        from api.database import engine, SessionLocal
        from api.models import Asset, DailyStockData
        
        print("✅ Database modules imported successfully")
        
        # Test connection
        db_session = SessionLocal()
        
        try:
            # Test asset query
            asset_count = db_session.query(Asset).count()
            print(f"Asset count: {asset_count}")
            
            # List assets
            assets = db_session.query(Asset).limit(5).all()
            print("Sample assets:")
            for asset in assets:
                print(f"  - {asset.symbol}: {asset.name}")
            
            # Test data query
            data_count = db_session.query(DailyStockData).count()
            print(f"Daily data count: {data_count}")
            
            return True
            
        finally:
            db_session.close()
            
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        import traceback
        traceback.print_exc()
        return False

def debug_streamlit_environment():
    """Debug Streamlit environment"""
    print("\n🔍 Debugging Streamlit environment...")
    
    # Check if running in Streamlit
    try:
        import streamlit as st
        print("✅ Streamlit imported successfully")
        
        # Check if we're in Streamlit context
        try:
            # This will work if we're in Streamlit context
            st.write("Test")
            print("✅ Running in Streamlit context")
        except:
            print("ℹ️  Not in Streamlit context (normal for script)")
            
    except Exception as e:
        print(f"❌ Streamlit import error: {e}")

def debug_file_permissions():
    """Debug file permissions"""
    print("\n🔍 Debugging file permissions...")
    
    db_path = current_dir / "database" / "stock_data.db"
    
    try:
        # Check read permission
        with open(db_path, 'rb') as f:
            data = f.read(100)  # Read first 100 bytes
        print("✅ Database file is readable")
        print(f"First 100 bytes: {data[:20]}...")
        
    except Exception as e:
        print(f"❌ File read error: {e}")

def main():
    """Main debug function"""
    print("🚀 QuantDB Database Debug")
    print("=" * 50)
    
    debug_database()
    debug_streamlit_environment()
    debug_file_permissions()
    
    print("\n" + "=" * 50)
    print("Debug completed!")

if __name__ == "__main__":
    main()
