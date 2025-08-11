#!/usr/bin/env python3
"""
Financial and Index Data Analysis Examples for QDB Package

This file demonstrates advanced usage patterns for financial data and index
analysis using the improved QDB package with AI agent-friendly documentation.

These examples show proper error handling, data analysis patterns, and
typical workflows for financial research and quantitative analysis.
"""

import qdb
from typing import List, Dict, Any
import pandas as pd


def example_financial_summary_analysis():
    """Example: Comprehensive financial summary analysis."""
    print("=== Financial Summary Analysis ===")
    
    # Major bank stocks for comparison
    bank_symbols = ["000001", "600000", "600036"]  # Ping An Bank, Pudong Development Bank, China Merchants Bank
    
    for symbol in bank_symbols:
        try:
            summary = qdb.get_financial_summary(symbol)
            
            if 'error' in summary:
                print(f"❌ {symbol}: {summary['error']}")
                continue
                
            print(f"\n📊 {symbol} Financial Summary:")
            print(f"   Available quarters: {summary['count']}")
            
            if summary['quarters']:
                latest = summary['quarters'][0]
                print(f"   Latest period: {latest['period']}")
                
                # Display key metrics
                net_profit = latest.get('net_profit')
                total_revenue = latest.get('total_revenue')
                roe = latest.get('roe')
                
                if net_profit:
                    print(f"   Net profit: {net_profit:.1f} billion yuan")
                if total_revenue:
                    print(f"   Total revenue: {total_revenue:.1f} billion yuan")
                    if net_profit:
                        margin = (net_profit / total_revenue) * 100
                        print(f"   Profit margin: {margin:.2f}%")
                if roe:
                    print(f"   ROE: {roe:.2f}%")
                
                # Analyze trends if multiple quarters available
                if len(summary['quarters']) >= 2:
                    current = summary['quarters'][0]
                    previous = summary['quarters'][1]
                    
                    current_profit = current.get('net_profit')
                    previous_profit = previous.get('net_profit')
                    
                    if current_profit and previous_profit:
                        growth = ((current_profit - previous_profit) / previous_profit) * 100
                        print(f"   QoQ profit growth: {growth:+.1f}%")
                        
        except Exception as e:
            print(f"❌ Error analyzing {symbol}: {e}")


def example_financial_indicators_exploration():
    """Example: Exploring detailed financial indicators."""
    print("\n=== Financial Indicators Exploration ===")
    
    symbol = "600036"  # China Merchants Bank - typically has good data coverage
    
    try:
        indicators = qdb.get_financial_indicators(symbol)
        
        if 'error' in indicators:
            print(f"❌ {symbol}: {indicators['error']}")
            return
            
        print(f"📈 {symbol} Financial Indicators:")
        print(f"   Data shape: {indicators['data_shape']}")
        print(f"   Available columns: {len(indicators.get('columns', []))}")
        
        # Display sample columns
        columns = indicators.get('columns', [])
        if columns:
            print(f"   Sample indicators:")
            for i, col in enumerate(columns[:8]):
                print(f"     {i+1}. {col}")
            if len(columns) > 8:
                print(f"     ... and {len(columns) - 8} more indicators")
        
        # Display sample data
        sample_data = indicators.get('sample_data', [])
        if sample_data:
            print(f"   Sample data (first row):")
            first_row = sample_data[0]
            for key, value in list(first_row.items())[:5]:
                print(f"     {key}: {value}")
            if len(first_row) > 5:
                print(f"     ... and {len(first_row) - 5} more fields")
                
    except Exception as e:
        print(f"❌ Error exploring indicators for {symbol}: {e}")


def example_index_data_analysis():
    """Example: Comprehensive index data analysis."""
    print("\n=== Index Data Analysis ===")
    
    # Major Chinese indices
    indices = {
        "000001": "Shanghai Composite Index",
        "399001": "Shenzhen Component Index",
        "399006": "ChiNext Index",
        "000300": "CSI 300 Index"
    }
    
    for symbol, name in indices.items():
        try:
            # Get recent 30 days of data
            df = qdb.get_index_data(symbol, start_date="20240101", end_date="20240201")
            
            if df.empty:
                print(f"❌ {name} ({symbol}): No data available")
                continue
                
            print(f"\n📊 {name} ({symbol}):")
            print(f"   Trading days: {len(df)}")
            print(f"   Index range: {df['low'].min():.2f} - {df['high'].max():.2f}")
            
            # Calculate performance metrics
            if len(df) >= 2:
                period_return = (df.iloc[-1]['close'] / df.iloc[0]['close'] - 1) * 100
                print(f"   Period return: {period_return:+.2f}%")
                
                # Calculate volatility
                daily_returns = df['close'].pct_change().dropna()
                volatility = daily_returns.std() * (252 ** 0.5) * 100  # Annualized
                print(f"   Annualized volatility: {volatility:.1f}%")
                
                # Recent performance
                if len(df) >= 5:
                    recent_return = (df.iloc[-1]['close'] / df.iloc[-6]['close'] - 1) * 100
                    print(f"   Last 5 days: {recent_return:+.2f}%")
                    
        except Exception as e:
            print(f"❌ Error analyzing {name}: {e}")


