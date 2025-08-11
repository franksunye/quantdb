# QDB for AI Agents

This document provides AI agents with essential information for using the QDB (QuantDB) package effectively.

## 🎯 Quick Start for AI Agents

```python
import qdb

# Get stock data with intelligent caching
df = qdb.get_stock_data("000001", days=30)

# Get financial summary
summary = qdb.get_financial_summary("000001")

# Get real-time data
realtime = qdb.get_realtime_data("000001")
```

## 📋 Complete API Reference

### Core Functions
- `get_stock_data(symbol, start_date, end_date, days, adjust)` - Historical stock data
- `get_realtime_data(symbol, force_refresh)` - Real-time stock quotes
- `get_stock_list(market, force_refresh)` - Stock listings with filtering

### Financial Analysis
- `get_financial_summary(symbol, force_refresh)` - Quarterly financial metrics
- `get_financial_indicators(symbol, force_refresh)` - 80+ detailed financial ratios

### Index Data
- `get_index_data(symbol, start_date, end_date, period, force_refresh)` - Historical index data
- `get_index_realtime(symbol, force_refresh)` - Real-time index quotes
- `get_index_list(category, force_refresh)` - Available market indices

### Utilities
- `cache_stats()` - Cache performance metrics
- `init()` - Initialize QDB system

## 🔧 Machine-Readable Resources

- **API Schema**: [docs/qdb-ai-agent-schema.json](docs/qdb-ai-agent-schema.json)
- **Usage Examples**: [examples/ai_agent_usage_examples.py](examples/ai_agent_usage_examples.py)
- **Financial Analysis**: [examples/financial_and_index_analysis.py](examples/financial_and_index_analysis.py)
- **Documentation Guide**: [docs/ai-agent-documentation-guide.md](docs/ai-agent-documentation-guide.md)

## 📊 Common Use Cases

### Stock Analysis
```python
# Get recent stock performance
df = qdb.get_stock_data("000001", days=30)
returns = df['close'].pct_change()
volatility = returns.std()
```

### Financial Analysis
```python
# Analyze company financials
summary = qdb.get_financial_summary("000001")
if summary['quarters']:
    latest = summary['quarters'][0]
    roe = latest.get('roe', 0)
```

### Market Monitoring
```python
# Monitor market indices
data = qdb.get_index_realtime("000001")  # Shanghai Composite
change_pct = data.get('change_percent', 0)
```

## ⚠️ Error Handling

All functions may raise:
- `ValueError`: Invalid parameters (symbol format, date range, etc.)
- `NetworkError`: Network connectivity issues
- `DataError`: Data unavailable or malformed
- `CacheError`: Local cache issues (non-critical)

```python
try:
    df = qdb.get_stock_data("000001", days=30)
except ValueError as e:
    # Handle invalid parameters
    print(f"Parameter error: {e}")
except NetworkError as e:
    # Handle network issues
    print(f"Network error: {e}")
```

## 🚀 Performance Tips

1. **Use caching**: Default behavior, provides 90%+ performance boost
2. **Batch operations**: Process multiple symbols efficiently
3. **Monitor cache**: Use `qdb.cache_stats()` for performance insights
4. **Smart refresh**: Use `force_refresh=True` only when needed

## 📈 Symbol Formats

- **Stocks**: 6-digit format (e.g., "000001", "600000", "300001")
- **Indices**: Standard format (e.g., "000001" for Shanghai Composite, "399006" for ChiNext)
- **Markets**: "SHSE" (Shanghai), "SZSE" (Shenzhen), "HKEX" (Hong Kong)

## 🔍 Data Coverage

- **Stock Data**: Chinese A-shares (Shanghai, Shenzhen, ChiNext)
- **Financial Data**: Quarterly reports, 80+ financial indicators
- **Index Data**: Major market indices with multiple frequencies
- **Real-time**: Current market data during trading hours

## 📚 Documentation Access

AI agents can access documentation through:
1. **Built-in docstrings**: `help(qdb.function_name)`
2. **GitHub repository**: Direct file access via GitHub API
3. **GitHub Pages**: Web-accessible documentation

For the most current and detailed documentation, always refer to the function docstrings using Python's `help()` function.
