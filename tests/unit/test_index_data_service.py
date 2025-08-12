# tests/unit/test_index_data_service.py
"""
Unit tests for the IndexDataService class.
"""

import os
import sys
import unittest
from datetime import date, datetime, timedelta
from unittest.mock import MagicMock, patch

import pandas as pd

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from core.models.index_data import (
    IndexData,
    IndexListCache,
    IndexListCacheManager,
    RealtimeIndexData,
)
from core.services.index_data_service import IndexDataService


class TestIndexDataService(unittest.TestCase):
    """Test cases for IndexDataService."""

    def setUp(self):
        """Set up test fixtures."""
        self.db_mock = MagicMock()
        self.akshare_adapter_mock = MagicMock()
        
        # Create service with mocked dependencies
        self.service = IndexDataService(self.db_mock, self.akshare_adapter_mock)

    def test_init(self):
        """Test service initialization."""
        self.assertEqual(self.service.db, self.db_mock)
        self.assertEqual(self.service.akshare_adapter, self.akshare_adapter_mock)

    @patch('core.services.index_data_service.logger')
    def test_get_index_data_cache_hit(self, logger_mock):
        """Test getting index data with cache hit."""
        # Setup cached data with to_dict method
        mock_data = [MagicMock()]
        mock_data[0].to_dict.return_value = {
            'date': date(2023, 12, 31),
            'close': 3000.0,
            'open': 2950.0,
            'high': 3050.0,
            'low': 2900.0
        }

        self.db_mock.query.return_value.filter.return_value.order_by.return_value.all.return_value = mock_data

        # Call method
        result = self.service.get_index_data('000001', '20231201', '20231231')

        # Verify result - should return DataFrame with cached data
        self.assertEqual(len(result), 1)
        self.assertEqual(result.iloc[0]['close'], 3000.0)

    @patch('core.services.index_data_service.logger')
    def test_get_index_data_cache_miss(self, logger_mock):
        """Test getting index data with cache miss."""
        # Setup cache miss
        self.db_mock.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

        # Setup AKShare data
        test_df = pd.DataFrame({
            'date': [datetime(2023, 12, 31)],
            'open': [2950.0],
            'high': [3050.0],
            'low': [2900.0],
            'close': [3000.0],
            'volume': [1000000]
        })
        self.akshare_adapter_mock.get_index_data.return_value = test_df

        # Call method
        result = self.service.get_index_data('000001', '20231201', '20231231')

        # Verify result - should return DataFrame, not dict
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 1)
        self.assertEqual(result.iloc[0]['close'], 3000.0)

        # Verify AKShare was called
        self.akshare_adapter_mock.get_index_data.assert_called_once()

    @patch('core.services.index_data_service.logger')
    def test_get_index_data_force_refresh(self, logger_mock):
        """Test getting index data with force refresh."""
        # Setup AKShare data
        test_df = pd.DataFrame({
            'date': [datetime(2023, 12, 31)],
            'close': [3000.0]
        })
        self.akshare_adapter_mock.get_index_data.return_value = test_df

        # Call method with force refresh
        result = self.service.get_index_data('000001', '20231201', '20231231', force_refresh=True)

        # Verify result - should return DataFrame, not dict
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 1)
        self.assertEqual(result.iloc[0]['close'], 3000.0)

    @patch('core.services.index_data_service.logger')
    def test_get_realtime_index_data_cache_hit(self, logger_mock):
        """Test getting realtime index data with cache hit."""
        # Setup cached data to be returned by _get_cached_realtime_index_data
        cached_data = {
            'symbol': '000001',
            'name': 'Test Index',
            'price': 3000.0,
            'cache_hit': True,
            'timestamp': '2023-12-31T10:00:00'
        }

        # Mock the _get_cached_realtime_index_data method to return cached data
        with patch.object(self.service, '_get_cached_realtime_index_data', return_value=cached_data):
            # Call method
            result = self.service.get_realtime_index_data('000001')

            # Verify result
            self.assertTrue(result['cache_hit'])
            self.assertEqual(result['price'], 3000.0)
            self.assertEqual(result['name'], 'Test Index')

    @patch('core.services.index_data_service.logger')
    def test_get_realtime_index_data_cache_miss(self, logger_mock):
        """Test getting realtime index data with cache miss."""
        # Mock _get_cached_realtime_index_data to return None (cache miss)
        with patch.object(self.service, '_get_cached_realtime_index_data', return_value=None):
            # Setup AKShare data as DataFrame
            test_df = pd.DataFrame({
                'name': ['Test Index'],
                'price': [3000.0],
                'change': [50.0],
                'pct_change': [1.69]
            })
            self.akshare_adapter_mock.get_index_realtime_data.return_value = test_df

            # Mock _is_trading_hours and _save_realtime_index_data_to_cache
            with patch.object(self.service, '_is_trading_hours', return_value=True), \
                 patch.object(self.service, '_save_realtime_index_data_to_cache'):

                # Call method
                result = self.service.get_realtime_index_data('000001')

                # Verify result
                self.assertFalse(result['cache_hit'])
                self.assertEqual(result['price'], 3000.0)
                self.assertEqual(result['name'], 'Test Index')

    @patch('core.services.index_data_service.logger')
    def test_get_index_list_cache_hit(self, logger_mock):
        """Test getting index list with cache hit."""
        # Mock _is_index_list_cache_fresh to return True (cache hit)
        with patch.object(self.service, '_is_index_list_cache_fresh', return_value=True):
            # Mock _get_cached_index_list to return test data
            cached_data = [
                {
                    'symbol': '000001',
                    'name': 'Test Index',
                    'price': 3000.0,
                    'pct_change': 1.5
                }
            ]
            with patch.object(self.service, '_get_cached_index_list', return_value=cached_data):
                # Call method
                result = self.service.get_index_list()

                # Verify result
                self.assertEqual(len(result), 1)
                self.assertEqual(result[0]['symbol'], '000001')

    @patch('core.services.index_data_service.logger')
    def test_get_index_list_cache_miss(self, logger_mock):
        """Test getting index list with cache miss."""
        # Mock _is_index_list_cache_fresh to return False (cache miss)
        with patch.object(self.service, '_is_index_list_cache_fresh', return_value=False):
            # Setup AKShare data
            test_df = pd.DataFrame({
                'symbol': ['000001', '399001'],
                'name': ['Test Index 1', 'Test Index 2'],
                'price': [3000.0, 2000.0],
                'pct_change': [1.5, -0.8]
            })
            self.akshare_adapter_mock.get_index_list.return_value = test_df

            # Mock the cache operations
            with patch.object(self.service, '_clear_old_index_list_cache'), \
                 patch.object(self.service, '_save_index_list_to_cache'):

                # Mock _get_cached_index_list to return the expected data after refresh
                cached_data = [
                    {'symbol': '000001', 'name': 'Test Index 1', 'price': 3000.0, 'pct_change': 1.5},
                    {'symbol': '399001', 'name': 'Test Index 2', 'price': 2000.0, 'pct_change': -0.8}
                ]
                with patch.object(self.service, '_get_cached_index_list', return_value=cached_data):
                    # Call method
                    result = self.service.get_index_list()

                    # Verify result
                    self.assertEqual(len(result), 2)
                    self.assertEqual(result[0]['symbol'], '000001')
                    self.assertEqual(result[1]['symbol'], '399001')

    def test_get_index_list_with_category_filter(self):
        """Test getting index list with category filter."""
        # Setup cached data with categories
        mock_cache_data = [
            MagicMock(symbol='000001', name='Test Index 1', category='Market'),
            MagicMock(symbol='399001', name='Test Index 2', category='Sector')
        ]
        
        self.db_mock.query.return_value.filter.return_value.all.return_value = mock_cache_data
        
        # Call method with category filter
        result = self.service._get_cached_index_list('Market')
        
        # Verify filtering was applied
        self.db_mock.query.return_value.filter.assert_called()

    @patch('core.services.index_data_service.logger')
    def test_get_index_data_akshare_error(self, logger_mock):
        """Test handling AKShare errors in index data."""
        # Setup cache miss
        self.db_mock.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

        # Setup AKShare error
        self.akshare_adapter_mock.get_index_data.side_effect = Exception("AKShare error")

        # Call method and expect exception to be raised
        with self.assertRaises(Exception) as context:
            self.service.get_index_data('000001', '20231201', '20231231')

        # Verify the exception message
        self.assertIn("AKShare error", str(context.exception))

    @patch('core.services.index_data_service.logger')
    def test_get_realtime_index_data_akshare_error(self, logger_mock):
        """Test handling AKShare errors in realtime index data."""
        # Mock _get_cached_realtime_index_data to return None (cache miss)
        with patch.object(self.service, '_get_cached_realtime_index_data', return_value=None):
            # Setup AKShare error - use correct method name
            self.akshare_adapter_mock.get_index_realtime_data.side_effect = Exception("AKShare error")

            # Call method
            result = self.service.get_realtime_index_data('000001')

            # Verify error handling
            self.assertIn('error', result)
            self.assertEqual(result['symbol'], '000001')
            self.assertFalse(result['cache_hit'])

    def test_save_index_data_to_cache(self):
        """Test saving index data to cache."""
        # Setup test data
        test_df = pd.DataFrame({
            'date': [datetime(2023, 12, 31)],
            'open': [2950.0],
            'close': [3000.0],
            'volume': [1000000]
        })

        # Mock database query to return None (no existing record)
        self.db_mock.query.return_value.filter.return_value.first.return_value = None

        # Call internal method
        self.service._save_index_data_to_cache('000001', test_df)

        # Verify database operations
        self.db_mock.add.assert_called()
        self.db_mock.commit.assert_called()

    def test_save_realtime_index_data_to_cache(self):
        """Test saving realtime index data to cache."""
        # Setup test data
        test_data = {
            'name': 'Test Index',
            'price': 3000.0,
            'change': 50.0,
            'pct_change': 1.69
        }

        # Mock database operations
        self.db_mock.query.return_value.filter.return_value.delete.return_value = None

        # Mock _is_trading_hours
        with patch.object(self.service, '_is_trading_hours', return_value=True):
            # Call internal method
            self.service._save_realtime_index_data_to_cache('000001', test_data)

            # Verify database operations
            self.db_mock.add.assert_called()
            self.db_mock.commit.assert_called()

    def test_save_index_list_to_cache(self):
        """Test saving index list to cache."""
        # Setup test data
        test_df = pd.DataFrame({
            'symbol': ['000001', '399001'],
            'name': ['Test Index 1', 'Test Index 2'],
            'price': [3000.0, 2000.0]
        })
        
        # Call internal method
        self.service._save_index_list_to_cache(test_df)
        
        # Verify database operations
        self.db_mock.add.assert_called()
        self.db_mock.commit.assert_called()

    def test_clear_old_index_list_cache(self):
        """Test clearing old index list cache."""
        # Call internal method
        self.service._clear_old_index_list_cache()
        
        # Verify database operations
        self.db_mock.query.assert_called()

    def test_is_trading_hours_during_trading(self):
        """Test trading hours detection during trading hours."""
        # Mock current time to be during trading hours (10:00 AM)
        with patch('core.services.index_data_service.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2023, 12, 25, 10, 0)  # Monday 10:00 AM
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
            
            result = self.service._is_trading_hours()
            
            # Should be True during trading hours on weekday
            self.assertTrue(result)

    def test_is_trading_hours_outside_trading(self):
        """Test trading hours detection outside trading hours."""
        # Mock current time to be outside trading hours (8:00 AM)
        with patch('core.services.index_data_service.datetime') as mock_datetime:
            # Create a proper mock that returns the expected datetime
            mock_now = datetime(2023, 12, 25, 8, 0)  # Monday 8:00 AM
            mock_datetime.now.return_value = mock_now
            # Keep the original datetime constructor for strptime calls
            mock_datetime.strptime = datetime.strptime

            result = self.service._is_trading_hours()

            # Should be False outside trading hours
            self.assertFalse(result)

    def test_is_trading_hours_weekend(self):
        """Test trading hours detection on weekend."""
        # Mock current time to be on weekend
        with patch('core.services.index_data_service.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2023, 12, 24, 10, 0)  # Sunday 10:00 AM
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
            
            result = self.service._is_trading_hours()
            
            # Should be False on weekend
            self.assertFalse(result)

    def test_get_cached_index_list_all_categories(self):
        """Test getting cached index list for all categories."""
        # Setup cached data with to_dict method
        mock_cache_data = [MagicMock(), MagicMock()]
        mock_cache_data[0].to_dict.return_value = {'symbol': '000001', 'name': 'Index 1'}
        mock_cache_data[1].to_dict.return_value = {'symbol': '000002', 'name': 'Index 2'}

        # Setup the complete mock chain for the query
        self.db_mock.query.return_value.filter.return_value.order_by.return_value.all.return_value = mock_cache_data

        # Call method
        result = self.service._get_cached_index_list(None)

        # Verify result
        self.assertEqual(len(result), 2)

    def test_get_cached_index_list_specific_category(self):
        """Test getting cached index list for specific category."""
        # Setup cached data with to_dict method
        mock_cache_data = [MagicMock()]
        mock_cache_data[0].to_dict.return_value = {
            'symbol': '000001',
            'name': 'Test Index',
            'category': 'Market',
            'price': 3000.0
        }

        # Setup the query chain properly
        mock_query = self.db_mock.query.return_value
        mock_query.filter.return_value = mock_query  # Make filter return the same query for chaining
        mock_query.order_by.return_value.all.return_value = mock_cache_data

        # Call method
        result = self.service._get_cached_index_list('Market')

        # Verify filtering was applied
        self.db_mock.query.return_value.filter.assert_called()
        # Verify result
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['name'], 'Test Index')


if __name__ == '__main__':
    unittest.main()
