#!/usr/bin/env python
# tests/integration/test_cache_api.py
"""
Integration tests for the cache API.
"""

import os
import unittest
from tempfile import NamedTemporaryFile
from fastapi.testclient import TestClient

from src.api.cache_api import router as cache_router
from src.cache.models import CacheEntryStatus, FreshnessStatus

class TestCacheAPI(unittest.TestCase):
    """Integration tests for the cache API."""

    def setUp(self):
        """Set up the test environment."""
        # Create temporary database files
        self.cache_db = NamedTemporaryFile(delete=False, suffix='.db')
        self.cache_db.close()
        self.freshness_db = NamedTemporaryFile(delete=False, suffix='.db')
        self.freshness_db.close()

        # Initialize the cache engine and freshness tracker
        self.cache_engine = CacheEngine(db_path=self.cache_db.name)
        self.freshness_tracker = FreshnessTracker(db_path=self.freshness_db.name)

        # Create a FastAPI test client
        from fastapi import FastAPI
        app = FastAPI()

        # Override the dependencies
        def get_cache_engine():
            return self.cache_engine

        def get_freshness_tracker():
            return self.freshness_tracker

        # Override the dependencies in the router
        from src.api.cache_api import get_cache_engine as original_get_cache_engine
        from src.api.cache_api import get_freshness_tracker as original_get_freshness_tracker

        app.dependency_overrides[original_get_cache_engine] = get_cache_engine
        app.dependency_overrides[original_get_freshness_tracker] = get_freshness_tracker

        app.include_router(cache_router)
        self.client = TestClient(app)

        # Add some test data to the cache
        for i in range(5):
            cache_key = f"test_key_{i}"
            data = {"test": f"data_{i}"}
            ttl = 60  # 1 minute
            self.cache_engine.set(cache_key, data, ttl=ttl)
            self.freshness_tracker.mark_updated(cache_key, ttl=ttl)

    def tearDown(self):
        """Clean up the test environment."""
        # Close the database connections
        del self.cache_engine
        del self.freshness_tracker

        # Remove the temporary database files
        os.unlink(self.cache_db.name)
        os.unlink(self.freshness_db.name)

    def test_get_cache_stats(self):
        """Test getting cache statistics."""
        # Get cache statistics
        response = self.client.get("/api/cache/stats")

        # Check the response
        self.assertEqual(response.status_code, 200)
        stats = response.json()
        self.assertEqual(stats["total_entries"], 5)
        self.assertEqual(stats["hits"], 0)
        self.assertEqual(stats["misses"], 0)
        self.assertEqual(stats["hit_rate"], 0)
        self.assertGreater(stats["total_size_bytes"], 0)
        self.assertEqual(stats["expired_entries"], 0)
        self.assertEqual(len(stats["entries_by_status"]), 1)
        self.assertEqual(stats["entries_by_status"][CacheEntryStatus.VALID.value], 5)
        self.assertEqual(len(stats["top_accessed_keys"]), 5)

    def test_get_freshness_stats(self):
        """Test getting freshness statistics."""
        # Get freshness statistics
        response = self.client.get("/api/cache/freshness/stats")

        # Check the response
        self.assertEqual(response.status_code, 200)
        stats = response.json()
        self.assertEqual(stats["total_entries"], 5)
        self.assertIn(FreshnessStatus.FRESH.value, stats["entries_by_status"])
        self.assertEqual(stats["entries_by_status"][FreshnessStatus.FRESH.value], 5)
        self.assertEqual(stats["expired_entries"], 0)
        self.assertEqual(stats["scheduled_updates"], 0)

    def test_get_cache_keys(self):
        """Test getting cache keys."""
        # Get all cache keys
        response = self.client.get("/api/cache/keys")

        # Check the response
        self.assertEqual(response.status_code, 200)
        keys = response.json()
        self.assertEqual(len(keys), 5)
        for i in range(5):
            self.assertIn(f"test_key_{i}", keys)

    def test_get_cache_keys_with_prefix(self):
        """Test getting cache keys with a prefix."""
        # Add some cache entries with a specific prefix
        for i in range(3):
            cache_key = f"prefix_test_key_{i}"
            data = {"test": f"data_{i}"}
            ttl = 60  # 1 minute
            self.cache_engine.set(cache_key, data, ttl=ttl)
            self.freshness_tracker.mark_updated(cache_key, ttl=ttl)

        # Get cache keys with the prefix
        response = self.client.get("/api/cache/keys?prefix=prefix")

        # Check the response
        self.assertEqual(response.status_code, 200)
        keys = response.json()
        self.assertEqual(len(keys), 3)
        for i in range(3):
            self.assertIn(f"prefix_test_key_{i}", keys)

    def test_get_cache_entry(self):
        """Test getting a cache entry."""
        # Get a specific cache entry
        cache_key = "test_key_0"
        response = self.client.get(f"/api/cache/entry/{cache_key}")

        # Check the response
        self.assertEqual(response.status_code, 200)
        entry = response.json()
        self.assertEqual(entry["key"], cache_key)
        self.assertEqual(entry["status"], CacheEntryStatus.VALID.value)
        self.assertEqual(entry["access_count"], 0)
        self.assertEqual(entry["freshness_status"], FreshnessStatus.FRESH.value)

    def test_get_nonexistent_cache_entry(self):
        """Test getting a nonexistent cache entry."""
        # Get a nonexistent cache entry
        cache_key = "nonexistent_key"
        response = self.client.get(f"/api/cache/entry/{cache_key}")

        # Check the response
        self.assertEqual(response.status_code, 404)

    def test_delete_cache_entry(self):
        """Test deleting a cache entry."""
        # Delete a specific cache entry
        cache_key = "test_key_0"
        # First, set the cache entry to make sure it exists
        self.cache_engine.set(cache_key, "test_value")
        # Then delete it using the API with path parameter
        response = self.client.delete(f"/api/cache/entry/{cache_key}")

        # Check the response
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(result["key"], cache_key)
        self.assertTrue(result["success"])

        # Try to get the deleted entry
        response = self.client.get(f"/api/cache/entry/{cache_key}")
        self.assertEqual(response.status_code, 404)

    def test_invalidate_cache_entry(self):
        """Test invalidating a cache entry."""
        # Invalidate a specific cache entry
        cache_key = "test_key_0"
        response = self.client.post("/api/cache/invalidate", json={"key": cache_key})

        # Check the response
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(result["key"], cache_key)
        self.assertTrue(result["success"])

        # Get the invalidated entry
        response = self.client.get(f"/api/cache/entry/{cache_key}")
        self.assertEqual(response.status_code, 200)
        entry = response.json()
        self.assertEqual(entry["status"], CacheEntryStatus.INVALID.value)

    def test_clear_cache(self):
        """Test clearing the cache."""
        # Clear the cache
        response = self.client.delete("/api/cache/clear")

        # Check the response
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertTrue(result["success"])

        # Get cache keys
        response = self.client.get("/api/cache/keys")
        self.assertEqual(response.status_code, 200)
        keys = response.json()
        self.assertEqual(len(keys), 0)

if __name__ == "__main__":
    unittest.main()
