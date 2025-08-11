#!/usr/bin/env python3
"""
Beta calculation example using Hong Kong stocks

Computes beta for Tencent (00700) vs market benchmark using QuantDB.
Beta measures how much a stock moves relative to the market.

Note: This example depends on AKShare's Hong Kong stock API, which may
experience network connectivity issues. If you see "AKShare returned empty data",
this is typically due to SSL connection problems with the data provider's servers,
not a code issue.

Usage: python examples/beta_hk_tencent.py
"""

import numpy as np
import pandas as pd
import qdb

# Configuration
STOCK_SYMBOL = "00700"   # Tencent Holdings
BENCH_SYMBOLS = ["02800", "00941", "00388"]  # Multiple benchmark options
DAYS = 5  # Test cache hit after 20-day data is cached


def compute_beta(stock_returns: pd.Series, market_returns: pd.Series):
    """Compute beta using simple linear regression."""
    # Align data and remove NaNs
    data = pd.DataFrame({"stock": stock_returns, "market": market_returns}).dropna()

    if len(data) < 3:
        raise ValueError(f"Need at least 3 data points, got {len(data)}")

    # Calculate beta using covariance formula: beta = cov(stock, market) / var(market)
    covariance = np.cov(data["stock"], data["market"])[0, 1]
    market_variance = np.var(data["market"], ddof=1)

    if market_variance == 0:
        raise ValueError("Market returns have zero variance")

    beta = covariance / market_variance
    alpha = np.mean(data["stock"]) - beta * np.mean(data["market"])
    r_squared = np.corrcoef(data["stock"], data["market"])[0, 1] ** 2

    return beta, alpha, r_squared, len(data)


def main():
    print("=== Beta Calculation: Tencent vs Market ===")

    # Fetch stock data
    print(f"Fetching {DAYS} days of data for {STOCK_SYMBOL}...")

    try:
        stock_data = qdb.get_stock_data(STOCK_SYMBOL, days=DAYS)
    except Exception as e:
        print(f"❌ Error fetching stock data: {e}")
        return

    if stock_data.empty:
        print("❌ No stock data available for Tencent (00700).")
        print("💡 This is likely due to network connectivity issues with AKShare's HK API.")
        return

    # Try multiple benchmark symbols
    market_data = None
    bench_symbol = None

    for symbol in BENCH_SYMBOLS:
        print(f"Trying benchmark {symbol}...")
        try:
            market_data = qdb.get_stock_data(symbol, days=DAYS)
            if not market_data.empty:
                bench_symbol = symbol
                print(f"✅ Using {symbol} as benchmark")
                break
        except Exception as e:
            print(f"⚠️ {symbol} failed: {e}")
            continue

    if market_data is None or market_data.empty:
        print("❌ No benchmark data available. All benchmark symbols failed.")
        print("💡 This is likely due to network connectivity issues with AKShare's HK API.")
        print("   Common causes:")
        print("   - SSL connection problems with data provider servers")
        print("   - Network firewall or proxy restrictions")
        print("   - Temporary API service unavailability")
        print("   Try again later or check your network connection.")
        return

    # Calculate daily returns
    stock_data = stock_data.reset_index()
    market_data = market_data.reset_index()

    stock_returns = stock_data["close"].pct_change().dropna()
    market_returns = market_data["close"].pct_change().dropna()

    # Compute beta
    try:
        beta, alpha, r2, n_obs = compute_beta(stock_returns, market_returns)

        print(f"\nResults ({n_obs} observations):")
        print(f"Stock:     {STOCK_SYMBOL}")
        print(f"Benchmark: {bench_symbol}")
        print(f"Beta:      {beta:.3f}")
        print(f"Alpha:     {alpha:.6f} (daily)")
        print(f"R²:        {r2:.3f}")
        print(f"\nInterpretation:")
        print(f"- Beta > 1: Stock is more volatile than market")
        print(f"- Beta < 1: Stock is less volatile than market")
        print(f"- R² shows how well market explains stock movement")

    except ValueError as e:
        print(f"❌ Cannot compute beta: {e}")


if __name__ == "__main__":
    main()

