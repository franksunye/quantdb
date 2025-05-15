# tests/test_data_import.py
"""
Tests for the data import service
"""
import os
import tempfile
import unittest
import pandas as pd
from unittest.mock import MagicMock, patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.api.database import Base
from src.api.models import Asset, Price
from src.services.data_import import DataImportService
from src.cache.cache_engine import CacheEngine
from src.cache.freshness_tracker import FreshnessTracker
from src.cache.akshare_adapter import AKShareAdapter


class TestDataImportService(unittest.TestCase):
    """Tests for the DataImportService class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create an in-memory SQLite database for testing
        self.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool
        )

        # Create tables
        Base.metadata.create_all(self.engine)

        # Create session
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.db = TestingSessionLocal()

        # Create mock cache components
        self.mock_cache_engine = MagicMock(spec=CacheEngine)
        self.mock_freshness_tracker = MagicMock(spec=FreshnessTracker)
        self.mock_akshare_adapter = MagicMock(spec=AKShareAdapter)

        # Create data import service with mock components
        self.import_service = DataImportService(
            db=self.db,
            cache_engine=self.mock_cache_engine,
            freshness_tracker=self.mock_freshness_tracker,
            akshare_adapter=self.mock_akshare_adapter
        )

    def tearDown(self):
        """Tear down test fixtures."""
        self.db.close()

    def test_import_asset(self):
        """Test importing an asset."""
        # Import an asset
        asset = self.import_service.import_asset(
            symbol="AAPL",
            name="Apple Inc.",
            isin="US0378331005",
            asset_type="stock",
            exchange="NASDAQ",
            currency="USD"
        )

        # Check that the asset was imported correctly
        self.assertEqual(asset.symbol, "AAPL")
        self.assertEqual(asset.name, "Apple Inc.")
        self.assertEqual(asset.isin, "US0378331005")
        self.assertEqual(asset.asset_type, "stock")
        self.assertEqual(asset.exchange, "NASDAQ")
        self.assertEqual(asset.currency, "USD")

        # Check that the asset is in the database
        db_asset = self.db.query(Asset).filter(Asset.symbol == "AAPL").first()
        self.assertIsNotNone(db_asset)
        self.assertEqual(db_asset.symbol, "AAPL")

    def test_import_price_data(self):
        """Test importing price data."""
        # Import an asset
        asset = self.import_service.import_asset(
            symbol="AAPL",
            name="Apple Inc.",
            isin="US0378331005",
            asset_type="stock",
            exchange="NASDAQ",
            currency="USD"
        )

        # Create sample price data
        price_data = [
            {
                "date": "2023-01-01",
                "open": 100.0,
                "high": 105.0,
                "low": 99.0,
                "close": 102.0,
                "volume": 1000000,
                "adjusted_close": 102.0
            },
            {
                "date": "2023-01-02",
                "open": 102.0,
                "high": 107.0,
                "low": 101.0,
                "close": 105.0,
                "volume": 1200000,
                "adjusted_close": 105.0
            }
        ]

        # Import price data
        imported_prices = self.import_service.import_price_data(asset.asset_id, price_data)

        # Check that the price data was imported correctly
        self.assertEqual(len(imported_prices), 2)

        # Check that the price data is in the database
        db_prices = self.db.query(Price).filter(Price.asset_id == asset.asset_id).all()
        self.assertEqual(len(db_prices), 2)

        # Check the values of the first price entry
        first_price = db_prices[0]
        self.assertEqual(first_price.date.isoformat(), "2023-01-01")
        self.assertEqual(first_price.open, 100.0)
        self.assertEqual(first_price.high, 105.0)
        self.assertEqual(first_price.low, 99.0)
        self.assertEqual(first_price.close, 102.0)
        self.assertEqual(first_price.volume, 1000000)
        self.assertEqual(first_price.adjusted_close, 102.0)

    @patch('pandas.read_csv')
    def test_import_from_csv(self, mock_read_csv):
        """Test importing price data from a CSV file."""
        # Import an asset
        asset = self.import_service.import_asset(
            symbol="AAPL",
            name="Apple Inc.",
            isin="US0378331005",
            asset_type="stock",
            exchange="NASDAQ",
            currency="USD"
        )

        # Create a mock DataFrame
        mock_df = pd.DataFrame([
            {
                "date": "2023-01-01",
                "open": 100.0,
                "high": 105.0,
                "low": 99.0,
                "close": 102.0,
                "volume": 1000000,
                "adjusted_close": 102.0
            }
        ])

        # Configure the mock to return the DataFrame
        mock_read_csv.return_value = mock_df

        # Mock the cache engine generate_key method
        self.mock_cache_engine.generate_key.return_value = "test_cache_key"

        # Create a temporary file
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as temp_file:
            temp_file_path = temp_file.name

        try:
            # Import from CSV
            result = self.import_service.import_from_csv(
                file_path=temp_file_path,
                asset_id=asset.asset_id
            )

            # Check that the import was successful
            self.assertEqual(result["asset_id"], asset.asset_id)
            self.assertEqual(result["file_path"], temp_file_path)
            self.assertEqual(result["records_imported"], 1)
            self.assertEqual(result["cache_key"], "test_cache_key")

            # Check that the cache methods were called
            self.mock_cache_engine.generate_key.assert_called_once()
            self.mock_cache_engine.set.assert_called_once()
            self.mock_freshness_tracker.mark_updated.assert_called_once()

        finally:
            # Clean up the temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    def test_import_from_akshare(self):
        """Test importing stock data from AKShare."""
        # Import an asset
        self.import_service.import_asset(
            symbol="000001",
            name="平安银行",
            isin="CNE000000040",
            asset_type="stock",
            exchange="SZSE",
            currency="CNY"
        )

        # Create a mock DataFrame
        mock_df = pd.DataFrame([
            {
                "date": "2023-01-01",
                "open": 10.0,
                "high": 10.5,
                "low": 9.8,
                "close": 10.2,
                "volume": 100000
            }
        ])

        # Configure the mock cache engine get method to return None (cache miss)
        self.mock_cache_engine.get.return_value = None

        # Configure the mock to return the DataFrame
        self.mock_akshare_adapter.get_stock_data.return_value = mock_df

        # Import from AKShare
        self.import_service.import_from_akshare(
            symbol="000001",
            start_date="20230101",
            end_date="20230101"
        )

        # Check that the AKShare adapter was called
        self.mock_akshare_adapter.get_stock_data.assert_called_once_with(
            symbol="000001",
            start_date="20230101",
            end_date="20230101",
            use_mock_data=False
        )




if __name__ == "__main__":
    unittest.main()
