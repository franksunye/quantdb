"""
Core models unit tests for QuantDB.

This module tests all core data models including:
- Asset model
- Stock data models (Daily, Intraday, Realtime)
- System metrics models
- Index data models
- Financial data models
"""

import unittest
from datetime import date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.models import (
    Asset,
    Base,
    DailyStockData,
    DataCoverage,
    FinancialIndicators,
    FinancialSummary,
    IndexData,
    IntradayStockData,
    RealtimeIndexData,
    RealtimeStockData,
    RequestLog,
    SystemMetrics,
)


class TestCoreModels(unittest.TestCase):
    """Test core data models."""

    def setUp(self):
        """Set up test database and session."""
        # Create a new in-memory database for each test
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        SessionLocal = sessionmaker(bind=self.engine)
        self.session = SessionLocal()

    def tearDown(self):
        """Clean up test session and database."""
        self.session.close()
        self.engine.dispose()


class TestAssetModel(TestCoreModels):
    """Test Asset model functionality."""
    
    def test_asset_creation(self):
        """Test basic asset creation."""
        asset = Asset(
            symbol="600000",
            name="浦发银行",
            isin="CNE000001Z5",
            asset_type="stock",
            exchange="SHSE",
            currency="CNY"
        )

        self.session.add(asset)
        self.session.commit()

        # Verify asset was created
        saved_asset = self.session.query(Asset).filter_by(symbol="600000").first()
        self.assertIsNotNone(saved_asset)
        self.assertEqual(saved_asset.name, "浦发银行")
        self.assertEqual(saved_asset.asset_type, "stock")
        self.assertEqual(saved_asset.exchange, "SHSE")
        self.assertEqual(saved_asset.currency, "CNY")
    
    def test_asset_with_enhanced_info(self):
        """Test asset with enhanced information."""
        asset = Asset(
            symbol="000001",
            name="平安银行",
            isin="CNE000000Q4",
            asset_type="stock",
            exchange="SZSE",
            currency="CNY",
            industry="银行",
            concept="金融科技,数字货币",
            pe_ratio=5.23,
            pb_ratio=0.67,
            roe=12.45,
            market_cap=2500000000000.0
        )

        self.session.add(asset)
        self.session.commit()

        saved_asset = self.session.query(Asset).filter_by(symbol="000001").first()
        self.assertEqual(saved_asset.industry, "银行")
        self.assertEqual(saved_asset.concept, "金融科技,数字货币")
        self.assertEqual(saved_asset.pe_ratio, 5.23)
        self.assertEqual(saved_asset.pb_ratio, 0.67)
        self.assertEqual(saved_asset.roe, 12.45)
        self.assertEqual(saved_asset.market_cap, 2500000000000.0)
    
    def test_asset_relationships(self):
        """Test asset relationships with stock data."""
        # Create asset
        asset = Asset(
            symbol="600036",
            name="招商银行",
            isin="CNE000000K6",
            asset_type="stock",
            exchange="SHSE",
            currency="CNY"
        )
        self.session.add(asset)
        self.session.commit()
        
        # Create daily stock data
        daily_data = DailyStockData(
            asset_id=asset.asset_id,
            trade_date=date(2024, 1, 15),
            open=35.50,
            high=36.20,
            low=35.30,
            close=36.00,
            volume=12500000
        )
        self.session.add(daily_data)
        self.session.commit()
        
        # Test relationship
        self.assertEqual(len(asset.daily_data), 1)
        self.assertEqual(asset.daily_data[0].close, 36.00)


