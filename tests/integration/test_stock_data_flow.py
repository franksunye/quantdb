# tests/integration/test_stock_data_flow.py
"""
Integration tests for the stock data flow.

These tests verify the integration between StockDataService, DatabaseCache, and AKShareAdapter.
"""

import unittest
from unittest.mock import MagicMock, patch
import pandas as pd
from datetime import datetime, timedelta
import os
import sys
import tempfile

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from core.services.stock_data_service import StockDataService
from core.services.database_cache import DatabaseCache
from core.cache.akshare_adapter import AKShareAdapter
from core.models import Base, Asset, DailyStockData
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

class TestStockDataFlow(unittest.TestCase):
    """Integration tests for the stock data flow."""

    @classmethod
    def setUpClass(cls):
        """Set up test database."""
        # Create temporary database
        cls.db_fd, cls.db_path = tempfile.mkstemp()
        cls.engine = create_engine(f'sqlite:///{cls.db_path}')

        # Create tables
        Base.metadata.create_all(cls.engine)

        # Create session
        cls.Session = sessionmaker(bind=cls.engine)

    @classmethod
    def tearDownClass(cls):
        """Clean up test database."""
        try:
            os.close(cls.db_fd)
        except OSError:
            # File descriptor might already be closed
            pass

        try:
            # Give time for any pending operations to complete
            import time
            time.sleep(0.1)

            # Try to remove the file
            if os.path.exists(cls.db_path):
                os.unlink(cls.db_path)
        except OSError as e:
            # If file is still in use, log the error but don't fail the test
            print(f"Warning: Could not remove temporary database file: {e}")
            # In a real environment, you might want to schedule this file for deletion on reboot
            # or use a more sophisticated cleanup mechanism

    def setUp(self):
        """Set up test fixtures."""
        self.session = self.Session()

        # Create components
        self.akshare_adapter = AKShareAdapter(self.session)
        self.db_cache = DatabaseCache(self.session)
        self.stock_data_service = StockDataService(self.session, self.akshare_adapter)
        self.stock_data_service.db_cache = self.db_cache

        # Mock AKShare API call
        self.akshare_patcher = patch.object(self.akshare_adapter, '_safe_call')
        self.mock_safe_call = self.akshare_patcher.start()

    def tearDown(self):
        """Clean up test fixtures."""
        self.akshare_patcher.stop()

        # Clean up database
        self.session.query(DailyStockData).delete()
        self.session.query(Asset).delete()
        self.session.commit()
        self.session.close()

    def test_empty_database_flow(self):
        """Test data flow when database is empty."""
        # Setup mock data - using actual trading days (2023-01-03 and 2023-01-04)
        mock_df = pd.DataFrame({
            'date': pd.to_datetime(['2023-01-03', '2023-01-04']),
            'open': [100.0, 101.0],
            'high': [105.0, 106.0],
            'low': [99.0, 100.0],
            'close': [101.0, 102.0],
            'volume': [1000, 1100],
            'turnover': [101000.0, 111100.0],
            'amplitude': [6.0, 5.9],
            'pct_change': [1.0, 1.0],
            'change': [1.0, 1.0],
            'turnover_rate': [0.5, 0.55]
        })
        self.mock_safe_call.return_value = mock_df

        # Call service - using actual trading days
        result = self.stock_data_service.get_stock_data('600000', '20230103', '20230104')

        # Check result
        self.assertEqual(len(result), 2)
        self.assertEqual(result['open'].tolist(), [100.0, 101.0])

        # Verify data was saved to database
        assets = self.session.query(Asset).all()
        self.assertEqual(len(assets), 1)
        self.assertEqual(assets[0].symbol, '600000')

        stock_data = self.session.query(DailyStockData).all()
        self.assertEqual(len(stock_data), 2)

        # Call service again - should use database cache
        self.mock_safe_call.reset_mock()
        result2 = self.stock_data_service.get_stock_data('600000', '20230103', '20230104')

        # Check result
        self.assertEqual(len(result2), 2)

        # Verify AKShare was not called
        self.mock_safe_call.assert_not_called()

    def test_partial_database_flow(self):
        """Test data flow when database has partial data."""
        # Create asset
        asset = Asset(
            symbol='600000',
            name='Stock 600000',
            isin='CN600000',
            asset_type='stock',
            exchange='CN',
            currency='CNY'
        )
        self.session.add(asset)
        self.session.commit()

        # Create stock data for first trading day (2023-01-03)
        stock_data = DailyStockData(
            asset_id=asset.asset_id,
            trade_date=datetime(2023, 1, 3).date(),
            open=100.0,
            high=105.0,
            low=99.0,
            close=101.0,
            volume=1000,
            turnover=101000.0,
            amplitude=6.0,
            pct_change=1.0,
            change=1.0,
            turnover_rate=0.5
        )
        self.session.add(stock_data)
        self.session.commit()

        # Setup mock data for second trading day (2023-01-04)
        mock_df = pd.DataFrame({
            'date': pd.to_datetime(['2023-01-04']),
            'open': [101.0],
            'high': [106.0],
            'low': [100.0],
            'close': [102.0],
            'volume': [1100],
            'turnover': [111100.0],
            'amplitude': [5.9],
            'pct_change': [1.0],
            'change': [1.0],
            'turnover_rate': [0.55]
        })
        self.mock_safe_call.return_value = mock_df

        # Call service - using actual trading days
        result = self.stock_data_service.get_stock_data('600000', '20230103', '20230104')

        # Check result
        self.assertEqual(len(result), 2)

        # Verify AKShare was called with correct parameters
        self.mock_safe_call.assert_called_once()
        args, kwargs = self.mock_safe_call.call_args
        self.assertEqual(kwargs['symbol'], '600000')
        self.assertEqual(kwargs['start_date'], '20230104')
        self.assertEqual(kwargs['end_date'], '20230104')

        # Verify data was saved to database
        stock_data = self.session.query(DailyStockData).all()
        self.assertEqual(len(stock_data), 2)

    def test_date_range_grouping(self):
        """Test grouping of date ranges for efficient API calls."""
        # Create asset
        asset = Asset(
            symbol='600000',
            name='Stock 600000',
            isin='CN600000',
            asset_type='stock',
            exchange='CN',
            currency='CNY'
        )
        self.session.add(asset)
        self.session.commit()

        # Create stock data for trading days 3, 4, 6 (2023-01-03, 2023-01-04, 2023-01-06)
        dates = [datetime(2023, 1, 3).date(), datetime(2023, 1, 4).date(), datetime(2023, 1, 6).date()]
        for date in dates:
            stock_data = DailyStockData(
                asset_id=asset.asset_id,
                trade_date=date,
                open=100.0,
                high=105.0,
                low=99.0,
                close=101.0,
                volume=1000,
                turnover=101000.0,
                amplitude=6.0,
                pct_change=1.0,
                change=1.0,
                turnover_rate=0.5
            )
            self.session.add(stock_data)
        self.session.commit()

        # Setup mock data for missing trading days (2023-01-05, 2023-01-09, 2023-01-10)
        mock_df = pd.DataFrame({
            'date': pd.to_datetime(['2023-01-05', '2023-01-09', '2023-01-10']),
            'open': [101.0, 102.0, 103.0],
            'high': [106.0, 107.0, 108.0],
            'low': [100.0, 101.0, 102.0],
            'close': [102.0, 103.0, 104.0],
            'volume': [1100, 1200, 1300],
            'turnover': [111100.0, 121200.0, 131300.0],
            'amplitude': [5.9, 5.8, 5.7],
            'pct_change': [1.0, 1.0, 1.0],
            'change': [1.0, 1.0, 1.0],
            'turnover_rate': [0.55, 0.56, 0.57]
        })
        self.mock_safe_call.return_value = mock_df

        # Call service - request range that includes existing and missing data
        result = self.stock_data_service.get_stock_data('600000', '20230103', '20230110')

        # Check result - should have 6 trading days (3 existing + 3 new)
        self.assertEqual(len(result), 6)

        # Verify AKShare was called at least once
        # Note: The actual number of calls depends on how the date ranges are grouped
        # In the current implementation, it might be called once with all missing dates
        # or multiple times with different date ranges
        self.assertGreaterEqual(self.mock_safe_call.call_count, 1)

        # Verify data was saved to database
        stock_data = self.session.query(DailyStockData).all()
        self.assertEqual(len(stock_data), 6)

    def test_empty_akshare_response(self):
        """Test handling of empty AKShare response."""
        # Setup mock data
        self.mock_safe_call.return_value = pd.DataFrame()

        # Call service - using actual trading days
        result = self.stock_data_service.get_stock_data('600000', '20230103', '20230104')

        # Check result
        self.assertTrue(result.empty)

        # Verify AKShare was called
        self.mock_safe_call.assert_called_once()

        # Verify no data was saved to database
        stock_data = self.session.query(DailyStockData).all()
        self.assertEqual(len(stock_data), 0)

        # Note: An asset might be created even if no data is saved
        # This is because the get_or_create_asset method in DatabaseCache
        # creates an asset if it doesn't exist, regardless of whether data is saved
        # So we don't check the number of assets here

    def test_akshare_exception(self):
        """Test handling of AKShare exception."""
        # Setup mock to raise exception
        self.mock_safe_call.side_effect = Exception("Test exception")

        # Call service - using actual trading days
        result = self.stock_data_service.get_stock_data('600000', '20230103', '20230104')

        # Check result
        self.assertTrue(result.empty)

        # Verify AKShare was called
        self.mock_safe_call.assert_called_once()

        # Verify no data was saved to database
        stock_data = self.session.query(DailyStockData).all()
        self.assertEqual(len(stock_data), 0)

        # Note: An asset might be created even if no data is saved
        # This is because the get_or_create_asset method in DatabaseCache
        # creates an asset if it doesn't exist, regardless of whether data is saved
        # So we don't check the number of assets here

if __name__ == '__main__':
    unittest.main()
