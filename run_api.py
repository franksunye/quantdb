#!/usr/bin/env python3
"""
QuantDB API Server Launcher

This script starts the QuantDB API server using the new core architecture.
"""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def setup_environment():
    """Setup environment for API server"""
    print("🔧 Setting up environment...")

    # Create necessary directories
    directories = ["database", "logs", "data"]

    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Created directory: {directory}")

    # Set default environment variables if not already set
    env_defaults = {
        "ENVIRONMENT": "development",
        "DATABASE_URL": "sqlite:///./database/quantdb.db",
        "API_HOST": "0.0.0.0",
        "API_PORT": "8000",
        "LOG_LEVEL": "INFO",
        "ENABLE_CACHE": "true",
    }

    for key, value in env_defaults.items():
        if key not in os.environ:
            os.environ[key] = value
            print(f"✅ Set {key}={value}")


def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = [
        "fastapi",
        "uvicorn",
        "sqlalchemy",
        "pandas",
        "akshare",
        "psutil",
    ]

    missing = []

    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)

    if missing:
        print(f"❌ Missing required packages: {', '.join(missing)}")
        print("Please install them with: pip install " + " ".join(missing))
        return False

    return True


def main():
    """Main function to start the API server"""
    print("🚀 QuantDB API Server")
    print("=" * 50)

    # Check dependencies
    if not check_dependencies():
        sys.exit(1)

    # Setup environment
    setup_environment()

    # Import and start the API server
    try:
        print("📡 Starting API server...")
        from api.main import run_server

        run_server()
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"💥 Error starting server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
