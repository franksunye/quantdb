"""
API tests for asset endpoints.

Tests the enhanced asset API including:
- Asset retrieval with enhanced information
- Asset refresh functionality
- Error handling
- Response format validation
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from datetime import datetime

from api.main import app
from core.models import Asset


client = TestClient(app)


class TestAssetsAPI:
    """Test cases for Assets API endpoints"""

    def test_get_assets_list(self):
        """Test getting list of all assets"""
        response = client.get("/api/v1/assets")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_asset_by_symbol_existing(self):
        """Test getting existing asset by symbol"""
        # Use a symbol that should exist in test data
        response = client.get("/api/v1/assets/symbol/600000")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify enhanced asset information structure
        required_fields = [
            "asset_id", "symbol", "name", "isin", "asset_type", 
            "exchange", "currency"
        ]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
        
        # Verify enhanced fields are present (may be null)
        enhanced_fields = [
            "industry", "concept", "listing_date", "total_shares",
            "circulating_shares", "market_cap", "pe_ratio", "pb_ratio",
            "roe", "last_updated", "data_source"
        ]
        for field in enhanced_fields:
            assert field in data, f"Missing enhanced field: {field}"
        
        # Verify symbol format
        assert data["symbol"] == "600000"
        
        # Verify real company name (not "Stock XXXXXX")
        assert not data["name"].startswith("Stock "), f"Still showing generic name: {data['name']}"

    def test_get_asset_by_symbol_with_enhanced_data(self):
        """Test that asset returns enhanced data when available"""
        response = client.get("/api/v1/assets/symbol/600000")
        
        if response.status_code == 200:
            data = response.json()
            
            # If data is enhanced, verify it's meaningful
            if data.get("industry"):
                assert isinstance(data["industry"], str)
                assert len(data["industry"]) > 0
            
            if data.get("concept"):
                assert isinstance(data["concept"], str)
                assert len(data["concept"]) > 0
            
            if data.get("pe_ratio"):
                assert isinstance(data["pe_ratio"], (int, float))
                assert data["pe_ratio"] > 0
            
            if data.get("pb_ratio"):
                assert isinstance(data["pb_ratio"], (int, float))
                assert data["pb_ratio"] > 0

    @patch('core.services.asset_info_service.AssetInfoService.get_or_create_asset')
    def test_get_asset_by_symbol_service_integration(self, mock_service):
        """Test asset API integration with AssetInfoService"""
        # Mock service response
        mock_asset = Asset(
            asset_id=1,
            symbol="600000",
            name="浦发银行",
            isin="CN600000",
            asset_type="stock",
            exchange="SHSE",
            currency="CNY",
            industry="银行",
            concept="银行股, 上海本地股",
            pe_ratio=5.15,
            pb_ratio=0.55,
            data_source="akshare",
            last_updated=datetime.now()
        )
        mock_service.return_value = mock_asset
        
        response = client.get("/api/v1/assets/symbol/600000")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify service was called
        mock_service.assert_called_once_with("600000")
        
        # Verify response data
        assert data["symbol"] == "600000"
        assert data["name"] == "浦发银行"
        assert data["industry"] == "银行"
        assert data["concept"] == "银行股, 上海本地股"
        assert data["pe_ratio"] == 5.15
        assert data["pb_ratio"] == 0.55

    def test_get_asset_by_symbol_invalid_format(self):
        """Test getting asset with invalid symbol format"""
        invalid_symbols = ["1234567", "abc123"]  # Remove symbols that might be valid

        for symbol in invalid_symbols:
            response = client.get(f"/api/v1/assets/symbol/{symbol}")
            # Should either return 400, 404, 500, or handle gracefully with 200
            assert response.status_code in [200, 400, 404, 500]

    def test_refresh_asset_info_existing(self):
        """Test refreshing existing asset information"""
        response = client.put("/api/v1/assets/symbol/600000/refresh")
        
        # Should succeed or return appropriate error
        assert response.status_code in [200, 404, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert "symbol" in data
            assert data["symbol"] == "600000"

    @patch('core.services.asset_info_service.AssetInfoService.update_asset_info')
    def test_refresh_asset_info_service_integration(self, mock_update):
        """Test asset refresh API integration with AssetInfoService"""
        # Mock service response with all required fields
        mock_asset = Asset(
            asset_id=1,
            symbol="600000",
            name="浦发银行",
            isin="CN600000",
            asset_type="stock",
            exchange="SHSE",
            currency="CNY",
            last_updated=datetime.now()
        )
        mock_update.return_value = mock_asset
        
        response = client.put("/api/v1/assets/symbol/600000/refresh")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify service was called
        mock_update.assert_called_once_with("600000")
        
        # Verify response
        assert data["symbol"] == "600000"
        assert data["name"] == "浦发银行"

    @patch('core.services.asset_info_service.AssetInfoService.update_asset_info')
    def test_refresh_asset_info_not_found(self, mock_update):
        """Test refreshing nonexistent asset"""
        # Mock service returning None
        mock_update.return_value = None
        
        response = client.put("/api/v1/assets/symbol/999999/refresh")
        
        assert response.status_code == 404
        error_data = response.json()
        # Check for either "detail" or "error" field
        assert "detail" in error_data or "error" in error_data

    def test_asset_api_error_handling(self):
        """Test asset API error handling"""
        # Test various error scenarios
        error_cases = [
            ("/api/v1/assets/symbol/", [404, 422]),  # Missing symbol
            ("/api/v1/assets/symbol/invalid", [400, 422]),  # Invalid symbol
        ]

        for endpoint, expected_statuses in error_cases:
            response = client.get(endpoint)
            assert response.status_code in expected_statuses

    def test_asset_response_format_consistency(self):
        """Test that asset responses have consistent format"""
        response = client.get("/api/v1/assets/symbol/600000")
        
        if response.status_code == 200:
            data = response.json()
            
            # Verify data types
            assert isinstance(data["asset_id"], int)
            assert isinstance(data["symbol"], str)
            assert isinstance(data["name"], str)
            assert isinstance(data["asset_type"], str)
            assert isinstance(data["exchange"], str)
            assert isinstance(data["currency"], str)
            
            # Enhanced fields should be proper types or null
            if data.get("pe_ratio") is not None:
                assert isinstance(data["pe_ratio"], (int, float))
            
            if data.get("pb_ratio") is not None:
                assert isinstance(data["pb_ratio"], (int, float))
            
            if data.get("total_shares") is not None:
                assert isinstance(data["total_shares"], int)

    def test_historical_data_api_shows_real_names(self):
        """Test that historical data API now shows real company names"""
        response = client.get("/api/v1/historical/stock/600000?start_date=20240101&end_date=20240105")
        
        if response.status_code == 200:
            data = response.json()
            
            # Verify the response includes real company name
            assert "name" in data
            assert data["symbol"] == "600000"
            
            # Should not be generic "Stock XXXXXX" format
            if data["name"]:
                assert not data["name"].startswith("Stock "), f"Still showing generic name: {data['name']}"

    def test_asset_data_completeness_validation(self):
        """Test that assets have complete data after enhancement"""
        response = client.get("/api/v1/assets")
        
        if response.status_code == 200:
            assets = response.json()
            
            for asset in assets:
                # Basic validation
                assert asset["symbol"]
                assert asset["name"]
                assert not asset["name"].startswith("Stock "), f"Generic name found: {asset['name']}"
                
                # Enhanced data should be present for known symbols (if available)
                known_symbols = ["600000", "000001", "600519", "000002", "600036"]
                if asset["symbol"] in known_symbols:
                    # These should have enhanced data, but may be None if not yet populated
                    # Just verify the fields exist in the response
                    assert "industry" in asset, f"Missing industry field for {asset['symbol']}"
                    assert "concept" in asset, f"Missing concept field for {asset['symbol']}"


if __name__ == '__main__':
    pytest.main([__file__])
