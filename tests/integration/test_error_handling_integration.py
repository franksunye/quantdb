"""
Integration tests for error handling.

This module tests the integration of the error handling system with the API.
"""
import unittest
import json
from fastapi.testclient import TestClient
from fastapi import HTTPException, status

from src.api.main import app
from src.config import API_PREFIX
from src.api.errors import (
    ErrorCode,
    QuantDBException,
    DataNotFoundException,
    DataFetchException,
    AKShareException,
    DatabaseException,
    MCPProcessingException
)

# Create test client
client = TestClient(app)

class TestErrorHandlingIntegration(unittest.TestCase):
    """Integration tests for error handling."""

    def test_not_found_error(self):
        """Test 404 Not Found error."""
        # Make request to non-existent endpoint
        response = client.get("/nonexistent-endpoint")

        # Check response
        self.assertEqual(response.status_code, 404)

        # Parse response content
        content = response.json()

        # Check content structure (FastAPI default 404 format)
        self.assertIn("detail", content)
        self.assertEqual(content["detail"], "Not Found")

    def test_method_not_allowed_error(self):
        """Test 405 Method Not Allowed error."""
        # Make request with wrong method to historical endpoint
        response = client.post(f"{API_PREFIX}/historical/stock/000001")

        # Check response
        self.assertEqual(response.status_code, 405)

        # Parse response content
        content = response.json()

        # Check content structure (FastAPI default 405 format)
        self.assertIn("detail", content)
        self.assertEqual(content["detail"], "Method Not Allowed")

    def test_validation_error(self):
        """Test validation error."""
        # Make request with invalid query parameters to assets endpoint
        response = client.get(
            f"{API_PREFIX}/assets",
            params={"limit": -1}  # Invalid limit value
        )

        # Check response
        self.assertEqual(response.status_code, 422)

        # Parse response content
        content = response.json()

        # Check content structure
        self.assertIn("error", content)
        self.assertEqual(content["error"]["code"], ErrorCode.VALIDATION_ERROR)
        self.assertIn("message", content["error"])
        self.assertEqual(content["error"]["status_code"], 422)
        self.assertIn("details", content["error"])
        self.assertIn("errors", content["error"]["details"])
        self.assertIn("path", content["error"])
        self.assertTrue(content["error"]["path"].startswith(f"{API_PREFIX}/assets"))
        self.assertIn("timestamp", content["error"])

    def test_invalid_date_format(self):
        """Test invalid date format error."""
        # Make request with invalid date format
        response = client.get(
            f"{API_PREFIX}/historical/stock/000001",
            params={"start_date": "invalid-date", "end_date": "2025-04-30"}
        )

        # Check response
        self.assertEqual(response.status_code, 500)  # Historical endpoint returns 500 for validation errors

        # Parse response content
        content = response.json()

        # Check content structure
        self.assertIn("error", content)
        self.assertEqual(content["error"]["code"], ErrorCode.INTERNAL_ERROR)
        self.assertIn("message", content["error"])
        self.assertEqual(content["error"]["status_code"], 500)
        # Note: Internal errors don't have detailed error structure
        self.assertIn("path", content["error"])
        self.assertIn("timestamp", content["error"])

    def test_invalid_symbol_format(self):
        """Test invalid symbol format error."""
        # Make request with invalid symbol format
        response = client.get(
            f"{API_PREFIX}/historical/stock/INVALID!@#",
            params={"start_date": "2025-04-01", "end_date": "2025-04-30"}
        )

        # Check response
        self.assertEqual(response.status_code, 400)  # Symbol validation returns 400

        # Parse response content
        content = response.json()

        # Check content structure
        self.assertIn("error", content)
        self.assertEqual(content["error"]["code"], ErrorCode.BAD_REQUEST)
        self.assertIn("message", content["error"])
        self.assertEqual(content["error"]["status_code"], 400)
        self.assertIn("details", content["error"])
        # Note: details might be empty for some error types
        self.assertIn("path", content["error"])
        self.assertIn("timestamp", content["error"])

    def test_invalid_date_range(self):
        """Test invalid date range error."""
        # Make request with end_date before start_date
        response = client.get(
            f"{API_PREFIX}/historical/stock/000001",
            params={"start_date": "2025-04-30", "end_date": "2025-04-01"}
        )

        # Check response
        self.assertEqual(response.status_code, 500)  # Historical endpoint returns 500 for validation errors

        # Parse response content
        content = response.json()

        # Check content structure
        self.assertIn("error", content)
        self.assertIn("message", content["error"])
        self.assertIn("status_code", content["error"])
        self.assertIn("path", content["error"])
        self.assertIn("timestamp", content["error"])

    def test_assets_validation_error(self):
        """Test assets endpoint validation error."""
        # Make request with invalid query parameters to assets endpoint
        response = client.get(
            f"{API_PREFIX}/assets",
            params={
                "skip": -1,  # Invalid skip value
                "limit": 2000  # Invalid limit value (exceeds maximum)
            }
        )

        # Check response - assets endpoint returns 422 for validation errors
        self.assertEqual(response.status_code, 422)

        # Parse response content
        content = response.json()

        # Check content structure - validation error format
        self.assertIn("error", content)
        self.assertEqual(content["error"]["code"], ErrorCode.VALIDATION_ERROR)
        self.assertIn("message", content["error"])
        self.assertIn("details", content["error"])

if __name__ == "__main__":
    unittest.main()
