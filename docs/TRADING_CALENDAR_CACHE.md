# Trading Calendar Cache Management

## 📋 Overview

QuantDB uses an intelligent caching system for trading calendars to provide optimal performance while ensuring data accuracy. This document explains how the cache works and how it's managed.

## 🔧 Cache Mechanism

### Cache Location
- **Development**: `data/trading_calendar_cache.pkl` (not tracked in Git)
- **User Installation**: `~/.quantdb_cache/` or similar user cache directory
- **Format**: Pickle file containing multi-market trading calendar data

### Cache Content
```python
{
    "trading_dates": {
        "china_a": set(['20240101', '20240102', ...]),
        "hong_kong": set(['20240102', '20240103', ...])
    },
    "last_update": {
        "china_a": datetime(2024, 1, 1, 12, 0, 0),
        "hong_kong": datetime(2024, 1, 1, 12, 0, 0)
    },
    "version": "2.0_multi_market"
}
```

### Data Range
- **Historical**: Past 5 years of trading days
- **Future**: Next 3 years of trading days
- **Total**: ~8 years of trading calendar data
- **Size**: ~40KB for all markets

## ⏰ Cache Update Strategy

### Automatic Updates
1. **First Use**: Cache generated automatically if not exists
2. **Age-based**: Cache expires after 30 days
3. **Year-based**: Cache refreshes when entering a new year
4. **Version-based**: Old cache format automatically upgraded

### Update Triggers
```python
# Cache will update if:
- Cache file doesn't exist
- Cache is older than 30 days
- Cache was created in a previous year
- Cache format version is outdated
```

### Manual Refresh
```python
from core.services.trading_calendar import get_trading_calendar

calendar = get_trading_calendar()

# Refresh specific market
calendar.refresh_calendar(Market.HONG_KONG)

# Refresh all markets
calendar.refresh_calendar()
```

## 🏗️ Development vs Production

### Development Environment
- Cache file excluded from Git (`.gitignore`)
- Developers generate their own cache locally
- Cache regenerated as needed during development

### PyPI Package
- No pre-built cache included in package
- Users generate cache on first use
- Ensures fresh data for each installation

### Benefits
- ✅ No stale cache data in releases
- ✅ Always up-to-date trading calendars
- ✅ Smaller package size
- ✅ User-specific cache optimization

## 📊 Cache Performance

### Initial Generation
- **Time**: 1-2 seconds for all markets
- **Network**: Fetches from pandas_market_calendars
- **Fallback**: AKShare for China A-shares if needed

### Cached Access
- **Time**: <100ms to load from disk
- **Memory**: Minimal impact with set-based storage
- **Efficiency**: O(1) lookup for trading day checks

## 🔍 Cache Monitoring

### Check Cache Status
```python
from core.services.trading_calendar import get_trading_calendar

calendar = get_trading_calendar()
info = calendar.get_calendar_info()

print(f"Cache exists: {info['cache_exists']}")
print(f"Cache age: {info['cache_age_days']} days")
print(f"Cache year: {info['cache_year']}")
print(f"Current year: {info['current_year']}")
print(f"Total trading days: {info['total_trading_days']}")
```

### Market-Specific Info
```python
# Check specific market
hk_info = calendar.get_calendar_info(Market.HONG_KONG)
print(f"HK trading days: {hk_info['total_trading_days']}")
print(f"Last update: {hk_info['last_update']}")
```

## 🚀 Best Practices

### For Users
1. **Let it auto-update**: Cache updates automatically when needed
2. **Don't manually delete**: Cache regeneration takes time
3. **Check status**: Use `get_calendar_info()` to monitor cache health

### For Developers
1. **Don't commit cache**: Cache file is in `.gitignore`
2. **Test with fresh cache**: Delete local cache to test generation
3. **Document changes**: Update this file when modifying cache logic

### For CI/CD
1. **No cache in builds**: Each build generates fresh cache
2. **Test cache generation**: Ensure cache can be created in clean environment
3. **Verify data accuracy**: Test trading day calculations after cache updates

## 🔄 Migration Guide

### From v2.2.11 to v2.2.12+
- **Automatic**: Old cache format automatically upgraded
- **No action needed**: Users benefit from improved cache logic
- **Better performance**: Longer cache validity (30 days vs 7 days)

### Cache Location Changes
If cache location changes in future versions, migration will be handled automatically with backward compatibility.

## 🐛 Troubleshooting

### Cache Issues
```python
# Force refresh if cache seems stale
calendar.refresh_calendar()

# Check if in fallback mode
info = calendar.get_calendar_info()
for market, details in info['market_details'].items():
    if details['is_fallback_mode']:
        print(f"Warning: {market} is in fallback mode")
```

### Performance Issues
- **Slow startup**: Cache might be regenerating (normal on first use)
- **Frequent updates**: Check if cache file has proper permissions
- **Memory usage**: Cache uses minimal memory with set-based storage

### Data Accuracy
- **Wrong holidays**: Cache might be stale, try manual refresh
- **Missing trading days**: Check if market is supported
- **Incorrect year**: Cache auto-refreshes for new year

## 📈 Future Improvements

### Planned Features
- [ ] Incremental cache updates (only fetch new data)
- [ ] Compressed cache format for smaller size
- [ ] Network-based cache sharing for teams
- [ ] Real-time holiday updates from exchanges

### Performance Optimizations
- [ ] Lazy loading for unused markets
- [ ] Memory-mapped cache files for large datasets
- [ ] Parallel cache generation for multiple markets
