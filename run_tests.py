"""
Script to run tests with proper setup
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

def run_tests(test_path=None):
    """Run the tests"""
    # Build the command
    command = [sys.executable, "-m", "pytest"]

    if test_path:
        command.append(test_path)

    # Add verbose flag
    command.append("-v")

    # Run the tests
    result = subprocess.run(command)

    return result.returncode

if __name__ == "__main__":
    # Ensure required directories exist
    ensure_directories_exist()

    # Initialize the database
    initialize_database()

    # Get the test path from command line arguments
    test_path = sys.argv[1] if len(sys.argv) > 1 else None

    # Run the tests
    exit_code = run_tests(test_path)

    # Exit with the same code as the tests
    sys.exit(exit_code)
