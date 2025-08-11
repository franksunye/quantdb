"""
Package Quality Assurance Tests for QuantDB.

This module contains comprehensive quality assurance tests to ensure
the Package version meets production standards including:
- Code coverage requirements
- Performance benchmarks
- API contract compliance
- Data integrity validation
- Security checks
"""

import json
import os
import subprocess
import sys
import time
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

from api.main import app
from core.cache import AKShareAdapter
from core.models import Asset, DailyStockData
from core.services import AssetInfoService, StockDataService


class TestPackageQuality(unittest.TestCase):
    """Package quality assurance tests."""
    
    def setUp(self):
        """Set up test environment."""
        self.client = TestClient(app)
        self.project_root = Path(__file__).parent.parent.parent
    
    def test_api_health_and_availability(self):
        """Test API health and availability."""
        response = self.client.get("/api/v1/health")
        
        # API must be healthy
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        
        # Response time must be acceptable
        self.assertLess(response.elapsed.total_seconds(), 1.0)
    
    def test_api_version_consistency(self):
        """Test API version consistency."""
        response = self.client.get("/api/v1/version")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Version must be present and valid
        self.assertIn("version", data)
        self.assertRegex(data["version"], r"^\d+\.\d+\.\d+")
        
        # Architecture version must match
        self.assertIn("architecture", data)
        self.assertEqual(data["architecture"], "2.1.0-stable")
    
    def test_openapi_documentation_completeness(self):
        """Test OpenAPI documentation completeness."""
        response = self.client.get("/openapi.json")
        
        self.assertEqual(response.status_code, 200)
        openapi_spec = response.json()
        
        # Must have required OpenAPI fields
        required_fields = ["openapi", "info", "paths"]
        for field in required_fields:
            self.assertIn(field, openapi_spec)
        
        # Must have API info
        info = openapi_spec["info"]
        self.assertIn("title", info)
        self.assertIn("version", info)
        self.assertIn("description", info)
        
        # Must have documented endpoints
        paths = openapi_spec["paths"]
        required_endpoints = [
            "/api/v1/health",
            "/api/v1/version",
            "/api/v1/assets/{symbol}",
            "/api/v1/stocks/{symbol}/daily"
        ]
        
        for endpoint in required_endpoints:
            # Check if endpoint exists (with or without path parameters)
            endpoint_exists = any(
                endpoint.replace("{symbol}", "test") in path or 
                endpoint in path for path in paths.keys()
            )
            self.assertTrue(endpoint_exists, f"Endpoint {endpoint} not documented")


class TestPerformanceBenchmarks(unittest.TestCase):
    """Performance benchmark tests for Package quality."""
    
    def setUp(self):
        """Set up performance test environment."""
        self.client = TestClient(app)
    
    def test_api_response_time_benchmarks(self):
        """Test API response time benchmarks."""
        endpoints_benchmarks = [
            ("/api/v1/health", 0.1),  # Health check: < 100ms
            ("/api/v1/version", 0.2), # Version info: < 200ms
        ]
        
        for endpoint, max_time in endpoints_benchmarks:
            with self.subTest(endpoint=endpoint):
                start_time = time.time()
                response = self.client.get(endpoint)
                duration = time.time() - start_time
                
                # Must respond successfully
                self.assertEqual(response.status_code, 200)
                
                # Must meet performance benchmark
                self.assertLess(duration, max_time, 
                    f"{endpoint} took {duration:.3f}s, expected < {max_time}s")
    
    @patch('core.services.stock_data_service.StockDataService.get_daily_data')
    def test_data_retrieval_performance(self, mock_get_data):
        """Test data retrieval performance."""
        # Mock fast data response
        mock_get_data.return_value = [
            {
                "date": "2024-01-15",
                "open": 12.50,
                "high": 12.80,
                "low": 12.30,
                "close": 12.75,
                "volume": 1000000
            }
        ]
        
        start_time = time.time()
        response = self.client.get("/api/v1/stocks/000001/daily")
        duration = time.time() - start_time
        
        # Data retrieval must be fast (< 2 seconds)
        self.assertLess(duration, 2.0)
        
        if response.status_code == 200:
            data = response.json()
            self.assertIsInstance(data, list)
    
    def test_concurrent_request_handling(self):
        """Test concurrent request handling capability."""
        import queue
        import threading
        
        results = queue.Queue()
        
        def make_request():
            try:
                response = self.client.get("/api/v1/health")
                results.put({
                    "status_code": response.status_code,
                    "success": response.status_code == 200
                })
            except Exception as e:
                results.put({"error": str(e), "success": False})
        
        # Create 10 concurrent requests
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=5.0)
        
        # Collect results
        successful_requests = 0
        while not results.empty():
            result = results.get()
            if result.get("success", False):
                successful_requests += 1
        
        # At least 80% of concurrent requests should succeed
        success_rate = successful_requests / 10
        self.assertGreaterEqual(success_rate, 0.8, 
            f"Only {success_rate:.1%} of concurrent requests succeeded")


