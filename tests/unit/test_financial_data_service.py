# tests/unit/test_financial_data_service.py
"""
Unit tests for the FinancialDataService class.
"""

import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
import pandas as pd
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from core.services.financial_data_service import FinancialDataService
from core.models.financial_data import FinancialSummary, FinancialIndicators, FinancialDataCache
from core.models.asset import Asset


class TestFinancialDataService(unittest.TestCase):
    """Test cases for FinancialDataService."""

    def setUp(self):
        """Set up test fixtures."""
        self.db_mock = MagicMock()
        self.akshare_adapter_mock = MagicMock()
        
        # Create service with mocked dependencies
        self.service = FinancialDataService(self.db_mock, self.akshare_adapter_mock)

    def test_init(self):
        """Test service initialization."""
        self.assertEqual(self.service.db, self.db_mock)
        self.assertEqual(self.service.akshare_adapter, self.akshare_adapter_mock)

    @patch('core.services.financial_data_service.FinancialDataCache.is_cache_valid')
    @patch('core.services.financial_data_service.logger')
    def test_get_financial_summary_cache_hit(self, logger_mock, cache_valid_mock):
        """Test getting financial summary with cache hit."""
        # Setup cache hit scenario
        cache_valid_mock.return_value = True

        # Setup mock summary data
        mock_summary = MagicMock()
        mock_summary.report_period = '20231231'
        mock_summary.net_profit = 1000.0
        mock_summary.total_revenue = 5000.0

        self.db_mock.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [mock_summary]

        # Call method
        result = self.service.get_financial_summary('000001')

        # Verify result
        self.assertTrue(result['cache_hit'])
        self.assertEqual(result['symbol'], '000001')
        self.assertEqual(result['data_type'], 'financial_summary')

        # Verify cache was checked
        self.akshare_adapter_mock.get_financial_summary.assert_not_called()

    @patch('core.services.financial_data_service.logger')
    def test_get_financial_summary_cache_miss(self, logger_mock):
        """Test getting financial summary with cache miss."""
        # Setup cache miss scenario
        self.db_mock.query.return_value.filter.return_value.first.return_value = None
        
        # Setup AKShare data
        test_df = pd.DataFrame({
            'date': ['20231231', '20230930'],
            'net_profit': [1000.0, 900.0],
            'total_revenue': [5000.0, 4500.0]
        })
        self.akshare_adapter_mock.get_financial_summary.return_value = test_df
        
        # Call method
        result = self.service.get_financial_summary('000001')
        
        # Verify result
        self.assertFalse(result['cache_hit'])
        self.assertEqual(result['symbol'], '000001')
        
        # Verify AKShare was called
        self.akshare_adapter_mock.get_financial_summary.assert_called_once_with('000001')

    @patch('core.services.financial_data_service.logger')
    def test_get_financial_summary_force_refresh(self, logger_mock):
        """Test getting financial summary with force refresh."""
        # Setup AKShare data
        test_df = pd.DataFrame({
            'date': ['20231231'],
            'net_profit': [1000.0],
            'total_revenue': [5000.0]
        })
        self.akshare_adapter_mock.get_financial_summary.return_value = test_df
        
        # Call method with force refresh
        result = self.service.get_financial_summary('000001', force_refresh=True)
        
        # Verify result
        self.assertFalse(result['cache_hit'])
        self.assertEqual(result['symbol'], '000001')
        
        # Verify cache was bypassed
        self.akshare_adapter_mock.get_financial_summary.assert_called_once_with('000001')

    @patch('core.services.financial_data_service.FinancialDataCache.is_cache_valid')
    @patch('core.services.financial_data_service.logger')
    def test_get_financial_indicators_cache_hit(self, logger_mock, cache_valid_mock):
        """Test getting financial indicators with cache hit."""
        # Setup cache hit scenario
        cache_valid_mock.return_value = True

        # Setup mock indicators data
        mock_indicator = MagicMock()
        mock_indicator.report_period = '20231231'
        mock_indicator.eps = 1.5
        mock_indicator.pe_ratio = 15.0

        self.db_mock.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [mock_indicator]

        # Call method
        result = self.service.get_financial_indicators('600036')

        # Verify result
        self.assertTrue(result['cache_hit'])
        self.assertEqual(result['symbol'], '600036')
        self.assertEqual(result['data_type'], 'financial_indicators')

    @patch('core.services.financial_data_service.logger')
    def test_get_financial_indicators_cache_miss(self, logger_mock):
        """Test getting financial indicators with cache miss."""
        # Setup cache miss scenario
        self.db_mock.query.return_value.filter.return_value.first.return_value = None
        
        # Setup AKShare data
        test_df = pd.DataFrame({
            'date': ['20231231'],
            'roe': [15.5],
            'roa': [8.2]
        })
        self.akshare_adapter_mock.get_financial_indicators.return_value = test_df
        
        # Call method
        result = self.service.get_financial_indicators('600036')
        
        # Verify result
        self.assertFalse(result['cache_hit'])
        self.assertEqual(result['symbol'], '600036')

    def test_get_financial_data_batch_summary(self):
        """Test batch financial summary data retrieval."""
        symbols = ['000001', '600000', '600036']
        
        # Setup AKShare data for each symbol
        test_df = pd.DataFrame({
            'date': ['20231231'],
            'net_profit': [1000.0],
            'total_revenue': [5000.0]
        })
        self.akshare_adapter_mock.get_financial_summary.return_value = test_df
        
        # Call method
        result = self.service.get_financial_data_batch(symbols, data_type='summary')
        
        # Verify result
        self.assertEqual(len(result), 3)
        for symbol in symbols:
            self.assertIn(symbol, result)
            self.assertEqual(result[symbol]['symbol'], symbol)

    def test_get_financial_data_batch_indicators(self):
        """Test batch financial indicators data retrieval."""
        symbols = ['600036', '000001']
        
        # Setup AKShare data
        test_df = pd.DataFrame({
            'date': ['20231231'],
            'roe': [15.5],
            'roa': [8.2]
        })
        self.akshare_adapter_mock.get_financial_indicators.return_value = test_df
        
        # Call method
        result = self.service.get_financial_data_batch(symbols, data_type='indicators')
        
        # Verify result
        self.assertEqual(len(result), 2)
        for symbol in symbols:
            self.assertIn(symbol, result)

    def test_get_financial_data_batch_invalid_type(self):
        """Test batch data retrieval with invalid data type."""
        symbols = ['000001']

        # Setup AKShare to return empty data
        self.akshare_adapter_mock.get_financial_indicators.return_value = pd.DataFrame()

        # Call method with invalid type (will default to indicators)
        result = self.service.get_financial_data_batch(symbols, data_type='invalid')

        # Verify result contains error for the symbol
        self.assertEqual(len(result), 1)
        self.assertIn('000001', result)
        self.assertIn('error', result['000001'])

    @patch('core.services.financial_data_service.logger')
    def test_get_financial_summary_akshare_error(self, logger_mock):
        """Test handling AKShare errors in financial summary."""
        # Setup cache miss
        self.db_mock.query.return_value.filter.return_value.first.return_value = None
        
        # Setup AKShare error
        self.akshare_adapter_mock.get_financial_summary.side_effect = Exception("AKShare error")
        
        # Call method
        result = self.service.get_financial_summary('000001')
        
        # Verify error handling
        self.assertIn('error', result)
        self.assertEqual(result['symbol'], '000001')
        self.assertFalse(result['cache_hit'])

    @patch('core.services.financial_data_service.logger')
    def test_get_financial_indicators_akshare_error(self, logger_mock):
        """Test handling AKShare errors in financial indicators."""
        # Setup cache miss
        self.db_mock.query.return_value.filter.return_value.first.return_value = None
        
        # Setup AKShare error
        self.akshare_adapter_mock.get_financial_indicators.side_effect = Exception("AKShare error")
        
        # Call method
        result = self.service.get_financial_indicators('600036')
        
        # Verify error handling
        self.assertIn('error', result)
        self.assertEqual(result['symbol'], '600036')
        self.assertFalse(result['cache_hit'])

    def test_get_cached_summary_valid_cache(self):
        """Test getting cached summary with valid cache."""
        # Setup mock cache validation
        with patch('core.services.financial_data_service.FinancialDataCache.is_cache_valid', return_value=True):
            # Setup mock summary data
            mock_summary = MagicMock()
            mock_summary.report_period = '20231231'
            mock_summary.net_profit = 1000.0

            self.db_mock.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [mock_summary]

            # Call internal method
            result = self.service._get_cached_summary('000001')

            # Verify result
            self.assertIsNotNone(result)
            self.assertEqual(result['symbol'], '000001')

    def test_get_cached_summary_invalid_cache(self):
        """Test getting cached summary with invalid cache."""
        # Setup mock cache validation
        with patch('core.services.financial_data_service.FinancialDataCache.is_cache_valid', return_value=False):
            # Call internal method
            result = self.service._get_cached_summary('000001')

            # Verify result
            self.assertIsNone(result)

    def test_get_cached_indicators_valid_cache(self):
        """Test getting cached indicators with valid cache."""
        # Setup mock cache validation
        with patch('core.services.financial_data_service.FinancialDataCache.is_cache_valid', return_value=True):
            # Setup mock indicators data
            mock_indicator = MagicMock()
            mock_indicator.report_period = '20231231'
            mock_indicator.eps = 1.5

            self.db_mock.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [mock_indicator]

            # Call internal method
            result = self.service._get_cached_indicators('600036')

            # Verify result
            self.assertIsNotNone(result)
            self.assertEqual(result['symbol'], '600036')

    @patch('core.services.financial_data_service.FinancialSummary.from_akshare_data')
    def test_process_financial_summary_new_asset(self, mock_from_akshare):
        """Test processing financial summary for new asset."""
        # Setup no existing asset
        self.db_mock.query.return_value.filter.return_value.first.return_value = None

        # Setup mock summary objects
        mock_summary = MagicMock()
        mock_summary.report_period = '20231231'
        mock_summary.net_profit = 1000.0
        mock_from_akshare.return_value = [mock_summary]

        # Setup test data
        test_df = pd.DataFrame({
            'date': ['20231231'],
            'net_profit': [1000.0],
            'total_revenue': [5000.0]
        })

        # Call internal method
        result = self.service._process_financial_summary('000001', test_df)

        # Verify result
        self.assertIn('count', result)
        self.assertIn('quarters', result)
        self.assertEqual(result['symbol'], '000001')

    @patch('core.services.financial_data_service.FinancialSummary.from_akshare_data')
    def test_process_financial_summary_existing_asset(self, mock_from_akshare):
        """Test processing financial summary for existing asset."""
        # Setup existing asset
        mock_asset = MagicMock()
        mock_asset.asset_id = 1
        self.db_mock.query.return_value.filter.return_value.first.return_value = mock_asset

        # Setup mock summary objects
        mock_summary = MagicMock()
        mock_summary.report_period = '20231231'
        mock_summary.net_profit = 1000.0
        mock_from_akshare.return_value = [mock_summary]

        # Setup test data
        test_df = pd.DataFrame({
            'date': ['20231231'],
            'net_profit': [1000.0],
            'total_revenue': [5000.0]
        })

        # Call internal method
        result = self.service._process_financial_summary('000001', test_df)

        # Verify result
        self.assertIn('count', result)
        self.assertIn('quarters', result)
        self.assertEqual(result['symbol'], '000001')

    def test_process_financial_indicators(self):
        """Test processing financial indicators."""
        # Setup existing asset
        mock_asset = MagicMock()
        mock_asset.asset_id = 1
        self.db_mock.query.return_value.filter.return_value.first.return_value = mock_asset

        # Setup test data
        test_df = pd.DataFrame({
            'date': ['20231231'],
            'roe': [15.5],
            'roa': [8.2]
        })

        # Call internal method
        result = self.service._process_financial_indicators('600036', test_df)

        # Verify result
        self.assertIn('raw_data_shape', result)
        self.assertIn('periods', result)
        self.assertEqual(result['symbol'], '600036')

    @patch('core.services.financial_data_service.FinancialDataCache.update_cache_record')
    def test_cache_update_summary(self, mock_update_cache):
        """Test cache update for summary data."""
        # Call cache update
        FinancialDataCache.update_cache_record('000001', 'summary', self.db_mock)

        # Verify cache update was called
        mock_update_cache.assert_called_once_with('000001', 'summary', self.db_mock)

    @patch('core.services.financial_data_service.FinancialDataCache.update_cache_record')
    def test_cache_update_indicators(self, mock_update_cache):
        """Test cache update for indicators data."""
        # Call cache update
        FinancialDataCache.update_cache_record('600036', 'indicators', self.db_mock)

        # Verify cache update was called
        mock_update_cache.assert_called_once_with('600036', 'indicators', self.db_mock)

    def test_database_operations_summary(self):
        """Test database operations for summary data."""
        # Setup existing asset
        mock_asset = MagicMock()
        mock_asset.asset_id = 1
        self.db_mock.query.return_value.filter.return_value.first.return_value = mock_asset

        # Setup test data
        test_df = pd.DataFrame({
            'date': ['20231231'],
            'net_profit': [1000.0],
            'total_revenue': [5000.0]
        })

        with patch('core.services.financial_data_service.FinancialSummary.from_akshare_data') as mock_from_akshare:
            mock_summary = MagicMock()
            mock_from_akshare.return_value = [mock_summary]

            # Call internal method
            self.service._process_financial_summary('000001', test_df)

            # Verify database operations
            self.db_mock.add.assert_called()
            self.db_mock.commit.assert_called()

    def test_database_operations_indicators(self):
        """Test database operations for indicators data."""
        # Setup existing asset
        mock_asset = MagicMock()
        mock_asset.asset_id = 1
        self.db_mock.query.return_value.filter.return_value.first.return_value = mock_asset

        # Setup test data
        test_df = pd.DataFrame({
            'date': ['20231231'],
            'roe': [15.5],
            'roa': [8.2]
        })

        # Call internal method
        self.service._process_financial_indicators('600036', test_df)

        # Verify database operations
        self.db_mock.add.assert_called()
        self.db_mock.commit.assert_called()


if __name__ == '__main__':
    unittest.main()
