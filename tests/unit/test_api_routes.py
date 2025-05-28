#!/usr/bin/env python
# tests/unit/test_api_routes.py
"""
Unit tests for API routes.

This script tests the API routes to ensure they are correctly registered
and respond to requests as expected.
"""

import os
import sys
import unittest
from fastapi.testclient import TestClient

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.api.main import app
from src.config import API_PREFIX
from src.enhanced_logger import setup_enhanced_logger

# Setup logger
logger = setup_enhanced_logger(__name__)

# Create test client
client = TestClient(app)


class TestAPIRoutes(unittest.TestCase):
    """Unit tests for API routes."""

    def test_root_endpoint(self):
        """Test the root endpoint."""
        response = client.get("/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("message", data)
        self.assertIn("documentation", data)
        self.assertIn("environment", data)

    def test_health_endpoint(self):
        """Test the health check endpoint."""
        response = client.get(f"{API_PREFIX}/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("status", data)
        self.assertEqual(data["status"], "ok")
        self.assertIn("version", data)
        self.assertIn("api_version", data)
        self.assertIn("timestamp", data)

    def test_assets_endpoints(self):
        """Test the assets endpoints."""
        # Test assets list endpoint
        response = client.get(f"{API_PREFIX}/assets/")
        self.assertEqual(response.status_code, 200)

        # Test asset by ID endpoint (will likely 404 but should be registered)
        response = client.get(f"{API_PREFIX}/assets/1")
        self.assertIn(response.status_code, [200, 404])  # Either OK or Not Found

        # Test asset by symbol endpoint (will likely 404 but should be registered)
        response = client.get(f"{API_PREFIX}/assets/symbol/000001")
        self.assertIn(response.status_code, [200, 404])  # Either OK or Not Found

    def test_prices_endpoints(self):
        """Test the prices endpoints."""
        # Test prices list endpoint
        response = client.get(f"{API_PREFIX}/prices/")
        self.assertEqual(response.status_code, 200)

        # Test prices by asset ID endpoint (will likely 404 but should be registered)
        response = client.get(f"{API_PREFIX}/prices/asset/1")
        self.assertIn(response.status_code, [200, 404])  # Either OK or Not Found

        # Test prices by symbol endpoint (will likely 404 but should be registered)
        response = client.get(f"{API_PREFIX}/prices/symbol/000001")
        self.assertIn(response.status_code, [200, 404])  # Either OK or Not Found

    def test_import_endpoints(self):
        """Test the import endpoints."""
        # Test import stock endpoint (POST only, so expect 405 Method Not Allowed)
        response = client.get(f"{API_PREFIX}/import/stock")
        self.assertEqual(response.status_code, 405)

        # Test import index endpoint (POST only, so expect 405 Method Not Allowed)
        response = client.get(f"{API_PREFIX}/import/index")
        self.assertEqual(response.status_code, 405)

        # Test import index constituents endpoint (POST only, so expect 405 Method Not Allowed)
        response = client.get(f"{API_PREFIX}/import/index/constituents")
        self.assertEqual(response.status_code, 405)

    def test_cache_endpoints(self):
        """Test the cache endpoints."""
        # Test cache status endpoint
        response = client.get(f"{API_PREFIX}/cache/status")
        self.assertEqual(response.status_code, 200)

        # Test cache keys endpoint
        response = client.get(f"{API_PREFIX}/cache/keys")
        self.assertEqual(response.status_code, 200)

        # Test cache key endpoint (will likely 404 but should be registered)
        response = client.get(f"{API_PREFIX}/cache/key/test_key")
        self.assertIn(response.status_code, [200, 404])  # Either OK or Not Found

    def test_historical_endpoints(self):
        """Test the historical data endpoints."""
        # Test historical stock endpoint (will likely 400 due to validation but should be registered)
        response = client.get(f"{API_PREFIX}/historical/stock/000001")
        self.assertIn(response.status_code, [200, 400, 404])  # Either OK, Bad Request, or Not Found

    def test_mcp_endpoint(self):
        """Test the MCP endpoint."""
        # Test MCP query endpoint (POST only, so expect 405 Method Not Allowed)
        response = client.get(f"{API_PREFIX}/mcp/query")
        self.assertEqual(response.status_code, 405)

    def test_version_endpoints(self):
        """Test the version endpoints."""
        # Test version info endpoint
        response = client.get(f"{API_PREFIX}/version")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("versions", data)
        self.assertIn("latest", data)
        self.assertIn("current", data)

        # Test current version endpoint
        current_version = data["current"]
        response = client.get(f"{API_PREFIX}/version/{current_version}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("version", data)
        self.assertIn("api_version", data)
        self.assertIn("release_date", data)

        # Test version history endpoint
        response = client.get(f"{API_PREFIX}/version/history")
        self.assertIn(response.status_code, [200, 404])  # Either OK or Not Found

    def test_error_handling(self):
        """Test error handling."""
        # Test 404 Not Found
        response = client.get("/nonexistent-endpoint")
        self.assertEqual(response.status_code, 404)

        # Test validation error
        response = client.post(f"{API_PREFIX}/mcp/query", json={})
        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
