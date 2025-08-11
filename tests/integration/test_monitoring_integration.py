# tests/integration/test_monitoring_integration.py
"""
Integration tests for the monitoring system.

These tests verify the integration between MonitoringService, MonitoringMiddleware,
and the database layer.
"""

import asyncio
import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.models import Asset, Base, DailyStockData, DataCoverage, RequestLog
from core.services.monitoring_middleware import RequestMonitor, monitor_stock_request
from core.services.monitoring_service import MonitoringService


class TestMonitoringIntegration(unittest.TestCase):
    """Integration tests for the monitoring system."""

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
            pass

        try:
            import time
            time.sleep(0.1)
            if os.path.exists(cls.db_path):
                os.unlink(cls.db_path)
        except OSError as e:
            print(f"Warning: Could not remove temporary database file: {e}")

    def setUp(self):
        """Set up test fixtures."""
        self.session = self.Session()
        self.monitoring_service = MonitoringService(self.session)
        self.request_monitor = RequestMonitor(self.session)

    def tearDown(self):
        """Clean up test fixtures."""
        # Clean up database
        self.session.query(RequestLog).delete()
        self.session.query(DataCoverage).delete()
        self.session.query(DailyStockData).delete()
        self.session.query(Asset).delete()
        self.session.commit()
        self.session.close()

    def test_end_to_end_monitoring_flow(self):
        """Test complete monitoring flow from request to database."""
        # Create test asset and data
        asset = Asset(
            symbol='600000',
            name='Test Stock',
            isin='CN600000',
            asset_type='stock',
            exchange='CN',
            currency='CNY'
        )
        self.session.add(asset)
        self.session.commit()

        # Add some stock data
        for i in range(5):
            stock_data = DailyStockData(
                asset_id=asset.asset_id,
                trade_date=datetime(2023, 1, 1 + i).date(),
                open=100.0 + i,
                high=105.0 + i,
                low=99.0 + i,
                close=101.0 + i,
                volume=1000 + i * 100,
                turnover=101000.0 + i * 10000,
                amplitude=6.0,
                pct_change=1.0,
                change=1.0,
                turnover_rate=0.5
            )
            self.session.add(stock_data)
        self.session.commit()

        # Log a request
        self.monitoring_service.log_request(
            symbol="600000",
            start_date="20230101",
            end_date="20230105",
            endpoint="/api/v1/historical/stock/600000",
            response_time_ms=150.5,
            status_code=200,
            record_count=5,
            cache_hit=True,
            akshare_called=False,
            cache_hit_ratio=1.0,
            user_agent="test-agent",
            ip_address="127.0.0.1"
        )

        # Verify request log was created
        request_logs = self.session.query(RequestLog).all()
        self.assertEqual(len(request_logs), 1)
        
        log = request_logs[0]
        self.assertEqual(log.symbol, "600000")
        self.assertEqual(log.response_time_ms, 150.5)
        self.assertEqual(log.record_count, 5)
        self.assertTrue(log.cache_hit)

        # Verify data coverage was updated
        coverage = self.session.query(DataCoverage).filter(
            DataCoverage.symbol == "600000"
        ).first()
        self.assertIsNotNone(coverage)
        self.assertEqual(coverage.total_records, 5)
        self.assertEqual(coverage.access_count, 1)

        # Test water pool status
        status = self.monitoring_service.get_water_pool_status()
        self.assertEqual(status["water_pool"]["total_symbols"], 1)
        self.assertEqual(status["water_pool"]["total_records"], 5)
        self.assertEqual(status["today_performance"]["total_requests"], 1)
        self.assertEqual(status["today_performance"]["cache_hits"], 1)

    def test_multiple_requests_monitoring(self):
        """Test monitoring multiple requests over time."""
        # Create test asset
        asset = Asset(
            symbol='000001',
            name='Test Stock 2',
            isin='CN000001',
            asset_type='stock',
            exchange='CN',
            currency='CNY'
        )
        self.session.add(asset)
        self.session.commit()

        # Log multiple requests
        requests_data = [
            {"cache_hit": True, "akshare_called": False, "response_time": 50.0},
            {"cache_hit": False, "akshare_called": True, "response_time": 200.0},
            {"cache_hit": True, "akshare_called": False, "response_time": 45.0},
            {"cache_hit": False, "akshare_called": True, "response_time": 180.0},
        ]

        for i, req_data in enumerate(requests_data):
            self.monitoring_service.log_request(
                symbol="000001",
                start_date="20230101",
                end_date="20230102",
                endpoint="/api/v1/historical/stock/000001",
                response_time_ms=req_data["response_time"],
                status_code=200,
                record_count=2,
                cache_hit=req_data["cache_hit"],
                akshare_called=req_data["akshare_called"],
                cache_hit_ratio=1.0 if req_data["cache_hit"] else 0.0
            )

        # Verify all requests were logged
        request_logs = self.session.query(RequestLog).all()
        self.assertEqual(len(request_logs), 4)

        # Test performance trends
        trends = self.monitoring_service.get_performance_trends(days=1)
        self.assertIn("trends", trends)
        
        if trends["trends"]:  # If there are trends (depends on date grouping)
            trend = trends["trends"][0]
            self.assertEqual(trend["total_requests"], 4)
            self.assertEqual(trend["akshare_calls"], 2)
            self.assertEqual(trend["cache_hit_rate"], "50.0%")

    def test_request_monitor_integration(self):
        """Test RequestMonitor integration with database."""
        # Create mock request
        mock_request = MagicMock()
        mock_request.headers = {"user-agent": "test-browser"}
        mock_request.client.host = "192.168.1.1"

        # Log request using RequestMonitor
        self.request_monitor.log_stock_request(
            symbol="600519",
            start_date="20230101",
            end_date="20230103",
            endpoint="/api/v1/historical/stock/600519",
            response_time_ms=75.0,
            status_code=200,
            record_count=3,
            cache_hit=False,
            akshare_called=True,
            cache_hit_ratio=0.0,
            request=mock_request
        )

        # Verify request was logged
        request_logs = self.session.query(RequestLog).all()
        self.assertEqual(len(request_logs), 1)
        
        log = request_logs[0]
        self.assertEqual(log.symbol, "600519")
        self.assertEqual(log.user_agent, "test-browser")
        self.assertEqual(log.ip_address, "192.168.1.1")

    def test_decorator_integration(self):
        """Test monitor_stock_request decorator integration."""
        # Create a database getter function
        def get_db():
            yield self.session

        # Create test function
        @monitor_stock_request(get_db)
        async def test_api_function(symbol, start_date, end_date, request=None):
            return {
                "data": [
                    {"date": "20230101", "price": 100},
                    {"date": "20230102", "price": 101}
                ],
                "metadata": {
                    "cache_info": {
                        "cache_hit": True,
                        "akshare_called": False,
                        "cache_hit_ratio": 1.0
                    }
                }
            }

        # Run the decorated function
        result = asyncio.run(test_api_function(
            symbol="300001",
            start_date="20230101",
            end_date="20230102"
        ))

        # Verify function result
        self.assertIn("data", result)
        self.assertEqual(len(result["data"]), 2)

        # Verify monitoring was performed
        request_logs = self.session.query(RequestLog).all()
        self.assertEqual(len(request_logs), 1)
        
        log = request_logs[0]
        self.assertEqual(log.symbol, "300001")
        self.assertEqual(log.record_count, 2)
        self.assertTrue(log.cache_hit)

    def test_error_handling_integration(self):
        """Test error handling in monitoring integration."""
        # Create a database getter function
        def get_db():
            yield self.session

        # Create test function that raises an error
        @monitor_stock_request(get_db)
        async def failing_api_function(symbol, start_date, end_date, request=None):
            raise ValueError("Simulated API error")

        # Run the decorated function and expect exception
        with self.assertRaises(ValueError):
            asyncio.run(failing_api_function(
                symbol="400001",
                start_date="20230101",
                end_date="20230102"
            ))

        # Verify error was logged
        request_logs = self.session.query(RequestLog).all()
        self.assertEqual(len(request_logs), 1)
        
        log = request_logs[0]
        self.assertEqual(log.symbol, "400001")
        self.assertEqual(log.status_code, 500)
        self.assertEqual(log.record_count, 0)

    def test_data_coverage_accumulation(self):
        """Test data coverage accumulation over multiple requests."""
        # Create test asset
        asset = Asset(
            symbol='002001',
            name='Test Stock 3',
            isin='CN002001',
            asset_type='stock',
            exchange='CN',
            currency='CNY'
        )
        self.session.add(asset)
        self.session.commit()

        # Add initial stock data
        for i in range(3):
            stock_data = DailyStockData(
                asset_id=asset.asset_id,
                trade_date=datetime(2023, 1, 1 + i).date(),
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

        # Log first request
        self.monitoring_service.log_request(
            symbol="002001",
            start_date="20230101",
            end_date="20230103",
            endpoint="/api/v1/historical/stock/002001",
            response_time_ms=100.0,
            status_code=200,
            record_count=3,
            cache_hit=False,
            akshare_called=True
        )

        # Verify initial coverage
        coverage = self.session.query(DataCoverage).filter(
            DataCoverage.symbol == "002001"
        ).first()
        self.assertEqual(coverage.access_count, 1)
        self.assertEqual(coverage.total_records, 3)

        # Add more stock data
        for i in range(3, 6):
            stock_data = DailyStockData(
                asset_id=asset.asset_id,
                trade_date=datetime(2023, 1, 1 + i).date(),
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

        # Log second request
        self.monitoring_service.log_request(
            symbol="002001",
            start_date="20230104",
            end_date="20230106",
            endpoint="/api/v1/historical/stock/002001",
            response_time_ms=120.0,
            status_code=200,
            record_count=3,
            cache_hit=False,
            akshare_called=True
        )

        # Verify updated coverage
        coverage = self.session.query(DataCoverage).filter(
            DataCoverage.symbol == "002001"
        ).first()
        self.assertEqual(coverage.access_count, 2)
        self.assertEqual(coverage.total_records, 6)
        self.assertEqual(coverage.earliest_date, "20230101")
        self.assertEqual(coverage.latest_date, "20230106")


if __name__ == '__main__':
    unittest.main()
