# tests/unit/test_query_service.py
"""
Unit tests for the QueryService class.
"""

import os
import sys
import unittest
from datetime import date, timedelta
from unittest.mock import MagicMock, patch

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from core.models.asset import Asset
from core.models.stock_data import DailyStockData
from core.services.query_service import QueryService


class TestQueryService(unittest.TestCase):
    """Test cases for QueryService."""

    def setUp(self):
        """Set up test fixtures."""
        self.db_mock = MagicMock()
        
        # Create service with mocked dependencies
        self.service = QueryService(self.db_mock)

    def test_init(self):
        """Test service initialization."""
        self.assertEqual(self.service.db, self.db_mock)

    def test_query_assets_basic(self):
        """Test basic asset query without filters."""
        # Setup mock query results
        mock_assets = [MagicMock(), MagicMock()]
        mock_query = self.db_mock.query.return_value
        mock_query.count.return_value = 2
        mock_query.offset.return_value.limit.return_value.all.return_value = mock_assets
        
        # Call method
        assets, total_count = self.service.query_assets()
        
        # Verify result
        self.assertEqual(len(assets), 2)
        self.assertEqual(total_count, 2)
        self.db_mock.query.assert_called_with(Asset)

    def test_query_assets_with_filters(self):
        """Test asset query with filters."""
        # Setup filters
        filters = {'asset_type': 'stock', 'exchange': 'SHSE'}

        # Setup mock query chain properly
        mock_assets = [MagicMock()]

        # Mock the Asset table columns for filter validation
        with patch('core.services.query_service.Asset') as mock_asset_class:
            mock_table = MagicMock()
            mock_table.columns = {'asset_type': MagicMock(), 'exchange': MagicMock()}
            mock_asset_class.__table__ = mock_table
            mock_asset_class.asset_type = MagicMock()
            mock_asset_class.exchange = MagicMock()

            # Setup the query chain
            mock_query = self.db_mock.query.return_value
            # Make sure filter returns the same query object for chaining
            mock_query.filter.return_value = mock_query
            mock_query.count.return_value = 1
            mock_query.offset.return_value.limit.return_value.all.return_value = mock_assets

            # Call method
            assets, total_count = self.service.query_assets(filters=filters)

            # Verify result
            self.assertEqual(len(assets), 1)
            self.assertEqual(total_count, 1)

    def test_query_assets_with_sorting_asc(self):
        """Test asset query with ascending sorting."""
        # Setup mock query results
        mock_assets = [MagicMock()]
        mock_query = self.db_mock.query.return_value
        mock_query.count.return_value = 1
        mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_assets
        
        # Call method
        assets, total_count = self.service.query_assets(sort_by='symbol', sort_order='asc')
        
        # Verify result
        self.assertEqual(len(assets), 1)
        mock_query.order_by.assert_called()

    def test_query_assets_with_sorting_desc(self):
        """Test asset query with descending sorting."""
        # Setup mock query results
        mock_assets = [MagicMock()]
        mock_query = self.db_mock.query.return_value
        mock_query.count.return_value = 1
        mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_assets
        
        # Call method
        assets, total_count = self.service.query_assets(sort_by='symbol', sort_order='desc')
        
        # Verify result
        self.assertEqual(len(assets), 1)
        mock_query.order_by.assert_called()

    @patch('core.services.query_service.logger')
    def test_query_assets_invalid_sort_field(self, logger_mock):
        """Test asset query with invalid sort field."""
        # Setup mock query results
        mock_assets = [MagicMock()]
        mock_query = self.db_mock.query.return_value
        mock_query.count.return_value = 1
        mock_query.offset.return_value.limit.return_value.all.return_value = mock_assets
        
        # Call method with invalid sort field
        assets, total_count = self.service.query_assets(sort_by='invalid_field')
        
        # Verify warning was logged
        logger_mock.warning.assert_called_with("Invalid sort field: invalid_field")

    def test_query_assets_with_pagination(self):
        """Test asset query with pagination."""
        # Setup mock query results
        mock_assets = [MagicMock()]
        mock_query = self.db_mock.query.return_value
        mock_query.count.return_value = 100
        mock_query.offset.return_value.limit.return_value.all.return_value = mock_assets
        
        # Call method with pagination
        assets, total_count = self.service.query_assets(skip=10, limit=5)
        
        # Verify pagination
        mock_query.offset.assert_called_with(10)
        mock_query.offset.return_value.limit.assert_called_with(5)
        self.assertEqual(total_count, 100)

    def test_query_prices_basic(self):
        """Test basic price query."""
        # Setup mock query results
        mock_prices = [MagicMock(), MagicMock()]
        mock_query = self.db_mock.query.return_value
        mock_query.count.return_value = 2
        mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_prices
        
        # Call method
        prices, total_count = self.service.query_prices()
        
        # Verify result
        self.assertEqual(len(prices), 2)
        self.assertEqual(total_count, 2)
        self.db_mock.query.assert_called_with(DailyStockData)

    def test_query_prices_with_asset_id(self):
        """Test price query with asset ID filter."""
        # Setup mock query results
        mock_prices = [MagicMock()]
        mock_query = self.db_mock.query.return_value
        # Setup the filter chain properly
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_prices

        # Call method
        prices, total_count = self.service.query_prices(asset_id=1)

        # Verify result
        self.assertEqual(len(prices), 1)
        self.assertEqual(total_count, 1)

    def test_query_prices_with_symbol(self):
        """Test price query with symbol filter."""
        # Setup mock query results
        mock_prices = [MagicMock()]
        mock_query = self.db_mock.query.return_value
        # Setup the join and filter chain properly
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_prices

        # Call method
        prices, total_count = self.service.query_prices(symbol='000001')
        
        # Verify result
        self.assertEqual(len(prices), 1)

    def test_query_prices_with_date_range(self):
        """Test price query with date range."""
        # Setup mock query results
        mock_prices = [MagicMock()]
        mock_query = self.db_mock.query.return_value
        # Setup the filter chain properly for date filters
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_prices

        # Call method
        start_date = date(2023, 1, 1)
        end_date = date(2023, 12, 31)
        prices, total_count = self.service.query_prices(start_date=start_date, end_date=end_date)

        # Verify result
        self.assertEqual(len(prices), 1)
        self.assertEqual(total_count, 1)

    def test_query_prices_symbol_not_found(self):
        """Test price query when symbol is not found."""
        # Setup mock query results for empty result
        mock_query = self.db_mock.query.return_value
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 0
        mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []

        # Call method
        prices, total_count = self.service.query_prices(symbol='INVALID')

        # Verify empty result
        self.assertEqual(len(prices), 0)
        self.assertEqual(total_count, 0)

    def test_query_daily_stock_data_basic(self):
        """Test basic daily stock data query."""
        # Setup mock query results
        mock_data = [MagicMock(), MagicMock()]
        mock_query = self.db_mock.query.return_value
        mock_query.count.return_value = 2
        mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_data
        
        # Call method
        data, total_count = self.service.query_daily_stock_data()
        
        # Verify result
        self.assertEqual(len(data), 2)
        self.assertEqual(total_count, 2)

    def test_query_daily_stock_data_with_asset_id(self):
        """Test daily stock data query with asset ID."""
        # Setup mock query results
        mock_data = [MagicMock()]
        mock_query = self.db_mock.query.return_value
        # Setup the filter chain properly
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_data

        # Call method
        data, total_count = self.service.query_daily_stock_data(asset_id=1)

        # Verify result
        self.assertEqual(len(data), 1)
        self.assertEqual(total_count, 1)

    def test_query_daily_stock_data_with_symbol(self):
        """Test daily stock data query with symbol."""
        # Setup mock query results
        mock_data = [MagicMock()]
        mock_query = self.db_mock.query.return_value
        # Setup the join and filter chain properly
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_data

        # Call method
        data, total_count = self.service.query_daily_stock_data(symbol='000001')

        # Verify result
        self.assertEqual(len(data), 1)
        self.assertEqual(total_count, 1)

    def test_apply_asset_filters_symbol(self):
        """Test applying symbol filter to asset query."""
        # Setup mock query
        mock_query = MagicMock()
        filters = {'symbol': '000001'}
        
        # Call internal method
        result = self.service._apply_asset_filters(mock_query, filters)
        
        # Verify filter was applied
        mock_query.filter.assert_called()

    def test_apply_asset_filters_name(self):
        """Test applying name filter to asset query."""
        # Setup mock query
        mock_query = MagicMock()
        filters = {'name': '平安银行'}
        
        # Call internal method
        result = self.service._apply_asset_filters(mock_query, filters)
        
        # Verify filter was applied
        mock_query.filter.assert_called()

    def test_apply_asset_filters_asset_type(self):
        """Test applying asset type filter to asset query."""
        # Setup mock query
        mock_query = MagicMock()
        filters = {'asset_type': 'stock'}
        
        # Call internal method
        result = self.service._apply_asset_filters(mock_query, filters)
        
        # Verify filter was applied
        mock_query.filter.assert_called()

    def test_apply_asset_filters_exchange(self):
        """Test applying exchange filter to asset query."""
        # Setup mock query
        mock_query = MagicMock()
        filters = {'exchange': 'SHSE'}
        
        # Call internal method
        result = self.service._apply_asset_filters(mock_query, filters)
        
        # Verify filter was applied
        mock_query.filter.assert_called()

    def test_apply_asset_filters_currency(self):
        """Test applying currency filter to asset query."""
        # Setup mock query
        mock_query = MagicMock()
        filters = {'currency': 'CNY'}
        
        # Call internal method
        result = self.service._apply_asset_filters(mock_query, filters)
        
        # Verify filter was applied
        mock_query.filter.assert_called()

    def test_apply_asset_filters_multiple(self):
        """Test applying multiple filters to asset query."""
        # Setup mock query that returns itself for chaining
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query

        # Mock Asset table columns for filter validation
        with patch('core.services.query_service.Asset') as mock_asset_class:
            mock_table = MagicMock()
            mock_table.columns = {
                'asset_type': MagicMock(),
                'exchange': MagicMock(),
                'currency': MagicMock()
            }
            mock_asset_class.__table__ = mock_table
            mock_asset_class.asset_type = MagicMock()
            mock_asset_class.exchange = MagicMock()
            mock_asset_class.currency = MagicMock()

            filters = {
                'asset_type': 'stock',
                'exchange': 'SHSE',
                'currency': 'CNY'
            }

            # Call internal method
            result = self.service._apply_asset_filters(mock_query, filters)

            # Verify multiple filters were applied (each filter calls filter() once)
            self.assertEqual(mock_query.filter.call_count, 3)

    def test_apply_price_filters_asset_id(self):
        """Test applying asset ID filter to price query."""
        # Setup mock query
        mock_query = MagicMock()
        
        # Call internal method
        result = self.service._apply_price_filters(mock_query, asset_id=1)
        
        # Verify filter was applied
        mock_query.filter.assert_called()

    def test_apply_price_filters_date_range(self):
        """Test applying date range filter to price query."""
        # Setup mock query
        mock_query = MagicMock()
        start_date = date(2023, 1, 1)
        end_date = date(2023, 12, 31)
        
        # Call internal method
        result = self.service._apply_price_filters(mock_query, start_date=start_date, end_date=end_date)
        
        # Verify filter was applied
        mock_query.filter.assert_called()

    def test_apply_price_filters_start_date_only(self):
        """Test applying start date filter only to price query."""
        # Setup mock query
        mock_query = MagicMock()
        start_date = date(2023, 1, 1)
        
        # Call internal method
        result = self.service._apply_price_filters(mock_query, start_date=start_date)
        
        # Verify filter was applied
        mock_query.filter.assert_called()

    def test_apply_price_filters_end_date_only(self):
        """Test applying end date filter only to price query."""
        # Setup mock query
        mock_query = MagicMock()
        end_date = date(2023, 12, 31)
        
        # Call internal method
        result = self.service._apply_price_filters(mock_query, end_date=end_date)
        
        # Verify filter was applied
        mock_query.filter.assert_called()

    @patch('core.services.query_service.logger')
    def test_query_assets_exception(self, logger_mock):
        """Test handling exceptions in asset query."""
        # Setup mock to raise exception
        self.db_mock.query.side_effect = Exception("Database error")
        
        # Call method and expect exception
        with self.assertRaises(Exception):
            self.service.query_assets()
        
        # Verify error was logged
        logger_mock.error.assert_called()

    @patch('core.services.query_service.logger')
    def test_query_prices_exception(self, logger_mock):
        """Test handling exceptions in price query."""
        # Setup mock to raise exception
        self.db_mock.query.side_effect = Exception("Database error")
        
        # Call method and expect exception
        with self.assertRaises(Exception):
            self.service.query_prices()
        
        # Verify error was logged
        logger_mock.error.assert_called()

    @patch('core.services.query_service.logger')
    def test_query_daily_stock_data_exception(self, logger_mock):
        """Test handling exceptions in daily stock data query."""
        # Setup mock to raise exception
        self.db_mock.query.side_effect = Exception("Database error")
        
        # Call method and expect exception
        with self.assertRaises(Exception):
            self.service.query_daily_stock_data()
        
        # Verify error was logged
        logger_mock.error.assert_called()


if __name__ == '__main__':
    unittest.main()
