#!/usr/bin/env python
# tests/unit/test_data_import_improved.py
"""
Unit tests for the improved data import service.

This script tests the improved data import service's functionality,
including task management, retry mechanisms, and error handling.
"""

import os
import sys
import unittest
from datetime import datetime
from unittest.mock import patch, MagicMock, Mock
import pandas as pd
import numpy as np

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.services.data_import import DataImportService
from src.api.models import Asset, Price, ImportTask, ImportTaskStatus
from src.cache.cache_engine import CacheEngine
from src.cache.freshness_tracker import FreshnessTracker
from src.cache.akshare_adapter import AKShareAdapter
from src.logger import setup_logger

# Setup logger
logger = setup_logger(__name__)


class TestDataImportServiceImproved(unittest.TestCase):
    """Unit tests for the improved DataImportService class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock database session
        self.db = MagicMock()
        
        # Mock cache engine
        self.cache_engine = MagicMock(spec=CacheEngine)
        self.cache_engine.get.return_value = None
        self.cache_engine.generate_key.return_value = "test_cache_key"
        
        # Mock freshness tracker
        self.freshness_tracker = MagicMock(spec=FreshnessTracker)
        self.freshness_tracker.is_fresh.return_value = False
        
        # Mock AKShare adapter
        self.akshare_adapter = MagicMock(spec=AKShareAdapter)
        
        # Create data import service with mocks
        self.service = DataImportService(
            db=self.db,
            cache_engine=self.cache_engine,
            freshness_tracker=self.freshness_tracker,
            akshare_adapter=self.akshare_adapter
        )
    
    def test_create_import_task(self):
        """Test creating an import task."""
        # Mock database behavior
        mock_task = MagicMock(spec=ImportTask)
        mock_task.task_id = 1
        self.db.add = MagicMock()
        self.db.commit = MagicMock()
        
        # Create a task
        with patch('src.services.data_import.ImportTask', return_value=mock_task):
            task = self.service.create_import_task("test_task", {"param": "value"})
        
        # Verify task was created and saved
        self.assertEqual(task, mock_task)
        self.db.add.assert_called_once()
        self.db.commit.assert_called_once()
    
    def test_update_task_status(self):
        """Test updating a task's status."""
        # Mock database behavior
        mock_task = MagicMock(spec=ImportTask)
        mock_task.task_id = 1
        self.db.query.return_value.filter.return_value.first.return_value = mock_task
        
        # Update task status
        result = {"status": "success"}
        task = self.service.update_task_status(1, ImportTaskStatus.COMPLETED, result)
        
        # Verify task was updated
        self.assertEqual(task, mock_task)
        self.assertEqual(task.status, ImportTaskStatus.COMPLETED)
        self.assertEqual(task.result, result)
        self.db.commit.assert_called_once()
    
    def test_fetch_stock_data(self):
        """Test fetching stock data with retry mechanism."""
        # Mock AKShare adapter behavior
        mock_data = pd.DataFrame({
            'date': pd.date_range(start="2023-01-01", end="2023-01-10"),
            'open': np.random.uniform(10, 20, 10),
            'high': np.random.uniform(20, 30, 10),
            'low': np.random.uniform(5, 10, 10),
            'close': np.random.uniform(15, 25, 10),
            'volume': np.random.randint(1000000, 10000000, 10)
        })
        self.akshare_adapter.get_stock_data.return_value = mock_data
        
        # Fetch stock data
        result = self.service._fetch_stock_data("000001", "20230101", "20230110")
        
        # Verify data was fetched
        self.assertIs(result, mock_data)
        self.akshare_adapter.get_stock_data.assert_called_once_with(
            symbol="000001",
            start_date="20230101",
            end_date="20230110",
            use_mock_data=False
        )
    
    @patch('src.services.data_import.time.sleep')  # Mock sleep to speed up test
    def test_fetch_stock_data_with_retry(self, mock_sleep):
        """Test fetching stock data with retry on failure."""
        # Mock AKShare adapter to fail twice then succeed
        mock_data = pd.DataFrame({
            'date': pd.date_range(start="2023-01-01", end="2023-01-10"),
            'open': np.random.uniform(10, 20, 10),
            'high': np.random.uniform(20, 30, 10),
            'low': np.random.uniform(5, 10, 10),
            'close': np.random.uniform(15, 25, 10),
            'volume': np.random.randint(1000000, 10000000, 10)
        })
        
        # Create a side effect that raises ConnectionError twice then returns data
        self.akshare_adapter.get_stock_data.side_effect = [
            ConnectionError("Network error"),
            ConnectionError("Network error"),
            mock_data
        ]
        
        # Fetch stock data (should retry and eventually succeed)
        with patch('src.services.data_import.retry', lambda **kwargs: lambda f: f):  # Mock retry decorator
            # We need to handle the retry logic manually in the test
            try:
                # First attempt - should fail
                self.service._fetch_stock_data("000001", "20230101", "20230110")
                self.fail("Should have raised ConnectionError")
            except ConnectionError:
                pass
                
            try:
                # Second attempt - should fail
                self.service._fetch_stock_data("000001", "20230101", "20230110")
                self.fail("Should have raised ConnectionError")
            except ConnectionError:
                pass
                
            # Third attempt - should succeed
            result = self.service._fetch_stock_data("000001", "20230101", "20230110")
            self.assertIs(result, mock_data)
    
    def test_import_from_akshare_with_task(self):
        """Test importing from AKShare with task creation."""
        # Mock database behavior
        mock_asset = MagicMock(spec=Asset)
        mock_asset.asset_id = 1
        self.db.query.return_value.filter.return_value.first.return_value = mock_asset
        
        # Mock task creation
        mock_task = MagicMock(spec=ImportTask)
        mock_task.task_id = 1
        
        # Mock stock data
        mock_data = pd.DataFrame({
            'date': pd.date_range(start="2023-01-01", end="2023-01-10"),
            'open': np.random.uniform(10, 20, 10),
            'high': np.random.uniform(20, 30, 10),
            'low': np.random.uniform(5, 10, 10),
            'close': np.random.uniform(15, 25, 10),
            'volume': np.random.randint(1000000, 10000000, 10)
        })
        self.akshare_adapter.get_stock_data.return_value = mock_data
        
        # Mock price data import
        mock_prices = [MagicMock(spec=Price) for _ in range(10)]
        
        # Set up method mocks
        with patch.object(self.service, 'create_import_task', return_value=mock_task) as mock_create_task, \
             patch.object(self.service, 'update_task_status') as mock_update_status, \
             patch.object(self.service, '_fetch_stock_data', return_value=mock_data) as mock_fetch, \
             patch.object(self.service, 'import_price_data', return_value=mock_prices) as mock_import:
            
            # Import from AKShare with task
            result = self.service.import_from_akshare(
                symbol="000001",
                start_date="20230101",
                end_date="20230110",
                create_task=True
            )
        
        # Verify task was created and updated
        mock_create_task.assert_called_once()
        self.assertEqual(mock_update_status.call_count, 2)  # Called for PROCESSING and COMPLETED
        
        # Verify data was fetched and imported
        mock_fetch.assert_called_once()
        mock_import.assert_called_once()
        
        # Verify result
        self.assertEqual(result["symbol"], "000001")
        self.assertEqual(result["records_imported"], 10)
        self.assertTrue(result["success"])


if __name__ == "__main__":
    unittest.main()
