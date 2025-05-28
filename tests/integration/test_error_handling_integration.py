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
        
        # Check content structure
        self.assertIn("error", content)
        self.assertEqual(content["error"]["code"], ErrorCode.NOT_FOUND)
        self.assertIn("message", content["error"])
        self.assertEqual(content["error"]["status_code"], 404)
        self.assertIn("path", content["error"])
        self.assertEqual(content["error"]["path"], "/nonexistent-endpoint")
        self.assertIn("timestamp", content["error"])
    
    def test_method_not_allowed_error(self):
        """Test 405 Method Not Allowed error."""
        # Make request with wrong method
        response = client.get(f"{API_PREFIX}/mcp/query")
        
        # Check response
        self.assertEqual(response.status_code, 405)
        
        # Parse response content
        content = response.json()
        
        # Check content structure
        self.assertIn("error", content)
        self.assertIn("message", content["error"])
        self.assertEqual(content["error"]["status_code"], 405)
        self.assertIn("path", content["error"])
        self.assertEqual(content["error"]["path"], f"{API_PREFIX}/mcp/query")
        self.assertIn("timestamp", content["error"])
    
    def test_validation_error(self):
        """Test validation error."""
        # Make request with invalid data
        response = client.post(
            f"{API_PREFIX}/mcp/query",
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
        self.assertEqual(content["error"]["path"], f"{API_PREFIX}/mcp/query")
        self.assertIn("timestamp", content["error"])
    
    def test_invalid_date_format(self):
        """Test invalid date format error."""
        # Make request with invalid date format
        response = client.get(
            f"{API_PREFIX}/historical/stock/000001",
            params={"start_date": "invalid-date", "end_date": "2025-04-30"}
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
        self.assertIn("timestamp", content["error"])
    
    def test_invalid_symbol_format(self):
        """Test invalid symbol format error."""
        # Make request with invalid symbol format
        response = client.get(
            f"{API_PREFIX}/historical/stock/INVALID!@#",
            params={"start_date": "2025-04-01", "end_date": "2025-04-30"}
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
        self.assertIn("timestamp", content["error"])
    
    def test_invalid_date_range(self):
        """Test invalid date range error."""
        # Make request with end_date before start_date
        response = client.get(
            f"{API_PREFIX}/historical/stock/000001",
            params={"start_date": "2025-04-30", "end_date": "2025-04-01"}
        )
        
        # Check response
        self.assertIn(response.status_code, [400, 422])  # Either Bad Request or Validation Error
        
        # Parse response content
        content = response.json()
        
        # Check content structure
        self.assertIn("error", content)
        self.assertIn("message", content["error"])
        self.assertIn("status_code", content["error"])
        self.assertIn("path", content["error"])
        self.assertIn("timestamp", content["error"])
    
    def test_mcp_query_error(self):
        """Test MCP query error."""
        # Make request with invalid query
        response = client.post(
            f"{API_PREFIX}/mcp/query",
            json={
                "query": "",  # Empty query
                "session_id": "test_session",
                "context": {}
            }
        )
        
        # Check response
        self.assertIn(response.status_code, [400, 422])  # Either Bad Request or Validation Error
        
        # Parse response content
        content = response.json()
        
        # Check content structure
        self.assertIn("error", content)
        self.assertIn("message", content["error"])
        self.assertIn("status_code", content["error"])
        self.assertIn("path", content["error"])
        self.assertIn("timestamp", content["error"])


if __name__ == "__main__":
    unittest.main()
