#!/usr/bin/env python
# tests/unit/test_cache_engine.py
"""
Unit tests for the CacheEngine class.
"""

import os
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from tempfile import NamedTemporaryFile

import pandas as pd

from src.cache.cache_engine import CacheEngine
from src.cache.models import CacheEntryStatus


class TestCacheEngine(unittest.TestCase):
    """Test cases for the CacheEngine class."""

    def setUp(self):
        """Set up the test environment."""
        # Create a temporary database file
        self.temp_db = NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.cache_engine = CacheEngine(db_path=self.temp_db.name)

    def tearDown(self):
        """Clean up the test environment."""
        # Close the database connection
        del self.cache_engine
        # Remove the temporary database file
        os.unlink(self.temp_db.name)

    def test_set_and_get(self):
        """Test setting and getting a cache entry."""
        # Set a cache entry
        key = "test_key"
        data = {"test": "data"}
        ttl = 60  # 1 minute
        self.assertTrue(self.cache_engine.set(key, data, ttl=ttl))

        # Get the cache entry
        result = self.cache_engine.get(key)
        self.assertEqual(result, data)

    def test_set_and_get_with_namespace(self):
        """Test setting and getting a cache entry with a namespace."""
        # Set a cache entry with a namespace
        namespace = "test_namespace"
        key = self.cache_engine.generate_key("test_key", namespace=namespace)
        data = {"test": "data"}
        ttl = 60  # 1 minute
        self.assertTrue(self.cache_engine.set(key, data, ttl=ttl))

        # Get the cache entry
        result = self.cache_engine.get(key)
        self.assertEqual(result, data)

    def test_set_and_get_with_version(self):
        """Test setting and getting a cache entry with a version."""
        # Set a cache entry with a version
        version = "1.0"
        key = self.cache_engine.generate_key("test_key", version=version)
        data = {"test": "data"}
        ttl = 60  # 1 minute
        self.assertTrue(self.cache_engine.set(key, data, ttl=ttl))

        # Get the cache entry
        result = self.cache_engine.get(key)
        self.assertEqual(result, data)

    def test_set_and_get_with_prefix(self):
        """Test setting and getting a cache entry with a prefix."""
        # Set a cache entry with a prefix
        prefix = "test_prefix"
        key = self.cache_engine.generate_key("test_key", prefix=prefix)
        data = {"test": "data"}
        ttl = 60  # 1 minute
        self.assertTrue(self.cache_engine.set(key, data, ttl=ttl))

        # Get the cache entry
        result = self.cache_engine.get(key)
        self.assertEqual(result, data)

    def test_set_and_get_with_complex_data(self):
        """Test setting and getting a cache entry with complex data."""
        # Set a cache entry with a pandas DataFrame
        key = "test_key_df"
        data = pd.DataFrame({
            "A": [1, 2, 3],
            "B": [4, 5, 6]
        })
        ttl = 60  # 1 minute
        self.assertTrue(self.cache_engine.set(key, data, ttl=ttl))

        # Get the cache entry
        result = self.cache_engine.get(key)
        pd.testing.assert_frame_equal(result, data)

    def test_set_and_get_with_expiration(self):
        """Test setting and getting a cache entry with expiration."""
        # Set a cache entry with a short TTL
        key = "test_key_expire"
        data = {"test": "data"}
        ttl = 1  # 1 second
        self.assertTrue(self.cache_engine.set(key, data, ttl=ttl))

        # Wait for the entry to expire
        import time
        time.sleep(2)

        # Get the cache entry
        result = self.cache_engine.get(key)
        self.assertIsNone(result)

    def test_invalidate(self):
        """Test invalidating a cache entry."""
        # Set a cache entry
        key = "test_key_invalidate"
        data = {"test": "data"}
        ttl = 60  # 1 minute
        self.assertTrue(self.cache_engine.set(key, data, ttl=ttl))

        # Invalidate the cache entry
        self.assertTrue(self.cache_engine.invalidate(key))

        # Get the cache entry
        result = self.cache_engine.get(key)
        self.assertIsNone(result)

    def test_delete(self):
        """Test deleting a cache entry."""
        # Set a cache entry
        key = "test_key_delete"
        data = {"test": "data"}
        ttl = 60  # 1 minute
        self.assertTrue(self.cache_engine.set(key, data, ttl=ttl))

        # Delete the cache entry
        self.assertTrue(self.cache_engine.delete(key))

        # Get the cache entry
        result = self.cache_engine.get(key)
        self.assertIsNone(result)

    def test_clear(self):
        """Test clearing all cache entries."""
        # Set multiple cache entries
        for i in range(5):
            key = f"test_key_{i}"
            data = {"test": f"data_{i}"}
            ttl = 60  # 1 minute
            self.assertTrue(self.cache_engine.set(key, data, ttl=ttl))

        # Clear all cache entries
        self.assertTrue(self.cache_engine.clear())

        # Get all keys
        keys = self.cache_engine.get_keys()
        self.assertEqual(len(keys), 0)

    def test_get_keys(self):
        """Test getting all cache keys."""
        # Set multiple cache entries
        for i in range(5):
            key = f"test_key_{i}"
            data = {"test": f"data_{i}"}
            ttl = 60  # 1 minute
            self.assertTrue(self.cache_engine.set(key, data, ttl=ttl))

        # Get all keys
        keys = self.cache_engine.get_keys()
        self.assertEqual(len(keys), 5)
        for i in range(5):
            self.assertIn(f"test_key_{i}", keys)

    def test_get_keys_with_prefix(self):
        """Test getting cache keys with a prefix."""
        # Set multiple cache entries with different prefixes
        for i in range(3):
            key = f"prefix1_key_{i}"
            data = {"test": f"data_{i}"}
            ttl = 60  # 1 minute
            self.assertTrue(self.cache_engine.set(key, data, ttl=ttl))

        for i in range(2):
            key = f"prefix2_key_{i}"
            data = {"test": f"data_{i}"}
            ttl = 60  # 1 minute
            self.assertTrue(self.cache_engine.set(key, data, ttl=ttl))

        # Get keys with prefix1
        keys = self.cache_engine.get_keys(prefix="prefix1")
        self.assertEqual(len(keys), 3)
        for i in range(3):
            self.assertIn(f"prefix1_key_{i}", keys)

        # Get keys with prefix2
        keys = self.cache_engine.get_keys(prefix="prefix2")
        self.assertEqual(len(keys), 2)
        for i in range(2):
            self.assertIn(f"prefix2_key_{i}", keys)

    def test_get_stats(self):
        """Test getting cache statistics."""
        # Set multiple cache entries
        for i in range(5):
            key = f"test_key_{i}"
            data = {"test": f"data_{i}"}
            ttl = 60  # 1 minute
            self.assertTrue(self.cache_engine.set(key, data, ttl=ttl))

        # Get some entries to increment hit count
        for i in range(3):
            self.cache_engine.get(f"test_key_{i}")

        # Get non-existent entries to increment miss count
        for i in range(2):
            self.cache_engine.get(f"non_existent_key_{i}")

        # Get cache statistics
        stats = self.cache_engine.get_stats()

        # Check basic statistics
        self.assertEqual(stats["total_entries"], 5)
        self.assertEqual(stats["hits"], 3)
        self.assertEqual(stats["misses"], 2)
        self.assertEqual(stats["hit_rate"], 0.6)
        self.assertGreater(stats["total_size_bytes"], 0)
        self.assertEqual(stats["expired_entries"], 0)
        self.assertEqual(len(stats["entries_by_status"]), 1)
        self.assertEqual(stats["entries_by_status"][CacheEntryStatus.VALID.value], 5)
        self.assertEqual(len(stats["top_accessed_keys"]), 5)

        # Check advanced statistics
        self.assertIn("hot_keys", stats)
        self.assertIn("recent_keys", stats)
        self.assertIn("recent_accessed_keys", stats)
        self.assertIn("soon_expire_keys", stats)
        self.assertIn("largest_entries", stats)
        self.assertIn("bytes_per_entry", stats)
        self.assertIn("expiration_rate", stats)
        self.assertIn("cache_health", stats)


if __name__ == "__main__":
    unittest.main()
