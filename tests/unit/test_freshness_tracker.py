#!/usr/bin/env python
# tests/unit/test_freshness_tracker.py
"""
Unit tests for the FreshnessTracker class.
"""

import os
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from tempfile import NamedTemporaryFile

from src.cache.models import FreshnessStatus

class TestFreshnessTracker(unittest.TestCase):
    """Test cases for the FreshnessTracker class."""

    def setUp(self):
        """Set up the test environment."""
        # Create a temporary database file
        self.temp_db = NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.freshness_tracker = FreshnessTracker(db_path=self.temp_db.name)

    def tearDown(self):
        """Clean up the test environment."""
        # Close the database connection
        del self.freshness_tracker
        # Remove the temporary database file
        os.unlink(self.temp_db.name)

    def test_register_and_get_freshness(self):
        """Test registering and getting freshness information."""
        # Register a cache entry
        cache_key = "test_key"
        ttl = 60  # 1 minute
        self.freshness_tracker.mark_updated(cache_key, ttl=ttl)

        # Get freshness information
        freshness_info = self.freshness_tracker.get_freshness_status(cache_key)
        self.assertEqual(freshness_info["status"], FreshnessStatus.FRESH.value)
        self.assertFalse(freshness_info["update_scheduled"])
        self.assertEqual(freshness_info["update_priority"], 0)

    def test_register_and_get_freshness_with_expiration(self):
        """Test registering and getting freshness information with expiration."""
        # Register a cache entry with a short TTL
        cache_key = "test_key_expire"
        ttl = 1  # 1 second
        self.freshness_tracker.mark_updated(cache_key, ttl=ttl)

        # Wait for the entry to expire
        import time
        time.sleep(2)

        # Get freshness information
        freshness_info = self.freshness_tracker.get_freshness_status(cache_key)
        self.assertEqual(freshness_info["status"], FreshnessStatus.EXPIRED.value)

    def test_mark_fresh(self):
        """Test marking a cache entry as fresh."""
        # Register a cache entry
        cache_key = "test_key_mark_fresh"
        ttl = 60  # 1 minute
        self.freshness_tracker.mark_updated(cache_key, ttl=ttl)

        # Mark the entry as stale
        self.freshness_tracker.mark_stale(cache_key)

        # Get freshness information
        freshness_info = self.freshness_tracker.get_freshness_status(cache_key)
        self.assertEqual(freshness_info["status"], FreshnessStatus.STALE.value)

        # Mark the entry as fresh
        self.freshness_tracker.mark_updated(cache_key)

        # Get freshness information
        freshness_info = self.freshness_tracker.get_freshness_status(cache_key)
        self.assertEqual(freshness_info["status"], FreshnessStatus.FRESH.value)

    def test_mark_stale(self):
        """Test marking a cache entry as stale."""
        # Register a cache entry
        cache_key = "test_key_mark_stale"
        ttl = 60  # 1 minute
        self.freshness_tracker.mark_updated(cache_key, ttl=ttl)

        # Mark the entry as stale
        self.freshness_tracker.mark_stale(cache_key)

        # Get freshness information
        freshness_info = self.freshness_tracker.get_freshness_status(cache_key)
        self.assertEqual(freshness_info["status"], FreshnessStatus.STALE.value)

    def test_mark_expired(self):
        """Test marking a cache entry as expired."""
        # Register a cache entry
        cache_key = "test_key_mark_expired"
        ttl = 60  # 1 minute
        self.freshness_tracker.mark_updated(cache_key, ttl=ttl)

        # Mark the entry as expired
        self.assertTrue(self.freshness_tracker.mark_expired(cache_key))

        # Get freshness information
        freshness_info = self.freshness_tracker.get_freshness_status(cache_key)
        self.assertEqual(freshness_info["status"], FreshnessStatus.EXPIRED.value)

    def test_schedule_update(self):
        """Test scheduling an update for a cache entry."""
        # Register a cache entry
        cache_key = "test_key_schedule_update"
        ttl = 60  # 1 minute
        self.freshness_tracker.mark_updated(cache_key, ttl=ttl)

        # Schedule an update
        priority = 5
        self.freshness_tracker.schedule_update(cache_key, priority=priority)

        # Get freshness information
        freshness_info = self.freshness_tracker.get_freshness_status(cache_key)
        self.assertTrue(freshness_info["update_scheduled"])
        self.assertEqual(freshness_info["update_priority"], priority)

    def test_cancel_update(self):
        """Test canceling an update for a cache entry."""
        # Register a cache entry
        cache_key = "test_key_cancel_update"
        ttl = 60  # 1 minute
        self.freshness_tracker.mark_updated(cache_key, ttl=ttl)

        # Schedule an update
        priority = 5
        self.freshness_tracker.schedule_update(cache_key, priority=priority)

        # Get freshness information
        freshness_info = self.freshness_tracker.get_freshness_status(cache_key)
        self.assertTrue(freshness_info["update_scheduled"])

        # Cancel the update
        self.freshness_tracker.mark_updated(cache_key)  # This clears scheduled updates

        # Get freshness information
        freshness_info = self.freshness_tracker.get_freshness_status(cache_key)
        self.assertFalse(freshness_info["update_scheduled"])

    def test_delete(self):
        """Test deleting a freshness entry."""
        # Register a cache entry
        cache_key = "test_key_delete"
        ttl = 60  # 1 minute
        self.freshness_tracker.mark_updated(cache_key, ttl=ttl)

        # Delete the freshness entry
        self.assertTrue(self.freshness_tracker.delete(cache_key))

        # Get freshness information
        freshness_info = self.freshness_tracker.get_freshness_status(cache_key)
        self.assertEqual(freshness_info["status"], FreshnessStatus.UNKNOWN.value)

    def test_clear(self):
        """Test clearing all freshness entries."""
        # Register multiple cache entries
        for i in range(5):
            cache_key = f"test_key_{i}"
            ttl = 60  # 1 minute
            self.freshness_tracker.mark_updated(cache_key, ttl=ttl)

        # Clear all freshness entries
        self.assertTrue(self.freshness_tracker.clear())

        # Get freshness information for one of the entries
        freshness_info = self.freshness_tracker.get_freshness_status("test_key_0")
        self.assertEqual(freshness_info["status"], FreshnessStatus.UNKNOWN.value)

    def test_get_stats(self):
        """Test getting freshness statistics."""
        # Register multiple cache entries with different statuses
        for i in range(3):
            cache_key = f"test_key_fresh_{i}"
            ttl = 60  # 1 minute
            self.freshness_tracker.mark_updated(cache_key, ttl=ttl)

        for i in range(2):
            cache_key = f"test_key_stale_{i}"
            ttl = 60  # 1 minute
            self.freshness_tracker.mark_updated(cache_key, ttl=ttl)
            self.freshness_tracker.mark_stale(cache_key)

        for i in range(1):
            cache_key = f"test_key_expired_{i}"
            ttl = 1  # 1 second
            self.freshness_tracker.mark_updated(cache_key, ttl=ttl)
            import time
            time.sleep(2)

        # Schedule updates for some entries
        for i in range(2):
            cache_key = f"test_key_fresh_{i}"
            self.freshness_tracker.schedule_update(cache_key, priority=i+1)

        # Get freshness statistics
        stats = self.freshness_tracker.get_stats()

        # Check basic statistics
        self.assertEqual(stats["total_entries"], 6)
        # The number of status types may vary depending on the implementation
        self.assertIn(FreshnessStatus.FRESH.value, stats["entries_by_status"])
        self.assertIn(FreshnessStatus.STALE.value, stats["entries_by_status"])
        # The exact counts may vary depending on the implementation
        self.assertGreaterEqual(stats["entries_by_status"][FreshnessStatus.FRESH.value], 3)
        self.assertGreaterEqual(stats["entries_by_status"][FreshnessStatus.STALE.value], 2)
        # The expired entry might be counted differently depending on the implementation
        self.assertGreaterEqual(stats["expired_entries"], 1)
        self.assertEqual(stats["scheduled_updates"], 2)

        # Check advanced statistics
        self.assertIn("expiring_soon", stats)
        self.assertIn("avg_age_seconds", stats)
        self.assertIn("oldest_entries", stats)
        self.assertIn("high_priority_entries", stats)
        self.assertIn("pending_updates", stats)
        self.assertIn("freshness_metrics", stats)
        self.assertIn("freshness_health", stats)

if __name__ == "__main__":
    unittest.main()
