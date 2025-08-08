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
- Adjust TTL: `qdb.set_cache_expire(300)`  # 5 minutes
- Temporarily disable cache: `qdb.disable_cache()`

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
- Use shorter TTL: `qdb.set_cache_expire(1800)`  # 30 minutes
- Manually delete the SQLite file (default: `./database/stock_data.db`)

### Q: How to inspect cache usage?
**A:**
```python
stats = qdb.get_cache_stats()
print(f"Cache hit rate: {stats['hit_rate']:.2%}")
print(f"Cache size: {stats['cache_size']} records")
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
# Option 1: Clear specific symbol cache
qdb.clear_cache(symbol="000001")

# Option 2: Use shorter TTL
qdb.set_cache_expire(60)  # 1 minute

# Option 3: Temporarily disable cache
qdb.disable_cache()
data = qdb.stock_zh_a_hist("000001")
qdb.enable_cache()
```

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
- [Community](community/)