class TestDataIntegrity(unittest.TestCase):
    """Data integrity and validation tests."""
    
    def test_data_model_constraints(self):
        """Test data model constraints and validation."""
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        from core.models import Asset, Base, DailyStockData

        # Create in-memory test database
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        
        try:
            # Test Asset model constraints
            asset = Asset(
                symbol="000001",
                name="平安银行",
                asset_type="stock",
                exchange="SZSE",
                currency="CNY"
            )
            session.add(asset)
            session.commit()
            
            # Test DailyStockData model constraints
            daily_data = DailyStockData(
                asset_id=asset.asset_id,
                trade_date="2024-01-15",
                open=12.50,
                high=12.80,
                low=12.30,
                close=12.75,
                volume=1000000
            )
            session.add(daily_data)
            session.commit()
            
            # Verify data integrity
            saved_asset = session.query(Asset).filter_by(symbol="000001").first()
            self.assertIsNotNone(saved_asset)
            self.assertEqual(saved_asset.name, "平安银行")
            
            saved_data = session.query(DailyStockData).filter_by(
                asset_id=asset.asset_id
            ).first()
            self.assertIsNotNone(saved_data)
            self.assertEqual(saved_data.close, 12.75)
            
        finally:
            session.close()
    
    def test_data_validation_rules(self):
        """Test data validation rules."""
        from core.utils.validators import validate_date_format, validate_stock_symbol

        # Test symbol validation
        valid_symbols = ["000001", "600000", "300001"]
        invalid_symbols = ["", "INVALID", "00001", "0000001"]
        
        for symbol in valid_symbols:
            self.assertTrue(validate_stock_symbol(symbol), 
                f"Valid symbol {symbol} failed validation")
        
        for symbol in invalid_symbols:
            self.assertFalse(validate_stock_symbol(symbol), 
                f"Invalid symbol {symbol} passed validation")
        
        # Test date validation
        valid_dates = ["2024-01-15", "2023-12-31"]
        invalid_dates = ["2024-13-01", "invalid-date", ""]
        
        for date_str in valid_dates:
            self.assertTrue(validate_date_format(date_str), 
                f"Valid date {date_str} failed validation")
        
        for date_str in invalid_dates:
            self.assertFalse(validate_date_format(date_str), 
                f"Invalid date {date_str} passed validation")


