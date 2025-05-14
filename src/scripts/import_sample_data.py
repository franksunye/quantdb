"""
Script to import sample data into the database
"""
import os
import sys
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

# Add the parent directory to the path so we can import from src
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from src.api.database import SessionLocal
from src.services.data_import import DataImportService
from src.logger import setup_logger

# Setup logger
logger = setup_logger(__name__)

def create_sample_data_directory():
    """Create directory for sample data if it doesn't exist"""
    sample_data_dir = Path(__file__).resolve().parent.parent.parent / "data" / "sample"
    if not sample_data_dir.exists():
        sample_data_dir.mkdir(parents=True)
        logger.info(f"Created sample data directory: {sample_data_dir}")
    return sample_data_dir

def generate_sample_asset_data(sample_data_dir):
    """Generate sample asset data CSV"""
    assets_file = sample_data_dir / "sample_assets.csv"
    
    # Sample assets data
    assets_data = [
        {
            "symbol": "AAPL", 
            "name": "Apple Inc.", 
            "isin": "US0378331005", 
            "asset_type": "stock", 
            "exchange": "NASDAQ", 
            "currency": "USD"
        },
        {
            "symbol": "MSFT", 
            "name": "Microsoft Corporation", 
            "isin": "US5949181045", 
            "asset_type": "stock", 
            "exchange": "NASDAQ", 
            "currency": "USD"
        },
        {
            "symbol": "GOOG", 
            "name": "Alphabet Inc.", 
            "isin": "US02079K1079", 
            "asset_type": "stock", 
            "exchange": "NASDAQ", 
            "currency": "USD"
        },
        {
            "symbol": "AMZN", 
            "name": "Amazon.com Inc.", 
            "isin": "US0231351067", 
            "asset_type": "stock", 
            "exchange": "NASDAQ", 
            "currency": "USD"
        },
        {
            "symbol": "TSLA", 
            "name": "Tesla Inc.", 
            "isin": "US88160R1014", 
            "asset_type": "stock", 
            "exchange": "NASDAQ", 
            "currency": "USD"
        },
        {
            "symbol": "^GSPC", 
            "name": "S&P 500", 
            "isin": "US78378X1072", 
            "asset_type": "index", 
            "exchange": "NYSE", 
            "currency": "USD"
        },
        {
            "symbol": "^DJI", 
            "name": "Dow Jones Industrial Average", 
            "isin": "US2605661048", 
            "asset_type": "index", 
            "exchange": "NYSE", 
            "currency": "USD"
        }
    ]
    
    # Create DataFrame and save to CSV
    assets_df = pd.DataFrame(assets_data)
    assets_df.to_csv(assets_file, index=False)
    logger.info(f"Generated sample assets data: {assets_file}")
    
    return assets_file

def generate_sample_price_data(sample_data_dir, symbol, days=365):
    """Generate sample price data CSV for a symbol"""
    price_file = sample_data_dir / f"sample_prices_{symbol}.csv"
    
    # Generate dates
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)
    dates = pd.date_range(start=start_date, end=end_date)
    
    # Generate random price data
    import numpy as np
    np.random.seed(42)  # For reproducibility
    
    # Start with a base price
    if symbol == "AAPL":
        base_price = 150.0
    elif symbol == "MSFT":
        base_price = 300.0
    elif symbol == "GOOG":
        base_price = 2800.0
    elif symbol == "AMZN":
        base_price = 3500.0
    elif symbol == "TSLA":
        base_price = 900.0
    elif symbol == "^GSPC":
        base_price = 4500.0
    elif symbol == "^DJI":
        base_price = 35000.0
    else:
        base_price = 100.0
    
    # Generate price series with random walk
    price_series = [base_price]
    for i in range(1, len(dates)):
        # Random daily change (-2% to +2%)
        daily_change = np.random.normal(0.0005, 0.015)
        new_price = price_series[-1] * (1 + daily_change)
        price_series.append(new_price)
    
    # Create price data
    price_data = []
    for i, date in enumerate(dates):
        price = price_series[i]
        daily_volatility = price * 0.015  # 1.5% volatility
        
        # Generate OHLC data
        open_price = price * (1 + np.random.normal(0, 0.005))
        high_price = max(open_price, price) * (1 + abs(np.random.normal(0, 0.008)))
        low_price = min(open_price, price) * (1 - abs(np.random.normal(0, 0.008)))
        close_price = price
        
        # Generate volume
        volume = int(np.random.normal(1000000, 500000))
        if volume < 100000:
            volume = 100000
        
        price_data.append({
            "date": date.strftime("%Y-%m-%d"),
            "open": round(open_price, 2),
            "high": round(high_price, 2),
            "low": round(low_price, 2),
            "close": round(close_price, 2),
            "volume": volume,
            "adjusted_close": round(close_price, 2)
        })
    
    # Create DataFrame and save to CSV
    prices_df = pd.DataFrame(price_data)
    prices_df.to_csv(price_file, index=False)
    logger.info(f"Generated sample price data for {symbol}: {price_file}")
    
    return price_file

def import_sample_data():
    """Import sample data into the database"""
    try:
        # Create sample data directory
        sample_data_dir = create_sample_data_directory()
        
        # Create database session
        db = SessionLocal()
        
        # Create data import service
        import_service = DataImportService(db)
        
        # Generate and import sample asset data
        assets_file = generate_sample_asset_data(sample_data_dir)
        assets_df = pd.read_csv(assets_file)
        
        # Import assets
        imported_assets = []
        for _, row in assets_df.iterrows():
            asset = import_service.import_asset(
                symbol=row["symbol"],
                name=row["name"],
                isin=row["isin"],
                asset_type=row["asset_type"],
                exchange=row["exchange"],
                currency=row["currency"]
            )
            imported_assets.append(asset)
            logger.info(f"Imported asset: {asset.symbol} ({asset.name})")
        
        # Generate and import sample price data for each asset
        for asset in imported_assets:
            # Generate sample price data
            price_file = generate_sample_price_data(sample_data_dir, asset.symbol)
            
            # Import price data
            import_result = import_service.import_from_csv(
                file_path=str(price_file),
                asset_id=asset.asset_id
            )
            logger.info(f"Imported {import_result['records_imported']} price records for {asset.symbol}")
        
        logger.info("Sample data import completed successfully")
        return True
    
    except SQLAlchemyError as e:
        logger.error(f"Database error during sample data import: {e}")
        return False
    except Exception as e:
        logger.error(f"Error during sample data import: {e}")
        return False
    finally:
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    logger.info("Starting sample data import...")
    success = import_sample_data()
    if success:
        logger.info("Sample data import completed successfully")
    else:
        logger.error("Sample data import failed")
        sys.exit(1)
