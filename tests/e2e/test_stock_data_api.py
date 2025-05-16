# tests/e2e/test_stock_data_api.py
"""
End-to-end tests for the stock data API.

These tests verify the entire flow from API request to database and back.
"""

import unittest
from unittest.mock import patch
import os
import sys
import tempfile
import json
from datetime import datetime, timedelta
import pandas as pd
from fastapi.testclient import TestClient

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.api.main import app
from src.api.models import Base, Asset, DailyStockData
from src.cache.akshare_adapter_simplified import AKShareAdapter
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.api.database import get_db


class TestStockDataAPI(unittest.TestCase):
    """End-to-end tests for the stock data API."""

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

        # Override the get_db dependency
        def override_get_db():
            try:
                yield self.session
            finally:
                pass

        app.dependency_overrides[get_db] = override_get_db

        # Create test client
        self.client = TestClient(app)

        # Mock AKShare API call
        self.akshare_patcher = patch('akshare.stock_zh_a_hist')
        self.mock_stock_zh_a_hist = self.akshare_patcher.start()

    def tearDown(self):
        """Clean up test fixtures."""
        self.akshare_patcher.stop()

        # Clean up database
        self.session.query(DailyStockData).delete()
        self.session.query(Asset).delete()
        self.session.commit()
        self.session.close()

        # Remove dependency override
        app.dependency_overrides.clear()

    def test_get_stock_data_empty_database(self):
        """Test getting stock data when database is empty."""
        # Setup mock data
        mock_df = pd.DataFrame({
            'date': pd.to_datetime(['2023-01-01', '2023-01-02']),
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
        self.mock_stock_zh_a_hist.return_value = mock_df

        # Make API request
        response = self.client.get("/api/v1/historical/stock/600000?start_date=20230101&end_date=20230102")

        # Check response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["symbol"], "600000")
        self.assertEqual(len(data["data"]), 2)
        self.assertEqual(data["data"][0]["open"], 100.0)
        self.assertEqual(data["data"][1]["close"], 102.0)

        # Verify data was saved to database
        assets = self.session.query(Asset).all()
        self.assertEqual(len(assets), 1)
        self.assertEqual(assets[0].symbol, "600000")

        stock_data = self.session.query(DailyStockData).all()
        self.assertEqual(len(stock_data), 2)

        # Make the same request again - should use database cache
        self.mock_stock_zh_a_hist.reset_mock()
        response2 = self.client.get("/api/v1/historical/stock/600000?start_date=20230101&end_date=20230102")

        # Check response
        self.assertEqual(response2.status_code, 200)
        data2 = response2.json()
        self.assertEqual(len(data2["data"]), 2)

        # Verify AKShare was not called
        self.mock_stock_zh_a_hist.assert_not_called()

    def test_get_stock_data_partial_database(self):
        """Test getting stock data when database has partial data."""
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

        # Create stock data for first day
        stock_data = DailyStockData(
            asset_id=asset.asset_id,
            trade_date=datetime(2023, 1, 1).date(),
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

        # Setup mock data for second day
        mock_df = pd.DataFrame({
            'date': pd.to_datetime(['2023-01-02']),
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
        self.mock_stock_zh_a_hist.return_value = mock_df

        # Make API request
        response = self.client.get("/api/v1/historical/stock/600000?start_date=20230101&end_date=20230102")

        # Check response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["symbol"], "600000")
        self.assertEqual(len(data["data"]), 2)

        # Verify AKShare was called
        self.mock_stock_zh_a_hist.assert_called_once()

        # Verify data was saved to database
        stock_data = self.session.query(DailyStockData).all()
        self.assertEqual(len(stock_data), 2)

    def test_get_stock_data_invalid_symbol(self):
        """Test getting stock data with invalid symbol."""
        # Make API request with invalid symbol
        response = self.client.get("/api/v1/historical/stock/60000?start_date=20230101&end_date=20230102")

        # Check response
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("detail", data)
        self.assertIn("Symbol must be a 6-digit number", data["detail"])

    def test_get_stock_data_invalid_date(self):
        """Test getting stock data with invalid date."""
        # Make API request with invalid date
        response = self.client.get("/api/v1/historical/stock/600000?start_date=2023-01-01&end_date=20230102")

        # Check response
        self.assertEqual(response.status_code, 500)
        data = response.json()
        self.assertIn("detail", data)
        self.assertIn("Invalid date format", data["detail"])

    def test_get_stock_data_empty_response(self):
        """Test getting stock data with empty response from AKShare."""
        # Setup mock data
        self.mock_stock_zh_a_hist.return_value = pd.DataFrame()

        # Make API request
        response = self.client.get("/api/v1/historical/stock/600000?start_date=20230101&end_date=20230102")

        # Check response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["symbol"], "600000")
        self.assertEqual(len(data["data"]), 0)
        self.assertEqual(data["metadata"]["count"], 0)
        self.assertEqual(data["metadata"]["status"], "success")
        self.assertIn("No data found", data["metadata"]["message"])

    def test_get_database_cache_status(self):
        """Test getting database cache status."""
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

        # Create stock data
        for day in range(1, 6):
            stock_data = DailyStockData(
                asset_id=asset.asset_id,
                trade_date=datetime(2023, 1, day).date(),
                open=100.0 + day,
                high=105.0 + day,
                low=99.0 + day,
                close=101.0 + day,
                volume=1000 + day * 100,
                turnover=101000.0 + day * 10000,
                amplitude=6.0 - day * 0.1,
                pct_change=1.0,
                change=1.0,
                turnover_rate=0.5 + day * 0.01
            )
            self.session.add(stock_data)
        self.session.commit()

        # Make API request for specific symbol and date range
        response = self.client.get("/api/v1/database/cache/status?symbol=600000&start_date=20230101&end_date=20230110")

        # Check response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["symbol"], "600000")
        self.assertEqual(data["start_date"], "20230101")
        self.assertEqual(data["end_date"], "20230110")
        self.assertEqual(data["coverage"]["covered_dates"], 5)
        self.assertEqual(data["coverage"]["total_dates"], 10)
        self.assertEqual(data["coverage"]["coverage"], 0.5)

        # Make API request for general stats
        response = self.client.get("/api/v1/database/cache/status")

        # Check response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["total_assets"], 1)
        self.assertEqual(data["total_data_points"], 5)
        self.assertIn("date_range", data)
        self.assertIn("top_assets", data)
        self.assertEqual(len(data["top_assets"]), 1)
        self.assertEqual(data["top_assets"][0]["symbol"], "600000")
        self.assertEqual(data["top_assets"][0]["data_points"], 5)


if __name__ == '__main__':
    unittest.main()
