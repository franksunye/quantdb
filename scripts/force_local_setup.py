#!/usr/bin/env python
"""
Force local development setup for QuantDB
"""
import os
import sys
from pathlib import Path

def force_local_setup():
    """Force the environment to use local SQLite database."""
    print("=" * 50)
    print("Forcing Local Development Setup")
    print("=" * 50)
    
    # 1. Clear any problematic environment variables
    problematic_vars = []
    for key in list(os.environ.keys()):
        if any(keyword in key.upper() for keyword in ['SUPABASE', 'POSTGRES']) and 'DATABASE' in key.upper():
            problematic_vars.append(key)
            del os.environ[key]
    
    if problematic_vars:
        print(f"Cleared problematic environment variables: {problematic_vars}")
    
    # 2. Set local database URL
    os.environ['DATABASE_URL'] = 'sqlite:///./database/stock_data.db'
    print("Set DATABASE_URL to local SQLite")
    
    # 3. Ensure .env file has correct settings
    env_content = """# Database Configuration
# Local SQLite database for development
DATABASE_URL=sqlite:///./database/stock_data.db

# API Configuration
API_PREFIX=/api/v1
DEBUG=True
ENVIRONMENT=development

# Security
SECRET_KEY=dev-secret-key-for-local-development-only
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/quantdb.log

# External Services
WEBHOOK_URL=

# Note: Supabase configuration is commented out for local development
# Uncomment and configure these for production deployment:
# SUPABASE_URL=https://[YOUR_PROJECT_ID].supabase.co
# SUPABASE_KEY=[YOUR_SUPABASE_ANON_KEY]
# SUPABASE_SERVICE_KEY=[YOUR_SUPABASE_SERVICE_ROLE_KEY]
# SUPABASE_JWT_SECRET=[YOUR_SUPABASE_JWT_SECRET]
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    print("Updated .env file with local settings")
    
    # 4. Create necessary directories
    directories = ['database', 'data/raw', 'data/processed', 'logs', 'coverage_reports']
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"Ensured directory exists: {directory}")
    
    # 5. Test the configuration
    print("\nTesting configuration...")
    try:
        # Add project root to path
        project_root = Path(__file__).parent.parent
        sys.path.insert(0, str(project_root))
        
        from src.config import DATABASE_URL, DB_TYPE
        print(f"✅ DATABASE_URL: {DATABASE_URL}")
        print(f"✅ DB_TYPE: {DB_TYPE}")
        
        if 'sqlite' in DATABASE_URL.lower():
            print("✅ Configuration is correctly set to SQLite")
        else:
            print("❌ Configuration is still not using SQLite")
            return False
            
    except Exception as e:
        print(f"❌ Error testing configuration: {e}")
        return False
    
    # 6. Initialize database
    print("\nInitializing database...")
    try:
        from src.scripts.init_db import init_db
        if init_db():
            print("✅ Database initialized successfully")
        else:
            print("❌ Database initialization failed")
            return False
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("✅ Local setup completed successfully!")
    print("You can now run tests with:")
    print("python .\\scripts\\test_runner.py --unit --api")
    print("=" * 50)
    
    return True

if __name__ == "__main__":
    success = force_local_setup()
    if not success:
        sys.exit(1)
