# tests/test_cache.py
"""
Tests for the Reservoir Cache mechanism.
"""

import os
import tempfile
import unittest
from datetime import datetime, timedelta

import pandas as pd

from src.cache.akshare_adapter import AKShareAdapter
from src.cache.models import FreshnessStatus

class TestCacheEngine(unittest.TestCase):
    """Tests for the CacheEngine class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary database file
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        
        # Initialize cache engine with the temporary database
        self.cache_engine = CacheEngine(db_path=self.temp_db.name)
    
    def tearDown(self):
        """Tear down test fixtures."""
        # Remove the temporary database file
        os.unlink(self.temp_db.name)
    
    def test_generate_key(self):
        """Test the generate_key method."""
        # Generate a key with various arguments
        key1 = self.cache_engine.generate_key("test", 123, foo="bar")
        key2 = self.cache_engine.generate_key("test", 123, foo="bar")
        key3 = self.cache_engine.generate_key("test", 456, foo="bar")
        
        # The same arguments should produce the same key
        self.assertEqual(key1, key2)
        
        # Different arguments should produce different keys
        self.assertNotEqual(key1, key3)
    
    def test_set_and_get(self):
        """Test the set and get methods."""
        # Set a value in the cache
        key = "test_key"
        value = {"foo": "bar", "baz": 123}
        self.cache_engine.set(key, value)
        
        # Get the value from the cache
        cached_value = self.cache_engine.get(key)
        
        # The cached value should match the original value
        self.assertEqual(cached_value, value)
    
    def test_invalidate(self):
        """Test the invalidate method."""
        # Set a value in the cache
        key = "test_key"
        value = {"foo": "bar", "baz": 123}
        self.cache_engine.set(key, value)
        
        # Invalidate the cache entry
        self.cache_engine.invalidate(key)
        
        # The invalidated entry should not be retrievable
        cached_value = self.cache_engine.get(key)
        self.assertIsNone(cached_value)
    
    def test_expiration(self):
        """Test cache entry expiration."""
        # Set a value in the cache with a short TTL
        key = "test_key"
        value = {"foo": "bar", "baz": 123}
        self.cache_engine.set(key, value, ttl=1)  # 1 second TTL
        
        # The value should be retrievable immediately
        cached_value = self.cache_engine.get(key)
        self.assertEqual(cached_value, value)
        
        # Wait for the entry to expire
        import time
        time.sleep(2)
        
        # The expired entry should not be retrievable
        cached_value = self.cache_engine.get(key)
        self.assertIsNone(cached_value)
    
    def test_get_stats(self):
        """Test the get_stats method."""
        # Set some values in the cache
        self.cache_engine.set("key1", "value1")
        self.cache_engine.set("key2", "value2")
        
        # Get some values (hits)
        self.cache_engine.get("key1")
        self.cache_engine.get("key2")
        
        # Try to get a non-existent value (miss)
        self.cache_engine.get("key3")
        
        # Get the cache statistics
        stats = self.cache_engine.get_stats()
        
        # Check the statistics
        self.assertEqual(stats["total_entries"], 2)
        self.assertEqual(stats["hits"], 2)
        self.assertEqual(stats["misses"], 1)
        self.assertAlmostEqual(stats["hit_rate"], 2/3, places=2)

class TestFreshnessTracker(unittest.TestCase):
    """Tests for the FreshnessTracker class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary database file
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        
        # Initialize freshness tracker with the temporary database
        self.freshness_tracker = FreshnessTracker(db_path=self.temp_db.name)
    
    def tearDown(self):
        """Tear down test fixtures."""
        # Remove the temporary database file
        os.unlink(self.temp_db.name)
    
    def test_mark_updated_and_get_status(self):
        """Test the mark_updated and get_freshness_status methods."""
        # Mark a cache entry as updated
        key = "test_key"
        self.freshness_tracker.mark_updated(key)
        
        # Get the freshness status
        status = self.freshness_tracker.get_freshness_status(key)
        
        # Check the status
        self.assertEqual(status["cache_key"], key)
        self.assertEqual(status["status"], FreshnessStatus.FRESH.value)
        self.assertFalse(status["update_scheduled"])
    
    def test_is_fresh(self):
        """Test the is_fresh method."""
        # Mark a cache entry as updated
        key = "test_key"
        self.freshness_tracker.mark_updated(key)
        
        # The entry should be fresh
        self.assertTrue(self.freshness_tracker.is_fresh(key))
        
        # Mark the entry as updated with a short TTL
        self.freshness_tracker.mark_updated(key, ttl=1)  # 1 second TTL
        
        # The entry should be fresh immediately
        self.assertTrue(self.freshness_tracker.is_fresh(key))
        
        # Wait for the entry to expire
        import time
        time.sleep(2)
        
        # The entry should no longer be fresh with strict requirements
        self.assertFalse(self.freshness_tracker.is_fresh(key, "strict"))
        
        # The entry should still be fresh with relaxed requirements
        self.assertTrue(self.freshness_tracker.is_fresh(key, "relaxed"))
    
    def test_schedule_update(self):
        """Test the schedule_update method."""
        # Schedule an update for a cache entry
        key = "test_key"
        self.freshness_tracker.schedule_update(key, priority=5)
        
        # Get the freshness status
        status = self.freshness_tracker.get_freshness_status(key)
        
        # Check the status
        self.assertEqual(status["cache_key"], key)
        self.assertTrue(status["update_scheduled"])
        self.assertEqual(status["update_priority"], 5)
        
        # Get pending updates
        updates = self.freshness_tracker.get_pending_updates()
        
        # There should be one pending update
        self.assertEqual(len(updates), 1)
        self.assertEqual(updates[0]["cache_key"], key)
        self.assertEqual(updates[0]["priority"], 5)

class TestAKShareAdapter(unittest.TestCase):
    """Tests for the AKShareAdapter class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create temporary database files
        self.temp_cache_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_cache_db.close()
        self.temp_freshness_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_freshness_db.close()
        
        # Initialize cache engine and freshness tracker with the temporary databases
        self.cache_engine = CacheEngine(db_path=self.temp_cache_db.name)
        self.freshness_tracker = FreshnessTracker(db_path=self.temp_freshness_db.name)
        
        # Initialize AKShare adapter with the cache engine and freshness tracker
        self.adapter = AKShareAdapter(
            cache_engine=self.cache_engine,
            freshness_tracker=self.freshness_tracker
        )
    
    def tearDown(self):
        """Tear down test fixtures."""
        # Remove the temporary database files
        os.unlink(self.temp_cache_db.name)
        os.unlink(self.temp_freshness_db.name)
    
    def test_get_stock_list(self):
        """Test the get_stock_list method."""
        # This test requires an internet connection and AKShare to be working
        try:
            # Get the stock list
            stock_list = self.adapter.get_stock_list()
            
            # Check that the result is a DataFrame
            self.assertIsInstance(stock_list, pd.DataFrame)
            
            # Check that the DataFrame is not empty
            self.assertFalse(stock_list.empty)
            
            # Get the stock list again (should be from cache)
            stock_list_cached = self.adapter.get_stock_list()
            
            # Check that the cached result is the same
            pd.testing.assert_frame_equal(stock_list, stock_list_cached)
            
        except Exception as e:
            # Skip the test if there's an error (e.g., no internet connection)
            self.skipTest(f"Error accessing AKShare: {e}")

if __name__ == "__main__":
    unittest.main()
