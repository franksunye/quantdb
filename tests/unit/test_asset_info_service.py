"""
Unit tests for AssetInfoService.

Tests the asset information management service including:
- Asset creation and retrieval
- Data freshness checking
- AKShare integration
- Fallback mechanisms
"""

import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, date, timedelta
import pandas as pd

from core.services.asset_info_service import AssetInfoService
from core.models import Asset


class TestAssetInfoService(unittest.TestCase):
    """Test cases for AssetInfoService"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_db = MagicMock()
        self.service = AssetInfoService(self.mock_db)

    def test_standardize_symbol(self):
        """Test symbol standardization"""
        # Test various symbol formats
        test_cases = [
            ("600000", "600000"),
            ("sh600000", "600000"),
            ("SZ000001", "000001"),
            ("600000.SH", "600000"),
            ("1", "000001"),  # Padding
        ]
        
        for input_symbol, expected in test_cases:
            result = self.service._standardize_symbol(input_symbol)
            self.assertEqual(result, expected, f"Failed for input: {input_symbol}")

    def test_is_asset_data_stale_no_update_time(self):
        """Test stale data detection when no update time"""
        asset = Asset(symbol="600000", name="Test")
        asset.last_updated = None
        
        result = self.service._is_asset_data_stale(asset)
        self.assertTrue(result)

    def test_is_asset_data_stale_fresh_data(self):
        """Test stale data detection with fresh data"""
        asset = Asset(symbol="600000", name="Test")
        asset.last_updated = datetime.now() - timedelta(hours=12)  # 12 hours ago
        
        result = self.service._is_asset_data_stale(asset)
        self.assertFalse(result)

    def test_is_asset_data_stale_old_data(self):
        """Test stale data detection with old data"""
        asset = Asset(symbol="600000", name="Test")
        asset.last_updated = datetime.now() - timedelta(days=2)  # 2 days ago
        
        result = self.service._is_asset_data_stale(asset)
        self.assertTrue(result)

    def test_get_default_name(self):
        """Test default name mapping"""
        test_cases = [
            ("600000", "浦发银行"),
            ("000001", "平安银行"),
            ("600519", "贵州茅台"),
            ("999999", "Stock 999999"),  # Unknown symbol
        ]
        
        for symbol, expected in test_cases:
            result = self.service._get_default_name(symbol)
            self.assertEqual(result, expected)

    def test_get_default_industry(self):
        """Test default industry mapping"""
        test_cases = [
            ("600000", "银行"),
            ("000001", "银行"),
            ("600519", "食品饮料"),
            ("000002", "房地产"),
            ("999999", "其他"),  # Unknown symbol
        ]
        
        for symbol, expected in test_cases:
            result = self.service._get_default_industry(symbol)
            self.assertEqual(result, expected)

    def test_get_default_concept(self):
        """Test default concept mapping"""
        test_cases = [
            ("600000", "银行股, 上海本地股"),
            ("000001", "银行股, 深圳本地股"),
            ("600519", "白酒概念, 消费股"),
            ("999999", "其他概念"),  # Unknown symbol
        ]
        
        for symbol, expected in test_cases:
            result = self.service._get_default_concept(symbol)
            self.assertEqual(result, expected)

    def test_safe_float_valid_values(self):
        """Test safe float conversion with valid values"""
        test_cases = [
            (5.15, 5.15),
            ("5.15", 5.15),
            (0, 0.0),
            ("0", 0.0),
        ]
        
        for input_val, expected in test_cases:
            result = self.service._safe_float(input_val)
            self.assertEqual(result, expected)

    def test_safe_float_invalid_values(self):
        """Test safe float conversion with invalid values"""
        test_cases = [None, "-", "", "invalid", []]
        
        for input_val in test_cases:
            result = self.service._safe_float(input_val)
            self.assertIsNone(result)

    def test_parse_number_with_units(self):
        """Test number parsing with Chinese units"""
        test_cases = [
            ("100万", 1000000),
            ("5.5万", 55000),
            ("2亿", 200000000),
            ("1.5亿", 150000000),
            ("1000", 1000),
            ("", None),
            (None, None),
        ]
        
        for input_val, expected in test_cases:
            result = self.service._parse_number(input_val)
            self.assertEqual(result, expected)

    def test_parse_date_valid_formats(self):
        """Test date parsing with valid formats"""
        test_cases = [
            ("2023-01-01", date(2023, 1, 1)),
            ("1999-11-10", date(1999, 11, 10)),
        ]
        
        for input_val, expected in test_cases:
            result = self.service._parse_date(input_val)
            self.assertEqual(result, expected)

    def test_parse_date_invalid_formats(self):
        """Test date parsing with invalid formats"""
        test_cases = ["", None, "invalid", "2023/01/01", "01-01-2023"]
        
        for input_val in test_cases:
            result = self.service._parse_date(input_val)
            self.assertIsNone(result)

    @patch('src.services.asset_info_service.ak.stock_individual_info_em')
    def test_fetch_asset_basic_info_success(self, mock_akshare):
        """Test successful asset info fetching from AKShare"""
        # Mock AKShare response
        mock_data = pd.DataFrame({
            'item': ['股票简称', '上市时间', '总股本', '流通股', '总市值'],
            'value': ['浦发银行', '1999-11-10', '293.52亿', '293.52亿', '3500亿']
        })
        mock_akshare.return_value = mock_data
        
        # Mock realtime data
        with patch('src.services.asset_info_service.ak.stock_zh_a_spot_em') as mock_realtime:
            mock_realtime_data = pd.DataFrame({
                '代码': ['600000'],
                '市盈率-动态': [5.15],
                '市净率': [0.55]
            })
            mock_realtime.return_value = mock_realtime_data
            
            result = self.service._fetch_asset_basic_info("600000")
            
            # Verify results
            self.assertEqual(result['name'], '浦发银行')
            self.assertEqual(result['listing_date'], date(1999, 11, 10))
            self.assertEqual(result['total_shares'], 29352000000)
            self.assertEqual(result['pe_ratio'], 5.15)
            self.assertEqual(result['pb_ratio'], 0.55)

    @patch('src.services.asset_info_service.ak.stock_individual_info_em')
    def test_fetch_asset_basic_info_akshare_failure(self, mock_akshare):
        """Test asset info fetching when AKShare fails"""
        # Mock AKShare failure
        mock_akshare.side_effect = Exception("AKShare API error")
        
        result = self.service._fetch_asset_basic_info("600000")
        
        # Should return default name
        self.assertEqual(result['name'], '浦发银行')

    def test_get_or_create_asset_existing_fresh(self):
        """Test getting existing asset with fresh data"""
        # Mock existing fresh asset
        existing_asset = Asset(
            symbol="600000",
            name="浦发银行",
            last_updated=datetime.now() - timedelta(hours=12)
        )
        self.mock_db.query.return_value.filter.return_value.first.return_value = existing_asset
        
        result = self.service.get_or_create_asset("600000")
        
        self.assertEqual(result, existing_asset)
        self.mock_db.query.assert_called_once()

    def test_get_or_create_asset_existing_stale(self):
        """Test getting existing asset with stale data"""
        # Mock existing stale asset
        existing_asset = Asset(
            symbol="600000",
            name="浦发银行",
            last_updated=datetime.now() - timedelta(days=2)
        )
        self.mock_db.query.return_value.filter.return_value.first.return_value = existing_asset
        
        # Mock the update process
        with patch.object(self.service, '_update_asset_info') as mock_update:
            updated_asset = Asset(symbol="600000", name="浦发银行 Updated")
            mock_update.return_value = updated_asset
            
            result = self.service.get_or_create_asset("600000")
            
            mock_update.assert_called_once_with(existing_asset)
            self.assertEqual(result, updated_asset)

    def test_get_or_create_asset_new(self):
        """Test creating new asset"""
        # Mock no existing asset
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Mock the creation process
        with patch.object(self.service, '_create_new_asset') as mock_create:
            new_asset = Asset(symbol="600000", name="浦发银行")
            mock_create.return_value = new_asset
            
            result = self.service.get_or_create_asset("600000")
            
            mock_create.assert_called_once_with("600000")
            self.assertEqual(result, new_asset)

    def test_update_asset_info_existing_asset(self):
        """Test updating existing asset info"""
        # Mock existing asset
        existing_asset = Asset(symbol="600000", name="Old Name")
        self.mock_db.query.return_value.filter.return_value.first.return_value = existing_asset
        
        # Mock the update process
        with patch.object(self.service, '_update_asset_info') as mock_update:
            updated_asset = Asset(symbol="600000", name="浦发银行")
            mock_update.return_value = updated_asset
            
            result = self.service.update_asset_info("600000")
            
            mock_update.assert_called_once_with(existing_asset)
            self.assertEqual(result, updated_asset)

    def test_update_asset_info_nonexistent_asset(self):
        """Test updating nonexistent asset"""
        # Mock no existing asset
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = self.service.update_asset_info("999999")
        
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()
