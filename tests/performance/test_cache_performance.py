# tests/performance/test_cache_performance.py
"""
Performance tests for the cache system.

These tests compare the performance of the simplified cache architecture
with the original reservoir cache implementation.
"""

import unittest
import time
import os
import sys
import tempfile
import pandas as pd
from unittest.mock import patch
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.services.stock_data_service import StockDataService
from src.services.database_cache import DatabaseCache
from src.cache.akshare_adapter_simplified import AKShareAdapter
from src.api.models import Base, Asset, DailyStockData
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import original implementation for comparison
from src.cache.cache_engine import CacheEngine
from src.cache.freshness_tracker import FreshnessTracker
from src.cache.akshare_adapter import AKShareAdapter as OriginalAKShareAdapter
from src.services.data_import import DataImportService


class TestCachePerformance(unittest.TestCase):
    """Performance tests for the cache system."""

    @classmethod
    def setUpClass(cls):
        """Set up test database."""
        # Create temporary database for simplified implementation
        cls.db_fd, cls.db_path = tempfile.mkstemp()
        cls.engine = create_engine(f'sqlite:///{cls.db_path}')

        # Create tables
        Base.metadata.create_all(cls.engine)

        # Create session
        cls.Session = sessionmaker(bind=cls.engine)

        # Create temporary databases for original implementation
        cls.cache_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        cls.cache_db.close()
        cls.freshness_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        cls.freshness_db.close()

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
            time.sleep(0.1)

            # Try to remove the files
            if os.path.exists(cls.db_path):
                os.unlink(cls.db_path)
            if os.path.exists(cls.cache_db.name):
                os.unlink(cls.cache_db.name)
            if os.path.exists(cls.freshness_db.name):
                os.unlink(cls.freshness_db.name)
        except OSError as e:
            # If file is still in use, log the error but don't fail the test
            print(f"Warning: Could not remove temporary database file: {e}")

    def setUp(self):
        """Set up test fixtures."""
        self.session = self.Session()

        # Create components for simplified implementation
        self.akshare_adapter = AKShareAdapter(self.session)
        self.db_cache = DatabaseCache(self.session)
        self.stock_data_service = StockDataService(self.session, self.akshare_adapter)
        self.stock_data_service.db_cache = self.db_cache

        # Create components for original implementation
        self.cache_engine = CacheEngine(db_path=self.cache_db.name)
        self.freshness_tracker = FreshnessTracker(db_path=self.freshness_db.name)
        self.original_akshare_adapter = OriginalAKShareAdapter()
        self.data_import_service = DataImportService(
            db=self.session,
            cache_engine=self.cache_engine,
            freshness_tracker=self.freshness_tracker,
            akshare_adapter=self.original_akshare_adapter
        )

        # Mock AKShare API call for both implementations
        self.akshare_patcher = patch.object(self.akshare_adapter, '_safe_call')
        self.mock_safe_call = self.akshare_patcher.start()

        self.original_akshare_patcher = patch.object(self.original_akshare_adapter, 'get_stock_data')
        self.mock_original_get_stock_data = self.original_akshare_patcher.start()

    def tearDown(self):
        """Clean up test fixtures."""
        self.akshare_patcher.stop()
        self.original_akshare_patcher.stop()

        # Clean up database
        self.session.query(DailyStockData).delete()
        self.session.query(Asset).delete()
        self.session.commit()
        self.session.close()

    def _generate_mock_data(self, start_date, end_date):
        """Generate mock data for testing."""
        # Generate date range
        start = datetime.strptime(start_date, '%Y%m%d')
        end = datetime.strptime(end_date, '%Y%m%d')
        date_range = [start + timedelta(days=i) for i in range((end - start).days + 1)]

        # Create mock data
        data = {
            'date': pd.to_datetime([d.strftime('%Y-%m-%d') for d in date_range]),
            'open': [100.0 + i for i in range(len(date_range))],
            'high': [105.0 + i for i in range(len(date_range))],
            'low': [99.0 + i for i in range(len(date_range))],
            'close': [101.0 + i for i in range(len(date_range))],
            'volume': [1000 + i * 100 for i in range(len(date_range))],
            'turnover': [101000.0 + i * 1000 for i in range(len(date_range))],
            'amplitude': [6.0 for i in range(len(date_range))],
            'pct_change': [1.0 for i in range(len(date_range))],
            'change': [1.0 for i in range(len(date_range))],
            'turnover_rate': [0.5 for i in range(len(date_range))]
        }
        return pd.DataFrame(data)

    def test_performance_empty_database(self):
        """Test performance when database is empty."""
        # Setup mock data
        mock_df = self._generate_mock_data('20230101', '20230131')
        self.mock_safe_call.return_value = mock_df
        self.mock_original_get_stock_data.return_value = mock_df

        # Test simplified implementation
        start_time = time.time()
        result_simplified = self.stock_data_service.get_stock_data('600000', '20230101', '20230131')
        simplified_time = time.time() - start_time

        # Clean up database
        self.session.query(DailyStockData).delete()
        self.session.query(Asset).delete()
        self.session.commit()

        # Test original implementation
        start_time = time.time()
        result_original = self.data_import_service.import_from_akshare('600000', '20230101', '20230131')
        original_time = time.time() - start_time

        # Print performance comparison
        print(f"\nPerformance comparison (empty database):")
        print(f"Simplified implementation: {simplified_time:.4f} seconds")
        print(f"Original implementation: {original_time:.4f} seconds")
        print(f"Improvement: {(original_time - simplified_time) / original_time * 100:.2f}%")

        # Verify both implementations returned data
        self.assertGreater(len(result_simplified), 0)
        self.assertTrue(result_original.get('success', False))

    def test_performance_partial_database(self):
        """Test performance when database has partial data."""
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

        # Create stock data for first 15 days
        mock_df_first_half = self._generate_mock_data('20230101', '20230115')
        for _, row in mock_df_first_half.iterrows():
            stock_data = DailyStockData(
                asset_id=asset.asset_id,
                trade_date=row['date'].date(),
                open=row['open'],
                high=row['high'],
                low=row['low'],
                close=row['close'],
                volume=row['volume'],
                turnover=row['turnover'],
                amplitude=row['amplitude'],
                pct_change=row['pct_change'],
                change=row['change'],
                turnover_rate=row['turnover_rate']
            )
            self.session.add(stock_data)
        self.session.commit()

        # Setup mock data for second half
        mock_df_second_half = self._generate_mock_data('20230116', '20230131')
        self.mock_safe_call.return_value = mock_df_second_half
        self.mock_original_get_stock_data.return_value = mock_df_second_half

        # Test simplified implementation
        start_time = time.time()
        result_simplified = self.stock_data_service.get_stock_data('600000', '20230101', '20230131')
        simplified_time = time.time() - start_time

        # Test original implementation
        start_time = time.time()
        result_original = self.data_import_service.import_from_akshare('600000', '20230101', '20230131')
        original_time = time.time() - start_time

        # Print performance comparison
        print(f"\nPerformance comparison (partial database):")
        print(f"Simplified implementation: {simplified_time:.4f} seconds")
        print(f"Original implementation: {original_time:.4f} seconds")
        print(f"Improvement: {(original_time - simplified_time) / original_time * 100:.2f}%")

        # Verify both implementations returned data
        self.assertEqual(len(result_simplified), 31)  # Full month of data
        self.assertTrue(result_original.get('success', False))


if __name__ == '__main__':
    unittest.main()
