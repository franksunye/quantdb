---
title: API Schema - QuantDB AI Agent Support
description: Structured JSON schema defining all QuantDB functions, parameters, and return types optimized for AI agent consumption and automated tools.
keywords: api schema, json schema, function definitions, ai agent integration, automated validation
---

# API Schema

QuantDB provides a comprehensive JSON schema that defines all functions, parameters, and return types in a format optimized for AI agent consumption and automated tools.

## Schema Overview

The schema includes:

- **Package Information**: Installation and import details
- **Function Definitions**: Complete API surface with type information
- **Parameter Validation**: Constraints, patterns, and examples
- **Return Types**: Detailed structure of all return values
- **Error Handling**: Exception types and conditions
- **Usage Examples**: Practical code samples for each function

## Download Schema

📥 **[Download qdb-ai-agent-schema.json](qdb-ai-agent-schema.json)**

## Package Information

```json
{
  "package_info": {
    "name": "quantdb",
    "import_name": "qdb", 
    "version": "2.2.8",
    "description": "Intelligent caching wrapper for AKShare",
    "installation": "pip install quantdb"
  }
}
```

## Core Functions

### get_stock_data

Historical stock data retrieval with intelligent caching.

**Parameters:**
- `symbol` (string, required): 6-digit stock symbol
  - Pattern: `^[0-9]{6}$`
  - Examples: `"000001"`, `"600000"`, `"300001"`
- `start_date` (string, optional): Start date in YYYYMMDD format
- `end_date` (string, optional): End date in YYYYMMDD format  
- `days` (integer, optional): Number of recent trading days (1-1000)
- `adjust` (string, optional): Price adjustment type
  - Options: `""` (none), `"qfq"` (forward), `"hfq"` (backward)

**Returns:** `pd.DataFrame` with columns:
- `date`, `open`, `high`, `low`, `close`, `volume`, `amount`

**Example:**
```python
import qdb

# Get last 30 days
data = qdb.get_stock_data("000001", days=30)

# Get specific date range
data = qdb.get_stock_data("600000", start_date="20240101", end_date="20240201")
```

### get_realtime_data

Real-time stock quote information.

**Parameters:**
- `symbol` (string, required): 6-digit stock symbol
- `force_refresh` (boolean, optional): Bypass cache if True

**Returns:** `Dict[str, Any]` with real-time quote data including:
- `symbol`, `name`, `current_price`, `change`, `change_percent`
- `volume`, `amount`, `high`, `low`, `open`, `previous_close`

### get_stock_info

Basic stock information and metadata.

**Parameters:**
- `symbol` (string, required): 6-digit stock symbol

**Returns:** `Dict[str, Any]` with stock information including:
- `symbol`, `name`, `market`, `industry`, `listing_date`

## Asset Information Functions

### get_stock_list

Retrieve list of available stocks.

**Parameters:**
- `market` (string, optional): Market filter
  - Options: `"sh"` (Shanghai), `"sz"` (Shenzhen), `"all"` (default)

**Returns:** `pd.DataFrame` with stock list and basic information.

### get_industry_stocks

Get stocks by industry classification.

**Parameters:**
- `industry` (string, required): Industry name or code

**Returns:** `pd.DataFrame` with stocks in specified industry.

## Performance and Caching

### clear_cache

Clear local data cache.

**Parameters:**
- `symbol` (string, optional): Clear cache for specific symbol
- `older_than_days` (integer, optional): Clear cache older than N days

**Returns:** `Dict[str, Any]` with cache clearing results.

### get_cache_info

Get cache statistics and information.

**Returns:** `Dict[str, Any]` with cache metrics including:
- `total_size`, `entry_count`, `hit_rate`, `last_updated`

## Error Handling

The schema defines specific exception types:

### ValueError
- Invalid symbol format
- Invalid date parameters
- Parameter constraint violations

### NetworkError  
- Connection failures
- API rate limiting
- Timeout errors

### CacheError
- Local cache operation failures
- Database connection issues

### DataError
- Empty or malformed data
- Data validation failures

## Validation Rules

### Symbol Format
- Must be exactly 6 digits
- Shanghai stocks: 600000-699999
- Shenzhen stocks: 000000-399999

### Date Format
- Must be YYYYMMDD format
- Must be valid trading dates
- end_date must be >= start_date

### Parameter Constraints
- `days`: 1-1000 range
- Mutually exclusive: `days` vs `start_date/end_date`

## Usage Patterns

### Basic Data Retrieval
```python
import qdb

# Simple usage
data = qdb.get_stock_data("000001", days=30)
print(f"Retrieved {len(data)} trading days")
```

### Error Handling
```python
try:
    data = qdb.get_stock_data("600000", days=30)
except ValueError as e:
    print(f"Invalid parameters: {e}")
except NetworkError as e:
    print(f"Network error: {e}")
```

### Performance Optimization
```python
# Use caching effectively
recent_data = qdb.get_stock_data("000001", days=5)  # Fast from cache
historical_data = qdb.get_stock_data("600000", start_date="20230101", end_date="20231231")  # Cached after first fetch
```

## Integration Examples

### For AI Coding Assistants

The schema enables AI tools to:

1. **Validate function calls** before execution
2. **Generate accurate code** with proper error handling
3. **Suggest appropriate parameters** based on constraints
4. **Provide intelligent autocomplete** with examples

### For Documentation Tools

The schema supports:

1. **Automated API documentation** generation
2. **Interactive API explorers** with live validation
3. **Code example generation** with real parameters
4. **Test case generation** based on constraints

### For Testing Frameworks

The schema enables:

1. **Property-based testing** with parameter constraints
2. **Mock data generation** matching return types
3. **Contract testing** between API versions
4. **Automated regression testing** with schema validation

## Schema Maintenance

The schema is automatically updated when:

- New functions are added to the QuantDB API
- Function signatures change
- Parameter constraints are modified
- Return value structures evolve

For the latest schema version, always download from the official documentation site.

---

**Next Steps:**
- [Developer Guide](developer-guide.md): Comprehensive documentation standards
- [Overview](index.md): Introduction to AI Agent support
- [GitHub Repository](https://github.com/franksunye/quantdb): Source code and issues
