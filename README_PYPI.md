# QuantDB - Intelligent Stock Data Caching

[![PyPI version](https://img.shields.io/pypi/v/quantdb.svg)](https://pypi.org/project/quantdb/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/quantdb)](https://pypi.org/project/quantdb/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/quantdb)](https://pypi.org/project/quantdb/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Performance](https://img.shields.io/badge/performance-90%25_faster-brightgreen)](https://github.com/franksunye/quantdb)

**Intelligent caching wrapper for AKShare with 90%+ performance boost** - Complete stock data ecosystem with smart SQLite caching for Chinese financial markets.

> 📊 **Note**: Download statistics may take 24-48 hours to appear on PyPI and third-party services after a new release.

## 🚀 Quick Start

```bash
pip install quantdb  # One command, instant 90%+ speed boost!
```

```python
import qdb  # Note: import name is 'qdb' for simplicity
df = qdb.get_stock_data("000001", days=30)  # 90%+ faster than AKShare!
```

## ✨ Key Features

- **🚀 90%+ Performance Boost**: Local SQLite cache avoids repeated network requests
- **🧠 Smart Incremental Updates**: Only fetch missing data, maximize cache efficiency  
- **⚡ Millisecond Response**: Cache hit response time < 10ms
- **📅 Trading Calendar Integration**: Smart data acquisition based on real trading calendar
- **🔧 Zero Configuration**: Automatically initialize local cache database
- **🔄 Full AKShare Compatibility**: Drop-in replacement with same API interface
- **🌍 100% English Codebase**: International developer friendly
- **🎯 Multi-Market Support**: A-shares + Hong Kong stocks unified API

## 📊 Performance Comparison

| Operation | AKShare | QuantDB | Improvement |
|-----------|---------|---------|-------------|
| First Request | ~1000ms | ~1000ms | Same |
| Cache Hit | ~1000ms | ~18ms | **98.1% faster** |
| Bulk Operations | Very Slow | Lightning Fast | **90%+ faster** |

## 🔧 Core API

### Basic Usage
```python
import qdb

# Get stock data (with intelligent caching)
df = qdb.get_stock_data("000001", days=30)
df = qdb.get_stock_data("600000", start_date="20240101", end_date="20240201")

# Multiple stocks
stocks_data = qdb.get_multiple_stocks(["000001", "000002"], days=30)

# Asset information
asset_info = qdb.get_asset_info("000001")

# Cache management
stats = qdb.cache_stats()  # View cache statistics
qdb.clear_cache()         # Clear cache if needed
```

### AKShare Compatibility
```python
import qdb

# 100% compatible with AKShare API
df = qdb.stock_zh_a_hist("000001", start_date="20240101", end_date="20240201")
```

### Configuration
```python
import qdb

# Custom cache directory
qdb.set_cache_dir("./my_custom_cache")

# Logging level
qdb.set_log_level("INFO")  # DEBUG, INFO, WARNING, ERROR
```

## 🎯 Use Cases

- **Quantitative Research**: Frequent backtesting with cached historical data
- **Algorithm Trading**: Real-time data access with minimal latency
- **Financial Analysis**: Large-scale data processing with performance optimization
- **Portfolio Management**: Multi-asset data retrieval and analysis
- **Academic Research**: Reliable data source for financial studies

## 🔄 Coming Soon (v2.3.0)

- **Real-time Stock Quotes**: Live market data with smart caching
- **Stock List API**: Complete market coverage and filtering
- **Index Data**: Major indices support (SSE, SZSE, etc.)
- **Financial Metrics**: Key financial indicators and ratios

## 📚 Documentation & Support

- **GitHub Repository**: [https://github.com/franksunye/quantdb](https://github.com/franksunye/quantdb)
- **Full Documentation**: [https://github.com/franksunye/quantdb/docs](https://github.com/franksunye/quantdb/docs)
- **Issue Tracker**: [https://github.com/franksunye/quantdb/issues](https://github.com/franksunye/quantdb/issues)
- **API Reference**: Complete API documentation with examples

## 🏗️ Architecture

QuantDB provides multiple deployment options:

1. **📦 Python Package** (This Package): Local caching for individual developers
2. **🚀 API Service**: Enterprise-grade REST API with advanced features  
3. **☁️ Cloud Platform**: Web interface with visualization and monitoring

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](https://github.com/franksunye/quantdb/blob/main/CONTRIBUTING.md) for details.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](https://github.com/franksunye/quantdb/blob/main/LICENSE) file for details.

## 🙏 Acknowledgments

- Built on top of the excellent [AKShare](https://github.com/akfamily/akshare) library
- Inspired by the need for high-performance financial data access in Python

---

**Note**: Package name is `quantdb`, import name is `qdb` (similar to scikit-learn → sklearn)

*Made with ❤️ for the Python quantitative finance community*
