# User Guide

## 🎯 Overview

QuantDB is a high-performance stock data toolkit that provides 90%+ speedup for AKShare via intelligent local caching.

## 🚀 Key Features

### Smart Caching
- Transparent caching to avoid repeated API calls
- Multiple TTL strategies configurable
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
# Market snapshot
realtime = qdb.stock_zh_a_spot_em()
print(realtime.head())

# Single-symbol realtime info
stock_info = qdb.stock_individual_info_em(symbol="000001")
print(stock_info)
```

### Financial data

```python
# Financial indicators
financial = qdb.stock_financial_em(symbol="000001")
print(financial.head())

# Balance sheet
balance = qdb.stock_balance_sheet_by_report_em(symbol="000001")
print(balance.head())
```

## ⚙️ Advanced Configuration

### Cache settings

```python
import qdb

# TTL in seconds
qdb.set_cache_expire(3600)  # 1 hour

# Clear cache
qdb.clear_cache()

# Disable / enable cache
qdb.disable_cache()
qdb.enable_cache()
```

### Database settings

```python
# Custom database path
qdb.set_database_path("./my_stock_data.db")

# Cache statistics
stats = qdb.get_cache_stats()
print(f"Cache hit rate: {stats['hit_rate']:.2%}")
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
    portfolio_data[symbol] = {
        'data': data,
        'weight': weight,
        'latest_price': data['收盘'].iloc[-1]
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

## 📚 More Resources

- [04_api-reference.md](04_api-reference.md) — API Reference
- [05_examples.md](05_examples.md) — More examples
- [06_faq.md](06_faq.md) — FAQ
- [99_changelog.md](99_changelog.md) — Changelog
