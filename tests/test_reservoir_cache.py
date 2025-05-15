#!/usr/bin/env python
# tests/test_reservoir_cache.py
"""
Tests for the Reservoir Cache mechanism.

This module contains tests for the cache engine, freshness tracker,
and AKShare adapter components of the Reservoir Cache mechanism.
"""

import os
import sys
import unittest
import tempfile
from datetime import datetime, timedelta

import pandas as pd
import numpy as np

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.cache.cache_engine import CacheEngine
from src.cache.freshness_tracker import FreshnessTracker
from src.cache.akshare_adapter import AKShareAdapter
from src.cache.models import FreshnessStatus


class TestCacheEngine(unittest.TestCase):
    """Tests for the CacheEngine class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary database file
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_db.close()
        
        # Create a cache engine with the temporary database
        self.cache_engine = CacheEngine(db_path=self.temp_db.name)
    
    def tearDown(self):
        """Tear down test fixtures."""
        # Remove the temporary database file
        os.unlink(self.temp_db.name)
    
    def test_generate_key(self):
        """Test key generation."""
        # Generate a key with various types of arguments
        key1 = self.cache_engine.generate_key("test", 123, True)
        key2 = self.cache_engine.generate_key("test", 123, True)
        key3 = self.cache_engine.generate_key("test", 456, True)
        
        # Keys should be deterministic
        self.assertEqual(key1, key2)
        
        # Different arguments should produce different keys
        self.assertNotEqual(key1, key3)
    
    def test_set_and_get(self):
        """Test setting and getting cache entries."""
        # Generate a key
        key = self.cache_engine.generate_key("test_set_and_get")
        
        # Set a value
        data = {"value": 42, "name": "test"}
        self.cache_engine.set(key, data)
        
        # Get the value
        cached_data = self.cache_engine.get(key)
        
        # Check that the value is correct
        self.assertEqual(cached_data, data)
    
    def test_expiration(self):
        """Test cache entry expiration."""
        # Generate a key
        key = self.cache_engine.generate_key("test_expiration")
        
        # Set a value with a short TTL
        data = {"value": 42, "name": "test"}
        self.cache_engine.set(key, data, ttl=1)  # 1 second TTL
        
        # Get the value immediately (should be available)
        cached_data = self.cache_engine.get(key)
        self.assertEqual(cached_data, data)
        
        # Wait for the TTL to expire
        import time
        time.sleep(2)
        
        # Get the value again (should be None)
        cached_data = self.cache_engine.get(key)
        self.assertIsNone(cached_data)
    
    def test_invalidate(self):
        """Test invalidating cache entries."""
        # Generate a key
        key = self.cache_engine.generate_key("test_invalidate")
        
        # Set a value
        data = {"value": 42, "name": "test"}
        self.cache_engine.set(key, data)
        
        # Invalidate the entry
        self.cache_engine.invalidate(key)
        
        # Get the value (should be None)
        cached_data = self.cache_engine.get(key)
        self.assertIsNone(cached_data)
    
    def test_delete(self):
        """Test deleting cache entries."""
        # Generate a key
        key = self.cache_engine.generate_key("test_delete")
        
        # Set a value
        data = {"value": 42, "name": "test"}
        self.cache_engine.set(key, data)
        
        # Delete the entry
        self.cache_engine.delete(key)
        
        # Get the value (should be None)
        cached_data = self.cache_engine.get(key)
        self.assertIsNone(cached_data)
    
    def test_clear(self):
        """Test clearing all cache entries."""
        # Generate keys and set values
        key1 = self.cache_engine.generate_key("test_clear", 1)
        key2 = self.cache_engine.generate_key("test_clear", 2)
        
        self.cache_engine.set(key1, "value1")
        self.cache_engine.set(key2, "value2")
        
        # Clear the cache
        self.cache_engine.clear()
        
        # Get the values (should be None)
        self.assertIsNone(self.cache_engine.get(key1))
        self.assertIsNone(self.cache_engine.get(key2))
    
    def test_get_stats(self):
        """Test getting cache statistics."""
        # Generate keys and set values
        key1 = self.cache_engine.generate_key("test_stats", 1)
        key2 = self.cache_engine.generate_key("test_stats", 2)
        
        self.cache_engine.set(key1, "value1")
        self.cache_engine.set(key2, "value2")
        
        # Get the values to increment hit count
        self.cache_engine.get(key1)
        self.cache_engine.get(key1)  # Second hit
        
        # Get non-existent key to increment miss count
        self.cache_engine.get("nonexistent_key")
        
        # Get statistics
        stats = self.cache_engine.get_stats()
        
        # Check statistics
        self.assertEqual(stats["total_entries"], 2)
        self.assertEqual(stats["hits"], 2)
        self.assertEqual(stats["misses"], 1)
        self.assertAlmostEqual(stats["hit_rate"], 2/3, places=2)


class TestFreshnessTracker(unittest.TestCase):
    """Tests for the FreshnessTracker class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary database file
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_db.close()
        
        # Create a freshness tracker with the temporary database
        self.freshness_tracker = FreshnessTracker(db_path=self.temp_db.name)
    
    def tearDown(self):
        """Tear down test fixtures."""
        # Remove the temporary database file
        os.unlink(self.temp_db.name)
    
    def test_mark_updated(self):
        """Test marking a cache entry as updated."""
        # Generate a key
        key = "test_mark_updated"
        
        # Mark as updated
        self.freshness_tracker.mark_updated(key)
        
        # Get freshness status
        status = self.freshness_tracker.get_freshness_status(key)
        
        # Check status
        self.assertEqual(status["status"], FreshnessStatus.FRESH.value)
    
    def test_is_fresh(self):
        """Test checking if a cache entry is fresh."""
        # Generate a key
        key = "test_is_fresh"
        
        # Mark as updated with a short TTL
        self.freshness_tracker.mark_updated(key, ttl=1)  # 1 second TTL
        
        # Check if fresh immediately (should be True)
        self.assertTrue(self.freshness_tracker.is_fresh(key))
        
        # Wait for the TTL to expire
        import time
        time.sleep(2)
        
        # Check if fresh with strict requirement (should be False)
        self.assertFalse(self.freshness_tracker.is_fresh(key, freshness_requirement="strict"))
        
        # Check if fresh with relaxed requirement (should be True)
        self.assertTrue(self.freshness_tracker.is_fresh(key, freshness_requirement="relaxed"))
    
    def test_mark_expired(self):
        """Test marking a cache entry as expired."""
        # Generate a key
        key = "test_mark_expired"
        
        # Mark as updated
        self.freshness_tracker.mark_updated(key)
        
        # Mark as expired
        self.freshness_tracker.mark_expired(key)
        
        # Check if fresh with strict requirement (should be False)
        self.assertFalse(self.freshness_tracker.is_fresh(key, freshness_requirement="strict"))
        
        # Check if fresh with relaxed requirement (should be False)
        self.assertFalse(self.freshness_tracker.is_fresh(key, freshness_requirement="relaxed"))


if __name__ == "__main__":
    unittest.main()
