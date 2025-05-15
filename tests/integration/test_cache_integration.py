#!/usr/bin/env python
# tests/integration/test_cache_integration.py
"""
Integration tests for the cache system.
"""

import os
import unittest
from tempfile import NamedTemporaryFile

import pandas as pd

from src.cache.cache_engine import CacheEngine
from src.cache.freshness_tracker import FreshnessTracker
from src.cache.models import FreshnessStatus


class TestCacheIntegration(unittest.TestCase):
    """Integration tests for the cache system."""

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

    def tearDown(self):
        """Clean up the test environment."""
        # Close the database connections
        del self.cache_engine
        del self.freshness_tracker

        # Remove the temporary database files
        os.unlink(self.cache_db.name)
        os.unlink(self.freshness_db.name)

    def test_cache_and_freshness_integration(self):
        """Test the integration of cache engine and freshness tracker."""
        # Set a cache entry
        cache_key = "test_integration_key"
        data = {"test": "data"}
        ttl = 60  # 1 minute

        # Set the cache entry and mark it as updated in the freshness tracker
        self.assertTrue(self.cache_engine.set(cache_key, data, ttl=ttl))
        self.freshness_tracker.mark_updated(cache_key, ttl=ttl)

        # Get the cache entry and freshness information
        cached_data = self.cache_engine.get(cache_key)
        freshness_info = self.freshness_tracker.get_freshness_status(cache_key)

        # Check the results
        self.assertEqual(cached_data, data)
        self.assertEqual(freshness_info["status"], FreshnessStatus.FRESH.value)

        # Mark the entry as stale
        self.assertTrue(self.freshness_tracker.mark_stale(cache_key))

        # Get the freshness information
        freshness_info = self.freshness_tracker.get_freshness_status(cache_key)
        self.assertEqual(freshness_info["status"], FreshnessStatus.STALE.value)

        # Update the cache entry
        new_data = {"test": "updated_data"}
        self.assertTrue(self.cache_engine.set(cache_key, new_data, ttl=ttl))
        self.freshness_tracker.mark_updated(cache_key, ttl=ttl)

        # Get the cache entry and freshness information
        cached_data = self.cache_engine.get(cache_key)
        freshness_info = self.freshness_tracker.get_freshness_status(cache_key)

        # Check the results
        self.assertEqual(cached_data, new_data)
        self.assertEqual(freshness_info["status"], FreshnessStatus.FRESH.value)

        # Delete the cache entry
        self.assertTrue(self.cache_engine.delete(cache_key))
        self.assertTrue(self.freshness_tracker.delete(cache_key))

        # Get the cache entry and freshness information
        cached_data = self.cache_engine.get(cache_key)
        freshness_info = self.freshness_tracker.get_freshness_status(cache_key)

        # Check the results
        self.assertIsNone(cached_data)
        self.assertEqual(freshness_info["status"], FreshnessStatus.UNKNOWN.value)

    def test_cache_expiration_and_freshness(self):
        """Test cache expiration and freshness tracking."""
        # Set a cache entry with a short TTL
        cache_key = "test_expiration_key"
        data = {"test": "data"}
        ttl = 1  # 1 second

        # Set the cache entry and mark it as updated in the freshness tracker
        self.assertTrue(self.cache_engine.set(cache_key, data, ttl=ttl))
        self.freshness_tracker.mark_updated(cache_key, ttl=ttl)

        # Wait for the entry to expire
        import time
        time.sleep(2)

        # Get the cache entry and freshness information
        cached_data = self.cache_engine.get(cache_key)
        freshness_info = self.freshness_tracker.get_freshness_status(cache_key)

        # Check the results
        self.assertIsNone(cached_data)
        self.assertEqual(freshness_info["status"], FreshnessStatus.EXPIRED.value)

    def test_cache_invalidation_and_freshness(self):
        """Test cache invalidation and freshness tracking."""
        # Set a cache entry
        cache_key = "test_invalidation_key"
        data = {"test": "data"}
        ttl = 60  # 1 minute

        # Set the cache entry and mark it as updated in the freshness tracker
        self.assertTrue(self.cache_engine.set(cache_key, data, ttl=ttl))
        self.freshness_tracker.mark_updated(cache_key, ttl=ttl)

        # Invalidate the cache entry
        self.assertTrue(self.cache_engine.invalidate(cache_key))
        self.assertTrue(self.freshness_tracker.mark_stale(cache_key))

        # Get the cache entry and freshness information
        cached_data = self.cache_engine.get(cache_key)
        freshness_info = self.freshness_tracker.get_freshness_status(cache_key)

        # Check the results
        self.assertIsNone(cached_data)
        self.assertEqual(freshness_info["status"], FreshnessStatus.STALE.value)

    def test_cache_clear_and_freshness(self):
        """Test clearing the cache and freshness tracking."""
        # Set multiple cache entries
        for i in range(5):
            cache_key = f"test_clear_key_{i}"
            data = {"test": f"data_{i}"}
            ttl = 60  # 1 minute
            self.assertTrue(self.cache_engine.set(cache_key, data, ttl=ttl))
            self.freshness_tracker.mark_updated(cache_key, ttl=ttl)

        # Clear the cache and freshness tracker
        self.assertTrue(self.cache_engine.clear())
        self.assertTrue(self.freshness_tracker.clear())

        # Get cache statistics
        cache_stats = self.cache_engine.get_stats()
        freshness_stats = self.freshness_tracker.get_stats()

        # Check the results
        self.assertEqual(cache_stats["total_entries"], 0)
        self.assertEqual(freshness_stats["total_entries"], 0)

    def test_cache_and_freshness_with_complex_data(self):
        """Test cache and freshness with complex data."""
        # Set a cache entry with a pandas DataFrame
        cache_key = "test_complex_data_key"
        data = pd.DataFrame({
            "A": [1, 2, 3],
            "B": [4, 5, 6]
        })
        ttl = 60  # 1 minute

        # Set the cache entry and mark it as updated in the freshness tracker
        self.assertTrue(self.cache_engine.set(cache_key, data, ttl=ttl))
        self.freshness_tracker.mark_updated(cache_key, ttl=ttl)

        # Get the cache entry and freshness information
        cached_data = self.cache_engine.get(cache_key)
        freshness_info = self.freshness_tracker.get_freshness_status(cache_key)

        # Check the results
        pd.testing.assert_frame_equal(cached_data, data)
        self.assertEqual(freshness_info["status"], FreshnessStatus.FRESH.value)

    def test_cache_and_freshness_with_update_scheduling(self):
        """Test cache and freshness with update scheduling."""
        # Set a cache entry
        cache_key = "test_update_scheduling_key"
        data = {"test": "data"}
        ttl = 60  # 1 minute

        # Set the cache entry and mark it as updated in the freshness tracker
        self.assertTrue(self.cache_engine.set(cache_key, data, ttl=ttl))
        self.freshness_tracker.mark_updated(cache_key, ttl=ttl)

        # Schedule an update
        priority = 5
        self.freshness_tracker.schedule_update(cache_key, priority=priority)

        # Get the freshness information
        freshness_info = self.freshness_tracker.get_freshness_status(cache_key)

        # Check the results
        self.assertTrue(freshness_info["update_scheduled"])
        self.assertEqual(freshness_info["update_priority"], priority)

        # Cancel the update
        self.freshness_tracker.cancel_update(cache_key)

        # Get the freshness information
        freshness_info = self.freshness_tracker.get_freshness_status(cache_key)

        # Check the results
        self.assertFalse(freshness_info["update_scheduled"])


if __name__ == "__main__":
    unittest.main()
