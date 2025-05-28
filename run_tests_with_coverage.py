#!/usr/bin/env python
"""
Run tests with coverage.

This script runs the tests and generates a coverage report.
"""
import os
import sys
import subprocess
import argparse
import webbrowser
from datetime import datetime

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run tests with coverage")
    parser.add_argument(
        "--html", action="store_true", help="Generate HTML coverage report"
    )
    parser.add_argument(
        "--xml", action="store_true", help="Generate XML coverage report"
    )
    parser.add_argument(
        "--open", action="store_true", help="Open HTML coverage report in browser"
    )
    parser.add_argument(
        "--tests", type=str, default="tests", help="Tests to run (default: tests)"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Verbose output"
    )
    parser.add_argument(
        "--failfast", "-f", action="store_true", help="Stop on first failure"
    )
    return parser.parse_args()

def run_tests_with_coverage(args):
    """Run tests with coverage."""
    # Create command
    cmd = ["python", "-m", "pytest"]
    
    # Add arguments
    if args.verbose:
        cmd.append("-v")
    if args.failfast:
        cmd.append("-xvs")
    
    # Add tests
    cmd.append(args.tests)
    
    # Add coverage
    cmd = ["coverage", "run", "--source=src", "-m", "pytest"] + cmd[2:]
    
    # Print command
    print(f"Running: {' '.join(cmd)}")
    
    # Run command
    start_time = datetime.now()
    result = subprocess.run(cmd)
    end_time = datetime.now()
    
    # Print result
    duration = (end_time - start_time).total_seconds()
    print(f"\nTests completed in {duration:.2f} seconds")
    
    # Generate reports
    if args.html:
        print("\nGenerating HTML coverage report...")
        subprocess.run(["coverage", "html"])
        
        if args.open:
            print("Opening HTML coverage report in browser...")
            webbrowser.open(os.path.join(os.getcwd(), "coverage_html_report", "index.html"))
    
    if args.xml:
        print("\nGenerating XML coverage report...")
        subprocess.run(["coverage", "xml"])
    
    # Print coverage report
    print("\nCoverage report:")
    subprocess.run(["coverage", "report"])
    
    return result.returncode

def main():
    """Main function."""
    args = parse_args()
    sys.exit(run_tests_with_coverage(args))

if __name__ == "__main__":
    main()
