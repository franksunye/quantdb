# tests/test_mcp_cache.py
"""
Tests for the MCP interpreter with simplified architecture
"""
import unittest
from unittest.mock import MagicMock, patch
import json
import asyncio
from datetime import datetime, date, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.api.database import Base
from src.api.models import Asset, Price
from src.mcp.interpreter import MCPInterpreter
from src.mcp.schemas import MCPRequest, MCPResponse
from src.cache.akshare_adapter import AKShareAdapter

class TestMCPCache(unittest.TestCase):
    """Tests for the MCP interpreter with simplified architecture."""

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

        # Create mock AKShare adapter
        self.mock_akshare_adapter = MagicMock(spec=AKShareAdapter)

        # Create MCP interpreter with mock components
        self.interpreter = MCPInterpreter(
            db=self.db,
            akshare_adapter=self.mock_akshare_adapter
        )

        # Add test data
        self._add_test_data()

    def tearDown(self):
        """Tear down test fixtures."""
        self.db.close()

    def _add_test_data(self):
        """Add test data to the database."""
        # Add a test asset
        asset = Asset(
            symbol="AAPL",
            name="Apple Inc.",
            isin="US0378331005",
            asset_type="stock",
            exchange="NASDAQ",
            currency="USD"
        )
        self.db.add(asset)
        self.db.commit()

        # Add test price data
        today = date.today()
        for i in range(10):
            price_date = today - timedelta(days=i)
            price = Price(
                asset_id=asset.asset_id,
                date=price_date,
                open=100.0 + i,
                high=105.0 + i,
                low=99.0 + i,
                close=102.0 + i,
                volume=1000000 + i * 10000,
                adjusted_close=102.0 + i
            )
            self.db.add(price)

        self.db.commit()

    def test_get_price_from_database(self):
        """Test get_price intent with data from database."""
        # Create a test request
        request = MCPRequest(
            query="What is the price of AAPL?",
            session_id="test_session",
            context={}
        )

        # Process the request using asyncio.run
        response = asyncio.run(self.interpreter.process_request(request))

        # Check that the response is correct
        self.assertEqual(response.intent, "get_price")
        self.assertIn("prices", response.data)
        self.assertEqual(len(response.data["prices"]), 10)

        # Verify the AKShare adapter was not called (data was in database)
        self.mock_akshare_adapter.get_stock_data.assert_not_called()

    def test_get_price_akshare_fallback(self):
        """Test get_price intent with AKShare fallback."""
        # Configure database to return no data
        self.db.query(Price).delete()
        self.db.commit()

        # Configure mock AKShare adapter to return data
        import pandas as pd
        today = date.today()
        dates = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(10)]
        mock_df = pd.DataFrame({
            "date": dates,
            "open": [100.0 + i for i in range(10)],
            "high": [105.0 + i for i in range(10)],
            "low": [99.0 + i for i in range(10)],
            "close": [102.0 + i for i in range(10)],
            "volume": [1000000 + i * 10000 for i in range(10)]
        })
        self.mock_akshare_adapter.get_stock_data.return_value = mock_df

        # Create a test request
        request = MCPRequest(
            query="What is the price of AAPL?",
            session_id="test_session",
            context={}
        )

        # Process the request using asyncio.run
        response = asyncio.run(self.interpreter.process_request(request))

        # Check that the response is correct
        self.assertEqual(response.intent, "get_price")
        self.assertIn("prices", response.data)

        # Check that AKShare was called
        self.mock_akshare_adapter.get_stock_data.assert_called_once()

if __name__ == "__main__":
    unittest.main()