class TestStockDataModels(TestCoreModels):
    """Test stock data models."""
    
    def setUp(self):
        """Set up test data."""
        super().setUp()
        self.asset = Asset(
            symbol="000002",
            name="万科A",
            isin="CNE000000T3",  # Different ISIN to avoid conflicts
            asset_type="stock",
            exchange="SZSE",
            currency="CNY"
        )
        self.session.add(self.asset)
        self.session.commit()
    
    def test_daily_stock_data_creation(self):
        """Test daily stock data creation."""
        daily_data = DailyStockData(
            asset_id=self.asset.asset_id,
            trade_date=date(2024, 1, 15),
            open=15.50,
            high=16.20,
            low=15.30,
            close=16.00,
            volume=25000000,
            turnover=400000000.0,
            amplitude=5.81,
            pct_change=3.23,
            change=0.50,
            turnover_rate=2.15
        )
        
        self.session.add(daily_data)
        self.session.commit()
        
        saved_data = self.session.query(DailyStockData).filter_by(
            asset_id=self.asset.asset_id
        ).first()
        
        self.assertIsNotNone(saved_data)
        self.assertEqual(saved_data.open, 15.50)
        self.assertEqual(saved_data.close, 16.00)
        self.assertEqual(saved_data.volume, 25000000)
        self.assertEqual(saved_data.pct_change, 3.23)
    
    def test_realtime_stock_data_creation(self):
        """Test realtime stock data creation."""
        realtime_data = RealtimeStockData(
            symbol="000002",
            asset_id=self.asset.asset_id,
            price=16.25,
            change=0.25,
            pct_change=1.56,
            volume=15000000,
            turnover=243750000.0,
            high_price=16.30,
            low_price=15.95,
            open_price=16.00,
            prev_close=16.00
        )

        self.session.add(realtime_data)
        self.session.commit()

        saved_data = self.session.query(RealtimeStockData).filter_by(
            symbol="000002"
        ).first()

        self.assertIsNotNone(saved_data)
        self.assertEqual(saved_data.price, 16.25)
        self.assertEqual(saved_data.pct_change, 1.56)
    
    def test_intraday_stock_data_creation(self):
        """Test intraday stock data creation."""
        intraday_data = IntradayStockData(
            asset_id=self.asset.asset_id,
            capture_time=datetime.now(),
            latest_price=16.15,
            volume=1000000,
            turnover=16150000.0,
            pct_change=1.56,
            change=0.25
        )

        self.session.add(intraday_data)
        self.session.commit()

        saved_data = self.session.query(IntradayStockData).filter_by(
            asset_id=self.asset.asset_id
        ).first()

        self.assertIsNotNone(saved_data)
        self.assertEqual(saved_data.latest_price, 16.15)
        self.assertEqual(saved_data.volume, 1000000)


class TestSystemMetricsModels(TestCoreModels):
    """Test system metrics models."""
    
    def test_request_log_creation(self):
        """Test request log creation."""
        request_log = RequestLog(
            symbol="000001",
            start_date="20240101",
            end_date="20240131",
            endpoint="/api/v1/stocks/000001/daily",
            status_code=200,
            response_time_ms=125.0,
            record_count=21,
            cache_hit=False,
            akshare_called=True,
            user_agent="QuantDB-Client/1.0",
            ip_address="127.0.0.1"
        )

        self.session.add(request_log)
        self.session.commit()

        saved_log = self.session.query(RequestLog).first()
        self.assertIsNotNone(saved_log)
        self.assertEqual(saved_log.endpoint, "/api/v1/stocks/000001/daily")
        self.assertEqual(saved_log.status_code, 200)
        self.assertEqual(saved_log.response_time_ms, 125.0)
    
    def test_data_coverage_creation(self):
        """Test data coverage creation."""
        coverage = DataCoverage(
            symbol="000001",
            earliest_date="20240101",
            latest_date="20240131",
            total_records=21,
            first_requested=datetime.now(),
            last_accessed=datetime.now(),
            access_count=15
        )

        self.session.add(coverage)
        self.session.commit()

        saved_coverage = self.session.query(DataCoverage).first()
        self.assertIsNotNone(saved_coverage)
        self.assertEqual(saved_coverage.symbol, "000001")
        self.assertEqual(saved_coverage.total_records, 21)
        self.assertEqual(saved_coverage.access_count, 15)
    
    def test_system_metrics_creation(self):
        """Test system metrics creation."""
        metrics = SystemMetrics(
            total_symbols=150,
            total_records=50000,
            db_size_mb=125.5,
            avg_response_time_ms=85.5,
            cache_hit_rate=0.85,
            akshare_requests_today=25,
            requests_today=100,
            active_symbols_today=45,
            performance_improvement=0.75,
            cost_savings=75.0
        )

        self.session.add(metrics)
        self.session.commit()

        saved_metrics = self.session.query(SystemMetrics).first()
        self.assertIsNotNone(saved_metrics)
        self.assertEqual(saved_metrics.total_symbols, 150)
        self.assertEqual(saved_metrics.cache_hit_rate, 0.85)


