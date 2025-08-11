#!/usr/bin/env python
"""
Environment diagnostic script for QuantDB
"""
import os
import sys
from pathlib import Path


def diagnose_environment():
    """Diagnose the current environment configuration."""
    print("=" * 60)
    print("QuantDB Environment Diagnostic")
    print("=" * 60)

    # 1. Basic environment info
    print("\n1. Basic Environment Info:")
    print(f"   Python version: {sys.version}")
    print(f"   Current working directory: {os.getcwd()}")
    print(f"   Script location: {__file__}")

    # 2. Check for .env file
    print("\n2. Environment File Check:")
    env_file = Path(".env")
    if env_file.exists():
        print("   ✅ .env file exists")
        print("   Contents:")
        with open(".env", "r") as f:
            for line_num, line in enumerate(f, 1):
                if line.strip() and not line.strip().startswith("#"):
                    print(f"      {line_num}: {line.strip()}")
    else:
        print("   ❌ .env file does not exist")

    # 3. Environment variables
    print("\n3. Relevant Environment Variables:")
    relevant_vars = []
    for key, value in os.environ.items():
        if any(keyword in key.upper() for keyword in ["DATABASE", "SUPABASE", "POSTGRES", "SQL"]):
            relevant_vars.append((key, value))

    if relevant_vars:
        for key, value in sorted(relevant_vars):
            print(f"   {key}: {value}")
    else:
        print("   No relevant environment variables found")

    # 4. Try to import config
    print("\n4. Configuration Import Test:")
    try:
        # Add project root to path
        project_root = Path(__file__).parent.parent
        sys.path.insert(0, str(project_root))

        from core.utils.config import DATABASE_URL, DB_TYPE

        print(f"   ✅ Config imported successfully")
        print(f"   DATABASE_URL: {DATABASE_URL}")
        print(f"   DB_TYPE: {DB_TYPE}")

        # Check if it's trying to connect to Supabase
        if "supabase" in DATABASE_URL.lower() or "postgres" in DATABASE_URL.lower():
            print("   ⚠️  WARNING: Configuration is pointing to Supabase/PostgreSQL!")
            print("   This should be SQLite for local development.")
        else:
            print("   ✅ Configuration looks correct for local development")

    except Exception as e:
        print(f"   ❌ Error importing config: {e}")
        import traceback

        traceback.print_exc()

    # 5. Test database connection
    print("\n5. Database Connection Test:")
    try:
        from sqlalchemy import text

        from core.database import engine

        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print(f"   ✅ Database connection successful: {result.fetchone()}")
    except Exception as e:
        print(f"   ❌ Database connection failed: {e}")
        import traceback

        traceback.print_exc()

    # 6. Check database file
    print("\n6. Database File Check:")
    try:
        from core.utils.config import DATABASE_PATH

        db_path = Path(DATABASE_PATH)
        if db_path.exists():
            print(f"   ✅ Database file exists: {db_path}")
            print(f"   File size: {db_path.stat().st_size} bytes")
        else:
            print(f"   ⚠️  Database file does not exist: {db_path}")
            print(f"   Parent directory exists: {db_path.parent.exists()}")
    except Exception as e:
        print(f"   ❌ Error checking database file: {e}")

    print("\n" + "=" * 60)
    print("Diagnostic Complete")
    print("=" * 60)


if __name__ == "__main__":
    diagnose_environment()
