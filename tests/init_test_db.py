"""
Initialize the test database for testing
"""
import sys
from pathlib import Path

# Add the parent directory to the path so we can import from src
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.api.database import Base
from src.api.models import Asset, Price
from datetime import date, timedelta

def init_test_db():
    """Initialize the test database for testing"""
    # Create in-memory SQLite database for testing
    SQLALCHEMY_DATABASE_URL = "sqlite:///./database/test_db.db"
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    # Create tables
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    # Create session
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    
    # Add test data
    test_assets = [
        Asset(
            symbol="000001",
            name="平安银行",
            isin="CNE000000040",
            asset_type="stock",
            exchange="SZSE",
            currency="CNY"
        ),
        Asset(
            symbol="600519",
            name="贵州茅台",
            isin="CNE0000018R8",
            asset_type="stock",
            exchange="SHSE",
            currency="CNY"
        ),
        Asset(
            symbol="AAPL",
            name="Apple Inc.",
            isin="US0378331005",
            asset_type="stock",
            exchange="NASDAQ",
            currency="USD"
        ),
        Asset(
            symbol="MSFT",
            name="Microsoft Corporation",
            isin="US5949181045",
            asset_type="stock",
            exchange="NASDAQ",
            currency="USD"
        ),
        Asset(
            symbol="GOOG",
            name="Alphabet Inc.",
            isin="US02079K1079",
            asset_type="stock",
            exchange="NASDAQ",
            currency="USD"
        )
    ]
    
    db.add_all(test_assets)
    db.commit()
    
    # Add test prices
    today = date.today()
    test_prices = []
    
    # Add prices for test assets
    for asset in test_assets:
        for i in range(30):
            price_date = today - timedelta(days=i)
            test_prices.append(
                Price(
                    asset_id=asset.asset_id,
                    date=price_date,
                    open=100.0 + i,
                    high=105.0 + i,
                    low=95.0 + i,
                    close=102.0 + i,
                    volume=1000000 + i * 10000,
                    adjusted_close=102.0 + i
                )
            )
    
    db.add_all(test_prices)
    db.commit()
    
    db.close()
    
    print("Test database initialized successfully.")

if __name__ == "__main__":
    init_test_db()
