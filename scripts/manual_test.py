#!/usr/bin/env python
"""
QuantDB Manual Testing Script

This script performs comprehensive manual testing of all QuantDB components
to verify functionality in the local development environment.
"""

import os
import sys
import time
import requests
import subprocess
import signal
from pathlib import Path
from datetime import datetime

class ManualTester:
    """Manual testing suite for QuantDB."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.api_process = None
        self.test_results = []
        
    def print_header(self, title):
        """Print a formatted header."""
        print("\n" + "=" * 60)
        print(f" {title}")
        print("=" * 60)
    
    def print_test(self, test_name, status, details=""):
        """Print test result."""
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {test_name}")
        if details:
            print(f"   {details}")
        self.test_results.append((test_name, status, details))
    
    def test_environment_setup(self):
        """Test environment configuration."""
        self.print_header("Environment Setup Tests")
        
        # Test 1: Check .env file
        env_file = self.project_root / ".env"
        if env_file.exists():
            self.print_test("Environment file exists", True, str(env_file))
        else:
            self.print_test("Environment file exists", False, "Run: python setup_dev_env.py")
        
        # Test 2: Check database configuration
        try:
            sys.path.insert(0, str(self.project_root))
            from core.utils.config import DATABASE_URL, DB_TYPE
            
            if 'sqlite' in DATABASE_URL.lower():
                self.print_test("Database configuration", True, f"SQLite: {DATABASE_URL}")
            else:
                self.print_test("Database configuration", False, f"Not SQLite: {DATABASE_URL}")
        except Exception as e:
            self.print_test("Database configuration", False, str(e))
        
        # Test 3: Check required directories
        required_dirs = ['database', 'logs', 'data/raw', 'data/processed']
        for directory in required_dirs:
            dir_path = self.project_root / directory
            if dir_path.exists():
                self.print_test(f"Directory: {directory}", True)
            else:
                self.print_test(f"Directory: {directory}", False, "Missing")
    
    def test_database_connection(self):
        """Test database connectivity."""
        self.print_header("Database Connection Tests")
        
        try:
            from core.database import engine
            from sqlalchemy import text
            
            # Test connection
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                self.print_test("Database connection", True, f"Result: {result.fetchone()}")
            
            # Test table existence
            from core.models import Asset, DailyStockData
            from core.database import SessionLocal
            
            session = SessionLocal()
            try:
                asset_count = session.query(Asset).count()
                data_count = session.query(DailyStockData).count()
                self.print_test("Database tables", True, f"Assets: {asset_count}, Data: {data_count}")
            finally:
                session.close()
                
        except Exception as e:
            self.print_test("Database connection", False, str(e))
    
    def test_logging_system(self):
        """Test unified logging system."""
        self.print_header("Logging System Tests")
        
        try:
            from core.utils.logger import get_logger
            
            # Test logger creation
            logger = get_logger('manual_test')
            self.print_test("Logger creation", True, "Unified logger created")
            
            # Test logging levels
            logger.info("Manual test info message")
            logger.warning("Manual test warning message")
            logger.error("Manual test error message")
            
            # Check log file
            log_file = self.project_root / "logs" / "quantdb.log"
            if log_file.exists():
                self.print_test("Log file creation", True, str(log_file))
            else:
                self.print_test("Log file creation", False, "Log file not found")
                
        except Exception as e:
            self.print_test("Logging system", False, str(e))
    
    def start_api_server(self):
        """Start the API server for testing."""
        try:
            self.api_process = subprocess.Popen(
                [sys.executable, "-m", "src.api.main"],
                cwd=self.project_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait for server to start
            for _ in range(10):
                try:
                    response = requests.get("http://localhost:8000/api/v1/health", timeout=2)
                    if response.status_code == 200:
                        return True
                except:
                    pass
                time.sleep(1)
            
            return False
        except Exception:
            return False
    
    def stop_api_server(self):
        """Stop the API server."""
        if self.api_process:
            self.api_process.terminate()
            self.api_process.wait()
            self.api_process = None
    
    def test_api_endpoints(self):
        """Test API endpoints."""
        self.print_header("API Endpoint Tests")
        
        # Start API server
        if not self.start_api_server():
            self.print_test("API server startup", False, "Failed to start server")
            return
        
        self.print_test("API server startup", True, "Server started on port 8000")
        
        try:
            # Test root endpoint
            response = requests.get("http://localhost:8000/", timeout=5)
            if response.status_code == 200:
                self.print_test("Root endpoint", True, f"Status: {response.status_code}")
            else:
                self.print_test("Root endpoint", False, f"Status: {response.status_code}")
            
            # Test health endpoint
            response = requests.get("http://localhost:8000/api/v1/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.print_test("Health endpoint", True, f"Version: {data.get('version')}")
            else:
                self.print_test("Health endpoint", False, f"Status: {response.status_code}")
            
            # Test API documentation
            response = requests.get("http://localhost:8000/api/v1/docs", timeout=5)
            if response.status_code == 200:
                self.print_test("API documentation", True, "Swagger UI accessible")
            else:
                self.print_test("API documentation", False, f"Status: {response.status_code}")
            
            # Test assets endpoint
            response = requests.get("http://localhost:8000/api/v1/assets", timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.print_test("Assets endpoint", True, f"Assets count: {len(data)}")
            else:
                self.print_test("Assets endpoint", False, f"Status: {response.status_code}")
            
        except Exception as e:
            self.print_test("API endpoints", False, str(e))
        finally:
            self.stop_api_server()
    
    def test_cache_performance(self):
        """Test cache performance."""
        self.print_header("Cache Performance Tests")

        try:
            from core.services.stock_data_service import StockDataService
            from core.database import SessionLocal
            from core.cache.akshare_adapter import AKShareAdapter

            # Create dependencies
            db = SessionLocal()
            akshare_adapter = AKShareAdapter()
            service = StockDataService(db=db, akshare_adapter=akshare_adapter)

            try:
                # First call (from AKShare)
                start_time = time.time()
                data1 = service.get_stock_data('600000', '20230103', '20230105')
                time1 = time.time() - start_time

                # Second call (from cache)
                start_time = time.time()
                data2 = service.get_stock_data('600000', '20230103', '20230105')
                time2 = time.time() - start_time

                if len(data1) > 0 and len(data2) > 0:
                    speedup = time1 / time2 if time2 > 0 else float('inf')
                    self.print_test("Cache performance", True,
                                  f"First: {time1:.3f}s, Second: {time2:.3f}s, Speedup: {speedup:.1f}x")
                else:
                    self.print_test("Cache performance", False, "No data returned")
            finally:
                db.close()

        except Exception as e:
            self.print_test("Cache performance", False, str(e))
    
    def test_monitoring_system(self):
        """Test monitoring system."""
        self.print_header("Monitoring System Tests")

        try:
            from core.services.monitoring_service import MonitoringService
            from core.database import SessionLocal

            # Create dependencies
            db = SessionLocal()
            monitor = MonitoringService(db=db)

            try:
                # Test detailed coverage
                coverage = monitor.get_detailed_coverage()
                self.print_test("Data coverage stats", True, f"Coverage: {len(coverage)} symbols")

                # Test water pool status
                status = monitor.get_water_pool_status()
                self.print_test("Water pool status", True, f"Status keys: {list(status.keys())}")
            finally:
                db.close()

        except Exception as e:
            self.print_test("Monitoring system", False, str(e))
    
    def run_all_tests(self):
        """Run all manual tests."""
        print("🧪 QuantDB Manual Testing Suite")
        print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Run all test suites
        self.test_environment_setup()
        self.test_database_connection()
        self.test_logging_system()
        self.test_api_endpoints()
        self.test_cache_performance()
        self.test_monitoring_system()
        
        # Print summary
        self.print_header("Test Summary")
        
        passed = sum(1 for _, status, _ in self.test_results if status)
        total = len(self.test_results)
        
        print(f"📊 Total Tests: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {total - passed}")
        print(f"📈 Success Rate: {passed/total*100:.1f}%")
        
        if total - passed > 0:
            print("\n❌ Failed Tests:")
            for test_name, status, details in self.test_results:
                if not status:
                    print(f"   - {test_name}: {details}")
        
        print(f"\n🎯 Overall Status: {'✅ PASS' if passed == total else '❌ FAIL'}")
        
        return passed == total

def main():
    """Main function."""
    tester = ManualTester()
    
    try:
        success = tester.run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️ Testing interrupted by user")
        sys.exit(1)
    finally:
        # Ensure API server is stopped
        tester.stop_api_server()

if __name__ == "__main__":
    main()
