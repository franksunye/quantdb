# Frequently Asked Questions (FAQ)

## 🔧 Installation & Setup

### Q: How do I resolve dependency conflicts?
**A:** Use a virtual environment to isolate dependencies:
```bash
python -m venv quantdb_env
# Linux/Mac
source quantdb_env/bin/activate
# Windows (PowerShell)
quantdb_env\Scripts\Activate.ps1
pip install quantdb
```

### Q: How can I upgrade to the latest version?
**A:**
```bash
pip install --upgrade quantdb
```

### Q: Which Python versions are supported?
**A:** Python 3.8 and above. We recommend Python 3.9+ for best performance.

## 📊 Data Fetching

### Q: Why is the data sometimes not up-to-date?
**A:** Due to caching. You can:
- Clear cache: `qdb.clear_cache()`
- Use fresh fetch where available: `qdb.get_realtime_data(symbol, force_refresh=True)`
- Note: TTL is managed internally in this version; there are no `set_cache_expire` / `disable_cache` functions.

### Q: How do I fetch more historical data?
**A:** Use date parameters:
```python
data = qdb.stock_zh_a_hist(
    symbol="000001",
    start_date="20200101",
    end_date="20241231"
)
```

### Q: Which markets are supported?
**A:** Currently focusing on:
- Mainland China A-shares (SSE/SZSE)
- Hong Kong market
- US market (partial support)

## ⚡ Performance

### Q: How can I speed up data fetching?
**A:** Tips:
1. Keep cache enabled (default)
2. Use reasonable intervals when fetching in batch
3. Warm up cache for frequently used symbols
4. Periodically purge expired cache

### Q: Cache database grows too large, what can I do?
**A:**
- Clear cache periodically: `qdb.clear_cache()`
- Manually delete the cache DB file if needed (default: in your qdb cache dir)
- Note: TTL is managed internally; there is no `set_cache_expire()` function in this version

### Q: How to inspect cache usage?
**A:**
```python
stats = qdb.cache_stats()
print(stats)  # e.g. {'cache_dir': '...', 'cache_size_mb': 12.34, 'initialized': True, 'status': 'Running'}
```

## 🐛 Errors & Troubleshooting

### Q: Network errors?
**A:** Check:
1. Network connectivity
2. Firewall/Proxy constraints
3. Data source availability
4. Consider using a proxy or VPN if needed

### Q: Unexpected data format?
**A:** Possible reasons:
- Invalid symbol format (e.g., use "000001" not "1")
- Wrong date format (use "YYYYMMDD")
- Temporary data source changes

### Q: It runs slow, how to diagnose?
**A:**
1. First run downloads data — subsequent runs will be faster
2. Ensure cache is enabled
3. Check network speed
4. Reduce time range

## 🔄 Keeping data fresh

### Q: How to ensure latest data?
**A:**
```python
# Option 1: Force refresh where supported
rt = qdb.get_realtime_data("000001", force_refresh=True)

# Option 2: Clear all cache (symbol-level clearing not yet implemented in simplified mode)
qdb.clear_cache()

# Option 3: Bypass cache by using a narrower date range if needed
hist = qdb.stock_zh_a_hist("000001", start_date="20250101", end_date="20250131")
```

Note: TTL is managed internally in this version.

### Q: Update frequency?
**A:**
- Realtime quotes: often delayed ~15 minutes
- Daily data: updated after market close
- Financials: quarterly updates

## 🛠️ Integration

### Q: Production usage best practices?
**A:**
1. Use a dedicated database path
2. Tune TTL to your workload
3. Add retry logic
4. Monitor cache usage regularly

### Q: Can I combine with other data sources?
**A:** Yes. QuantDB is primarily a cache layer for AKShare, but you can:
- Combine multiple sources
- Validate and clean data
- Build your own data pipelines

### Q: How to contribute or report issues?
**A:**
- GitHub Issues: https://github.com/franksunye/quantdb/issues
- Pull Requests welcome
- Join Discussions

## 📚 More help

If you didn’t find your answer:

1. See the [User Guide](user-guide.md)
2. See the [API Reference](api-reference.md)
3. Open an Issue on GitHub

## 🔗 Links

- [Project Home](https://github.com/franksunye/quantdb)
- [PyPI](https://pypi.org/project/quantdb/)
- [AKShare Docs](https://akshare.akfamily.xyz/)
- [Community](https://github.com/franksunye/quantdb/discussions)
