#!/usr/bin/env python3
"""
Hong Kong Index Data Example

This example demonstrates how to use QuantDB to fetch Hong Kong stock index data,
including the major Hang Seng family indexes (HSI, HSCEI, HSTECH).

Features demonstrated:
- Historical data retrieval for HK indexes
- Realtime quotes for HK indexes  
- Index list with Hong Kong category
- Symbol alias support
- Data structure and formatting
"""

import sys
import os
from datetime import datetime, timedelta

# Add project root to path for development
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import qdb


def demo_hk_historical_data():
    """Demonstrate Hong Kong index historical data retrieval."""
    print("=" * 60)
    print("📈 Hong Kong Index Historical Data Demo")
    print("=" * 60)
    
    # Calculate date range (last 30 days)
    end_date = datetime.now().strftime('%Y%m%d')
    start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
    
    # Major Hong Kong indexes
    hk_indexes = {
        'HSI': 'Hang Seng Index',
        'HSCEI': 'Hang Seng China Enterprises Index',
        'HSTECH': 'Hang Seng TECH Index'
    }

    for symbol, name in hk_indexes.items():
        print(f"\n📊 Fetching {symbol} ({name}) data...")
        try:
            df = qdb.get_index_data(symbol, start_date, end_date, 'daily')
            
            if not df.empty:
                print(f"   ✅ Retrieved {len(df)} rows")
                print(f"   📅 Date range: {df['date'].min()} to {df['date'].max()}")
                print(f"   💰 Latest close: {df.iloc[-1]['close']:,.2f}")
                print(f"   📈 Period change: {((df.iloc[-1]['close'] / df.iloc[0]['close']) - 1) * 100:+.2f}%")
                
                # Show sample data
                print("   📋 Sample data (last 3 days):")
                sample = df.tail(3)[['date', 'open', 'high', 'low', 'close', 'volume']]
                for _, row in sample.iterrows():
                    print(f"      {row['date']}: {row['close']:,.2f} (Vol: {row['volume']:,})")
            else:
                print("   ❌ No data available")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")


def demo_hk_realtime_data():
    """Demonstrate Hong Kong index realtime data retrieval."""
    print("\n" + "=" * 60)
    print("⚡ Hong Kong Index Realtime Data Demo")
    print("=" * 60)
    
    hk_indexes = ['HSI', 'HSCEI', 'HSTECH']
    
    print("\n📊 Current Hong Kong Index Quotes:")
    print("-" * 60)
    
    for symbol in hk_indexes:
        try:
            quote = qdb.get_index_realtime(symbol)
            
            if quote:
                change_color = "🟢" if quote['change'] >= 0 else "🔴"
                print(f"{change_color} {symbol:8} | {quote['name']:12} | {quote['price']:>10,.2f} | {quote['change']:>+8.2f} ({quote['pct_change']:>+6.2f}%)")
            else:
                print(f"❌ {symbol:8} | No data available")
                
        except Exception as e:
            print(f"❌ {symbol:8} | Error: {e}")


def demo_symbol_aliases():
    """Demonstrate Hong Kong index symbol alias support."""
    print("\n" + "=" * 60)
    print("🔤 Symbol Alias Support Demo")
    print("=" * 60)
    
    # Test different symbol formats for HSI
    hsi_aliases = [
        'HSI',           # Standard
        '^HSI',          # Bloomberg style
        'HK.HSI',        # Market prefix
        'HANG SENG',     # Full name
        'HANG SENG INDEX'  # Full official name
    ]
    
    print("\n📋 Testing HSI symbol aliases:")
    print("-" * 40)
    
    end_date = datetime.now().strftime('%Y%m%d')
    start_date = (datetime.now() - timedelta(days=5)).strftime('%Y%m%d')
    
    for alias in hsi_aliases:
        try:
            df = qdb.get_index_data(alias, start_date, end_date, 'daily')
            
            if not df.empty:
                latest_close = df.iloc[-1]['close']
                print(f"✅ '{alias:15}' -> HSI data: {latest_close:,.2f}")
            else:
                print(f"❌ '{alias:15}' -> No data")
                
        except Exception as e:
            print(f"❌ '{alias:15}' -> Error: {str(e)[:30]}...")


def demo_hk_index_list():
    """Demonstrate Hong Kong index list retrieval."""
    print("\n" + "=" * 60)
    print("📋 Hong Kong Index List Demo")
    print("=" * 60)
    
    try:
        # Get all Hong Kong indexes
        hk_indexes = qdb.get_index_list(category='香港指数')
        
        if hk_indexes:
            print(f"\n📊 Found {len(hk_indexes)} Hong Kong indexes")
            print("-" * 60)
            
            # Show major indexes first
            major_symbols = ['HSI', 'HSCEI', 'HSTECH']
            major_indexes = [idx for idx in hk_indexes if idx['symbol'] in major_symbols]
            
            if major_indexes:
                print("🌟 Major Indexes:")
                for idx in major_indexes:
                    print(f"   {idx['symbol']:8} | {idx['name']:20} | {idx['price']:>10,.2f}")
            
            # Show other indexes (first 10)
            other_indexes = [idx for idx in hk_indexes if idx['symbol'] not in major_symbols][:10]
            if other_indexes:
                print(f"\n📈 Other Indexes (showing first 10 of {len(other_indexes)}):")
                for idx in other_indexes:
                    print(f"   {idx['symbol']:8} | {idx['name']:20} | {idx['price']:>10,.2f}")
                    
        else:
            print("❌ No Hong Kong indexes found")
            
    except Exception as e:
        print(f"❌ Error retrieving index list: {e}")


def demo_data_structure():
    """Demonstrate the data structure of Hong Kong index data."""
    print("\n" + "=" * 60)
    print("🏗️ Data Structure Demo")
    print("=" * 60)
    
    try:
        # Get sample historical data
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=3)).strftime('%Y%m%d')
        
        df = qdb.get_index_data('HSI', start_date, end_date, 'daily')
        
        if not df.empty:
            print("\n📊 Historical Data Structure:")
            print(f"   Columns: {list(df.columns)}")
            print(f"   Data types: {dict(df.dtypes)}")
            print(f"   Shape: {df.shape}")
            
            print("\n📋 Sample historical record:")
            sample = df.iloc[-1]
            for col in df.columns:
                print(f"   {col:12}: {sample[col]}")
        
        # Get sample realtime data
        quote = qdb.get_index_realtime('HSI')
        
        if quote:
            print("\n⚡ Realtime Data Structure:")
            print(f"   Keys: {list(quote.keys())}")
            
            print("\n📋 Sample realtime record:")
            for key, value in quote.items():
                print(f"   {key:12}: {value}")
                
    except Exception as e:
        print(f"❌ Error: {e}")


def main():
    """Run all Hong Kong index demos."""
    print("🇭🇰 QuantDB Hong Kong Index Support Demo")
    print("🚀 Demonstrating HSI, HSCEI, HSTECH data access")
    
    try:
        # Run all demos
        demo_hk_historical_data()
        demo_hk_realtime_data()
        demo_symbol_aliases()
        demo_hk_index_list()
        demo_data_structure()
        
        print("\n" + "=" * 60)
        print("🎉 Hong Kong Index Demo Completed Successfully!")
        print("📚 For more information, see: docs/guides/hong-kong-index-guide.md")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        print("💡 Make sure QuantDB is properly installed and configured")


if __name__ == "__main__":
    main()
