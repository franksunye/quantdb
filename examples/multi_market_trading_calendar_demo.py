#!/usr/bin/env python3
"""
Multi-Market Trading Calendar Demo

This example demonstrates the new multi-market trading calendar functionality
that supports both China A-shares and Hong Kong stock markets using pandas_market_calendars.
"""

import os
import sys
from datetime import datetime, timedelta

# Add the project root to Python path
sys.path.insert(0, os.path.abspath('.'))

def demo_basic_usage():
    """Demonstrate basic usage of the multi-market trading calendar"""
    print("🚀 Multi-Market Trading Calendar Demo")
    print("=" * 50)
    
    # Import the trading calendar functions
    from core.services.trading_calendar import (
        Market,
        is_trading_day,
        get_trading_days,
        is_hk_trading_day,
        get_hk_trading_days,
        is_china_a_trading_day,
        get_china_a_trading_days,
        get_trading_calendar
    )
    
    # Get some test dates
    today = datetime.now().strftime("%Y%m%d")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
    week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y%m%d")
    
    print(f"📅 Test dates: {week_ago} to {today}")
    
    # 1. Backward Compatibility - existing code still works
    print(f"\n1️⃣  Backward Compatibility (defaults to China A-shares)")
    print(f"   is_trading_day('{today}'): {is_trading_day(today)}")
    china_days = get_trading_days(week_ago, today)
    print(f"   Trading days in last week: {len(china_days)} days")
    
    # 2. Market-specific functions
    print(f"\n2️⃣  Market-Specific Functions")
    print(f"   🇨🇳 China A-shares:")
    print(f"      is_china_a_trading_day('{today}'): {is_china_a_trading_day(today)}")
    china_days = get_china_a_trading_days(week_ago, today)
    print(f"      Trading days: {len(china_days)} days")
    
    print(f"   🇭🇰 Hong Kong:")
    print(f"      is_hk_trading_day('{today}'): {is_hk_trading_day(today)}")
    hk_days = get_hk_trading_days(week_ago, today)
    print(f"      Trading days: {len(hk_days)} days")
    
    # 3. Symbol-based market detection
    print(f"\n3️⃣  Symbol-Based Market Detection")
    test_symbols = {
        "000001": "平安银行 (Shenzhen)",
        "600000": "浦发银行 (Shanghai)",
        "300001": "特锐德 (ChiNext)",
        "00700": "腾讯控股 (Hong Kong)",
        "HK.00700": "腾讯控股 (Hong Kong with prefix)"
    }
    
    for symbol, name in test_symbols.items():
        result = is_trading_day(today, symbol=symbol)
        market = Market.from_symbol(symbol)
        print(f"   {symbol} ({name})")
        print(f"      Market: {market.value}, Trading today: {result}")
    
    # 4. Explicit market parameter
    print(f"\n4️⃣  Explicit Market Parameter")
    china_explicit = is_trading_day(today, market=Market.CHINA_A)
    hk_explicit = is_trading_day(today, market=Market.HONG_KONG)
    print(f"   China A-shares (explicit): {china_explicit}")
    print(f"   Hong Kong (explicit): {hk_explicit}")
    
    # 5. Calendar information
    print(f"\n5️⃣  Calendar Information")
    calendar = get_trading_calendar()
    info = calendar.get_calendar_info()
    print(f"   Total trading days loaded: {info['total_trading_days']}")
    print(f"   Supported markets: {len(info['market_details'])}")
    
    for market_name, details in info['market_details'].items():
        print(f"      {market_name}: {details['trading_days']} days")


