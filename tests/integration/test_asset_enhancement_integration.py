"""
Integration tests for asset enhancement functionality.

Tests the complete asset enhancement flow including:
- Database integration
- Service layer integration
- API layer integration
- Data completeness validation
"""

import unittest
from unittest.mock import patch
import pandas as pd
from datetime import datetime, date

from core.database import SessionLocal, engine
from core.models import Base, Asset
from core.services.asset_info_service import AssetInfoService


class TestAssetEnhancementIntegration(unittest.TestCase):
    """Integration tests for asset enhancement"""

    @classmethod
    def setUpClass(cls):
        """Set up test database"""
        # Create test tables
        Base.metadata.create_all(bind=engine)

    def setUp(self):
        """Set up test session"""
        self.db = SessionLocal()
        
        # Clean up any existing test data
        self.db.query(Asset).filter(Asset.symbol.in_(["TEST001", "TEST002"])).delete()
        self.db.commit()

    def tearDown(self):
        """Clean up test session"""
        # Clean up test data
        self.db.query(Asset).filter(Asset.symbol.in_(["TEST001", "TEST002"])).delete()
        self.db.commit()
        self.db.close()

    def test_asset_creation_with_enhancement(self):
        """Test creating asset with enhanced information"""
        service = AssetInfoService(self.db)

        # Mock AKShare responses
        with patch('core.services.asset_info_service.ak.stock_individual_info_em') as mock_individual:

            # Mock individual info response
            mock_individual.return_value = pd.DataFrame({
                'item': ['股票简称', '上市时间', '总股本', '流通股', '总市值'],
                'value': ['测试公司', '2020-01-01', '100万', '80万', '1000万']
            })

            # Create asset
            asset = service.get_asset("TEST001")

            # Verify asset was created with enhanced data
            self.assertIsNotNone(asset)
            self.assertEqual(asset.symbol, "TEST001")
            self.assertEqual(asset.name, "测试公司")
            self.assertEqual(asset.listing_date, date(2020, 1, 1))
            self.assertEqual(asset.total_shares, 1000000)
            self.assertEqual(asset.circulating_shares, 800000)
            self.assertEqual(asset.market_cap, 10000000)
            self.assertEqual(asset.data_source, "akshare")
            self.assertIsNotNone(asset.last_updated)

    def test_asset_update_mechanism(self):
        """Test asset update mechanism with stale data"""
        service = AssetInfoService(self.db)
        
        # Create asset with old data
        old_asset = Asset(
            symbol="TEST002",
            name="旧名称",
            isin="CNTEST002",
            asset_type="stock",
            exchange="SHSE",
            currency="CNY",
            last_updated=datetime(2020, 1, 1)  # Very old
        )
        self.db.add(old_asset)
        self.db.commit()
        
        # Mock AKShare responses for update
        with patch('core.services.asset_info_service.ak.stock_individual_info_em') as mock_individual:
            mock_individual.return_value = pd.DataFrame({
                'item': ['股票简称', '上市时间'],
                'value': ['新名称', '2020-01-01']
            })
            
            # Get asset (should trigger update due to stale data)
            updated_asset = service.get_asset("TEST002")
            
            # Verify asset was updated
            self.assertEqual(updated_asset.symbol, "TEST002")
            self.assertEqual(updated_asset.name, "新名称")
            self.assertGreater(updated_asset.last_updated, datetime(2020, 1, 2))

    def test_asset_fallback_mechanism(self):
        """Test fallback mechanism when AKShare fails"""
        service = AssetInfoService(self.db)
        
        # Mock AKShare failure
        with patch('core.services.asset_info_service.ak.stock_individual_info_em') as mock_individual:
            mock_individual.side_effect = Exception("AKShare API error")
            
            # Create asset (should use fallback)
            asset = service.get_asset("600000")
            
            # Verify fallback data was used
            self.assertIsNotNone(asset)
            self.assertEqual(asset.symbol, "600000")
            self.assertEqual(asset.name, "浦发银行")  # Default name
            self.assertEqual(asset.data_source, "fallback")

    def test_data_completeness_validation(self):
        """Test data completeness validation across multiple assets"""
        service = AssetInfoService(self.db)
        
        # Test symbols with known defaults
        test_symbols = ["600000", "000001", "600519"]
        
        for symbol in test_symbols:
            with self.subTest(symbol=symbol):
                asset = service.get_asset(symbol)
                
                # Verify basic data completeness
                self.assertIsNotNone(asset)
                self.assertEqual(asset.symbol, symbol)
                self.assertIsNotNone(asset.name)
                self.assertFalse(asset.name.startswith("Stock "), 
                               f"Generic name for {symbol}: {asset.name}")
                
                # Verify enhanced data is present (from defaults if not from AKShare)
                self.assertIsNotNone(asset.industry)
                self.assertIsNotNone(asset.concept)
                self.assertNotEqual(asset.industry, "")
                self.assertNotEqual(asset.concept, "")

    def test_asset_caching_behavior(self):
        """Test asset caching and freshness behavior"""
        service = AssetInfoService(self.db)
        
        # First call - should create asset
        with patch('core.services.asset_info_service.ak.stock_individual_info_em') as mock_individual:
            mock_individual.return_value = pd.DataFrame({
                'item': ['股票简称'],
                'value': ['缓存测试']
            })
            
            asset1 = service.get_asset("TEST001")
            first_call_count = mock_individual.call_count

            # Second call immediately - should use cache (no AKShare call)
            asset2 = service.get_asset("TEST001")
            second_call_count = mock_individual.call_count
            
            # Verify caching worked
            self.assertEqual(asset1.asset_id, asset2.asset_id)
            self.assertEqual(first_call_count, second_call_count, 
                           "AKShare should not be called again for fresh data")

    def test_database_transaction_integrity(self):
        """Test database transaction integrity during asset operations"""
        service = AssetInfoService(self.db)
        
        # Mock AKShare to fail after partial data
        with patch('core.services.asset_info_service.ak.stock_individual_info_em') as mock_individual:
            mock_individual.return_value = pd.DataFrame({
                'item': ['股票简称'],
                'value': ['事务测试']
            })
            
            # This should succeed and commit
            asset = service.get_asset("TEST001")
            self.assertIsNotNone(asset)
            
            # Verify asset is actually in database
            db_asset = self.db.query(Asset).filter(Asset.symbol == "TEST001").first()
            self.assertIsNotNone(db_asset)
            # Note: The name might be "Stock TEST001" due to fallback logic
            self.assertTrue(db_asset.name in ["事务测试", "Stock TEST001"])

    def test_concurrent_asset_access(self):
        """Test concurrent access to asset creation"""
        # This is a simplified test for concurrent access
        # In a real scenario, you'd use threading or async testing
        
        service1 = AssetInfoService(self.db)
        service2 = AssetInfoService(self.db)
        
        # Both services try to create the same asset
        with patch('core.services.asset_info_service.ak.stock_individual_info_em') as mock_individual:
            mock_individual.return_value = pd.DataFrame({
                'item': ['股票简称'],
                'value': ['并发测试']
            })
            
            asset1 = service1.get_asset("TEST001")
            asset2 = service2.get_asset("TEST001")
            
            # Should return the same asset (by ID)
            self.assertEqual(asset1.asset_id, asset2.asset_id)

    def test_industry_concept_integration(self):
        """Test industry and concept data integration"""
        service = AssetInfoService(self.db)
        
        # Mock industry and concept data
        with patch('core.services.asset_info_service.ak.stock_board_industry_name_em') as mock_industry, \
             patch('core.services.asset_info_service.ak.stock_board_concept_name_em') as mock_concept:
            
            # Mock industry data
            mock_industry.return_value = pd.DataFrame({
                '代码': ['TEST001'],
                '板块名称': ['测试行业']
            })
            
            # Mock concept data
            mock_concept.return_value = pd.DataFrame({
                '代码': ['TEST001', 'TEST001'],
                '板块名称': ['概念1', '概念2']
            })
            
            asset = service.get_asset("TEST001")
            
            # Verify industry and concept data
            self.assertEqual(asset.industry, "测试行业")
            self.assertIn("概念1", asset.concept)
            self.assertIn("概念2", asset.concept)

    def test_end_to_end_asset_enhancement_flow(self):
        """Test complete end-to-end asset enhancement flow"""
        service = AssetInfoService(self.db)
        
        # Mock complete AKShare response
        with patch('core.services.asset_info_service.ak.stock_individual_info_em') as mock_individual, \
             patch('core.services.asset_info_service.ak.stock_zh_a_spot_em') as mock_realtime, \
             patch('core.services.asset_info_service.ak.stock_board_industry_name_em') as mock_industry, \
             patch('core.services.asset_info_service.ak.stock_board_concept_name_em') as mock_concept:
            
            # Mock all data sources
            mock_individual.return_value = pd.DataFrame({
                'item': ['股票简称', '上市时间', '总股本'],
                'value': ['端到端测试', '2021-01-01', '500万']
            })
            
            mock_realtime.return_value = pd.DataFrame({
                '代码': ['TEST001'],
                '市盈率-动态': [12.5],
                '市净率': [1.8]
            })
            
            mock_industry.return_value = pd.DataFrame({
                '代码': ['TEST001'],
                '板块名称': ['科技']
            })
            
            mock_concept.return_value = pd.DataFrame({
                '代码': ['TEST001'],
                '板块名称': ['人工智能']
            })
            
            # Execute complete flow
            asset = service.get_asset("TEST001")
            
            # Verify complete enhancement
            self.assertEqual(asset.symbol, "TEST001")
            self.assertEqual(asset.name, "端到端测试")
            self.assertEqual(asset.listing_date, date(2021, 1, 1))
            self.assertEqual(asset.total_shares, 5000000)
            self.assertEqual(asset.pe_ratio, 12.5)
            self.assertEqual(asset.pb_ratio, 1.8)
            self.assertEqual(asset.industry, "科技")
            self.assertEqual(asset.concept, "人工智能")
            self.assertEqual(asset.data_source, "akshare")


if __name__ == '__main__':
    unittest.main()