class TestIndexDataModels(TestCoreModels):
    """Test index data models."""
    
    def test_index_data_creation(self):
        """Test index data creation."""
        index_data = IndexData(
            symbol="000001",
            name="上证指数",
            date=date(2024, 1, 15),
            open_price=3000.50,
            high_price=3050.20,
            low_price=2995.30,
            close_price=3025.80,
            volume=250000000000,
            turnover=350000000000.0
        )

        self.session.add(index_data)
        self.session.commit()

        saved_data = self.session.query(IndexData).filter_by(symbol="000001").first()
        self.assertIsNotNone(saved_data)
        self.assertEqual(saved_data.name, "上证指数")
        self.assertEqual(saved_data.close_price, 3025.80)
    
    def test_realtime_index_data_creation(self):
        """Test realtime index data creation."""
        realtime_index = RealtimeIndexData(
            symbol="399001",
            name="深证成指",
            price=9500.25,
            change=25.80,
            pct_change=0.27,
            volume=180000000000,
            turnover=220000000000.0,
            timestamp=datetime.now()
        )

        self.session.add(realtime_index)
        self.session.commit()

        saved_data = self.session.query(RealtimeIndexData).filter_by(
            symbol="399001"
        ).first()
        self.assertIsNotNone(saved_data)
        self.assertEqual(saved_data.price, 9500.25)
        self.assertEqual(saved_data.pct_change, 0.27)


class TestFinancialDataModels(TestCoreModels):
    """Test financial data models."""
    
    def test_financial_summary_creation(self):
        """Test financial summary creation."""
        financial_summary = FinancialSummary(
            symbol="000001",
            report_period="20231231",
            report_type="Q4",
            total_revenue=125000000000.0,
            net_profit=35000000000.0,
            total_assets=2800000000000.0,
            shareholders_equity=280000000000.0,
            roe=12.5,
            roa=1.25,
            gross_margin=0.45,
            net_margin=0.28
        )

        self.session.add(financial_summary)
        self.session.commit()

        saved_summary = self.session.query(FinancialSummary).filter_by(
            symbol="000001"
        ).first()
        self.assertIsNotNone(saved_summary)
        self.assertEqual(saved_summary.net_profit, 35000000000.0)
        self.assertEqual(saved_summary.roe, 12.5)
    
    def test_financial_indicators_creation(self):
        """Test financial indicators creation."""
        indicators = FinancialIndicators(
            symbol="000001",
            report_period="20231231",
            eps=2.85,
            pe_ratio=5.23,
            pb_ratio=0.67,
            ps_ratio=1.45,
            revenue_growth=0.15,
            profit_growth=0.12,
            debt_to_equity=2.15,
            current_ratio=1.35,
            quick_ratio=1.20
        )

        self.session.add(indicators)
        self.session.commit()

        saved_indicators = self.session.query(FinancialIndicators).filter_by(
            symbol="000001"
        ).first()
        self.assertIsNotNone(saved_indicators)
        self.assertEqual(saved_indicators.pe_ratio, 5.23)
        self.assertEqual(saved_indicators.debt_to_equity, 2.15)


if __name__ == "__main__":
    unittest.main()
