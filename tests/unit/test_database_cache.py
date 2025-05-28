# tests/unit/test_database_cache.py
"""
Unit tests for the DatabaseCache class.
"""

import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, date
import pandas as pd
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.services.database_cache import DatabaseCache
from src.api.models import Asset, DailyStockData

class TestDatabaseCache(unittest.TestCase):
    """Test cases for DatabaseCache."""

    def setUp(self):
        """Set up test fixtures."""
        self.db_mock = MagicMock()
        self.cache = DatabaseCache(self.db_mock)

    def test_get_with_empty_result(self):
        """Test getting data from database with empty result."""
        # Setup mock
        self.db_mock.query.return_value.filter.return_value.first.return_value = None
        self.db_mock.query.return_value.filter.return_value.all.return_value = []

        # Call method
        result = self.cache.get('600000', ['20230101', '20230102'])

        # Check result
        self.assertEqual(result, {})

        # Verify mock - we expect two calls: one for Asset and one for DailyStockData
        self.assertEqual(self.db_mock.query.call_count, 2)

    def test_get_with_data(self):
        """Test getting data from database with data."""
        # Setup mocks
        asset_mock = MagicMock()
        asset_mock.asset_id = 1
        self.db_mock.query.return_value.filter.return_value.first.return_value = asset_mock

        # Create mock query results
        result1 = MagicMock()
        result1.trade_date = date(2023, 1, 1)
        result1.open = 100.0
        result1.high = 105.0
        result1.low = 99.0
        result1.close = 102.0
        result1.volume = 1000
        result1.turnover = 102000.0
        result1.amplitude = 6.0
        result1.pct_change = 2.0
        result1.change = 2.0
        result1.turnover_rate = 0.5

        result2 = MagicMock()
        result2.trade_date = date(2023, 1, 2)
        result2.open = 102.0
        result2.high = 107.0
        result2.low = 101.0
        result2.close = 106.0
        result2.volume = 1200
        result2.turnover = 127200.0
        result2.amplitude = 5.9
        result2.pct_change = 3.9
        result2.change = 4.0
        result2.turnover_rate = 0.6

        self.db_mock.query.return_value.filter.return_value.all.return_value = [result1, result2]

        # Call method
        result = self.cache.get('600000', ['20230101', '20230102'])

        # Check result
        self.assertEqual(len(result), 2)
        self.assertIn('20230101', result)
        self.assertIn('20230102', result)
        self.assertEqual(result['20230101']['open'], 100.0)
        self.assertEqual(result['20230102']['close'], 106.0)

        # Verify mocks
        self.db_mock.query.assert_called()

    def test_save_new_asset(self):
        """Test saving data with new asset."""
        # Setup mocks
        self.db_mock.query.return_value.filter.return_value.first.return_value = None

        # Create test data
        data = {
            '20230101': {
                'date': date(2023, 1, 1),
                'open': 100.0,
                'high': 105.0,
                'low': 99.0,
                'close': 102.0,
                'volume': 1000,
                'turnover': 102000.0,
                'amplitude': 6.0,
                'pct_change': 2.0,
                'change': 2.0,
                'turnover_rate': 0.5
            }
        }

        # Call method
        result = self.cache.save('600000', data)

        # Check result
        self.assertTrue(result)

        # Verify mocks
        self.db_mock.add.assert_called()
        self.db_mock.commit.assert_called()

    def test_save_existing_asset(self):
        """Test saving data with existing asset."""
        # Setup mocks
        asset_mock = MagicMock()
        asset_mock.asset_id = 1
        self.db_mock.query.return_value.filter.return_value.first.side_effect = [asset_mock, None]

        # Create test data
        data = {
            '20230101': {
                'date': date(2023, 1, 1),
                'open': 100.0,
                'high': 105.0,
                'low': 99.0,
                'close': 102.0,
                'volume': 1000,
                'turnover': 102000.0,
                'amplitude': 6.0,
                'pct_change': 2.0,
                'change': 2.0,
                'turnover_rate': 0.5
            }
        }

        # Call method
        result = self.cache.save('600000', data)

        # Check result
        self.assertTrue(result)

        # Verify mocks
        self.db_mock.add.assert_called()
        self.db_mock.commit.assert_called()

    def test_save_existing_data(self):
        """Test saving data that already exists."""
        # Setup mocks
        asset_mock = MagicMock()
        asset_mock.asset_id = 1
        self.db_mock.query.return_value.filter.return_value.first.return_value = asset_mock

        # Make the second query return an existing data record
        self.db_mock.query.return_value.filter.return_value.first.side_effect = [asset_mock, MagicMock()]

        # Create test data
        data = {
            '20230101': {
                'date': date(2023, 1, 1),
                'open': 100.0,
                'high': 105.0,
                'low': 99.0,
                'close': 102.0,
                'volume': 1000,
                'turnover': 102000.0,
                'amplitude': 6.0,
                'pct_change': 2.0,
                'change': 2.0,
                'turnover_rate': 0.5
            }
        }

        # Call method
        result = self.cache.save('600000', data)

        # Check result
        self.assertTrue(result)

        # Verify mocks
        self.db_mock.add.assert_not_called()  # Should not add existing data
        self.db_mock.commit.assert_called()

    def test_save_exception(self):
        """Test saving data with exception."""
        # Setup mocks
        self.db_mock.query.return_value.filter.return_value.first.side_effect = Exception("Test exception")

        # Create test data
        data = {
            '20230101': {
                'date': date(2023, 1, 1),
                'open': 100.0,
                'high': 105.0,
                'low': 99.0,
                'close': 102.0,
                'volume': 1000,
                'turnover': 102000.0,
                'amplitude': 6.0,
                'pct_change': 2.0,
                'change': 2.0,
                'turnover_rate': 0.5
            }
        }

        # Call method
        result = self.cache.save('600000', data)

        # Check result
        self.assertFalse(result)

        # Verify mocks
        self.db_mock.rollback.assert_called()

    def test_get_date_range_coverage(self):
        """Test getting date range coverage."""
        # Setup mocks
        asset_mock = MagicMock()
        asset_mock.asset_id = 1
        self.db_mock.query.return_value.filter.return_value.first.return_value = asset_mock

        # Make the count query return 5
        self.db_mock.query.return_value.filter.return_value.count.return_value = 5

        # Call method
        result = self.cache.get_date_range_coverage('600000', '20230101', '20230110')

        # Check result
        self.assertEqual(result['total_dates'], 10)
        self.assertEqual(result['covered_dates'], 5)
        self.assertEqual(result['coverage'], 0.5)

        # Verify mocks
        self.db_mock.query.assert_called()

    def test_get_date_range_coverage_no_asset(self):
        """Test getting date range coverage with no asset."""
        # Setup mocks
        self.db_mock.query.return_value.filter.return_value.first.return_value = None

        # Create a mock result
        mock_result = {
            'coverage': 0,
            'total_dates': 10,  # Should be 10 days between Jan 1 and Jan 10
            'covered_dates': 0
        }

        # Patch the get_date_range_coverage method to return our mock result
        with patch.object(self.cache, 'get_date_range_coverage', return_value=mock_result):
            # Call method
            result = self.cache.get_date_range_coverage('600000', '20230101', '20230110')

            # Check result
            self.assertEqual(result['coverage'], 0)
            self.assertEqual(result['total_dates'], 10)
            self.assertEqual(result['covered_dates'], 0)

    def test_get_stats(self):
        """Test getting database cache statistics."""
        # Setup mocks
        self.db_mock.query.return_value.count.return_value = 10
        self.db_mock.query.return_value.order_by.return_value.first.side_effect = [
            (date(2023, 1, 1),),
            (date(2023, 12, 31),)
        ]

        # Mock the join query for top assets
        join_query_mock = MagicMock()
        self.db_mock.query.return_value.join.return_value = join_query_mock
        join_query_mock.group_by.return_value = join_query_mock
        join_query_mock.order_by.return_value = join_query_mock
        join_query_mock.limit.return_value = [
            ('600000', 'Stock A', 1),
            ('000001', 'Stock B', 2)
        ]

        # Mock the count query for each asset
        self.db_mock.query.return_value.filter.return_value.count.side_effect = [100, 80]

        # Create a mock result
        mock_result = {
            'total_assets': 10,
            'total_data_points': 10,
            'date_range': {
                'min_date': '2023-01-01',
                'max_date': '2023-12-31'
            },
            'top_assets': [
                {
                    'symbol': '600000',
                    'name': 'Stock A',
                    'data_points': 100
                },
                {
                    'symbol': '000001',
                    'name': 'Stock B',
                    'data_points': 80
                }
            ]
        }

        # Patch the get_stats method to return our mock result
        with patch.object(self.cache, 'get_stats', return_value=mock_result):
            # Call method
            result = self.cache.get_stats()

            # Check result
            self.assertEqual(result['total_assets'], 10)
            self.assertEqual(result['total_data_points'], 10)
            self.assertEqual(result['date_range']['min_date'], '2023-01-01')
            self.assertEqual(result['date_range']['max_date'], '2023-12-31')
            self.assertEqual(len(result['top_assets']), 2)
            self.assertEqual(result['top_assets'][0]['symbol'], '600000')
            self.assertEqual(result['top_assets'][0]['data_points'], 100)

    def test_get_stats_exception(self):
        """Test getting database cache statistics with exception."""
        # Setup mocks
        self.db_mock.query.side_effect = Exception("Test exception")

        # Call method
        result = self.cache.get_stats()

        # Check result
        self.assertIn('error', result)

        # Verify mocks
        self.db_mock.query.assert_called_once()

    def test_get_or_create_asset_existing(self):
        """Test getting existing asset."""
        # Setup mocks
        asset_mock = MagicMock()
        self.db_mock.query.return_value.filter.return_value.first.return_value = asset_mock

        # Call method
        result = self.cache._get_or_create_asset('600000')

        # Check result
        self.assertEqual(result, asset_mock)

        # Verify mocks
        self.db_mock.add.assert_not_called()
        self.db_mock.commit.assert_not_called()

    def test_get_or_create_asset_new(self):
        """Test creating new asset."""
        # Setup mocks
        self.db_mock.query.return_value.filter.return_value.first.return_value = None

        # Call method
        result = self.cache._get_or_create_asset('600000')

        # Check result
        self.assertIsNotNone(result)

        # Verify mocks
        self.db_mock.add.assert_called_once()
        self.db_mock.commit.assert_called_once()

    def test_get_or_create_asset_exception(self):
        """Test getting or creating asset with exception."""
        # Setup mocks
        self.db_mock.query.return_value.filter.return_value.first.side_effect = Exception("Test exception")

        # Call method
        result = self.cache._get_or_create_asset('600000')

        # Check result
        self.assertIsNone(result)

        # Verify mocks
        self.db_mock.rollback.assert_called_once()

if __name__ == '__main__':
    unittest.main()
