#!/usr/bin/env python3
"""
Populate sample data for QuantDB Cloud Edition
"""
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd

# Add src directory to Python path
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

def populate_sample_assets():
    """Populate sample assets"""
    print("📊 Populating sample assets...")
    
    try:
        from api.database import SessionLocal
        from api.models import Asset
        
        db_session = SessionLocal()
        
        # Sample assets data
        sample_assets = [
            {
                'symbol': '600000',
                'name': '浦发银行',
                'isin': 'CNE000001Z29',
                'asset_type': 'stock',
                'exchange': 'SSE',
                'currency': 'CNY',
                'industry': '银行',
                'concept': '银行股',
                'pe_ratio': 4.5,
                'pb_ratio': 0.6,
                'roe': 12.5
            },
            {
                'symbol': '000001',
                'name': '平安银行',
                'isin': 'CNE000001307',
                'asset_type': 'stock',
                'exchange': 'SZSE',
                'currency': 'CNY',
                'industry': '银行',
                'concept': '银行股',
                'pe_ratio': 5.2,
                'pb_ratio': 0.8,
                'roe': 11.8
            },
            {
                'symbol': '600519',
                'name': '贵州茅台',
                'isin': 'CNE000001315',
                'asset_type': 'stock',
                'exchange': 'SSE',
                'currency': 'CNY',
                'industry': '食品饮料',
                'concept': '白酒概念',
                'pe_ratio': 28.5,
                'pb_ratio': 12.8,
                'roe': 25.2
            }
        ]
        
        for asset_data in sample_assets:
            # Check if asset already exists
            existing = db_session.query(Asset).filter(Asset.symbol == asset_data['symbol']).first()
            if not existing:
                asset = Asset(**asset_data)
                db_session.add(asset)
                print(f"  ✅ Added {asset_data['symbol']} - {asset_data['name']}")
            else:
                print(f"  ⏭️  {asset_data['symbol']} - {asset_data['name']} already exists")
        
        db_session.commit()
        db_session.close()
        
        print("✅ Sample assets populated successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Failed to populate sample assets: {e}")
        return False

def populate_sample_stock_data():
    """Populate sample stock data"""
    print("\n📈 Populating sample stock data...")
    
    try:
        from api.database import SessionLocal
        from api.models import Asset, DailyStockData
        
        db_session = SessionLocal()
        
        # Get sample assets
        assets = db_session.query(Asset).filter(Asset.symbol.in_(['600000', '000001', '600519'])).all()
        
        for asset in assets:
            # Check if data already exists
            existing_data = db_session.query(DailyStockData).filter(
                DailyStockData.asset_id == asset.asset_id
            ).first()
            
            if existing_data:
                print(f"  ⏭️  {asset.symbol} - {asset.name} already has data")
                continue
            
            # Generate sample data for last 30 days
            base_price = {'600000': 10.0, '000001': 15.0, '600519': 1800.0}.get(asset.symbol, 10.0)
            
            for i in range(30):
                trade_date = datetime.now().date() - timedelta(days=i)
                
                # Skip weekends (simple approximation)
                if trade_date.weekday() >= 5:
                    continue
                
                # Generate realistic price movement
                price_change = (i % 5 - 2) * 0.02  # -4% to +4% change
                open_price = base_price * (1 + price_change)
                close_price = open_price * (1 + (i % 3 - 1) * 0.01)
                high_price = max(open_price, close_price) * 1.02
                low_price = min(open_price, close_price) * 0.98
                
                volume = 1000000 + (i % 10) * 100000
                
                stock_data = DailyStockData(
                    asset_id=asset.asset_id,
                    trade_date=trade_date,
                    open=round(open_price, 2),
                    high=round(high_price, 2),
                    low=round(low_price, 2),
                    close=round(close_price, 2),
                    volume=volume,
                    turnover=round(close_price * volume, 2),
                    amplitude=round((high_price - low_price) / low_price * 100, 2),
                    pct_change=round((close_price - open_price) / open_price * 100, 2),
                    change=round(close_price - open_price, 2),
                    turnover_rate=round(volume / 1000000000 * 100, 2)
                )
                
                db_session.add(stock_data)
            
            print(f"  ✅ Added sample data for {asset.symbol} - {asset.name}")
        
        db_session.commit()
        db_session.close()
        
        print("✅ Sample stock data populated successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Failed to populate sample stock data: {e}")
        return False

def create_database_summary():
    """Create database summary"""
    print("\n📋 Creating database summary...")
    
    try:
        from api.database import SessionLocal
        from api.models import Asset, DailyStockData
        
        db_session = SessionLocal()
        
        asset_count = db_session.query(Asset).count()
        data_count = db_session.query(DailyStockData).count()
        
        # Get database file size
        db_path = current_dir / "database" / "stock_data.db"
        db_size = 0
        if db_path.exists():
            db_size = db_path.stat().st_size / 1024  # KB
        
        summary = f"""
# QuantDB Cloud Database Summary

**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Database Statistics
- **Assets**: {asset_count} stocks
- **Daily Data Records**: {data_count} records  
- **Database Size**: {db_size:.1f} KB
- **Database File**: `database/stock_data.db`

## Sample Assets Included
"""
        
        assets = db_session.query(Asset).all()
        for asset in assets:
            data_records = db_session.query(DailyStockData).filter(
                DailyStockData.asset_id == asset.asset_id
            ).count()
            summary += f"- **{asset.symbol}** - {asset.name} ({data_records} records)\n"
        
        summary += f"""
## Usage for Streamlit Cloud
This database file is pre-populated and ready for deployment to Streamlit Cloud.
The database includes sample data for demonstration and testing purposes.

## Benefits
✅ No runtime database initialization required
✅ Consistent data across local and cloud environments  
✅ Faster application startup
✅ Reliable demo data for users
"""
        
        # Save summary
        summary_path = current_dir / "DATABASE_SUMMARY.md"
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(summary)
        
        print(f"✅ Database summary saved to {summary_path}")
        
        db_session.close()
        return True
        
    except Exception as e:
        print(f"❌ Failed to create database summary: {e}")
        return False

def main():
    """Main function"""
    print("🚀 QuantDB Sample Data Population")
    print("=" * 50)
    
    # Populate sample data
    steps = [
        ("Sample Assets", populate_sample_assets),
        ("Sample Stock Data", populate_sample_stock_data),
        ("Database Summary", create_database_summary)
    ]
    
    for step_name, step_func in steps:
        print(f"\n📋 {step_name}")
        print("-" * 30)
        
        if not step_func():
            print(f"❌ {step_name} failed!")
            return False
    
    print("\n" + "=" * 50)
    print("🎉 Sample data population completed successfully!")
    print("📁 Database file ready for GitHub commit and Streamlit Cloud deployment")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
