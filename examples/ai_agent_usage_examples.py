#!/usr/bin/env python3
"""
AI Agent Usage Examples for QDB Package

This file demonstrates how AI agents can effectively use the QDB package
with the improved, standardized docstrings and clear parameter specifications.

These examples show proper error handling, parameter validation, and
typical usage patterns that AI agents should follow.
"""

from typing import Any, Dict, List

import pandas as pd

import qdb


def example_basic_stock_data():
    """Example: Basic stock data retrieval with proper error handling."""
    print("=== Basic Stock Data Retrieval ===")

    try:
        # Get recent data for Ping An Bank (000001)
        df = qdb.get_stock_data("000001", days=30)
        print(f"✅ Retrieved {len(df)} trading days for 000001")
        print(f"Price range: ¥{df['low'].min():.2f} - ¥{df['high'].max():.2f}")
        print(f"Latest close: ¥{df.iloc[-1]['close']:.2f}")

    except ValueError as e:
        print(f"❌ Invalid parameters: {e}")
    except Exception as e:
        print(f"❌ Error retrieving data: {e}")


def example_date_range_data():
    """Example: Getting data for specific date range."""
    print("\n=== Date Range Data Retrieval ===")

    try:
        # Get data for specific period
        df = qdb.get_stock_data(
            "600000",
            start_date="20240101",
            end_date="20240201",  # Pudong Development Bank
        )
        print(f"✅ Retrieved {len(df)} trading days for 600000")

        if not df.empty:
            returns = df["close"].pct_change().dropna()
            print(f"Average daily return: {returns.mean():.4f}")
            print(f"Volatility: {returns.std():.4f}")

    except ValueError as e:
        print(f"❌ Invalid date format or range: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")


def example_adjusted_prices():
    """Example: Using price adjustments for analysis."""
    print("\n=== Price Adjustment Examples ===")

    symbol = "300001"  # ChiNext stock

    try:
        # Get raw prices
        df_raw = qdb.get_stock_data(symbol, days=100, adjust="")
        print(f"✅ Raw prices: {len(df_raw)} days")

        # Get forward-adjusted prices (better for returns analysis)
        df_adj = qdb.get_stock_data(symbol, days=100, adjust="qfq")
        print(f"✅ Forward-adjusted prices: {len(df_adj)} days")

        if not df_raw.empty and not df_adj.empty:
            raw_return = (df_raw.iloc[-1]["close"] / df_raw.iloc[0]["close"] - 1) * 100
            adj_return = (df_adj.iloc[-1]["close"] / df_adj.iloc[0]["close"] - 1) * 100
            print(f"Raw return: {raw_return:.2f}%")
            print(f"Adjusted return: {adj_return:.2f}%")

    except Exception as e:
        print(f"❌ Error: {e}")


def example_realtime_data():
    """Example: Getting real-time stock quotes."""
    print("\n=== Real-time Data Examples ===")

    symbols = ["000001", "600000", "300001"]

    for symbol in symbols:
        try:
            data = qdb.get_realtime_data(symbol)

            print(f"📊 {symbol} - {data.get('name', 'Unknown')}")
            print(f"   Current: ¥{data.get('current_price', 0):.2f}")
            print(f"   Change: {data.get('change_percent', 0):+.2f}%")
            print(f"   Volume: {data.get('volume', 0):,}")
            print(f"   Status: {data.get('market_status', 'Unknown')}")

        except ValueError as e:
            print(f"❌ Invalid symbol {symbol}: {e}")
        except Exception as e:
            print(f"❌ Error for {symbol}: {e}")


def example_stock_list_filtering():
    """Example: Getting and filtering stock lists."""
    print("\n=== Stock List Filtering ===")

    try:
        # Get Shanghai stocks only
        sh_stocks = qdb.get_stock_list(market="SHSE")
        print(f"✅ Shanghai stocks: {len(sh_stocks)}")

        # Show first 5 stocks
        for stock in sh_stocks[:5]:
            print(
                f"   {stock['symbol']}: {stock['name']} ({stock.get('industry', 'N/A')})"
            )

        # Get all stocks and analyze by market
        all_stocks = qdb.get_stock_list()
        markets = {}
        for stock in all_stocks:
            market = stock.get("market", "Unknown")
            markets[market] = markets.get(market, 0) + 1

        print(f"\n📈 Market distribution:")
        for market, count in markets.items():
            print(f"   {market}: {count} stocks")

    except Exception as e:
        print(f"❌ Error: {e}")


