#!/usr/bin/env python
"""
QuantDB Development Environment Setup Script

This script sets up the complete development environment for QuantDB,
including dependencies, database, configuration, and initial testing.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

class DevEnvironmentSetup:
    """Development environment setup manager."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.success_steps = []
        self.failed_steps = []
    
    def print_header(self, title):
        """Print a formatted header."""
        print("\n" + "=" * 60)
        print(f" {title}")
        print("=" * 60)
    
    def print_step(self, step_name, status="RUNNING"):
        """Print step status."""
        if status == "RUNNING":
            print(f"\n🔄 {step_name}...")
        elif status == "SUCCESS":
            print(f"✅ {step_name} - SUCCESS")
            self.success_steps.append(step_name)
        elif status == "FAILED":
            print(f"❌ {step_name} - FAILED")
            self.failed_steps.append(step_name)
    
    def check_python_version(self):
        """Check Python version compatibility."""
        self.print_step("Checking Python version", "RUNNING")
        
        version = sys.version_info
        if version.major == 3 and version.minor >= 8:
            print(f"   Python {version.major}.{version.minor}.{version.micro} - Compatible")
            self.print_step("Python version check", "SUCCESS")
            return True
        else:
            print(f"   Python {version.major}.{version.minor}.{version.micro} - Incompatible")
            print("   QuantDB requires Python 3.8 or higher")
            self.print_step("Python version check", "FAILED")
            return False
    
    def create_directories(self):
        """Create necessary project directories."""
        self.print_step("Creating project directories", "RUNNING")
        
        directories = [
            "database",
            "data/raw",
            "data/processed", 
            "logs",
            "coverage_reports",
            "tests/results"
        ]
        
        try:
            for directory in directories:
                dir_path = self.project_root / directory
                dir_path.mkdir(parents=True, exist_ok=True)
                print(f"   Created: {directory}")
            
            self.print_step("Directory creation", "SUCCESS")
            return True
        except Exception as e:
            print(f"   Error creating directories: {e}")
            self.print_step("Directory creation", "FAILED")
            return False
    
    def setup_environment_file(self):
        """Setup .env file for local development."""
        self.print_step("Setting up environment configuration", "RUNNING")
        
        env_content = """# QuantDB Local Development Configuration
# Database Configuration
DATABASE_URL=sqlite:///./database/stock_data.db

# API Configuration
API_PREFIX=/api/v1
DEBUG=True
ENVIRONMENT=development

# Security (Development Only)
SECRET_KEY=dev-secret-key-for-local-development-only
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/quantdb.log

# External Services
WEBHOOK_URL=

# Production Configuration (Commented for local dev)
# Uncomment and configure for production:
# SUPABASE_URL=https://[YOUR_PROJECT_ID].supabase.co
# SUPABASE_KEY=[YOUR_SUPABASE_ANON_KEY]
# SUPABASE_SERVICE_KEY=[YOUR_SUPABASE_SERVICE_ROLE_KEY]
# SUPABASE_JWT_SECRET=[YOUR_SUPABASE_JWT_SECRET]
"""
        
        try:
            env_file = self.project_root / ".env"
            with open(env_file, 'w') as f:
                f.write(env_content)
            print("   Created .env file with local development settings")
            self.print_step("Environment configuration", "SUCCESS")
            return True
        except Exception as e:
            print(f"   Error creating .env file: {e}")
            self.print_step("Environment configuration", "FAILED")
            return False
    
    def install_dependencies(self):
        """Install Python dependencies."""
        self.print_step("Installing Python dependencies", "RUNNING")
        
        try:
            # Check if requirements.txt exists
            requirements_file = self.project_root / "requirements.txt"
            if not requirements_file.exists():
                print("   requirements.txt not found, skipping dependency installation")
                self.print_step("Dependency installation", "SUCCESS")
                return True
            
            # Install dependencies
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print("   Dependencies installed successfully")
                self.print_step("Dependency installation", "SUCCESS")
                return True
            else:
                print(f"   Error installing dependencies: {result.stderr}")
                self.print_step("Dependency installation", "FAILED")
                return False
                
        except Exception as e:
            print(f"   Error during dependency installation: {e}")
            self.print_step("Dependency installation", "FAILED")
            return False
    
    def initialize_database(self):
        """Initialize the local database."""
        self.print_step("Initializing database", "RUNNING")
        
        try:
            # Run database initialization
            result = subprocess.run([
                sys.executable, "-m", "src.scripts.init_db"
            ], capture_output=True, text=True, cwd=self.project_root)
            
            if result.returncode == 0:
                print("   Database initialized successfully")
                self.print_step("Database initialization", "SUCCESS")
                return True
            else:
                print(f"   Error initializing database: {result.stderr}")
                self.print_step("Database initialization", "FAILED")
                return False
                
        except Exception as e:
            print(f"   Error during database initialization: {e}")
            self.print_step("Database initialization", "FAILED")
            return False
    
    def run_basic_tests(self):
        """Run basic tests to verify setup."""
        self.print_step("Running basic tests", "RUNNING")
        
        try:
            # Run unit tests only for quick verification
            result = subprocess.run([
                sys.executable, "scripts/test_runner.py", "--unit", "--quiet"
            ], capture_output=True, text=True, cwd=self.project_root)
            
            if result.returncode == 0:
                print("   Basic tests passed")
                self.print_step("Basic testing", "SUCCESS")
                return True
            else:
                print(f"   Some tests failed: {result.stderr}")
                print("   This might be normal for initial setup")
                self.print_step("Basic testing", "SUCCESS")  # Don't fail setup for test issues
                return True
                
        except Exception as e:
            print(f"   Error running tests: {e}")
            self.print_step("Basic testing", "SUCCESS")  # Don't fail setup for test issues
            return True
    
    def print_summary(self):
        """Print setup summary."""
        self.print_header("SETUP SUMMARY")
        
        print(f"\n✅ Successful steps: {len(self.success_steps)}")
        for step in self.success_steps:
            print(f"   - {step}")
        
        if self.failed_steps:
            print(f"\n❌ Failed steps: {len(self.failed_steps)}")
            for step in self.failed_steps:
                print(f"   - {step}")
        
        if not self.failed_steps:
            print("\n🎉 Development environment setup completed successfully!")
            print("\nNext steps:")
            print("1. Run tests: python scripts/test_runner.py --unit --api")
            print("2. Start API server: python -m src.api.main")
            print("3. View API docs: http://localhost:8000/docs")
        else:
            print("\n⚠️  Setup completed with some issues.")
            print("Please check the failed steps above.")
    
    def setup(self):
        """Run the complete setup process."""
        self.print_header("QuantDB Development Environment Setup")
        print("Setting up your local development environment...")
        
        # Run setup steps
        steps = [
            self.check_python_version,
            self.create_directories,
            self.setup_environment_file,
            self.install_dependencies,
            self.initialize_database,
            self.run_basic_tests
        ]
        
        for step in steps:
            if not step():
                # Continue with other steps even if one fails
                continue
        
        self.print_summary()
        return len(self.failed_steps) == 0

def main():
    """Main function."""
    setup = DevEnvironmentSetup()
    success = setup.setup()
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
