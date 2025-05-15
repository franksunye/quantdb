"""
Script to run test coverage analysis and generate a report
"""
import os
import sys
import subprocess
import argparse
from pathlib import Path

def ensure_directories_exist():
    """Ensure required directories exist"""
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

def run_coverage(test_path=None, report_format="term", min_coverage=70, fail_under=False):
    """Run tests with coverage and generate a report"""
    # Build the command
    command = [
        sys.executable, 
        "-m", 
        "pytest", 
        "--cov=src", 
        f"--cov-report={report_format}"
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
    print(f"\nRunning tests with coverage...")
    result = subprocess.run(command)
    
    # Generate HTML report
    if report_format == "term":
        print("\nGenerating HTML report...")
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
        print(f"Open this file in a browser to view the detailed coverage report.")
    
    # Generate XML report for CI integration
    print("\nGenerating XML report for CI integration...")
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
    
    # Identify modules with low coverage
    print("\nIdentifying modules with low coverage...")
    low_coverage_modules = identify_low_coverage_modules(min_coverage)
    
    if low_coverage_modules:
        print(f"\nModules with coverage below {min_coverage}%:")
        for module, coverage in low_coverage_modules:
            print(f"  - {module}: {coverage}%")
    else:
        print(f"\nAll modules have coverage above {min_coverage}%.")
    
    return result.returncode

def identify_low_coverage_modules(min_coverage):
    """Identify modules with coverage below the minimum threshold"""
    # Parse the coverage.xml file to extract module coverage
    import xml.etree.ElementTree as ET
    
    try:
        tree = ET.parse("coverage_reports/coverage.xml")
        root = tree.getroot()
        
        low_coverage_modules = []
        
        for package in root.findall(".//package"):
            for class_elem in package.findall(".//class"):
                module_name = class_elem.get("name")
                
                # Skip __init__.py files
                if module_name.endswith("__init__"):
                    continue
                
                # Calculate coverage
                lines = class_elem.find(".//lines")
                if lines is not None:
                    total_lines = len(lines.findall(".//line"))
                    covered_lines = len(lines.findall(".//line[@hits='1']"))
                    
                    if total_lines > 0:
                        coverage = (covered_lines / total_lines) * 100
                        
                        if coverage < min_coverage:
                            low_coverage_modules.append((module_name, round(coverage, 2)))
        
        # Sort by coverage (ascending)
        low_coverage_modules.sort(key=lambda x: x[1])
        
        return low_coverage_modules
    except Exception as e:
        print(f"Error parsing coverage report: {e}")
        return []

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Run tests with coverage and generate a report")
    parser.add_argument("test_path", nargs="?", help="Path to the test file or directory to run")
    parser.add_argument("-f", "--format", choices=["term", "html", "xml"], default="term", 
                        help="Coverage report format (default: term)")
    parser.add_argument("-m", "--min-coverage", type=int, default=70, 
                        help="Minimum coverage threshold (default: 70)")
    parser.add_argument("--fail-under", action="store_true", 
                        help="Fail if coverage is under the minimum threshold")
    return parser.parse_args()

if __name__ == "__main__":
    # Parse arguments
    args = parse_args()
    
    # Ensure required directories exist
    ensure_directories_exist()
    
    # Initialize the database
    initialize_database()
    
    # Run the tests with coverage
    exit_code = run_coverage(args.test_path, args.format, args.min_coverage, args.fail_under)
    
    # Exit with the same code as the tests
    sys.exit(exit_code)