def example_index_realtime_monitoring():
    """Example: Real-time index monitoring."""
    print("\n=== Real-time Index Monitoring ===")
    
    major_indices = {
        "000001": "Shanghai Composite Index",
        "399001": "Shenzhen Component Index",
        "399006": "ChiNext Index"
    }
    
    print("📈 Market Dashboard:")
    for symbol, name in major_indices.items():
        try:
            data = qdb.get_index_realtime(symbol)
            
            current_value = data.get('current_value', 0)
            change_percent = data.get('change_percent', 0)
            market_status = data.get('market_status', 'unknown')
            
            # Status emoji
            if change_percent > 0:
                status = "📈"
            elif change_percent < 0:
                status = "📉"
            else:
                status = "➡️"
                
            print(f"   {status} {name}: {current_value:.2f} ({change_percent:+.2f}%)")
            print(f"      Market: {market_status}")
            
            # Additional details
            if 'open' in data and 'high' in data and 'low' in data:
                open_val = data['open']
                high_val = data['high']
                low_val = data['low']
                print(f"      Range: {low_val:.2f} - {high_val:.2f} (Open: {open_val:.2f})")
                
        except Exception as e:
            print(f"   ❌ {name}: Error - {e}")


def example_index_list_exploration():
    """Example: Exploring available indices."""
    print("\n=== Index List Exploration ===")
    
    try:
        # Get major indices
        major_indices = qdb.get_index_list(category="Major Shanghai-Shenzhen Indices")
        print(f"📋 Major Indices ({len(major_indices)} available):")
        
        for idx in major_indices[:8]:  # Show first 8
            symbol = idx.get('symbol', 'N/A')
            name = idx.get('name', 'N/A')
            exchange = idx.get('exchange', 'N/A')
            print(f"   {symbol}: {name} ({exchange})")
            
        if len(major_indices) > 8:
            print(f"   ... and {len(major_indices) - 8} more indices")
            
        # Get sector indices
        print(f"\n🏭 Exploring Sector Indices:")
        try:
            sector_indices = qdb.get_index_list(category="Sector Indices")
            print(f"   Total sector indices: {len(sector_indices)}")

            # Find technology-related indices
            tech_keywords = ['科技', '信息', '软件', '互联网', '电子', 'Technology', 'Information', 'Software', 'Internet', 'Electronics']
            tech_indices = []
            for idx in sector_indices:
                name = idx.get('name', '')
                if any(keyword in name for keyword in tech_keywords):
                    tech_indices.append(idx)
            
            print(f"   Technology-related indices: {len(tech_indices)}")
            for idx in tech_indices[:5]:
                print(f"     {idx.get('symbol', 'N/A')}: {idx.get('name', 'N/A')}")
                
        except Exception as e:
            print(f"   ⚠️ Sector indices not available: {e}")
            
    except Exception as e:
        print(f"❌ Error exploring indices: {e}")


def example_comparative_analysis():
    """Example: Comparative analysis across stocks and indices."""
    print("\n=== Comparative Analysis ===")
    
    # Compare bank stocks with banking index (if available)
    bank_stocks = ["000001", "600000", "600036"]
    
    print("🏦 Banking Sector Analysis:")
    
    # Analyze individual bank performance
    bank_performance = {}
    for symbol in bank_stocks:
        try:
            df = qdb.get_stock_data(symbol, days=30)
            if not df.empty and len(df) >= 2:
                return_30d = (df.iloc[-1]['close'] / df.iloc[0]['close'] - 1) * 100
                bank_performance[symbol] = return_30d
                print(f"   {symbol}: {return_30d:+.2f}% (30 days)")
        except Exception as e:
            print(f"   {symbol}: Error - {e}")
    
    # Compare with market indices
    print("\n📊 Market Comparison:")
    market_indices = ["000001", "000300"]  # Shanghai Composite Index, CSI 300 Index
    
    for idx_symbol in market_indices:
        try:
            df = qdb.get_index_data(idx_symbol, start_date="20240101", end_date="20240201")
            if not df.empty and len(df) >= 2:
                idx_return = (df.iloc[-1]['close'] / df.iloc[0]['close'] - 1) * 100
                print(f"   Index {idx_symbol}: {idx_return:+.2f}%")
        except Exception as e:
            print(f"   Index {idx_symbol}: Error - {e}")
    
    # Summary
    if bank_performance:
        avg_bank_return = sum(bank_performance.values()) / len(bank_performance)
        best_bank = max(bank_performance.items(), key=lambda x: x[1])
        worst_bank = min(bank_performance.items(), key=lambda x: x[1])
        
        print(f"\n📈 Banking Sector Summary:")
        print(f"   Average return: {avg_bank_return:+.2f}%")
        print(f"   Best performer: {best_bank[0]} ({best_bank[1]:+.2f}%)")
        print(f"   Worst performer: {worst_bank[0]} ({worst_bank[1]:+.2f}%)")


def main():
    """Run all financial and index analysis examples."""
    print("🏦 QDB Financial & Index Analysis Examples")
    print("=" * 60)
    
    # Initialize QDB
    try:
        qdb.init()
        print("✅ QDB initialized successfully\n")
    except Exception as e:
        print(f"⚠️ QDB initialization warning: {e}\n")
    
    # Run all examples
    example_financial_summary_analysis()
    example_financial_indicators_exploration()
    example_index_data_analysis()
    example_index_realtime_monitoring()
    example_index_list_exploration()
    example_comparative_analysis()
    
    print("\n" + "=" * 60)
    print("🎉 All financial and index analysis examples completed!")
    print("\nThese examples demonstrate advanced QDB usage patterns")
    print("for financial research and quantitative analysis.")


if __name__ == "__main__":
    main()
