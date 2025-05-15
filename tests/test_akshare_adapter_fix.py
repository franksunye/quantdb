#!/usr/bin/env python
# tests/test_akshare_adapter_fix.py
"""
Test script for the fixed AKShare adapter.

This script tests the AKShare adapter's ability to retrieve real data
from various sources and with different parameters.
"""

import os
import sys
import unittest
from datetime import datetime, timedelta

import pandas as pd

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.cache.cache_engine import CacheEngine
from src.cache.freshness_tracker import FreshnessTracker
from src.cache.akshare_adapter import AKShareAdapter
from src.logger import setup_logger

# Setup logger
logger = setup_logger(__name__)


class TestAKShareAdapterFix(unittest.TestCase):
    """Tests for the fixed AKShareAdapter class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Initialize cache engine and freshness tracker
        self.cache_engine = CacheEngine()
        self.freshness_tracker = FreshnessTracker()
        
        # Initialize AKShare adapter with the cache engine and freshness tracker
        self.adapter = AKShareAdapter(
            cache_engine=self.cache_engine,
            freshness_tracker=self.freshness_tracker
        )
        
        # Clear the cache to ensure a fresh start
        self.cache_engine.clear()
    
    def test_get_stock_data_with_valid_symbol(self):
        """Test getting stock data with a valid symbol."""
        # Define test parameters
        symbol = "000001"  # 平安银行
        end_date = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")
        
        # Get stock data
        try:
            df = self.adapter.get_stock_data(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date
            )
            
            # Check that the result is a DataFrame
            self.assertIsInstance(df, pd.DataFrame)
            
            # Check that the DataFrame is not empty
            self.assertFalse(df.empty)
            
            # Check that the DataFrame has the expected columns
            expected_columns = ['date', 'open', 'high', 'low', 'close', 'volume']
            for col in expected_columns:
                self.assertIn(col, df.columns)
            
            # Check that the date range is correct
            if not df.empty:
                min_date = pd.to_datetime(df['date'].min())
                max_date = pd.to_datetime(df['date'].max())
                expected_min_date = pd.to_datetime(start_date, format="%Y%m%d")
                expected_max_date = pd.to_datetime(end_date, format="%Y%m%d")
                
                # Allow for some flexibility in the date range due to weekends and holidays
                self.assertLessEqual((expected_min_date - min_date).days, 7)
                self.assertLessEqual((max_date - expected_max_date).days, 7)
            
            # Print some information about the retrieved data
            logger.info(f"Retrieved {len(df)} rows of data for {symbol}")
            if not df.empty:
                logger.info(f"Date range: {df['date'].min()} to {df['date'].max()}")
                logger.info(f"First few rows:\n{df.head()}")
        
        except Exception as e:
            self.fail(f"get_stock_data raised an exception: {e}")
    
    def test_get_stock_data_with_different_periods(self):
        """Test getting stock data with different periods."""
        # Define test parameters
        symbol = "000001"  # 平安银行
        end_date = datetime.now().strftime("%Y%m%d")
        
        # Test different periods
        periods = ["daily", "weekly", "monthly"]
        
        for period in periods:
            # Adjust start date based on period to get a reasonable amount of data
            if period == "daily":
                start_date = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")
            elif period == "weekly":
                start_date = (datetime.now() - timedelta(days=90)).strftime("%Y%m%d")
            else:  # monthly
                start_date = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")
            
            # Get stock data
            try:
                df = self.adapter.get_stock_data(
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date,
                    period=period
                )
                
                # Check that the result is a DataFrame
                self.assertIsInstance(df, pd.DataFrame)
                
                # Check that the DataFrame is not empty
                self.assertFalse(df.empty)
                
                # Print some information about the retrieved data
                logger.info(f"Retrieved {len(df)} rows of {period} data for {symbol}")
                if not df.empty:
                    logger.info(f"Date range: {df['date'].min()} to {df['date'].max()}")
                    logger.info(f"First few rows:\n{df.head()}")
            
            except Exception as e:
                self.fail(f"get_stock_data with period={period} raised an exception: {e}")
    
    def test_get_stock_data_with_price_adjustments(self):
        """Test getting stock data with different price adjustments."""
        # Define test parameters
        symbol = "000001"  # 平安银行
        end_date = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")
        
        # Test different adjustments
        adjustments = ["", "qfq", "hfq"]
        
        for adjust in adjustments:
            # Get stock data
            try:
                df = self.adapter.get_stock_data(
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date,
                    adjust=adjust
                )
                
                # Check that the result is a DataFrame
                self.assertIsInstance(df, pd.DataFrame)
                
                # Check that the DataFrame is not empty
                self.assertFalse(df.empty)
                
                # Print some information about the retrieved data
                logger.info(f"Retrieved {len(df)} rows of data for {symbol} with adjust={adjust}")
                if not df.empty:
                    logger.info(f"Date range: {df['date'].min()} to {df['date'].max()}")
                    logger.info(f"First few rows:\n{df.head()}")
            
            except Exception as e:
                self.fail(f"get_stock_data with adjust={adjust} raised an exception: {e}")
    
    def test_get_stock_data_with_different_date_formats(self):
        """Test getting stock data with different date formats."""
        # Define test parameters
        symbol = "000001"  # 平安银行
        
        # Test different date formats
        date_formats = [
            # (start_date, end_date)
            ("20230101", "20230131"),
            ("2023-01-01", "2023-01-31"),
            ("2023/01/01", "2023/01/31"),
            ("01/01/2023", "01/31/2023"),
            ("2023.01.01", "2023.01.31"),
            ("2023年01月01日", "2023年01月31日")
        ]
        
        for start_date, end_date in date_formats:
            # Get stock data
            try:
                df = self.adapter.get_stock_data(
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date
                )
                
                # Check that the result is a DataFrame
                self.assertIsInstance(df, pd.DataFrame)
                
                # Print some information about the retrieved data
                logger.info(f"Retrieved {len(df)} rows of data for {symbol} with dates {start_date} to {end_date}")
                if not df.empty:
                    logger.info(f"Date range: {df['date'].min()} to {df['date'].max()}")
                    logger.info(f"First few rows:\n{df.head()}")
            
            except Exception as e:
                self.fail(f"get_stock_data with dates {start_date} to {end_date} raised an exception: {e}")
    
    def test_get_stock_list(self):
        """Test getting the list of all stocks."""
        try:
            # Get the stock list
            stock_list = self.adapter.get_stock_list()
            
            # Check that the result is a DataFrame
            self.assertIsInstance(stock_list, pd.DataFrame)
            
            # Check that the DataFrame is not empty
            self.assertFalse(stock_list.empty)
            
            # Print some information about the retrieved data
            logger.info(f"Retrieved {len(stock_list)} stocks")
            if not stock_list.empty:
                logger.info(f"First few rows:\n{stock_list.head()}")
        
        except Exception as e:
            self.fail(f"get_stock_list raised an exception: {e}")
    
    def test_get_index_data(self):
        """Test getting index data."""
        # Define test parameters
        index_symbol = "000300"  # 沪深300指数
        end_date = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")
        
        try:
            # Get index data
            df = self.adapter.get_index_data(
                symbol=index_symbol,
                start_date=start_date,
                end_date=end_date
            )
            
            # Check that the result is a DataFrame
            self.assertIsInstance(df, pd.DataFrame)
            
            # Check that the DataFrame is not empty
            self.assertFalse(df.empty)
            
            # Print some information about the retrieved data
            logger.info(f"Retrieved {len(df)} rows of data for index {index_symbol}")
            if not df.empty:
                logger.info(f"Date range: {df['date'].min()} to {df['date'].max()}")
                logger.info(f"First few rows:\n{df.head()}")
        
        except Exception as e:
            self.fail(f"get_index_data raised an exception: {e}")


if __name__ == "__main__":
    unittest.main()