def demo_practical_examples():
    """Show practical examples of using the multi-market calendar"""
    print(f"\n\n💼 Practical Examples")
    print("=" * 50)
    
    from core.services.trading_calendar import (
        get_china_a_trading_days,
        get_hk_trading_days,
        is_trading_day
    )
    
    # Example 1: Portfolio management across markets
    print(f"📊 Example 1: Cross-Market Portfolio Analysis")
    
    # Get trading days for the last month
    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")
    
    china_days = get_china_a_trading_days(start_date, end_date)
    hk_days = get_hk_trading_days(start_date, end_date)
    
    print(f"   Period: {start_date} to {end_date}")
    print(f"   China A-shares trading days: {len(china_days)}")
    print(f"   Hong Kong trading days: {len(hk_days)}")
    
    # Find common trading days
    common_days = set(china_days) & set(hk_days)
    print(f"   Common trading days: {len(common_days)}")
    print(f"   Market-specific days: China A={len(china_days) - len(common_days)}, HK={len(hk_days) - len(common_days)}")
    
    # Example 2: Data collection scheduling
    print(f"\n📡 Example 2: Data Collection Scheduling")
    
    # Check if we should collect data today for different markets
    today = datetime.now().strftime("%Y%m%d")
    
    portfolios = {
        "China Tech": ["000001", "600000", "300001"],  # China A-shares
        "HK Blue Chips": ["00700", "00941", "01299"],  # Hong Kong stocks
        "Cross-Market": ["600000", "00700"]  # Mixed portfolio
    }
    
    for portfolio_name, symbols in portfolios.items():
        print(f"   {portfolio_name}:")
        for symbol in symbols:
            should_collect = is_trading_day(today, symbol=symbol)
            market = "China A" if symbol.startswith(('0', '3', '6')) else "Hong Kong"
            print(f"      {symbol} ({market}): {'✅ Collect' if should_collect else '❌ Skip'}")
    
    # Example 3: Holiday analysis
    print(f"\n🎉 Example 3: Holiday Analysis")
    
    # Check some known holiday periods
    holiday_periods = [
        ("20240101", "New Year's Day"),
        ("20240210", "Chinese New Year (approx)"),
        ("20240501", "Labor Day"),
        ("20241001", "National Day")
    ]
    
    for date, holiday_name in holiday_periods:
        china_trading = is_trading_day(date, market="china_a")  # Can use string too
        hk_trading = is_trading_day(date, symbol="00700")  # Or symbol-based detection
        
        print(f"   {date} ({holiday_name}):")
        print(f"      China A-shares: {'Trading' if china_trading else 'Holiday'}")
        print(f"      Hong Kong: {'Trading' if hk_trading else 'Holiday'}")


def demo_migration_guide():
    """Show how to migrate existing code to use the new features"""
    print(f"\n\n🔄 Migration Guide")
    print("=" * 50)
    
    print("Old code (still works):")
    print("```python")
    print("from core.services.trading_calendar import is_trading_day, get_trading_days")
    print("result = is_trading_day('20240101')  # Defaults to China A-shares")
    print("days = get_trading_days('20240101', '20240107')")
    print("```")
    
    print("\nNew code (with multi-market support):")
    print("```python")
    print("from core.services.trading_calendar import (")
    print("    Market, is_trading_day, get_trading_days,")
    print("    is_hk_trading_day, get_hk_trading_days")
    print(")")
    print("")
    print("# Explicit market specification")
    print("result = is_trading_day('20240101', market=Market.HONG_KONG)")
    print("")
    print("# Symbol-based market detection")
    print("result = is_trading_day('20240101', symbol='00700')  # Auto-detects HK")
    print("")
    print("# Market-specific convenience functions")
    print("hk_result = is_hk_trading_day('20240101')")
    print("hk_days = get_hk_trading_days('20240101', '20240107')")
    print("```")
    
    print("\nKey benefits:")
    print("✅ Full backward compatibility - existing code works unchanged")
    print("✅ Support for Hong Kong stock market")
    print("✅ Automatic market detection from stock symbols")
    print("✅ More accurate holiday calendars using pandas_market_calendars")
    print("✅ Better performance with intelligent caching")


if __name__ == "__main__":
    try:
        demo_basic_usage()
        demo_practical_examples()
        demo_migration_guide()
        
        print(f"\n\n🎉 Demo completed successfully!")
        print("The multi-market trading calendar is ready for production use.")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
