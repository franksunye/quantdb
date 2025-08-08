# Reddit Post Content for r/Python

## Title
[Release] QuantDB: 98% faster stock data caching for Python (AKShare compatible)

## Content

Hey r/Python! 👋

I'm excited to share **QuantDB**, a high-performance caching wrapper for AKShare that delivers **90%+ speed improvements** for stock data operations in Python.

### 🚀 What is QuantDB?

QuantDB is an intelligent caching layer for AKShare (the popular Chinese stock data library) that uses SQLite to cache data locally, dramatically reducing API calls and response times.

### ⚡ Performance Results

- **Cache hits**: ~18ms (vs ~1000ms for AKShare)
- **98.1% faster** for repeated queries
- **90%+ overall performance boost** in typical workflows

### 🔧 Quick Start

```bash
pip install quantdb
```

```python
import qdb  # Note: import name is 'qdb'

# Get stock data (automatically cached)
df = qdb.get_stock_data("000001", days=30)

# Real-time quotes
realtime = qdb.get_realtime_data("000001")

# Complete stock list
stocks = qdb.get_stock_list()
```

### ✨ Key Features

- **Zero configuration**: Works out of the box
- **AKShare compatible**: Drop-in replacement for common functions
- **Smart caching**: Only fetches missing data
- **Trading calendar aware**: Respects market schedules
- **Multiple deployment options**: Package, API service, or cloud platform

### 📊 Perfect for:

- Quantitative research and backtesting
- Algorithmic trading systems
- Financial data analysis
- Academic research in finance

### 🔗 Links

- **PyPI**: https://pypi.org/project/quantdb/?utm_source=reddit&utm_medium=social&utm_campaign=launch
- **GitHub**: https://github.com/franksunye/quantdb?utm_source=reddit&utm_medium=social&utm_campaign=launch
- **Documentation**: https://franksunye.github.io/quantdb/?utm_source=reddit&utm_medium=social&utm_campaign=launch

Would love to hear your feedback and answer any questions! 🙏

---

*Note: Package name is `quantdb`, import name is `qdb` (similar to scikit-learn → sklearn)*
