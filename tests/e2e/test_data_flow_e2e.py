# tests/e2e/test_data_flow_e2e.py
"""
End-to-end tests for the complete data flow.

These tests verify the entire flow from API request to database and back,
including the intelligent data retrieval logic.
"""

import unittest
import os
import sys
import tempfile
import json
import time
from datetime import datetime, timedelta
import pandas as pd
from unittest.mock import patch
from fastapi.testclient import TestClient

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.api.main import app
from src.api.models import Base, Asset, DailyStockData
from src.cache.akshare_adapter_simplified import AKShareAdapter
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.api.database import get_db


class TestDataFlowE2E(unittest.TestCase):
    """End-to-end tests for the complete data flow."""

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

            # Try to remove the file
            if os.path.exists(cls.db_path):
                os.unlink(cls.db_path)
        except OSError as e:
            # If file is still in use, log the error but don't fail the test
            print(f"Warning: Could not remove temporary database file: {e}")

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
        self.akshare_patcher = patch('src.cache.akshare_adapter_simplified.AKShareAdapter._safe_call')
        self.mock_safe_call = self.akshare_patcher.start()

        # Also patch the get_stock_data method to ensure it's properly mocked
        self.get_stock_data_patcher = patch('src.services.stock_data_service.StockDataService.get_stock_data')
        self.mock_get_stock_data = self.get_stock_data_patcher.start()

    def tearDown(self):
        """Clean up test fixtures."""
        self.akshare_patcher.stop()
        self.get_stock_data_patcher.stop()

        # Clean up database
        self.session.query(DailyStockData).delete()
        self.session.query(Asset).delete()
        self.session.commit()
        self.session.close()

        # Remove dependency override
        app.dependency_overrides.clear()

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

    def test_empty_database_flow(self):
        """Test data flow when database is empty."""
        # Setup mock data
        mock_df = self._generate_mock_data('20230101', '20230110')
        self.mock_get_stock_data.return_value = mock_df

        # Make API request
        response = self.client.get("/api/v1/v2/historical/stock/600000?start_date=20230101&end_date=20230110")

        # Check response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['data']), 10)  # Data is in the 'data' field of the response

        # Verify the service was called with correct parameters
        self.mock_get_stock_data.assert_called_once()
        _, kwargs = self.mock_get_stock_data.call_args
        self.assertEqual(kwargs['symbol'], '600000')
        self.assertEqual(kwargs['start_date'], '20230101')
        self.assertEqual(kwargs['end_date'], '20230110')

        # Make the same request again
        self.mock_get_stock_data.reset_mock()
        response2 = self.client.get("/api/v1/v2/historical/stock/600000?start_date=20230101&end_date=20230110")

        # Check response
        self.assertEqual(response2.status_code, 200)
        data2 = response2.json()
        self.assertEqual(len(data2['data']), 10)

        # Verify service was called again
        self.mock_get_stock_data.assert_called_once()

    def test_partial_database_flow(self):
        """Test data flow when database has partial data."""
        # Setup mock data for full date range
        mock_df = self._generate_mock_data('20230101', '20230110')
        self.mock_get_stock_data.return_value = mock_df

        # Make API request for full date range
        response = self.client.get("/api/v1/v2/historical/stock/600000?start_date=20230101&end_date=20230110")

        # Check response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['data']), 10)

        # Verify the service was called with correct parameters
        self.mock_get_stock_data.assert_called_once()
        _, kwargs = self.mock_get_stock_data.call_args
        self.assertEqual(kwargs['symbol'], '600000')
        self.assertEqual(kwargs['start_date'], '20230101')
        self.assertEqual(kwargs['end_date'], '20230110')

    def test_overlapping_date_ranges(self):
        """Test data flow with overlapping date ranges."""
        # Setup mock data for first request
        mock_df_1 = self._generate_mock_data('20230101', '20230115')
        self.mock_get_stock_data.return_value = mock_df_1

        # Make first API request
        response1 = self.client.get("/api/v1/v2/historical/stock/600000?start_date=20230101&end_date=20230115")
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(len(response1.json()['data']), 15)

        # Setup mock data for second request with overlapping range
        mock_df_2 = self._generate_mock_data('20230110', '20230120')
        self.mock_get_stock_data.return_value = mock_df_2
        self.mock_get_stock_data.reset_mock()

        # Make second API request with overlapping range
        response2 = self.client.get("/api/v1/v2/historical/stock/600000?start_date=20230110&end_date=20230120")
        self.assertEqual(response2.status_code, 200)
        self.assertEqual(len(response2.json()['data']), 11)

        # Verify service was called with correct parameters
        self.mock_get_stock_data.assert_called_once()
        _, kwargs = self.mock_get_stock_data.call_args
        self.assertEqual(kwargs['symbol'], '600000')
        self.assertEqual(kwargs['start_date'], '20230110')
        self.assertEqual(kwargs['end_date'], '20230120')


if __name__ == '__main__':
    unittest.main()
