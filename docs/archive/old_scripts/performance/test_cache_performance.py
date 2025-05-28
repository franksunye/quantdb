# tests/performance/test_cache_performance.py
"""
Performance tests for the cache system.

These tests measure the performance of the simplified cache architecture.
"""

import unittest
import time
import os
import sys
import tempfile
import pandas as pd
from unittest.mock import patch
from datetime import datetime, timedelta
import statistics

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.services.stock_data_service import StockDataService
from src.services.database_cache import DatabaseCache
from src.cache.akshare_adapter import AKShareAdapter
from src.api.models import Base, Asset, DailyStockData
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.enhanced_logger import setup_enhanced_logger

# Setup logger
logger = setup_enhanced_logger(__name__)

class TestCachePerformance(unittest.TestCase):
    """Performance tests for the cache system."""

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
            time.sleep(0.1)

            # Try to remove the files
            if os.path.exists(cls.db_path):
                os.unlink(cls.db_path)
        except OSError as e:
            # If file is still in use, log the error but don't fail the test
            logger.warning(f"Could not remove temporary database file: {e}")

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

        # Run multiple times to get average performance
        num_runs = 5
        response_times = []

        for _ in range(num_runs):
            # Clean up database
            self.session.query(DailyStockData).delete()
            self.session.query(Asset).delete()
            self.session.commit()

            # Test implementation
            start_time = time.time()
            result = self.stock_data_service.get_stock_data('600000', '20230101', '20230131')
            end_time = time.time()

            # Calculate response time
            response_time = end_time - start_time
            response_times.append(response_time)

        # Calculate statistics
        avg_time = statistics.mean(response_times)
        max_time = max(response_times)
        min_time = min(response_times)

        # Log results
        logger.info(f"Empty database performance:")
        logger.info(f"  Average: {avg_time:.4f}s")
        logger.info(f"  Maximum: {max_time:.4f}s")
        logger.info(f"  Minimum: {min_time:.4f}s")

        # Verify data was returned
        self.assertGreater(len(result), 0)

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

        # Run multiple times to get average performance
        num_runs = 5
        response_times = []

        for _ in range(num_runs):
            # Test implementation
            start_time = time.time()
            result = self.stock_data_service.get_stock_data('600000', '20230101', '20230131')
            end_time = time.time()

            # Calculate response time
            response_time = end_time - start_time
            response_times.append(response_time)

        # Calculate statistics
        avg_time = statistics.mean(response_times)
        max_time = max(response_times)
        min_time = min(response_times)

        # Log results
        logger.info(f"Partial database performance:")
        logger.info(f"  Average: {avg_time:.4f}s")
        logger.info(f"  Maximum: {max_time:.4f}s")
        logger.info(f"  Minimum: {min_time:.4f}s")

        # Verify data was returned
        self.assertEqual(len(result), 31)  # Full month of data

    def test_performance_full_database(self):
        """Test performance when database has all data."""
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

        # Create stock data for all days
        mock_df = self._generate_mock_data('20230101', '20230131')
        for _, row in mock_df.iterrows():
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

        # Run multiple times to get average performance
        num_runs = 5
        response_times = []

        for _ in range(num_runs):
            # Test implementation
            start_time = time.time()
            result = self.stock_data_service.get_stock_data('600000', '20230101', '20230131')
            end_time = time.time()

            # Calculate response time
            response_time = end_time - start_time
            response_times.append(response_time)

        # Calculate statistics
        avg_time = statistics.mean(response_times)
        max_time = max(response_times)
        min_time = min(response_times)

        # Log results
        logger.info(f"Full database performance:")
        logger.info(f"  Average: {avg_time:.4f}s")
        logger.info(f"  Maximum: {max_time:.4f}s")
        logger.info(f"  Minimum: {min_time:.4f}s")

        # Verify data was returned
        self.assertEqual(len(result), 31)  # Full month of data

if __name__ == '__main__':
    unittest.main()
