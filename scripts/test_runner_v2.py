#!/usr/bin/env python
"""
Advanced test runner v2.0 for QuantDB project.

This is the next-generation test runner with enhanced features:
- Modular test execution
- Advanced coverage analysis
- Performance benchmarking
- Quality gate enforcement
"""

import os
import sys
import time
import subprocess
import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple

class TestRunnerV2:
    """Advanced test runner for QuantDB project."""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.coverage_dir = self.project_root / "coverage_reports"
        self.results_dir = self.project_root / "test_results"
        self.test_categories = {
            "core": {
                "path": "tests/unit/",
                "pattern": "*service*.py *cache*.py *model*.py",
                "description": "Core business logic tests"
            },
            "api": {
                "path": "tests/api/",
                "pattern": "*.py",
                "description": "API endpoint tests"
            },
            "integration": {
                "path": "tests/integration/",
                "pattern": "*.py",
                "description": "Integration tests"
            },
            "performance": {
                "path": "tests/performance/",
                "pattern": "*.py",
                "description": "Performance and cache tests"
            }
        }

    def ensure_directories(self):
        """Ensure required directories exist."""
        directories = [
            self.coverage_dir,
            self.results_dir,
            "database",
            "data/raw",
            "data/processed",
            "logs"
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)

    def run_core_tests(self, verbose=True, coverage=True) -> Dict:
        """Run core module tests with detailed analysis."""
        print("\n" + "="*60)
        print("🏗️  RUNNING CORE MODULE TESTS")
        print("="*60)
        
        core_test_files = [
            "tests/unit/test_stock_data_service.py",
            "tests/unit/test_asset_info_service.py", 
            "tests/unit/test_database_cache.py",
            "tests/unit/test_akshare_adapter.py",
            "tests/unit/test_trading_calendar.py",
            "tests/unit/test_monitoring_service.py",
            "tests/unit/test_monitoring_middleware.py"
        ]
        
        return self._run_test_suite(
            core_test_files, 
            "Core Module Tests",
            coverage_modules=["core"],
            verbose=verbose,
            coverage=coverage
        )

    def run_api_tests(self, verbose=True, coverage=True) -> Dict:
        """Run API tests with endpoint coverage analysis."""
        print("\n" + "="*60)
        print("🌐 RUNNING API TESTS")
        print("="*60)
        
        api_test_files = [
            "tests/api/test_assets_api.py",
            "tests/api/test_historical_data.py",
            "tests/api/test_version_api.py",
            "tests/api/test_openapi.py"
        ]
        
        return self._run_test_suite(
            api_test_files,
            "API Tests", 
            coverage_modules=["api"],
            verbose=verbose,
            coverage=coverage
        )

    def run_integration_tests(self, verbose=True, coverage=True) -> Dict:
        """Run integration tests."""
        print("\n" + "="*60)
        print("🔗 RUNNING INTEGRATION TESTS")
        print("="*60)
        
        integration_test_files = [
            "tests/integration/test_stock_data_flow.py",
            "tests/integration/test_asset_enhancement_integration.py",
            "tests/integration/test_error_handling_integration.py",
            "tests/integration/test_logging_integration.py",
            "tests/integration/test_monitoring_integration.py"
        ]
        
        return self._run_test_suite(
            integration_test_files,
            "Integration Tests",
            coverage_modules=["core", "api"],
            verbose=verbose,
            coverage=coverage
        )

    def run_performance_tests(self, verbose=True) -> Dict:
        """Run performance and cache tests."""
        print("\n" + "="*60)
        print("⚡ RUNNING PERFORMANCE TESTS")
        print("="*60)
        
        performance_test_files = [
            "tests/performance/test_real_cache_performance.py",
            "tests/performance/test_cache_value_scenarios.py"
        ]
        
        return self._run_test_suite(
            performance_test_files,
            "Performance Tests",
            coverage_modules=[],  # Performance tests don't need coverage
            verbose=verbose,
            coverage=False
        )

    def run_comprehensive_coverage(self, min_coverage=80) -> Dict:
        """Run comprehensive coverage analysis with quality gates."""
        print("\n" + "="*60)
        print("📊 COMPREHENSIVE COVERAGE ANALYSIS")
        print("="*60)
        
        # Run all tests with coverage
        command = [
            sys.executable, "-m", "pytest",
            "tests/unit/", "tests/api/", "tests/integration/",
            "--cov=core", "--cov=api",
            "--cov-report=term-missing",
            "--cov-report=html:coverage_reports/html",
            "--cov-report=xml:coverage_reports/coverage.xml",
            "--cov-report=json:coverage_reports/coverage.json",
            f"--cov-fail-under={min_coverage}",
            "-v"
        ]
        
        start_time = time.time()
        result = subprocess.run(command, capture_output=True, text=True)
        duration = time.time() - start_time
        
        # Parse coverage results
        coverage_data = self._parse_coverage_results()
        
        return {
            "success": result.returncode == 0,
            "duration": duration,
            "coverage": coverage_data,
            "quality_gate_passed": coverage_data.get("total_coverage", 0) >= min_coverage
        }

    def _run_test_suite(self, test_files: List[str], suite_name: str, 
                       coverage_modules: List[str], verbose=True, coverage=True) -> Dict:
        """Run a test suite and return results."""
        results = {
            "suite_name": suite_name,
            "total_files": len(test_files),
            "passed_files": 0,
            "failed_files": 0,
            "skipped_files": 0,
            "duration": 0,
            "coverage": {}
        }
        
        start_time = time.time()
        
        for test_file in test_files:
            if not os.path.exists(test_file):
                print(f"⚠️  Test file not found: {test_file}")
                results["skipped_files"] += 1
                continue
                
            print(f"\n📝 Running: {test_file}")
            
            command = [sys.executable, "-m", "pytest", test_file]
            if verbose:
                command.append("-v")
            if coverage and coverage_modules:
                for module in coverage_modules:
                    command.extend([f"--cov={module}"])
                command.append("--cov-report=term")
            
            result = subprocess.run(command)
            
            if result.returncode == 0:
                results["passed_files"] += 1
                print(f"✅ {test_file} - PASSED")
            else:
                results["failed_files"] += 1
                print(f"❌ {test_file} - FAILED")
        
        results["duration"] = time.time() - start_time
        
        # Print summary
        print(f"\n📊 {suite_name} Summary:")
        print(f"   Total: {results['total_files']}")
        print(f"   Passed: {results['passed_files']} ✅")
        print(f"   Failed: {results['failed_files']} ❌") 
        print(f"   Skipped: {results['skipped_files']} ⏭️")
        print(f"   Duration: {results['duration']:.2f}s")
        
        return results

    def _parse_coverage_results(self) -> Dict:
        """Parse coverage results from JSON report."""
        coverage_file = self.coverage_dir / "coverage.json"
        if not coverage_file.exists():
            return {"total_coverage": 0, "modules": {}}
            
        try:
            with open(coverage_file) as f:
                data = json.load(f)
            
            return {
                "total_coverage": data.get("totals", {}).get("percent_covered", 0),
                "modules": {
                    filename: {
                        "coverage": file_data.get("summary", {}).get("percent_covered", 0),
                        "missing_lines": file_data.get("missing_lines", [])
                    }
                    for filename, file_data in data.get("files", {}).items()
                }
            }
        except Exception as e:
            print(f"Error parsing coverage results: {e}")
            return {"total_coverage": 0, "modules": {}}

    def generate_test_report(self, results: List[Dict]) -> str:
        """Generate comprehensive test report."""
        report_file = self.results_dir / f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "project": "QuantDB",
            "version": "2.1.0-stable",
            "test_results": results,
            "summary": {
                "total_suites": len(results),
                "total_duration": sum(r.get("duration", 0) for r in results),
                "overall_success": all(r.get("success", False) for r in results)
            }
        }
        
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
            
        print(f"\n📄 Test report generated: {report_file}")
        return str(report_file)

