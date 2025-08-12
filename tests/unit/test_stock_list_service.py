# tests/unit/test_stock_list_service.py
"""
Unit tests for the StockListService class.
"""

import os
import sys
import unittest
from datetime import date, timedelta
from unittest.mock import MagicMock, patch

import pandas as pd

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from core.models.stock_list import StockListCache, StockListCacheManager
from core.services.stock_list_service import StockListService


class TestStockListService(unittest.TestCase):
    """Test cases for StockListService."""

    def setUp(self):
        """Set up test fixtures."""
        self.db_mock = MagicMock()
        self.akshare_adapter_mock = MagicMock()
        
        # Create service with mocked dependencies
        self.service = StockListService(self.db_mock, self.akshare_adapter_mock)

    def test_init(self):
        """Test service initialization."""
        self.assertEqual(self.service.db, self.db_mock)
        self.assertEqual(self.service.akshare_adapter, self.akshare_adapter_mock)
        self.assertIsNotNone(self.service.cache_manager)

    @patch('core.services.stock_list_service.logger')
    def test_get_stock_list_cache_hit(self, logger_mock):
        """Test getting stock list with cache hit."""
        # Setup cache manager to return fresh cache
        with patch.object(self.service.cache_manager, 'is_cache_fresh', return_value=True):
            # Setup cached data
            mock_cache_data = [
                MagicMock(symbol='000001', name='平安银行', market='SZSE'),
                MagicMock(symbol='600000', name='浦发银行', market='SHSE')
            ]
            # Mock the to_dict method for each cache object
            for mock_obj in mock_cache_data:
                mock_obj.to_dict.return_value = {
                    'symbol': mock_obj.symbol,
                    'name': mock_obj.name,
                    'market': mock_obj.market
                }

            self.db_mock.query.return_value.filter.return_value.order_by.return_value.all.return_value = mock_cache_data

            # Call method
            result = self.service.get_stock_list()

            # Verify result
            self.assertEqual(len(result), 2)
            logger_mock.info.assert_any_call("Using cached stock list data")

    @patch('core.services.stock_list_service.logger')
    def test_get_stock_list_cache_miss(self, logger_mock):
        """Test getting stock list with cache miss."""
        # Setup cache manager to return stale cache
        with patch.object(self.service.cache_manager, 'is_cache_fresh', return_value=False), \
             patch.object(self.service.cache_manager, 'clear_old_cache'):

            # Setup AKShare data
            test_df = pd.DataFrame({
                'symbol': ['000001', '600000', '600519'],
                'name': ['平安银行', '浦发银行', '贵州茅台'],
                'market': ['SZSE', 'SHSE', 'SHSE']
            })
            self.akshare_adapter_mock.get_stock_list.return_value = test_df

            # Setup cached data return
            mock_cache_data = [
                MagicMock(symbol='000001', name='平安银行', market='SZSE'),
                MagicMock(symbol='600000', name='浦发银行', market='SHSE'),
                MagicMock(symbol='600519', name='贵州茅台', market='SHSE')
            ]
            for mock_obj in mock_cache_data:
                mock_obj.to_dict.return_value = {
                    'symbol': mock_obj.symbol,
                    'name': mock_obj.name,
                    'market': mock_obj.market
                }
            self.db_mock.query.return_value.filter.return_value.order_by.return_value.all.return_value = mock_cache_data

            # Call method
            result = self.service.get_stock_list()

            # Verify result
            self.assertEqual(len(result), 3)
            logger_mock.info.assert_any_call("Cache is stale or force refresh requested, fetching from AKShare")

            # Verify AKShare was called
            self.akshare_adapter_mock.get_stock_list.assert_called_once()

    @patch('core.services.stock_list_service.logger')
    def test_get_stock_list_force_refresh(self, logger_mock):
        """Test getting stock list with force refresh."""
        # Setup AKShare data
        test_df = pd.DataFrame({
            'symbol': ['000001', '600000'],
            'name': ['平安银行', '浦发银行'],
            'market': ['SZSE', 'SHSE']
        })
        self.akshare_adapter_mock.get_stock_list.return_value = test_df
        
        # Call method with force refresh
        result = self.service.get_stock_list(force_refresh=True)
        
        # Verify result
        self.assertEqual(len(result), 2)
        logger_mock.info.assert_any_call("Cache is stale or force refresh requested, fetching from AKShare")

    def test_get_stock_list_with_market_filter(self):
        """Test getting stock list with market filter."""
        # Setup cached data
        mock_cache_data = [
            MagicMock(symbol='000001', name='平安银行', market='SZSE'),
            MagicMock(symbol='600000', name='浦发银行', market='SHSE')
        ]
        self.db_mock.query.return_value.filter.return_value.all.return_value = mock_cache_data
        
        # Call method with market filter
        result = self.service._get_cached_stock_list('SHSE')
        
        # Verify filtering was applied
        self.db_mock.query.return_value.filter.assert_called()

    @patch('core.services.stock_list_service.logger')
    def test_get_stock_list_akshare_empty(self, logger_mock):
        """Test getting stock list when AKShare returns empty data."""
        # Setup cache miss
        self.service.cache_manager.is_cache_fresh.return_value = False
        
        # Setup empty AKShare data
        self.akshare_adapter_mock.get_stock_list.return_value = pd.DataFrame()
        
        # Setup fallback cached data
        mock_cache_data = [MagicMock(symbol='000001', name='平安银行')]
        self.db_mock.query.return_value.filter.return_value.all.return_value = mock_cache_data
        
        # Call method
        result = self.service.get_stock_list()
        
        # Verify fallback to cached data
        self.assertEqual(len(result), 1)
        logger_mock.warning.assert_any_call("No stock list data available from AKShare")

    @patch('core.services.stock_list_service.logger')
    def test_get_stock_list_akshare_error(self, logger_mock):
        """Test handling AKShare errors in stock list."""
        # Setup cache miss
        self.service.cache_manager.is_cache_fresh.return_value = False
        
        # Setup AKShare error
        self.akshare_adapter_mock.get_stock_list.side_effect = Exception("AKShare error")
        
        # Setup fallback cached data
        mock_cache_data = [MagicMock(symbol='000001', name='平安银行')]
        self.db_mock.query.return_value.filter.return_value.all.return_value = mock_cache_data
        
        # Call method
        result = self.service.get_stock_list()
        
        # Verify fallback to cached data
        self.assertEqual(len(result), 1)
        logger_mock.error.assert_called()

    def test_save_stock_list_to_cache(self):
        """Test saving stock list to cache."""
        # Setup test data
        test_df = pd.DataFrame({
            'symbol': ['000001', '600000'],
            'name': ['平安银行', '浦发银行'],
            'market': ['SZSE', 'SHSE']
        })
        
        # Call internal method
        self.service._save_stock_list_to_cache(test_df)
        
        # Verify database operations
        self.db_mock.add.assert_called()
        self.db_mock.commit.assert_called()

    def test_clear_old_stock_list_cache(self):
        """Test clearing old stock list cache."""
        # Call internal method
        self.service._clear_old_stock_list_cache()
        
        # Verify database operations
        self.db_mock.query.assert_called()

    def test_get_cached_stock_list_all_markets(self):
        """Test getting cached stock list for all markets."""
        # Setup cached data
        mock_cache_data = [
            MagicMock(symbol='000001', name='平安银行', market='SZSE'),
            MagicMock(symbol='600000', name='浦发银行', market='SHSE')
        ]
        self.db_mock.query.return_value.filter.return_value.all.return_value = mock_cache_data
        
        # Call method
        result = self.service._get_cached_stock_list(None)
        
        # Verify result
        self.assertEqual(len(result), 2)

    def test_get_cached_stock_list_specific_market(self):
        """Test getting cached stock list for specific market."""
        # Setup cached data for specific market
        mock_cache_data = [MagicMock(symbol='000001', name='平安银行', market='SZSE')]
        self.db_mock.query.return_value.filter.return_value.all.return_value = mock_cache_data
        
        # Call method
        result = self.service._get_cached_stock_list('SZSE')
        
        # Verify filtering was applied
        self.db_mock.query.return_value.filter.assert_called()
        self.assertEqual(len(result), 1)

    def test_convert_cache_to_dict_list(self):
        """Test converting cache objects to dictionary list."""
        # Setup mock cache objects
        mock_cache_data = [
            MagicMock(symbol='000001', name='平安银行', market='SZSE', price=10.5),
            MagicMock(symbol='600000', name='浦发银行', market='SHSE', price=12.3)
        ]
        
        # Call internal method
        result = self.service._convert_cache_to_dict_list(mock_cache_data)
        
        # Verify result structure
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['symbol'], '000001')
        self.assertEqual(result[1]['symbol'], '600000')

    def test_get_stock_count_by_market(self):
        """Test getting stock count by market."""
        # Setup mock query results
        self.db_mock.query.return_value.filter.return_value.count.return_value = 5
        
        # Call method
        result = self.service.get_stock_count_by_market('SHSE')
        
        # Verify result
        self.assertEqual(result, 5)
        self.db_mock.query.assert_called()

    def test_get_total_stock_count(self):
        """Test getting total stock count."""
        # Setup mock query results
        self.db_mock.query.return_value.filter.return_value.count.return_value = 10
        
        # Call method
        result = self.service.get_total_stock_count()
        
        # Verify result
        self.assertEqual(result, 10)

    def test_get_market_summary(self):
        """Test getting market summary."""
        # Setup mock query results for different markets
        def mock_count_side_effect(*args, **kwargs):
            # Return different counts based on filter
            return 5  # Simplified for testing
        
        self.db_mock.query.return_value.filter.return_value.count.side_effect = mock_count_side_effect
        
        # Call method
        result = self.service.get_market_summary()
        
        # Verify result structure
        self.assertIsInstance(result, dict)
        self.assertIn('total', result)

    def test_search_stocks_by_name(self):
        """Test searching stocks by name."""
        # Setup mock search results
        mock_results = [
            MagicMock(symbol='000001', name='平安银行', market='SZSE'),
            MagicMock(symbol='000002', name='万科A', market='SZSE')
        ]
        self.db_mock.query.return_value.filter.return_value.all.return_value = mock_results
        
        # Call method
        result = self.service.search_stocks_by_name('平安')
        
        # Verify result
        self.assertEqual(len(result), 2)
        self.db_mock.query.return_value.filter.assert_called()

    def test_search_stocks_by_symbol(self):
        """Test searching stocks by symbol."""
        # Setup mock search results
        mock_results = [MagicMock(symbol='000001', name='平安银行', market='SZSE')]
        self.db_mock.query.return_value.filter.return_value.all.return_value = mock_results
        
        # Call method
        result = self.service.search_stocks_by_symbol('0000')
        
        # Verify result
        self.assertEqual(len(result), 1)
        self.db_mock.query.return_value.filter.assert_called()

    def test_get_stocks_by_market_with_pagination(self):
        """Test getting stocks by market with pagination."""
        # Setup mock paginated results
        mock_results = [
            MagicMock(symbol='000001', name='平安银行', market='SZSE'),
            MagicMock(symbol='000002', name='万科A', market='SZSE')
        ]
        self.db_mock.query.return_value.filter.return_value.offset.return_value.limit.return_value.all.return_value = mock_results
        
        # Call method
        result = self.service.get_stocks_by_market('SZSE', skip=0, limit=10)
        
        # Verify result
        self.assertEqual(len(result), 2)
        self.db_mock.query.return_value.filter.return_value.offset.assert_called_with(0)
        self.db_mock.query.return_value.filter.return_value.offset.return_value.limit.assert_called_with(10)

    def test_is_stock_exists(self):
        """Test checking if stock exists."""
        # Setup mock query result
        mock_stock = MagicMock()
        self.db_mock.query.return_value.filter.return_value.first.return_value = mock_stock
        
        # Call method
        result = self.service.is_stock_exists('000001')
        
        # Verify result
        self.assertTrue(result)
        self.db_mock.query.return_value.filter.assert_called()

    def test_is_stock_not_exists(self):
        """Test checking if stock does not exist."""
        # Setup mock query result
        self.db_mock.query.return_value.filter.return_value.first.return_value = None
        
        # Call method
        result = self.service.is_stock_exists('999999')
        
        # Verify result
        self.assertFalse(result)

    def test_get_stock_info(self):
        """Test getting stock information."""
        # Setup mock stock info
        mock_stock = MagicMock()
        mock_stock.symbol = '000001'
        mock_stock.name = '平安银行'
        mock_stock.market = 'SZSE'
        self.db_mock.query.return_value.filter.return_value.first.return_value = mock_stock
        
        # Call method
        result = self.service.get_stock_info('000001')
        
        # Verify result
        self.assertIsNotNone(result)
        self.assertEqual(result.symbol, '000001')

    def test_get_stock_info_not_found(self):
        """Test getting stock information when not found."""
        # Setup mock query result
        self.db_mock.query.return_value.filter.return_value.first.return_value = None
        
        # Call method
        result = self.service.get_stock_info('999999')
        
        # Verify result
        self.assertIsNone(result)

    def test_update_stock_cache_stats(self):
        """Test updating stock cache statistics."""
        # Setup test data
        total_count = 100
        
        # Call method
        self.service._update_cache_stats(total_count)
        
        # Verify database operations
        self.db_mock.add.assert_called()
        self.db_mock.commit.assert_called()

    def test_get_cache_info(self):
        """Test getting cache information."""
        # Setup mock cache manager
        mock_manager = MagicMock()
        mock_manager.cache_date = date.today()
        mock_manager.total_count = 100
        self.db_mock.query.return_value.filter.return_value.first.return_value = mock_manager
        
        # Call method
        result = self.service.get_cache_info()
        
        # Verify result
        self.assertIsNotNone(result)
        self.assertEqual(result.total_count, 100)

    def test_clear_all_cache(self):
        """Test clearing all cache."""
        # Call method
        result = self.service.clear_all_cache()
        
        # Verify database operations
        self.db_mock.query.assert_called()
        self.assertTrue(result)


if __name__ == '__main__':
    unittest.main()