def example_cache_monitoring():
    """Example: Monitoring cache performance."""
    print("\n=== Cache Performance Monitoring ===")

    try:
        stats = qdb.cache_stats()

        print(f"📊 Cache Statistics:")
        print(f"   Directory: {stats.get('cache_dir', 'Unknown')}")
        print(f"   Size: {stats.get('cache_size_mb', 0):.1f} MB")
        print(f"   Status: {stats.get('status', 'Unknown')}")
        print(f"   Initialized: {stats.get('initialized', False)}")

        # Performance assessment
        hit_rate = stats.get("hit_rate", 0)
        if hit_rate > 80:
            print("   🟢 Excellent cache performance!")
        elif hit_rate > 50:
            print("   🟡 Good cache performance")
        else:
            print("   🔴 Consider warming up cache")

    except Exception as e:
        print(f"❌ Cache error: {e}")


def example_error_handling_patterns():
    """Example: Comprehensive error handling patterns."""
    print("\n=== Error Handling Patterns ===")

    # Test invalid symbol format
    try:
        df = qdb.get_stock_data("INVALID")
    except ValueError as e:
        print(f"✅ Caught invalid symbol: {e}")

    # Test conflicting parameters
    try:
        df = qdb.get_stock_data("000001", days=30, start_date="20240101")
    except ValueError as e:
        print(f"✅ Caught parameter conflict: {e}")

    # Test invalid date format
    try:
        df = qdb.get_stock_data("000001", start_date="2024-01-01")  # Wrong format
    except ValueError as e:
        print(f"✅ Caught invalid date format: {e}")

    # Test invalid market filter
    try:
        stocks = qdb.get_stock_list(market="INVALID")
    except ValueError as e:
        print(f"✅ Caught invalid market: {e}")


def example_batch_processing():
    """Example: Efficient batch processing of multiple stocks."""
    print("\n=== Batch Processing Example ===")

    symbols = ["000001", "000002", "600000", "600036", "300001"]

    try:
        # Method 1: Using get_multiple_stocks (if available)
        try:
            batch_data = qdb.get_multiple_stocks(symbols, days=30)
            print(f"✅ Batch method: Retrieved data for {len(batch_data)} symbols")

            for symbol, df in batch_data.items():
                if not df.empty:
                    latest_price = df.iloc[-1]["close"]
                    print(f"   {symbol}: ¥{latest_price:.2f}")
                else:
                    print(f"   {symbol}: No data available")

        except AttributeError:
            # Fallback to individual calls
            print("📝 Using individual calls method:")
            for symbol in symbols:
                try:
                    df = qdb.get_stock_data(symbol, days=5)
                    if not df.empty:
                        latest_price = df.iloc[-1]["close"]
                        print(f"   {symbol}: ¥{latest_price:.2f}")
                except Exception as e:
                    print(f"   {symbol}: Error - {e}")

    except Exception as e:
        print(f"❌ Batch processing error: {e}")


def main():
    """Run all examples to demonstrate AI agent usage patterns."""
    print("🤖 QDB AI Agent Usage Examples")
    print("=" * 50)

    # Initialize QDB (optional, but good practice)
    try:
        qdb.init()
        print("✅ QDB initialized successfully\n")
    except Exception as e:
        print(f"⚠️ QDB initialization warning: {e}\n")

    # Run all examples
    example_basic_stock_data()
    example_date_range_data()
    example_adjusted_prices()
    example_realtime_data()
    example_stock_list_filtering()
    example_cache_monitoring()
    example_error_handling_patterns()
    example_batch_processing()

    print("\n" + "=" * 50)
    print("🎉 All examples completed!")
    print("\nThese examples demonstrate proper QDB usage patterns")
    print("that AI agents should follow for reliable operation.")


if __name__ == "__main__":
    main()
