# Installation

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

## 📚 What’s next
- [02_quickstart.md](02_quickstart.md) — 5-minute quickstart
- [03_user-guide.md](03_user-guide.md) — comprehensive user guide
- [04_api-reference.md](04_api-reference.md) — complete API reference
