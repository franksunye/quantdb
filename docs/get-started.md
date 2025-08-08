# Get Started

A quick guide to install and use QuantDB in minutes.

## 📦 Install from PyPI (recommended)

```bash
pip install quantdb
```

## 🔧 Install from source

```bash
# Clone the repository
git clone https://github.com/franksunye/quantdb.git
cd quantdb

# Install dependencies (optional)
pip install -r requirements.txt

# Install the package in editable mode
pip install -e .
```

## 📋 Requirements

- Python 3.8+
- OS: Windows, macOS, or Linux
- Memory: 4GB+ recommended
- Disk: 1GB+ recommended (for local cache)

## 🔍 Verify installation

```python
import qdb

# Check version
print(qdb.__version__)

# Basic test
data = qdb.stock_zh_a_hist("000001")
print(data.head())
```

## Import and Initialize
```python
import quantdb as qdb  # package name: quantdb, import name: qdb

# Optional: specify cache directory
db_dir = "./my_quantdb_cache"
qdb.init(cache_dir=db_dir)
```

Tip: First call auto-initializes, explicit init is not required.

## Basic Usage
```python
import qdb

# 1) Stock history (simplified API)
df = qdb.get_stock_data("000001", days=30)

# 2) Batch fetch
data = qdb.get_multiple_stocks(["000001", "000002", "600000"], days=30)

# 3) Realtime data
rt = qdb.get_realtime_data("000001")

# 4) Stock list (filter by market)
all_stocks = qdb.get_stock_list()
```

## Advanced Usage
```python
# AKShare-compatible interface
df = qdb.stock_zh_a_hist("000001", start_date="20240101", end_date="20240201")

# Cache management
stats = qdb.cache_stats()
qdb.clear_cache()            # clear all
qdb.clear_cache("000001")    # clear by symbol

# Configuration
qdb.set_cache_dir("./qdb_cache")
qdb.set_log_level("INFO")
```

See API Reference for financial summaries/indicators and more.

## Run the examples
The repository includes runnable scripts:
```bash
python examples/basic_usage.py
python examples/realtime.py
python examples/stock_list.py
python examples/finance.py
python examples/cache_management.py
```

## 🚨 Troubleshooting

### Dependency conflicts
Use a virtual environment to isolate dependencies:

```bash
python -m venv quantdb_env
# Linux/Mac
source quantdb_env/bin/activate
# Windows (PowerShell)
quantdb_env\Scripts\Activate.ps1

pip install quantdb
```

### Slow downloads
If you experience slow downloads due to regional network issues, consider using a closer mirror or a stable network.

## 📚 What's next
- [user-guide.md](user-guide.md) — comprehensive user guide
- [api-reference.md](api-reference.md) — complete API reference
- [faq.md](faq.md) — frequently asked questions
