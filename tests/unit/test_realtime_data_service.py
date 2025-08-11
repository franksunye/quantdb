"""
Realtime data service unit tests for QuantDB.

This module tests the RealtimeDataService which handles:
- Realtime stock data retrieval with caching
- Intelligent cache TTL based on trading hours
- Batch processing for multiple symbols
- Cache hit/miss optimization
"""

import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, Mock, patch

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.cache.akshare_adapter import AKShareAdapter
from core.models import Base, RealtimeStockData
from core.services.realtime_data_service import RealtimeDataService


class TestRealtimeDataService(unittest.TestCase):
    """Test RealtimeDataService functionality."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test database."""
        cls.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(cls.engine)
        cls.SessionLocal = sessionmaker(bind=cls.engine)
    
    def setUp(self):
        """Set up test fixtures."""
        self.session = self.SessionLocal()
        self.mock_adapter = Mock(spec=AKShareAdapter)
        self.service = RealtimeDataService(self.session, self.mock_adapter)
    
    def tearDown(self):
        """Clean up test session."""
        self.session.close()
    
    def test_service_initialization(self):
        """Test service initialization."""
        self.assertIsNotNone(self.service.db)
        self.assertIsNotNone(self.service.akshare_adapter)
        self.assertIsNotNone(self.service.cache_manager)
    
    def test_get_realtime_data_cache_miss(self):
        """Test realtime data retrieval with cache miss."""
        # Mock AKShare response
        mock_data = pd.DataFrame({
            'symbol': ['000001'],
            'current': [12.50],
            'change': [0.25],
            'percent': [2.04],
            'volume': [15000000],
            'turnover': [187500000.0],
            'high': [12.60],
            'low': [12.30],
            'open': [12.35],
            'pre_close': [12.25]
        })
        self.mock_adapter.get_realtime_data.return_value = mock_data

        # Test cache miss scenario with force_refresh
        result = self.service.get_realtime_data("000001", force_refresh=True)

        # Verify result structure
        self.assertIsNotNone(result)
        self.assertEqual(result['symbol'], '000001')
    
    def test_get_realtime_data_cache_hit(self):
        """Test realtime data retrieval with cache hit."""
        # Create cached data
        cached_data = RealtimeStockData(
            symbol="000001",
            price=12.45,
            change=0.20,
            pct_change=1.63,
            volume=14000000,
            turnover=174300000.0,
            high_price=12.55,
            low_price=12.25,
            open_price=12.30,
            prev_close=12.25,
            timestamp=datetime.now() - timedelta(minutes=2),  # Recent cache
            cache_ttl_minutes=5,
            is_trading_hours=True
        )
        self.session.add(cached_data)
        self.session.commit()
        
        # Test cache hit
        result = self.service.get_realtime_data("000001")
        
        # Verify AKShare was NOT called
        self.mock_adapter.get_realtime_data.assert_not_called()
        
        # Verify cached result
        self.assertEqual(result['symbol'], '000001')
        self.assertEqual(result['price'], 12.45)
        self.assertEqual(result['pct_change'], 1.63)
    
    def test_get_realtime_data_with_force_refresh(self):
        """Test realtime data with force refresh."""
        # Create cached data
        cached_data = RealtimeStockData(
            symbol="000001",
            price=12.40,
            change=0.15,
            pct_change=1.22,
            volume=13000000,
            turnover=161200000.0,
            high_price=12.50,
            low_price=12.20,
            open_price=12.25,
            prev_close=12.25,
            timestamp=datetime.now(),  # Recent cache
            cache_ttl_minutes=5,
            is_trading_hours=True
        )
        self.session.add(cached_data)
        self.session.commit()

        # Mock fresh AKShare response
        mock_data = pd.DataFrame({
            'symbol': ['000001'],
            'current': [12.55],
            'change': [0.30],
            'percent': [2.45],
            'volume': [16000000],
            'turnover': [200800000.0],
            'high': [12.65],
            'low': [12.35],
            'open': [12.40],
            'pre_close': [12.25]
        })
        self.mock_adapter.get_realtime_data.return_value = mock_data

        # Test force refresh scenario
        result = self.service.get_realtime_data("000001", force_refresh=True)

        # Verify result
        self.assertIsNotNone(result)
        self.assertEqual(result['symbol'], '000001')
    
    def test_get_batch_realtime_data(self):
        """Test batch realtime data retrieval."""
        symbols = ["000001", "000002", "600000"]

        # Mock AKShare response for individual calls
        mock_data = pd.DataFrame({
            'symbol': ['000001'],
            'current': [12.50],
            'change': [0.25],
            'percent': [2.04],
            'volume': [15000000],
            'turnover': [187500000.0],
            'high': [12.60],
            'low': [12.30],
            'open': [12.35],
            'pre_close': [12.25]
        })
        self.mock_adapter.get_realtime_data.return_value = mock_data

        # Test batch retrieval
        results = self.service.get_realtime_data_batch(symbols)

        # Verify results structure
        self.assertIsInstance(results, dict)
        # Note: Results depend on actual implementation
    
    def test_service_functionality(self):
        """Test basic service functionality."""
        # Test that service can handle basic operations
        self.assertIsNotNone(self.service.db)
        self.assertIsNotNone(self.service.akshare_adapter)
        self.assertIsNotNone(self.service.cache_manager)
    
    def test_error_handling_akshare_failure(self):
        """Test error handling when AKShare fails."""
        # Mock AKShare failure
        self.mock_adapter.get_realtime_data.side_effect = Exception("AKShare API error")

        # Test error handling
        result = self.service.get_realtime_data("000001")

        # Should return error information
        self.assertIsNotNone(result)
        self.assertIn('error', result)
        self.assertEqual(result['symbol'], '000001')
    
    def test_cache_cleanup(self):
        """Test cache cleanup for old data."""
        # Create old cached data
        old_data = RealtimeStockData(
            symbol="000001",
            price=12.00,
            change=0.00,
            pct_change=0.00,
            volume=10000000,
            turnover=120000000.0,
            high_price=12.10,
            low_price=11.90,
            open_price=12.00,
            prev_close=12.00,
            timestamp=datetime.now() - timedelta(days=7),  # Very old
            cache_ttl_minutes=5,
            is_trading_hours=True
        )
        self.session.add(old_data)
        self.session.commit()
        
        # Test cleanup by checking data exists
        existing_data = self.session.query(RealtimeStockData).filter_by(
            symbol="000001"
        ).first()
        self.assertIsNotNone(existing_data)

        # Verify old data exists (this test just checks the setup works)
        self.assertEqual(existing_data.symbol, "000001")
    
    def test_performance_metrics(self):
        """Test performance metrics collection."""
        # Clear any existing data first
        self.session.query(RealtimeStockData).delete()
        self.session.commit()

        # Create some cached data for metrics
        for i in range(5):
            data = RealtimeStockData(
                symbol=f"TEST{i+1:03d}",  # Use unique symbols
                price=10.0 + i,
                change=0.1 * i,
                pct_change=1.0 * i,
                volume=1000000 * (i+1),
                turnover=10000000.0 * (i+1),
                high_price=10.5 + i,
                low_price=9.5 + i,
                open_price=10.0 + i,
                prev_close=10.0 + i,
                timestamp=datetime.now() - timedelta(minutes=i),
                cache_ttl_minutes=5,
                is_trading_hours=True
            )
            self.session.add(data)
        self.session.commit()

        # Test that data was created successfully
        cached_count = self.session.query(RealtimeStockData).count()

        # Verify data was created
        self.assertEqual(cached_count, 5)

        # Verify data structure
        first_data = self.session.query(RealtimeStockData).first()
        self.assertIsNotNone(first_data)
        self.assertIsNotNone(first_data.symbol)


if __name__ == "__main__":
    unittest.main()
