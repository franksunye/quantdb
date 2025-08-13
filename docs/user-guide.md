# User Guide

## 🎯 Overview

QuantDB is a high-performance stock data toolkit that provides 90%+ speedup for AKShare via intelligent local caching.

## 🚀 Key Features

### Smart Caching
- Transparent caching to avoid repeated API calls
- Smart internal TTL management (no manual configuration required)
- Significant speed improvement on repeated queries

### Easy to Use
- AKShare-compatible interfaces
- Import and use, no code changes required
- Works with common AKShare stock endpoints

## 📊 Basic Usage

### Historical data

```python
import qdb

# Ping An Bank (000001) daily history
data = qdb.stock_zh_a_hist("000001")
print(data.head())

# Specify time range
data = qdb.stock_zh_a_hist(
    symbol="000001",
    start_date="20240101",
    end_date="20241231"
)
```

### Realtime quotes

```python
# Single-symbol realtime quote
tick = qdb.get_realtime_data("000001")
print(tick)

# Market snapshot and basic stock list
stocks = qdb.get_stock_list()  # cached daily
print(f"Total stocks: {len(stocks)}")
print(stocks[0])
```

### Financial data

```python
# Financial summary (last quarters)
summary = qdb.get_financial_summary(symbol="000001")
print(summary)

# Financial indicators (sample columns and data)
indicators = qdb.get_financial_indicators(symbol="000001")
print(indicators)
```

## ⚙️ Advanced Configuration

### Cache settings

```python
import qdb

# Cache statistics
stats = qdb.cache_stats()
print(stats)

# Clear cache (all or by symbol placeholder)
qdb.clear_cache()            # clear all
# qdb.clear_cache("000001")   # clearing by symbol is not yet implemented in simplified mode

# Configuration
qdb.set_cache_dir("./qdb_cache")
qdb.set_log_level("INFO")
```

Note: TTL is managed internally in this version. There are no `set_cache_expire` / `disable_cache` / `enable_cache` functions.

### Logging & paths

```python
# Change cache directory (affects where the local SQLite cache is stored)
qdb.set_cache_dir("./qdb_cache")

# Set log level
qdb.set_log_level("INFO")

# Inspect cache stats
stats = qdb.cache_stats()
print(stats)
```

## 🔧 Performance Tips

### Batch fetching

```python
# Fetch multiple symbols
symbols = ["000001", "000002", "600000", "600036"]
data_dict = {}

for symbol in symbols:
    data_dict[symbol] = qdb.stock_zh_a_hist(symbol)

print(f"Fetched {len(data_dict)} symbols")
```

### Cache warm-up

```python
# Preload commonly used symbols
popular_stocks = ["000001", "000002", "600000", "600036", "000858"]

for symbol in popular_stocks:
    qdb.stock_zh_a_hist(symbol)  # warm up cache

print("Cache warm-up completed")
```

## 📈 Use Cases

### Portfolio analysis

```python
import pandas as pd
import qdb

# Example portfolio
portfolio = {
    "000001": 0.3,  # 30%
    "600000": 0.4,  # 40%
    "000858": 0.3   # 30%
}

# Fetch data
portfolio_data = {}
for symbol, weight in portfolio.items():
    data = qdb.stock_zh_a_hist(symbol)
    if data.empty:
        continue  # skip if no data returned
    price_col = '收盘' if '收盘' in data.columns else 'close'
    portfolio_data[symbol] = {
        'data': data,
        'weight': weight,
        'latest_price': data[price_col].iloc[-1]
    }

# Compute a simple metric
total_value = sum(info['latest_price'] * info['weight']
                 for info in portfolio_data.values())
print(f"Portfolio current value: {total_value:.2f}")
```

### Technical indicators

```python
import qdb
import pandas as pd

# Data
data = qdb.stock_zh_a_hist("000001")

# Moving averages
data['MA5'] = data['收盘'].rolling(window=5).mean()
data['MA20'] = data['收盘'].rolling(window=20).mean()

# RSI
def calculate_rsi(prices, window=14):
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

data['RSI'] = calculate_rsi(data['收盘'])

print(data[['收盘', 'MA5', 'MA20', 'RSI']].tail())
```

## 🚨 Notes

1. Data freshness depends on TTL; adjust as needed
2. Network is required for first-time fetches
3. Cache database may grow over time; consider periodic cleanup
4. Respect data source rate limits and terms

## Run the examples

The repository includes runnable scripts to try common features:

```bash
python examples/basic_usage.py
python examples/realtime.py
python examples/stock_list.py
python examples/finance.py
python examples/cache_management.py
python examples/hong_kong_indexes.py    # 🇭🇰 Hong Kong index demo
python examples/multi_market_trading_calendar_demo.py  # Multi-market trading calendar
```

Outputs depend on data source and time. For reproducibility, pin dates or rely on cache.

## 📚 More Resources

- [api-reference.md](api-reference.md) — API Reference
- [faq.md](faq.md) — FAQ
- [changelog.md](changelog.md) — Changelog
