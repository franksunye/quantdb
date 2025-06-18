"""
Test configuration for QuantDB Cloud Edition
"""
import pytest
import tempfile
import os
import sys
from pathlib import Path

# Add src directory to Python path
current_dir = Path(__file__).parent.parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

@pytest.fixture(scope="session")
def test_db():
    """Create a temporary test database"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_file:
        test_db_path = tmp_file.name
    
    # Set environment variable for test database
    os.environ["DATABASE_URL"] = f"sqlite:///{test_db_path}"
    
    yield test_db_path
    
    # Cleanup
    if os.path.exists(test_db_path):
        os.unlink(test_db_path)

@pytest.fixture
def db_session(test_db):
    """Create a database session for testing"""
    from api.database import engine, SessionLocal, Base
    from api.models import Asset, DailyStockData  # Import models to register them
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    session = SessionLocal()
    
    yield session
    
    # Cleanup
    session.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def sample_asset_data():
    """Sample asset data for testing"""
    return {
        'symbol': '600000',
        'name': '浦发银行',
        'isin': 'CNE000001Z29',
        'asset_type': 'stock',
        'exchange': 'SSE',
        'currency': 'CNY',
        'industry': '银行',
        'concept': '银行股',
        'total_shares': 29352000000,
        'circulating_shares': 29352000000,
        'pe_ratio': 4.5,
        'pb_ratio': 0.6,
        'roe': 12.5
    }

@pytest.fixture
def sample_stock_data():
    """Sample stock data for testing"""
    import pandas as pd
    from datetime import datetime, timedelta
    
    dates = [datetime.now() - timedelta(days=i) for i in range(5, 0, -1)]
    
    return pd.DataFrame({
        'date': dates,
        'open': [10.0, 10.1, 10.2, 10.3, 10.4],
        'high': [10.5, 10.6, 10.7, 10.8, 10.9],
        'low': [9.5, 9.6, 9.7, 9.8, 9.9],
        'close': [10.2, 10.3, 10.4, 10.5, 10.6],
        'volume': [1000000, 1100000, 1200000, 1300000, 1400000],
        'turnover': [10200000, 11330000, 12480000, 13650000, 14840000],
        'amplitude': [10.0, 9.9, 9.8, 9.7, 9.6],
        'pct_change': [2.0, 0.98, 0.97, 0.96, 0.95],
        'change': [0.2, 0.1, 0.1, 0.1, 0.1],
        'turnover_rate': [3.4, 3.7, 4.1, 4.4, 4.8]
    })

@pytest.fixture
def mock_akshare_adapter():
    """Mock AKShare adapter for testing"""
    class MockAKShareAdapter:
        def get_stock_data(self, symbol, start_date, end_date, adjust=""):
            # Return sample data
            import pandas as pd
            from datetime import datetime
            
            return pd.DataFrame({
                'date': [datetime.now()],
                'open': [10.0],
                'high': [10.5],
                'low': [9.5],
                'close': [10.2],
                'volume': [1000000],
                'turnover': [10200000],
                'amplitude': [10.0],
                'pct_change': [2.0],
                'change': [0.2],
                'turnover_rate': [3.4]
            })
    
    return MockAKShareAdapter()
