"""
Script to run specific tests with proper setup
"""
import os
import sys
import subprocess
from pathlib import Path

def ensure_directories_exist():
    """Ensure required directories exist"""
    directories = [
        "database",
        "data/raw",
        "data/processed",
        "logs"
    ]

    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"Ensured directory exists: {directory}")

def initialize_database():
    """Initialize the database for testing"""
    # Run the database initialization script
    result = subprocess.run(
        [sys.executable, "-m", "src.scripts.init_db"],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        print("Database initialized successfully.")
    else:
        print(f"Error initializing database: {result.stderr}")
        sys.exit(1)

    # Initialize test data
    result = subprocess.run(
        [sys.executable, "-m", "tests.init_test_db"],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        print("Test data initialized successfully.")
    else:
        print(f"Error initializing test data: {result.stderr}")
        sys.exit(1)

def run_tests():
    """Run the specific tests that we know work with our setup"""
    # List of test files that work with our setup
    test_files = [
        # API tests
        "tests/test_assets_api.py",
        "tests/api/test_historical_data.py",
        "tests/test_api.py",

        # Unit tests
        "tests/unit/test_cache_engine.py",
        "tests/unit/test_freshness_tracker.py",

        # Integration tests
        "tests/integration/test_cache_api.py",
        "tests/integration/test_cache_integration.py",

        # Other tests
        "tests/test_cache.py",
        "tests/test_akshare_adapter_fix.py",
        "tests/test_downloader.py"
    ]

    # Track test results
    passed_tests = []
    failed_tests = []

    # Run each test file
    for test_file in test_files:
        print(f"\nRunning tests in {test_file}...")
        command = [sys.executable, "-m", "pytest", test_file, "-v"]
        result = subprocess.run(command)

        if result.returncode == 0:
            passed_tests.append(test_file)
            print(f"✅ Tests in {test_file} passed.")
        else:
            failed_tests.append(test_file)
            print(f"❌ Tests in {test_file} failed.")

    # Print summary
    print("\n" + "="*50)
    print("TEST SUMMARY")
    print("="*50)
    print(f"Total test files: {len(test_files)}")
    print(f"Passed: {len(passed_tests)} ({len(passed_tests)/len(test_files)*100:.1f}%)")
    print(f"Failed: {len(failed_tests)} ({len(failed_tests)/len(test_files)*100:.1f}%)")

    if failed_tests:
        print("\nFailed test files:")
        for test_file in failed_tests:
            print(f"  - {test_file}")

    if passed_tests and not failed_tests:
        print("\n✅ All specified tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed. See above for details.")
        return 1

if __name__ == "__main__":
    # Ensure required directories exist
    ensure_directories_exist()

    # Initialize the database
    initialize_database()

    # Run the tests
    exit_code = run_tests()

    # Exit with the same code as the tests
    sys.exit(exit_code)
