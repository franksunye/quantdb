#!/usr/bin/env python
"""
Unified test runner for QuantDB project.

This script consolidates all test running functionality into a single tool,
replacing the multiple test scripts with a unified interface.
"""

import os
import sys
import time
import subprocess
import requests
import argparse
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import List, Optional

class TestRunner:
    """Unified test runner for the QuantDB project."""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.logs_dir = self.project_root / "logs"
        self.coverage_dir = self.project_root / "coverage_reports"

    def ensure_directories_exist(self):
        """Ensure required directories exist."""
        directories = [
            "database",
            "data/raw",
            "data/processed",
            "logs",
            "coverage_reports"
        ]

        for directory in directories:
            os.makedirs(directory, exist_ok=True)
            print(f"Ensured directory exists: {directory}")

    def initialize_database(self):
        """Initialize the database for testing."""
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
            return False

        # Initialize test data
        result = subprocess.run(
            [sys.executable, "-m", "tests.init_test_db"],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print("Test data initialized successfully.")
            return True
        else:
            print(f"Error initializing test data: {result.stderr}")
            return False

    def is_api_running(self, host="localhost", port=8000):
        """Check if the API server is running."""
        try:
            response = requests.get(f"http://{host}:{port}/api/v1/health", timeout=5)
            return response.status_code == 200
        except:
            return False

    def start_api_server(self, port=8000):
        """Start the API server for E2E tests."""
        print(f"Starting API server on port {port}...")
        try:
            process = subprocess.Popen(
                [sys.executable, "-m", "src.api.main", "--port", str(port)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            # Wait for server to start
            for _ in range(30):  # Wait up to 30 seconds
                if self.is_api_running(port=port):
                    print(f"API server started successfully on port {port}")
                    return process
                time.sleep(1)

            print("Failed to start API server")
            process.terminate()
            return None
        except Exception as e:
            print(f"Error starting API server: {e}")
            return None

    def run_unit_tests(self, verbose=True, coverage=False):
        """Run unit tests."""
        print("\n" + "="*50)
        print("RUNNING UNIT TESTS")
        print("="*50)

        test_files = [
            "tests/unit/test_akshare_adapter.py",
            "tests/unit/test_database_cache.py",
            "tests/unit/test_stock_data_service.py",
            "tests/unit/test_enhanced_logger.py",
            "tests/unit/test_error_handling.py"
        ]

        return self._run_test_files(test_files, "Unit Tests", verbose, coverage)

    def run_integration_tests(self, verbose=True, coverage=False):
        """Run integration tests."""
        print("\n" + "="*50)
        print("RUNNING INTEGRATION TESTS")
        print("="*50)

        test_files = [
            "tests/integration/test_stock_data_flow.py",
            "tests/integration/test_error_handling_integration.py",
            "tests/integration/test_logging_integration.py"
        ]

        return self._run_test_files(test_files, "Integration Tests", verbose, coverage)

    def run_api_tests(self, verbose=True, coverage=False):
        """Run API tests."""
        print("\n" + "="*50)
        print("RUNNING API TESTS")
        print("="*50)

        test_files = [
            "tests/test_assets_api.py",
            "tests/api/test_historical_data.py",
            "tests/test_api.py",
            "tests/api/test_version_api.py"
        ]

        return self._run_test_files(test_files, "API Tests", verbose, coverage)

    def run_e2e_tests(self, verbose=True, coverage=False, auto_start_server=False):
        """Run end-to-end tests."""
        print("\n" + "="*50)
        print("RUNNING END-TO-END TESTS")
        print("="*50)

        # 新的E2E测试不需要外部服务器，它们会自己管理服务器
        test_files = [
            "tests/e2e/test_user_scenarios.py"
        ]

        print("运行新的自管理E2E测试...")
        result = self._run_test_files(test_files, "End-to-End Tests", verbose, coverage)

        # 如果新测试失败，可以尝试运行旧的E2E测试（如果用户要求）
        if not result and auto_start_server:
            print("\n新E2E测试失败，尝试运行传统E2E测试...")

            # Check if API server is running
            server_process = None
            if not self.is_api_running():
                print("API server is not running.")
                print("Auto-starting API server...")
                server_process = self.start_api_server()
                if not server_process:
                    print("Cannot run legacy E2E tests without the API server.")
                    return False

            try:
                legacy_test_files = [
                    "tests/e2e/test_stock_data_api_simplified.py",
                    "tests/e2e/test_stock_data_http_api.py"
                ]

                legacy_result = self._run_test_files(legacy_test_files, "Legacy End-to-End Tests", verbose, coverage)
                result = result or legacy_result
            finally:
                # Stop the API server if we started it
                if server_process:
                    print("Stopping API server...")
                    server_process.terminate()
                    server_process.wait()
                    print("API server stopped.")

        return result

    def run_performance_tests(self, verbose=True):
        """Run performance tests."""
        print("\n" + "="*50)
        print("RUNNING PERFORMANCE TESTS")
        print("="*50)

        test_files = [
            "tests/performance/test_api_performance.py",
            "tests/performance/test_cache_performance.py"
        ]

        return self._run_test_files(test_files, "Performance Tests", verbose, False)

    def run_specific_tests(self, test_pattern: str, verbose=True, coverage=False):
        """Run specific tests matching a pattern."""
        print(f"\n" + "="*50)
        print(f"RUNNING SPECIFIC TESTS: {test_pattern}")
        print("="*50)

        command = [sys.executable, "-m", "pytest", "-k", test_pattern]

        if verbose:
            command.append("-v")

        if coverage:
            command.extend(["--cov=src", "--cov-report=term"])

        result = subprocess.run(command)
        return result.returncode == 0

    def run_coverage_analysis(self, test_path=None, min_coverage=70, fail_under=False,
                            html_report=True, xml_report=True, open_browser=False):
        """Run comprehensive coverage analysis."""
        print("\n" + "="*50)
        print("RUNNING COVERAGE ANALYSIS")
        print("="*50)

        # Build the command
        command = [
            sys.executable,
            "-m",
            "pytest",
            "--cov=src",
            "--cov-report=term"
        ]

        # Add minimum coverage threshold if specified
        if fail_under:
            command.append(f"--cov-fail-under={min_coverage}")

        # Add test path if specified
        if test_path:
            command.append(test_path)

        # Add verbose flag
        command.append("-v")

        # Run the tests with coverage
        print(f"Running tests with coverage...")
        result = subprocess.run(command)

        # Generate HTML report
        if html_report:
            print("\nGenerating HTML coverage report...")
            html_command = [
                sys.executable,
                "-m",
                "pytest",
                "--cov=src",
                "--cov-report=html:coverage_reports/html"
            ]
            if test_path:
                html_command.append(test_path)

            subprocess.run(html_command)

            # Print the path to the HTML report
            html_report_path = os.path.abspath("coverage_reports/html/index.html")
            print(f"\nHTML report generated at: {html_report_path}")

            if open_browser:
                print("Opening HTML coverage report in browser...")
                webbrowser.open(f"file://{html_report_path}")

        # Generate XML report for CI integration
        if xml_report:
            print("\nGenerating XML coverage report...")
            xml_command = [
                sys.executable,
                "-m",
                "pytest",
                "--cov=src",
                "--cov-report=xml:coverage_reports/coverage.xml"
            ]
            if test_path:
                xml_command.append(test_path)

            subprocess.run(xml_command)

        return result.returncode == 0

    def _run_test_files(self, test_files: List[str], test_type: str, verbose=True, coverage=False):
        """Run a list of test files."""
        passed_tests = []
        failed_tests = []

        for test_file in test_files:
            if not os.path.exists(test_file):
                print(f"⚠️  Test file not found: {test_file}")
                continue

            print(f"\nRunning tests in {test_file}...")
            command = [sys.executable, "-m", "pytest", test_file]

            if verbose:
                command.append("-v")

            if coverage:
                command.extend(["--cov=src", "--cov-report=term"])

            result = subprocess.run(command)

            if result.returncode == 0:
                passed_tests.append(test_file)
                print(f"✅ Tests in {test_file} passed.")
            else:
                failed_tests.append(test_file)
                print(f"❌ Tests in {test_file} failed.")

        # Print summary
        print(f"\n{test_type} Summary:")
        print(f"Total test files: {len(test_files)}")
        print(f"Passed: {len(passed_tests)} ({len(passed_tests)/len(test_files)*100:.1f}%)")
        print(f"Failed: {len(failed_tests)} ({len(failed_tests)/len(test_files)*100:.1f}%)")

        if failed_tests:
            print(f"\nFailed test files:")
            for test_file in failed_tests:
                print(f"  - {test_file}")

        return len(failed_tests) == 0

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Unified test runner for QuantDB")

    # Test type selection
    parser.add_argument("--unit", action="store_true", help="Run unit tests")
    parser.add_argument("--integration", action="store_true", help="Run integration tests")
    parser.add_argument("--api", action="store_true", help="Run API tests")
    parser.add_argument("--e2e", action="store_true", help="Run end-to-end tests")
    parser.add_argument("--performance", action="store_true", help="Run performance tests")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    parser.add_argument("--coverage", action="store_true", help="Run coverage analysis")

    # Test selection
    parser.add_argument("--pattern", type=str, help="Run tests matching pattern")
    parser.add_argument("--file", type=str, help="Run specific test file")

    # Options
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--quiet", "-q", action="store_true", help="Quiet output")
    parser.add_argument("--with-coverage", action="store_true", help="Include coverage in test runs")
    parser.add_argument("--auto-start-server", action="store_true", help="Auto-start API server for E2E tests")

    # Coverage options
    parser.add_argument("--min-coverage", type=int, default=70, help="Minimum coverage threshold")
    parser.add_argument("--fail-under", action="store_true", help="Fail if coverage below threshold")
    parser.add_argument("--html-report", action="store_true", default=True, help="Generate HTML coverage report")
    parser.add_argument("--xml-report", action="store_true", default=True, help="Generate XML coverage report")
    parser.add_argument("--open-browser", action="store_true", help="Open HTML report in browser")

    args = parser.parse_args()

    # Create test runner
    runner = TestRunner()

    # Ensure directories exist
    runner.ensure_directories_exist()

    # Initialize database
    if not runner.initialize_database():
        print("Failed to initialize database. Exiting.")
        sys.exit(1)

    verbose = args.verbose and not args.quiet
    success = True

    try:
        if args.coverage:
            success = runner.run_coverage_analysis(
                test_path=args.file,
                min_coverage=args.min_coverage,
                fail_under=args.fail_under,
                html_report=args.html_report,
                xml_report=args.xml_report,
                open_browser=args.open_browser
            )
        elif args.pattern:
            success = runner.run_specific_tests(args.pattern, verbose, args.with_coverage)
        elif args.file:
            success = runner._run_test_files([args.file], "Specific Test", verbose, args.with_coverage)
        elif args.unit:
            success = runner.run_unit_tests(verbose, args.with_coverage)
        elif args.integration:
            success = runner.run_integration_tests(verbose, args.with_coverage)
        elif args.api:
            success = runner.run_api_tests(verbose, args.with_coverage)
        elif args.e2e:
            success = runner.run_e2e_tests(verbose, args.with_coverage, args.auto_start_server)
        elif args.performance:
            success = runner.run_performance_tests(verbose)
        elif args.all:
            print("Running all test suites...")
            success = True
            success &= runner.run_unit_tests(verbose, args.with_coverage)
            success &= runner.run_integration_tests(verbose, args.with_coverage)
            success &= runner.run_api_tests(verbose, args.with_coverage)
            # Auto-start server for E2E tests when running all tests
            success &= runner.run_e2e_tests(verbose, args.with_coverage, True)
            success &= runner.run_performance_tests(verbose)
        else:
            # Default: run the most stable tests
            print("Running default test suite (unit + integration + API tests)...")
            success = True
            success &= runner.run_unit_tests(verbose, args.with_coverage)
            success &= runner.run_integration_tests(verbose, args.with_coverage)
            success &= runner.run_api_tests(verbose, args.with_coverage)

    except KeyboardInterrupt:
        print("\nTest execution interrupted by user.")
        sys.exit(1)

    # Exit with appropriate code
    if success:
        print("\n✅ All tests completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
