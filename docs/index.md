# QuantDB Documentation

High-performance, developer-friendly stock data toolkit. QuantDB adds 90%+ speedup to AKShare via local SQLite intelligent caching. Import name is `qdb`.

- PyPI: https://pypi.org/project/quantdb/
- Source & Issues: https://github.com/franksunye/quantdb

## Quickstart

```bash
pip install quantdb
```

```python
import qdb

# Recent 30 days (auto cache)
df = qdb.get_stock_data("000001", days=30)

# Realtime quote (may take ~1 minute on first run)
tick = qdb.get_realtime_data("000001")

# Stock list (cached daily; first run may take ~2 minutes)
stocks = qdb.get_stock_list()
```

See Get Started and Examples for more usage.

## Why QuantDB
- 90%+ faster: millisecond response on cache hits
- AKShare-compatible: seamless migration of common interfaces
- Simple API: qdb.get_stock_data / get_realtime_data etc.
- Offline-friendly: local cache supports offline access

## Products
- Python package (qdb): for developers
- API service (FastAPI): for integration
- Cloud app (Streamlit): zero-install visualization

## Docs Navigation
- Get Started: installation, init, common calls
- API Reference: public functions and parameters
- Examples: runnable scripts and outputs
