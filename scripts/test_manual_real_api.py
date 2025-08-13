#!/usr/bin/env python3
"""
Manual Real API Test Runner

This script runs tests that use real external APIs (AKShare, etc.).
These tests should NEVER be run in CI/CD environments.

Usage:
    python scripts/test_manual_real_api.py --performance
    python scripts/test_manual_real_api.py --e2e
    python scripts/test_manual_real_api.py --all
"""

import argparse
import subprocess
import sys
from pathlib import Path


def run_performance_tests():
    """Run real API performance tests."""
    print("🚀 Running Real API Performance Tests...")
    print("⚠️  WARNING: These tests will make real AKShare API calls!")
    
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/performance/test_real_cache_performance.py",
        "tests/performance/test_cache_value_scenarios.py",
        "-v",
        "--tb=short",
        "-s"  # Show print statements
    ]
    
    try:
        result = subprocess.run(cmd, check=True)
        print("✅ Performance tests completed!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Performance tests failed! Exit code: {e.returncode}")
        return False


def run_e2e_tests():
    """Run real API end-to-end tests."""
    print("🌐 Running Real API E2E Tests...")
    print("⚠️  WARNING: These tests will make real HTTP requests!")
    
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/e2e/test_real_user_scenarios.py",
        "tests/e2e/test_user_scenarios.py",
        "-v",
        "--tb=short",
        "-s"  # Show print statements
    ]
    
    try:
        result = subprocess.run(cmd, check=True)
        print("✅ E2E tests completed!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ E2E tests failed! Exit code: {e.returncode}")
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run manual Real API tests (NOT for CI)"
    )
    
    parser.add_argument(
        "--performance",
        action="store_true",
        help="Run performance tests with real AKShare API"
    )
    
    parser.add_argument(
        "--e2e",
        action="store_true",
        help="Run end-to-end tests with real HTTP requests"
    )
    
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all real API tests"
    )
    
    args = parser.parse_args()
    
    if not any([args.performance, args.e2e, args.all]):
        parser.print_help()
        return
    
    print("🧪 Manual Real API Test Runner")
    print("=" * 50)
    print("🚨 WARNING: These tests use real external APIs!")
    print("🚨 DO NOT run in CI/CD environments!")
    print("🚨 May incur API costs and take significant time!")
    print("=" * 50)
    
    # Confirm with user
    response = input("Do you want to continue? (y/N): ")
    if response.lower() != 'y':
        print("❌ Tests cancelled by user")
        return
    
    success = True
    
    if args.all or args.performance:
        success &= run_performance_tests()
    
    if args.all or args.e2e:
        success &= run_e2e_tests()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 All manual tests completed successfully!")
    else:
        print("❌ Some manual tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
