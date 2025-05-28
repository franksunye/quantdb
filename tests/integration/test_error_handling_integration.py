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
        # Make request with wrong method to import endpoint
        response = client.get(f"{API_PREFIX}/import/stock")

        # Check response
        self.assertEqual(response.status_code, 405)

        # Parse response content
        content = response.json()

        # Check content structure (FastAPI default 405 format)
        self.assertIn("detail", content)
        self.assertEqual(content["detail"], "Method Not Allowed")

    def test_validation_error(self):
        """Test validation error."""
        # Make request with invalid data to import endpoint
        response = client.post(
            f"{API_PREFIX}/import/stock",
            json={}  # Missing required fields
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
        self.assertEqual(content["error"]["path"], f"{API_PREFIX}/import/stock")
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
        self.assertIn("errors", content["error"]["details"])
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

    def test_import_validation_error(self):
        """Test import endpoint validation error."""
        # Make request with invalid data to import endpoint
        response = client.post(
            f"{API_PREFIX}/import/stock",
            json={
                "symbol": "INVALID",  # Invalid symbol format
                "start_date": "invalid-date",
                "end_date": "2025-04-30"
            }
        )

        # Check response - import endpoint returns 200 but with success=false for errors
        self.assertEqual(response.status_code, 200)

        # Parse response content
        content = response.json()

        # Check content structure - import endpoint returns success=false for errors
        self.assertIn("success", content)
        self.assertFalse(content["success"])
        self.assertIn("message", content)
        self.assertIn("symbol", content)

if __name__ == "__main__":
    unittest.main()
