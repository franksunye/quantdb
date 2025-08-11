# AKShare → QuantDB Migration Guide: Zero Changes, Rollback-Ready

Applicable Version: v2.2.8 | Last Updated: 2025-08-08

## TL;DR (One-Minute Quick Start)
1. Install:
```bash
pip install quantdb
```
2. Import:
```python
import qdb  # Package name: quantdb; Import name: qdb
```
3. Replace calls (example):
```python
# Before (AKShare)
# from akshare import stock_zh_a_hist
# df = stock_zh_a_hist(symbol="000001", start_date="20240101", end_date="20240201")

# After (QuantDB, fully compatible interface)
import qdb

df = qdb.stock_zh_a_hist("000001", start_date="20240101", end_date="20240201")
```
4. Other common calls:
```python
# Recent 30 days data (simplified API)
df = qdb.get_stock_data("000001", days=30)
# Real-time
entry = qdb.get_realtime_data("000001")
# Stock list
stocks = qdb.get_stock_list()
```

## Why Migrate to QuantDB?
- 98.1% performance improvement: Cache hits ~18ms (from ~1000ms to millisecond level)
- 100% AKShare interface compatibility: Minimal changes, preserve original workflow
- Production ready: 259 tests 100% passed, comprehensive error handling
- Multi-market support: A-shares + Hong Kong stocks unified API

## Common API Mappings
- Historical data:
  - AKShare: `stock_zh_a_hist(symbol, start_date, end_date, ...)`
  - QuantDB: `qdb.stock_zh_a_hist(symbol, start_date, end_date, ...)`
  - QuantDB (simplified): `qdb.get_stock_data(symbol, days=30)`
- Real-time data:
  - QuantDB: `qdb.get_realtime_data(symbol)` / `qdb.get_realtime_data_batch(symbols)`
- Stock list:
  - QuantDB: `qdb.get_stock_list(market=None)`
- Financial data:
  - QuantDB: `qdb.get_financial_summary(symbol)` / `qdb.get_financial_indicators(symbol)`
- Index data:
  - QuantDB: `qdb.get_index_data(symbol, start_date, end_date)` etc.

Note: QuantDB maintains consistent data structure and semantics with AKShare; the difference lies in caching, performance, and stability.

## Migration Path Options

### Path A: Minimal Changes (Recommended)
- Replace AKShare calls with equivalent `qdb.*` interfaces at existing usage points
- Advantages: Controllable, progressive; no need for large-scale refactoring
- Example:
```python
# Original code
# from akshare import stock_zh_a_hist
# df = stock_zh_a_hist("000001", start_date="20240101", end_date="20240201")

# After replacement
import qdb

df = qdb.stock_zh_a_hist("000001", start_date="20240101", end_date="20240201")
```

### Path B: Adapter (Alias Compatibility)
- Define aliases at the boundary layer to minimize business code changes
```python
import qdb

# In your project's data_api.py boundary layer
stock_zh_a_hist = qdb.stock_zh_a_hist
get_realtime_data = qdb.get_realtime_data
get_stock_list = qdb.get_stock_list
```
- Business layer continues with `from data_api import stock_zh_a_hist`, achieving smooth replacement

## Performance and Validation

### Acceptance Checklist
- [ ] Core paths available (historical/real-time/list)
- [ ] First request ~1-2s; repeated requests ~10-50ms
- [ ] Results consistent with AKShare (fields/semantics)
- [ ] Logging and error handling normal

### Benchmark Testing Example
```python
import time
import qdb

symbol = "000001"

# Cold start (will access AKShare)
start = time.time(); qdb.get_stock_data(symbol, days=30); cold = time.time() - start
# Cache hit
start = time.time(); qdb.get_stock_data(symbol, days=30); warm = time.time() - start

print(f"First: {cold:.3f}s, Cache hit: {warm:.3f}s, Improvement: {(cold-warm)/cold*100:.1f}%")
```

## Rollback Strategy
- QuantDB is a compatible enhancement that won't break original workflows; if rollback is needed, simply switch imports and calls back to AKShare
- Keep a "switch" (like environment variable/config item) to quickly switch data layers for troubleshooting

## Frequently Asked Questions (FAQ)
- Still slow on first request? Normal, first request accesses AKShare; subsequent cache hits are millisecond-level
- Import failure? Please confirm using `pip install quantdb` and import name is `import qdb`
- Cache directory permissions (Windows)? Recommend using project-internal or user directory paths

## References and Resources
- Documentation: https://franksunye.github.io/quantdb/
- PyPI: https://pypi.org/project/quantdb/
- GitHub: https://github.com/franksunye/quantdb
- Issues: https://github.com/franksunye/quantdb/issues
