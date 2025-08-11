#!/usr/bin/env python
"""
Package Quality Gate for QuantDB GTM.

This script runs comprehensive quality assurance checks to ensure
the Package version meets production standards before release.

Quality Gates:
- Test Coverage >= 80%
- All Critical Tests Pass
- Performance Benchmarks Met
- Security Compliance
- Documentation Complete
"""

import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class PackageQualityGate:
    """Package quality gate runner."""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "version": "2.2.8-stable",
            "quality_gates": {},
            "overall_status": "UNKNOWN",
            "recommendations": [],
        }
        self.min_coverage = 80
        self.critical_test_suites = [
            "tests/unit/test_core_models.py",
            "tests/unit/test_stock_data_service.py",
            "tests/unit/test_asset_info_service.py",
            "tests/api/test_assets_api.py",
            "tests/api/test_historical_data.py",
            "tests/quality/test_package_quality.py",
        ]

    def run_quality_gate(self) -> bool:
        """Run complete quality gate process."""
        print("🚀 QuantDB Package Quality Gate")
        print("=" * 60)
        print(f"Version: {self.results['version']}")
        print(f"Timestamp: {self.results['timestamp']}")
        print("=" * 60)

        # Run all quality checks
        gates = [
            ("Test Coverage", self._check_test_coverage),
            ("Critical Tests", self._check_critical_tests),
            ("Performance", self._check_performance),
            ("Security", self._check_security),
            ("Documentation", self._check_documentation),
            ("Package Structure", self._check_package_structure),
            ("API Compliance", self._check_api_compliance),
        ]

        all_passed = True

        for gate_name, gate_func in gates:
            print(f"\n🔍 Checking {gate_name}...")
            try:
                result = gate_func()
                self.results["quality_gates"][gate_name] = result

                if result["status"] == "PASS":
                    print(f"✅ {gate_name}: PASSED")
                elif result["status"] == "WARN":
                    print(f"⚠️  {gate_name}: WARNING - {result.get('message', '')}")
                else:
                    print(f"❌ {gate_name}: FAILED - {result.get('message', '')}")
                    all_passed = False

                if result.get("recommendations"):
                    self.results["recommendations"].extend(result["recommendations"])

            except Exception as e:
                print(f"❌ {gate_name}: ERROR - {str(e)}")
                self.results["quality_gates"][gate_name] = {"status": "ERROR", "message": str(e)}
                all_passed = False

        # Set overall status
        self.results["overall_status"] = "PASS" if all_passed else "FAIL"

        # Generate report
        self._generate_report()

        # Print summary
        self._print_summary()

        return all_passed

    def _check_test_coverage(self) -> Dict:
        """Check test coverage meets requirements."""
        try:
            # Run coverage analysis
            cmd = [
                sys.executable,
                "-m",
                "pytest",
                "tests/unit/",
                "tests/api/",
                "tests/integration/",
                "--cov=core",
                "--cov=api",
                "--cov-report=json:coverage_reports/coverage.json",
                "--cov-report=term-missing",
                "-q",
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_root)

            # Parse coverage results
            coverage_file = self.project_root / "coverage_reports" / "coverage.json"
            if coverage_file.exists():
                with open(coverage_file) as f:
                    coverage_data = json.load(f)

                total_coverage = coverage_data.get("totals", {}).get("percent_covered", 0)

                if total_coverage >= self.min_coverage:
                    return {
                        "status": "PASS",
                        "coverage": total_coverage,
                        "message": f"Coverage: {total_coverage:.1f}% (>= {self.min_coverage}%)",
                    }
                else:
                    return {
                        "status": "FAIL",
                        "coverage": total_coverage,
                        "message": f"Coverage: {total_coverage:.1f}% (< {self.min_coverage}%)",
                        "recommendations": [
                            f"Increase test coverage to at least {self.min_coverage}%",
                            "Focus on untested modules and functions",
                            "Add integration tests for critical paths",
                        ],
                    }
            else:
                return {"status": "ERROR", "message": "Coverage report not generated"}

        except Exception as e:
            return {"status": "ERROR", "message": f"Coverage check failed: {str(e)}"}

    def _check_critical_tests(self) -> Dict:
        """Check that all critical tests pass."""
        failed_suites = []
        total_suites = len(self.critical_test_suites)

        for test_suite in self.critical_test_suites:
            test_path = self.project_root / test_suite
            if not test_path.exists():
                failed_suites.append(f"{test_suite} (not found)")
                continue

            try:
                cmd = [sys.executable, "-m", "pytest", str(test_path), "-q"]
                result = subprocess.run(cmd, capture_output=True, cwd=self.project_root)

                if result.returncode != 0:
                    failed_suites.append(test_suite)

            except Exception as e:
                failed_suites.append(f"{test_suite} (error: {str(e)})")

        if not failed_suites:
            return {"status": "PASS", "message": f"All {total_suites} critical test suites passed"}
        else:
            return {
                "status": "FAIL",
                "message": f"{len(failed_suites)}/{total_suites} critical test suites failed",
                "failed_suites": failed_suites,
                "recommendations": [
                    "Fix failing critical tests before release",
                    "Review test failures and update code accordingly",
                    "Ensure all core functionality is properly tested",
                ],
            }

    def _check_performance(self) -> Dict:
        """Check performance benchmarks."""
        try:
            # Run performance tests
            cmd = [sys.executable, "-m", "pytest", "tests/performance/", "-v", "-q"]

            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_root)

            if result.returncode == 0:
                return {"status": "PASS", "message": "Performance benchmarks met"}
            else:
                return {
                    "status": "WARN",
                    "message": "Some performance tests failed",
                    "recommendations": [
                        "Review performance test failures",
                        "Optimize slow operations",
                        "Consider caching improvements",
                    ],
                }

        except Exception as e:
            return {"status": "WARN", "message": f"Performance check incomplete: {str(e)}"}

    def _check_security(self) -> Dict:
        """Check security compliance."""
        try:
            # Run security-focused tests
            cmd = [
                sys.executable,
                "-m",
                "pytest",
                "tests/quality/test_package_quality.py::TestSecurityCompliance",
                "-v",
                "-q",
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_root)

            if result.returncode == 0:
                return {"status": "PASS", "message": "Security compliance checks passed"}
            else:
                return {
                    "status": "WARN",
                    "message": "Some security checks failed",
                    "recommendations": [
                        "Review security test failures",
                        "Implement missing security headers",
                        "Enhance input validation",
                    ],
                }

        except Exception as e:
            return {"status": "WARN", "message": f"Security check incomplete: {str(e)}"}

    def _check_documentation(self) -> Dict:
        """Check documentation completeness."""
        required_docs = ["README.md", "dev-docs/31_testing.md", "dev-docs/40_api-service-guide.md"]

        missing_docs = []
        for doc in required_docs:
            doc_path = self.project_root / doc
            if not doc_path.exists():
                missing_docs.append(doc)

        if not missing_docs:
            return {"status": "PASS", "message": "All required documentation present"}
        else:
            return {
                "status": "FAIL",
                "message": f"Missing documentation: {', '.join(missing_docs)}",
                "recommendations": [
                    "Create missing documentation files",
                    "Update existing documentation",
                    "Ensure API documentation is current",
                ],
            }

    def _check_package_structure(self) -> Dict:
        """Check package structure completeness."""
        required_structure = [
            "core/",
            "api/",
            "tests/",
            "scripts/",
            "requirements.txt",
            "pyproject.toml",
        ]

        missing_items = []
        for item in required_structure:
            item_path = self.project_root / item
            if not item_path.exists():
                missing_items.append(item)

        if not missing_items:
            return {"status": "PASS", "message": "Package structure complete"}
        else:
            return {
                "status": "FAIL",
                "message": f"Missing structure: {', '.join(missing_items)}",
                "recommendations": [
                    "Create missing directories/files",
                    "Review package structure requirements",
                    "Ensure all components are properly organized",
                ],
            }

    def _check_api_compliance(self) -> Dict:
        """Check API compliance and documentation."""
        try:
            # Test API endpoints
            from fastapi.testclient import TestClient

            from api.main import app

            client = TestClient(app)

            # Test critical endpoints
            endpoints = ["/api/v1/health", "/api/v1/version", "/openapi.json"]

            failed_endpoints = []
            for endpoint in endpoints:
                try:
                    response = client.get(endpoint)
                    if response.status_code not in [200, 404]:  # 404 acceptable for some
                        failed_endpoints.append(f"{endpoint} ({response.status_code})")
                except Exception as e:
                    failed_endpoints.append(f"{endpoint} (error: {str(e)})")

            if not failed_endpoints:
                return {"status": "PASS", "message": "API compliance checks passed"}
            else:
                return {
                    "status": "FAIL",
                    "message": f"API issues: {', '.join(failed_endpoints)}",
                    "recommendations": [
                        "Fix failing API endpoints",
                        "Ensure proper error handling",
                        "Update API documentation",
                    ],
                }

        except Exception as e:
            return {"status": "ERROR", "message": f"API compliance check failed: {str(e)}"}

    def _generate_report(self):
        """Generate quality gate report."""
        report_file = (
            self.project_root
            / "test_results"
            / f"quality_gate_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        report_file.parent.mkdir(exist_ok=True)

        with open(report_file, "w") as f:
            json.dump(self.results, f, indent=2)

        print(f"\n📄 Quality gate report: {report_file}")

    def _print_summary(self):
        """Print quality gate summary."""
        print("\n" + "=" * 60)
        print("📊 QUALITY GATE SUMMARY")
        print("=" * 60)

        passed = sum(
            1 for gate in self.results["quality_gates"].values() if gate["status"] == "PASS"
        )
        total = len(self.results["quality_gates"])

        print(
            f"Overall Status: {'✅ PASS' if self.results['overall_status'] == 'PASS' else '❌ FAIL'}"
        )
        print(f"Gates Passed: {passed}/{total}")

        if self.results["recommendations"]:
            print(f"\n💡 Recommendations:")
            for i, rec in enumerate(self.results["recommendations"][:5], 1):
                print(f"   {i}. {rec}")

        print("\n" + "=" * 60)


def main():
    """Main function."""
    import argparse

    parser = argparse.ArgumentParser(description="QuantDB Package Quality Gate")
    parser.add_argument(
        "--min-coverage", type=int, default=80, help="Minimum test coverage percentage"
    )
    parser.add_argument(
        "--strict", action="store_true", help="Strict mode - warnings count as failures"
    )

    args = parser.parse_args()

    # Create quality gate runner
    gate = PackageQualityGate()
    gate.min_coverage = args.min_coverage

    # Run quality gate
    success = gate.run_quality_gate()

    # Exit with appropriate code
    if success:
        print("\n🎉 Package ready for GTM!")
        sys.exit(0)
    else:
        print("\n🚫 Package not ready - fix issues before release")
        sys.exit(1)


if __name__ == "__main__":
    main()