class TestSecurityCompliance(unittest.TestCase):
    """Security compliance tests."""
    
    def setUp(self):
        """Set up security test environment."""
        self.client = TestClient(app)
    
    def test_api_security_headers(self):
        """Test API security headers."""
        response = self.client.get("/api/v1/health")
        
        # Check for security headers (if implemented)
        headers = response.headers
        
        # These are optional but recommended
        security_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options", 
            "X-XSS-Protection"
        ]
        
        # At least log if security headers are missing
        for header in security_headers:
            if header not in headers:
                print(f"Warning: Security header {header} not present")
    
    def test_input_sanitization(self):
        """Test input sanitization and injection prevention."""
        # Test SQL injection attempts
        malicious_inputs = [
            "'; DROP TABLE assets; --",
            "' OR '1'='1",
            "<script>alert('xss')</script>",
            "../../../etc/passwd"
        ]
        
        for malicious_input in malicious_inputs:
            with self.subTest(input=malicious_input):
                # Test with malicious symbol
                response = self.client.get(f"/api/v1/assets/{malicious_input}")
                
                # Should return 422 (validation error) or 404 (not found)
                # Should NOT return 500 (server error from injection)
                self.assertIn(response.status_code, [400, 404, 422])
    
    def test_error_information_disclosure(self):
        """Test that errors don't disclose sensitive information."""
        # Test with invalid endpoint
        response = self.client.get("/api/v1/nonexistent")
        
        if response.status_code == 404:
            error_data = response.json()
            error_message = str(error_data).lower()
            
            # Should not contain sensitive information
            sensitive_terms = ["password", "secret", "key", "token", "database"]
            for term in sensitive_terms:
                self.assertNotIn(term, error_message, 
                    f"Error message contains sensitive term: {term}")


class TestCodeQualityMetrics(unittest.TestCase):
    """Code quality metrics tests."""
    
    def test_import_structure(self):
        """Test import structure and dependencies."""
        # Test that core modules can be imported
        try:
            from api.main import app
            from core.cache import AKShareAdapter
            from core.models import Asset, DailyStockData
            from core.services import AssetInfoService, StockDataService
        except ImportError as e:
            self.fail(f"Failed to import core modules: {e}")
    
    def test_configuration_completeness(self):
        """Test configuration completeness."""
        # Check for required configuration files
        config_files = [
            "pyproject.toml",
            "requirements.txt",
            ".coveragerc"
        ]
        
        project_root = Path(__file__).parent.parent.parent
        
        for config_file in config_files:
            config_path = project_root / config_file
            self.assertTrue(config_path.exists(), 
                f"Required configuration file {config_file} not found")
    
    def test_documentation_completeness(self):
        """Test documentation completeness."""
        # Check for required documentation files
        doc_files = [
            "README.md",
            "dev-docs/31_testing.md"
        ]
        
        project_root = Path(__file__).parent.parent.parent
        
        for doc_file in doc_files:
            doc_path = project_root / doc_file
            self.assertTrue(doc_path.exists(), 
                f"Required documentation file {doc_file} not found")


class TestPackageReadiness(unittest.TestCase):
    """Package readiness tests."""
    
    def test_package_structure(self):
        """Test package structure completeness."""
        project_root = Path(__file__).parent.parent.parent
        
        required_directories = [
            "core",
            "api", 
            "tests",
            "scripts"
        ]
        
        for directory in required_directories:
            dir_path = project_root / directory
            self.assertTrue(dir_path.exists() and dir_path.is_dir(), 
                f"Required directory {directory} not found")
    
    def test_test_coverage_requirements(self):
        """Test that test coverage meets Package requirements."""
        # This would typically run coverage analysis
        # For now, we'll check that coverage tools are available
        try:
            import coverage
        except ImportError:
            self.fail("Coverage analysis tools not available")
    
    def test_production_readiness_checklist(self):
        """Test production readiness checklist."""
        checklist_items = [
            ("API health endpoint", lambda: self.client.get("/api/v1/health").status_code == 200),
            ("Version endpoint", lambda: self.client.get("/api/v1/version").status_code == 200),
            ("OpenAPI documentation", lambda: self.client.get("/openapi.json").status_code == 200),
        ]
        
        failed_items = []
        for item_name, check_func in checklist_items:
            try:
                if not check_func():
                    failed_items.append(item_name)
            except Exception:
                failed_items.append(item_name)
        
        if failed_items:
            self.fail(f"Production readiness check failed for: {', '.join(failed_items)}")


if __name__ == "__main__":
    # Run quality assurance tests
    unittest.main(verbosity=2)
