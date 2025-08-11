#!/usr/bin/env python3
"""
QuantDB Coverage Report Generator

This script generates test coverage reports in various formats and enforces coverage thresholds.
Used by CI/CD pipeline and local development.

Usage:
    python run_coverage.py --format xml
    python run_coverage.py --format html
    python run_coverage.py --format term
    python run_coverage.py --threshold 70
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


def ensure_directories():
    """Ensure required directories exist."""
    directories = [
        "coverage_reports",
        "coverage_reports/html",
        "database",
        "data/raw",
        "data/processed",
        "logs",
    ]

    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✓ Directory ensured: {directory}")


def run_coverage_analysis(format_type="xml", threshold=70, verbose=False):
    """
    Run pytest with coverage analysis.

    Args:
        format_type (str): Output format - 'xml', 'html', 'term', or 'all'
        threshold (int): Coverage threshold percentage
        verbose (bool): Enable verbose output
    """
    print(f"🧪 Running coverage analysis with {threshold}% threshold...")

    # Base pytest command
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests/",
        "--cov=qdb",
        "--cov=core",
        f"--cov-fail-under={threshold}",
        "--cov-report=term-missing",
    ]

    # Add format-specific reports
    if format_type in ["xml", "all"]:
        cmd.append("--cov-report=xml:coverage_reports/coverage.xml")
        print("📄 XML report will be generated at: coverage_reports/coverage.xml")

    if format_type in ["html", "all"]:
        cmd.append("--cov-report=html:coverage_reports/html")
        print("🌐 HTML report will be generated at: coverage_reports/html/index.html")

    # Add verbose flag if requested
    if verbose:
        cmd.append("-v")

    print(f"🚀 Running command: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, check=True, capture_output=False, text=True)
        print(f"✅ Coverage analysis completed successfully!")
        print(f"✅ Coverage threshold of {threshold}% was met!")
        return True

    except subprocess.CalledProcessError as e:
        print(f"❌ Coverage analysis failed!")
        print(f"❌ Coverage threshold of {threshold}% was NOT met!")
        print(f"Exit code: {e.returncode}")
        return False


def generate_coverage_summary():
    """Generate a brief coverage summary."""
    try:
        # Try to read coverage data if available
        cmd = [sys.executable, "-m", "coverage", "report", "--show-missing"]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print("\n📊 Coverage Summary:")
            print("=" * 50)
            print(result.stdout)
        else:
            print("ℹ️  Coverage summary not available (run coverage analysis first)")

    except Exception as e:
        print(f"⚠️  Could not generate coverage summary: {e}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate test coverage reports for QuantDB",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_coverage.py --format xml
  python run_coverage.py --format html --threshold 80
  python run_coverage.py --format all --verbose
  python run_coverage.py --summary-only
        """,
    )

    parser.add_argument(
        "--format",
        choices=["xml", "html", "term", "all"],
        default="xml",
        help="Coverage report format (default: xml)",
    )

    parser.add_argument(
        "--threshold",
        type=int,
        default=70,
        help="Coverage threshold percentage (default: 70)",
    )

    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")

    parser.add_argument(
        "--summary-only",
        action="store_true",
        help="Only show coverage summary (don't run tests)",
    )

    args = parser.parse_args()

    print("🎯 QuantDB Coverage Report Generator")
    print("=" * 40)

    # Ensure directories exist
    ensure_directories()

    if args.summary_only:
        generate_coverage_summary()
        return

    # Run coverage analysis
    success = run_coverage_analysis(
        format_type=args.format, threshold=args.threshold, verbose=args.verbose
    )

    # Generate summary
    generate_coverage_summary()

    # Print final status
    print("\n" + "=" * 50)
    if success:
        print("🎉 Coverage analysis completed successfully!")
        print(f"✅ Coverage threshold of {args.threshold}% was met!")

        if args.format in ["html", "all"]:
            print(f"🌐 View HTML report: coverage_reports/html/index.html")
        if args.format in ["xml", "all"]:
            print(f"📄 XML report: coverage_reports/coverage.xml")

    else:
        print("❌ Coverage analysis failed!")
        print(f"❌ Coverage threshold of {args.threshold}% was NOT met!")
        sys.exit(1)


if __name__ == "__main__":
    main()
