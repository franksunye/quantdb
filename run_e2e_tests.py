"""
Script to run end-to-end tests for the QuantDB project.

This script:
1. Ensures required directories exist
2. Checks if the API server is running
3. Runs the end-to-end tests

Options:
--debug: Enable debug mode for detailed logging
"""
import os
import sys
import time
import subprocess
import requests
import argparse
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

def is_api_running():
    """Check if the API server is running"""
    try:
        response = requests.get("http://localhost:8000/api/v1/health")
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        return False

def start_api_server():
    """Start the API server"""
    print("Starting API server...")

    # Start the server in a new process
    process = subprocess.Popen(
        [sys.executable, "-m", "src.api.main"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # Wait for the server to start
    max_wait_time = 10  # seconds
    start_time = time.time()

    while time.time() - start_time < max_wait_time:
        if is_api_running():
            print("API server started successfully.")
            return process

        time.sleep(0.5)

    # If we get here, the server didn't start
    print("Failed to start API server.")
    process.terminate()
    return None

def run_e2e_tests(debug=False):
    """
    Run the end-to-end tests

    Args:
        debug: Enable debug mode for detailed logging
    """
    # List of E2E test files
    test_files = [
        "tests/e2e/test_data_flow_api.py"
    ]

    # Track test results
    passed_tests = []
    failed_tests = []

    # Run each test file
    for test_file in test_files:
        print(f"\nRunning tests in {test_file}...")

        # Build command with debug flag if requested
        command = [sys.executable, "-m", "pytest", test_file, "-v"]
        if debug:
            # Add debug flag for pytest
            command.append("--debug")
            print("Debug mode enabled - detailed logging will be generated")

        result = subprocess.run(command)

        if result.returncode == 0:
            passed_tests.append(test_file)
            print(f"✅ Tests in {test_file} passed.")
        else:
            failed_tests.append(test_file)
            print(f"❌ Tests in {test_file} failed.")

    # Print summary
    print("\n" + "="*50)
    print("E2E TEST SUMMARY")
    print("="*50)
    print(f"Total test files: {len(test_files)}")
    print(f"Passed: {len(passed_tests)} ({len(passed_tests)/len(test_files)*100:.1f}%)")
    print(f"Failed: {len(failed_tests)} ({len(failed_tests)/len(test_files)*100:.1f}%)")

    if failed_tests:
        print("\nFailed test files:")
        for test_file in failed_tests:
            print(f"  - {test_file}")

    if passed_tests and not failed_tests:
        print("\n✅ All E2E tests passed!")
        if debug:
            print("\nDetailed logs are available in the logs directory.")
        return 0
    else:
        print("\n❌ Some E2E tests failed. See above for details.")
        if debug:
            print("\nDetailed logs are available in the logs directory.")
        return 1

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Run end-to-end tests for the QuantDB project')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode for detailed logging')
    parser.add_argument('--auto-start', action='store_true', help='Automatically start the API server if not running')
    args = parser.parse_args()

    # Print debug status
    if args.debug:
        print("Debug mode enabled - detailed logging will be generated")

    # Ensure required directories exist
    ensure_directories_exist()

    # Check if API server is running
    server_process = None
    if not is_api_running():
        print("API server is not running.")

        if args.auto_start:
            print("Auto-starting API server...")
            server_process = start_api_server()
            if not server_process:
                print("Cannot run E2E tests without the API server.")
                sys.exit(1)
        else:
            choice = input("Do you want to start the API server? (y/n): ")

            if choice.lower() == 'y':
                server_process = start_api_server()
                if not server_process:
                    print("Cannot run E2E tests without the API server.")
                    sys.exit(1)
            else:
                print("Cannot run E2E tests without the API server.")
                sys.exit(1)

    try:
        # Run the tests with debug mode if requested
        exit_code = run_e2e_tests(debug=args.debug)
    finally:
        # Stop the API server if we started it
        if server_process:
            print("Stopping API server...")
            server_process.terminate()
            server_process.wait()
            print("API server stopped.")

    # Exit with the same code as the tests
    sys.exit(exit_code)
