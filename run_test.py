"""
Script to run a single test file with proper setup
"""
import os
import sys
import subprocess
import argparse

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

def run_test(test_path, verbose=True, coverage=False):
    """Run a single test file"""
    # Build the command
    command = [sys.executable, "-m", "pytest", test_path]
    
    # Add verbose flag
    if verbose:
        command.append("-v")
    
    # Add coverage flag
    if coverage:
        command.extend(["--cov=src", "--cov-report=term"])
    
    # Run the test
    print(f"\nRunning test: {test_path}")
    result = subprocess.run(command)
    
    if result.returncode == 0:
        print(f"\n✅ Test passed: {test_path}")
    else:
        print(f"\n❌ Test failed: {test_path}")
    
    return result.returncode

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Run a single test file with proper setup")
    parser.add_argument("test_path", help="Path to the test file or directory to run")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument("-c", "--coverage", action="store_true", help="Enable coverage reporting")
    return parser.parse_args()

if __name__ == "__main__":
    # Parse arguments
    args = parse_args()
    
    # Ensure required directories exist
    ensure_directories_exist()
    
    # Initialize the database
    initialize_database()
    
    # Run the test
    exit_code = run_test(args.test_path, args.verbose, args.coverage)
    
    # Exit with the same code as the test
    sys.exit(exit_code)
