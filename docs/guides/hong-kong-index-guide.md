# Hong Kong Index Support Guide

QuantDB now provides comprehensive support for Hong Kong stock indexes, including the major Hang Seng family indexes.

## 🏷️ Supported Indexes

### Major Hong Kong Indexes
- **HSI** - Hang Seng Index
- **HSCEI** - Hang Seng China Enterprises Index
- **HSTECH** - Hang Seng TECH Index

## 🔤 Symbol Conventions

QuantDB follows international conventions for Hong Kong index symbols while supporting common aliases:

### Standard Symbols
```python
# Recommended standard symbols
"HSI"      # Hang Seng Index
"HSCEI"    # Hang Seng China Enterprises Index
"HSTECH"   # Hang Seng TECH Index
```

### Supported Aliases
```python
# All these variations work for HSI:
"HSI", "hsi", "^HSI", "HK.HSI"
"HANG SENG", "HANG SENG INDEX", "HANGSENG", "HANGSENG INDEX"

# All these variations work for HSCEI:
"HSCEI", "^HSCEI", "HANG SENG CHINA ENTERPRISES"
"HS CHINA ENTERPRISES", "H SHARES"

# All these variations work for HSTECH:
"HSTECH", "^HSTECH", "HANG SENG TECH", "HANGSENG TECH"
```

## 📊 Usage Examples

### Historical Data
```python
import qdb

# Get HSI historical data (last 30 days)
hsi_data = qdb.get_index_data('HSI', '20240101', '20240131', 'daily')
print(f"Retrieved {len(hsi_data)} rows of HSI data")
print(hsi_data.head())

# Using aliases also works
hsi_data = qdb.get_index_data('^HSI', '20240101', '20240131', 'daily')
hsi_data = qdb.get_index_data('HANG SENG', '20240101', '20240131', 'daily')

# Get HSCEI data
hscei_data = qdb.get_index_data('HSCEI', '20240101', '20240131', 'daily')

# Get HSTECH data
hstech_data = qdb.get_index_data('HSTECH', '20240101', '20240131', 'daily')
```

### Realtime Data
```python
# Get realtime HSI quote
hsi_quote = qdb.get_index_realtime('HSI')
print(f"HSI Current Price: {hsi_quote['price']}")
print(f"Change: {hsi_quote['change']} ({hsi_quote['pct_change']}%)")

# Get realtime quotes for all major HK indexes
for symbol in ['HSI', 'HSCEI', 'HSTECH']:
    quote = qdb.get_index_realtime(symbol)
    print(f"{symbol}: {quote['price']} ({quote['pct_change']:+.2f}%)")
```

### Index List
```python
# Get all Hong Kong indexes (using internal category code)
hk_indexes = qdb.get_index_list(category='香港指数')
print(f"Found {len(hk_indexes)} Hong Kong indexes")

# Display major indexes
major_indexes = ['HSI', 'HSCEI', 'HSTECH']
for idx in hk_indexes:
    if idx['symbol'] in major_indexes:
        print(f"{idx['symbol']}: {idx['name']} - {idx['price']}")
```

## 📈 Data Structure

### Historical Data Columns
```python
# Returned DataFrame columns:
['date', 'open', 'high', 'low', 'close', 'volume', 'name']

# Example data:
#        date     open     high      low    close    volume        name
# 0  2024-01-01  16400.0  16600.0  16350.0  16500.0  1000000    Hang Seng Index
# 1  2024-01-02  16500.0  16700.0  16450.0  16600.0  1100000    Hang Seng Index
```

### Realtime Data Structure
```python
# Returned dictionary keys:
{
    'symbol': 'HSI',
    'name': 'Hang Seng Index',
    'price': 24906.811,
    'change': 100.0,
    'pct_change': 0.40,
    'prev_close': 24806.811,
    'open': 24850.0,
    'high': 24950.0,
    'low': 24800.0
}
```

## 🔄 API Endpoints

### REST API Usage
```bash
# Historical data
GET /api/v1/index/historical/HSI?start_date=20240101&end_date=20240131&period=daily

# Realtime data
GET /api/v1/index/realtime/HSI

# Index categories (includes Hong Kong indexes)
GET /api/v1/index/categories

# Hong Kong index list (using internal category code)
GET /api/v1/index/list?category=%E9%A6%99%E6%B8%AF%E6%8C%87%E6%95%B0
```

## ⚡ Performance & Caching

- **Smart Caching**: Hong Kong index data is cached with the same intelligent strategy as A-share indexes
- **Data Source**: 100% powered by AKShare's Hong Kong index APIs
- **Update Frequency**: Realtime data refreshed on each call; historical data cached appropriately
- **Backward Compatibility**: Zero impact on existing A-share index functionality

## 🌐 International Standards

QuantDB's Hong Kong index support follows international financial data conventions:

- **Symbol Format**: Standard international codes (HSI, HSCEI, HSTECH)
- **Alias Support**: Common variations used by international platforms
- **Data Structure**: Consistent with global financial data standards
- **API Design**: RESTful endpoints following international best practices

## 🧪 Testing & Validation

All Hong Kong index functionality has been thoroughly tested:

- ✅ Symbol normalization with 100% accuracy
- ✅ Historical data retrieval with real market data
- ✅ Realtime data with live price feeds
- ✅ Index list with complete category support
- ✅ Backward compatibility with A-share indexes

## 📞 Support

For questions about Hong Kong index support:
- Check the main [FAQ](../faq.md)
- Review [API Reference](../api-reference.md)
- Visit our [Community Discussions](../community/DISCUSSIONS.md)

---

*Hong Kong index support is available in QuantDB v2.3.0+ and maintains full backward compatibility with existing functionality.*