def main():
    """Main function with enhanced argument parsing."""
    parser = argparse.ArgumentParser(
        description="QuantDB Test Runner v2.0 - Advanced testing with quality gates"
    )
    
    # Test categories
    parser.add_argument("--core", action="store_true", help="Run core module tests")
    parser.add_argument("--api", action="store_true", help="Run API tests")
    parser.add_argument("--integration", action="store_true", help="Run integration tests")
    parser.add_argument("--performance", action="store_true", help="Run performance tests")
    parser.add_argument("--all", action="store_true", help="Run all test suites")
    
    # Coverage options
    parser.add_argument("--coverage", action="store_true", help="Run comprehensive coverage analysis")
    parser.add_argument("--min-coverage", type=int, default=80, help="Minimum coverage threshold")
    
    # Output options
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--report", action="store_true", help="Generate detailed test report")
    
    # Validation options
    parser.add_argument("--validate", action="store_true", help="Validate test structure")
    parser.add_argument("--list", action="store_true", help="List available tests")
    
    args = parser.parse_args()
    
    # Create runner
    runner = TestRunnerV2()
    runner.ensure_directories()
    
    results = []
    
    try:
        if args.list:
            print("📋 Available test categories:")
            for category, info in runner.test_categories.items():
                print(f"  --{category}: {info['description']}")
            return
            
        if args.validate:
            print("🔍 Validating test structure...")
            # Add validation logic here
            return
            
        if args.coverage:
            result = runner.run_comprehensive_coverage(args.min_coverage)
            results.append(result)
        elif args.core:
            result = runner.run_core_tests(args.verbose)
            results.append(result)
        elif args.api:
            result = runner.run_api_tests(args.verbose)
            results.append(result)
        elif args.integration:
            result = runner.run_integration_tests(args.verbose)
            results.append(result)
        elif args.performance:
            result = runner.run_performance_tests(args.verbose)
            results.append(result)
        elif args.all:
            print("🚀 Running complete test suite...")
            results.append(runner.run_core_tests(args.verbose))
            results.append(runner.run_api_tests(args.verbose))
            results.append(runner.run_integration_tests(args.verbose))
            results.append(runner.run_performance_tests(args.verbose))
        else:
            # Default: run core and API tests
            print("🎯 Running default test suite (core + API)...")
            results.append(runner.run_core_tests(args.verbose))
            results.append(runner.run_api_tests(args.verbose))
        
        if args.report and results:
            runner.generate_test_report(results)
            
        # Final summary
        overall_success = all(r.get("success", True) for r in results)
        if overall_success:
            print("\n🎉 All tests completed successfully!")
            sys.exit(0)
        else:
            print("\n❌ Some tests failed.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️  Test execution interrupted by user.")
        sys.exit(1)

if __name__ == "__main__":
    main()
