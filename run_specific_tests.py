#!/usr/bin/env python3
"""
QuantDB Specific Test Runner

This script runs a curated set of tests that are known to work reliably in CI/CD environments.
It focuses on core functionality and avoids tests that might have environment-specific issues.

Usage:
    python run_specific_tests.py
    python run_specific_tests.py --verbose
    python run_specific_tests.py --coverage
"""

import argparse
import subprocess
import sys
import os
from pathlib import Path


def ensure_directories():
    """Ensure required directories exist."""
    directories = [
        "database",
        "data/raw", 
        "data/processed",
        "logs",
        "coverage_reports"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)


def initialize_test_environment():
    """Initialize test environment and database."""
    print("🔧 Initializing test environment...")
    
    try:
        # Initialize test database
        init_cmd = [sys.executable, "-m", "tests.init_test_db"]
        result = subprocess.run(init_cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Test database initialized successfully")
        else:
            print("⚠️  Test database initialization had issues, continuing...")
            
    except Exception as e:
        print(f"⚠️  Could not initialize test database: {e}")
        print("Continuing with tests...")


def run_specific_tests(verbose=False, with_coverage=False):
    """
    Run specific tests that are known to work reliably.
    
    Args:
        verbose (bool): Enable verbose output
        with_coverage (bool): Include coverage analysis
    """
    print("🧪 Running specific test suite...")
    
    # Core test files that should work reliably
    test_files = [
        "tests/unit/test_qdb_init.py",
        "tests/unit/test_qdb_client.py", 
        "tests/unit/test_qdb_exceptions.py",
        "tests/unit/test_qdb_simple_client.py",
        "tests/unit/test_helpers.py",
        "tests/integration/test_qdb_api_integration.py"
    ]
    
    # Filter to only existing test files
    existing_tests = []
    for test_file in test_files:
        if Path(test_file).exists():
            existing_tests.append(test_file)
        else:
            print(f"⚠️  Test file not found: {test_file}")
    
    if not existing_tests:
        print("❌ No test files found! Running all tests in tests/ directory...")
        existing_tests = ["tests/"]
    
    # Build pytest command
    cmd = [sys.executable, "-m", "pytest"] + existing_tests
    
    if with_coverage:
        cmd.extend([
            "--cov=qdb",
            "--cov=core", 
            "--cov-report=term-missing",
            "--cov-report=xml:coverage_reports/coverage.xml"
        ])
    
    if verbose:
        cmd.append("-v")
    else:
        cmd.append("-q")
    
    # Add markers to focus on stable tests
    cmd.extend([
        "-m", "not slow",  # Skip slow tests
        "--tb=short"       # Shorter traceback format
    ])
    
    print(f"🚀 Running command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True)
        print("✅ Specific tests completed successfully!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Some tests failed! Exit code: {e.returncode}")
        return False


def run_fallback_tests(verbose=False):
    """
    Run a minimal fallback test suite if specific tests fail.
    """
    print("🔄 Running fallback test suite...")
    
    # Very basic test command
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/",
        "-x",  # Stop on first failure
        "--tb=line",  # Minimal traceback
        "-q"
    ]
    
    if verbose:
        cmd.append("-v")
    
    try:
        result = subprocess.run(cmd, check=True)
        print("✅ Fallback tests completed successfully!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Fallback tests also failed! Exit code: {e.returncode}")
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run specific tests for QuantDB CI/CD",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    
    parser.add_argument(
        "--coverage",
        action="store_true", 
        help="Include coverage analysis"
    )
    
    parser.add_argument(
        "--fallback-only",
        action="store_true",
        help="Run only fallback tests"
    )
    
    args = parser.parse_args()
    
    print("🎯 QuantDB Specific Test Runner")
    print("=" * 40)
    
    # Ensure directories exist
    ensure_directories()
    
    # Initialize test environment
    initialize_test_environment()
    
    success = False
    
    if args.fallback_only:
        success = run_fallback_tests(verbose=args.verbose)
    else:
        # Try specific tests first
        success = run_specific_tests(verbose=args.verbose, with_coverage=args.coverage)
        
        # If specific tests fail, try fallback
        if not success:
            print("\n🔄 Specific tests failed, trying fallback tests...")
            success = run_fallback_tests(verbose=args.verbose)
    
    # Print final status
    print("\n" + "=" * 40)
    if success:
        print("🎉 Test execution completed successfully!")
    else:
        print("❌ Test execution failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
