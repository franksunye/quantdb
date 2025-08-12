"""
Integration tests for logging system.

This module tests the integration of the enhanced logging system with the API.
"""
import json
import os
import tempfile
import time
import unittest
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from api.main import app
from core.utils.config import API_PREFIX

# Migrated to core
from core.utils.logger import EnhancedLogger, log_function, setup_enhanced_logger

# Create test client
client = TestClient(app)

class TestLoggingIntegration(unittest.TestCase):
    """Integration tests for logging system."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary log file
        self.temp_dir = tempfile.TemporaryDirectory()
        self.log_file = os.path.join(self.temp_dir.name, "test_log.log")

        # Create logger
        self.logger = EnhancedLogger(
            name="test_integration",
            log_file=self.log_file,
            level="DEBUG",
            console_output=False,  # Disable console output for tests
            detailed=True
        )

    def tearDown(self):
        """Tear down test fixtures."""
        # Clean up temporary directory
        self.temp_dir.cleanup()

    def test_api_request_logging(self):
        """Test API request logging."""
        # Make API request
        response = client.get("/")

        # Check response
        self.assertEqual(response.status_code, 200)

        # Check response content
        data = response.json()
        self.assertIn("message", data)
        self.assertEqual(data["message"], "Welcome to QuantDB API")

    def test_health_check_logging(self):
        """Test health check logging."""
        # Make API request
        response = client.get(f"{API_PREFIX}/health")

        # Check response
        self.assertEqual(response.status_code, 200)

        # Check response content
        data = response.json()
        self.assertIn("status", data)
        self.assertEqual(data["status"], "healthy")  # V1端点返回"healthy"

    def test_error_logging(self):
        """Test error logging."""
        # Make API request to non-existent endpoint
        response = client.get("/nonexistent-endpoint")

        # Check response
        self.assertEqual(response.status_code, 404)

        # Check response content
        data = response.json()
        self.assertIn("detail", data)
        self.assertEqual(data["detail"], "Not Found")

    def test_validation_error_logging(self):
        """Test validation error logging."""
        # Make API request with invalid query parameters
        response = client.get(
            f"{API_PREFIX}/assets",
            params={"limit": -1}  # Invalid limit value
        )

        # Check response
        self.assertEqual(response.status_code, 422)

        # Check response content
        data = response.json()
        self.assertIn("error", data)
        self.assertEqual(data["error"]["code"], "VALIDATION_ERROR")

    def test_log_function_integration(self):
        """Test log_function decorator integration."""
        # Define a test function with the decorator
        @log_function(logger=self.logger)
        def test_api_call():
            # Make API request
            return client.get("/")

        # Call the function
        response = test_api_call()

        # Check the response
        self.assertEqual(response.status_code, 200)

        # Check log file content
        with open(self.log_file, "r") as f:
            log_content = f.read()

            # Check that function start and end messages are in the log
            self.assertIn("FUNCTION START: test_api_call", log_content)
            self.assertIn("FUNCTION END: test_api_call - Success", log_content)

    def test_context_logging_integration(self):
        """Test context logging integration."""
        # Start context
        context_id = self.logger.start_context(metadata={"test": "value"})

        # Make API request
        response = client.get("/")

        # Check response
        self.assertEqual(response.status_code, 200)

        # Log response
        self.logger.info(f"API response: {response.status_code}")
        self.logger.log_data("response_data", response.json())

        # Add metrics
        self.logger.add_metric("response_time", 0.123)

        # End context
        self.logger.end_context()

        # Check log file content
        with open(self.log_file, "r") as f:
            log_content = f.read()

            # Check that context start and end messages are in the log
            self.assertIn("CONTEXT START", log_content)
            self.assertIn("CONTEXT END", log_content)
            self.assertIn("API response: 200", log_content)
            self.assertIn("DATA [response_data]", log_content)
            self.assertIn("CONTEXT METRICS", log_content)
            self.assertIn("response_time", log_content)

    def test_error_handling_with_logging(self):
        """Test error handling with logging."""
        # Start context
        context_id = self.logger.start_context()

        try:
            # Make API request to non-existent endpoint
            response = client.get("/nonexistent-endpoint")

            # Log response
            self.logger.info(f"API response: {response.status_code}")
            self.logger.log_data("response_data", response.json())
        except Exception as e:
            # Log error
            self.logger.error(f"API request failed: {str(e)}", exc_info=e)
        finally:
            # End context
            self.logger.end_context()

        # Check log file content
        with open(self.log_file, "r") as f:
            log_content = f.read()

            # Check that context start and end messages are in the log
            self.assertIn("CONTEXT START", log_content)
            self.assertIn("CONTEXT END", log_content)
            self.assertIn("API response: 404", log_content)
            self.assertIn("DATA [response_data]", log_content)

    def test_performance_metrics_logging(self):
        """Test performance metrics logging."""
        # Start context
        context_id = self.logger.start_context()

        # Record start time
        start_time = time.time()

        # Make API request
        response = client.get("/")

        # Record end time
        end_time = time.time()

        # Calculate duration
        duration = end_time - start_time

        # Log performance metrics
        self.logger.add_metric("api_request_time", duration)
        self.logger.info(f"API request completed in {duration:.4f}s")

        # End context
        self.logger.end_context()

        # Check log file content
        with open(self.log_file, "r") as f:
            log_content = f.read()

            # Check that performance metrics are in the log
            self.assertIn("CONTEXT METRICS", log_content)
            self.assertIn("api_request_time", log_content)
            self.assertIn("API request completed in", log_content)

if __name__ == "__main__":
    unittest.main()
