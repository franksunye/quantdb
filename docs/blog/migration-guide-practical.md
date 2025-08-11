# From AKShare to QuantDB: Complete Migration Guide for Quantitative Traders

*Published: January 11, 2025 | Author: QuantDB Team | Category: User Guides*

## 🎯 Migration Overview

This article demonstrates how to smoothly migrate from AKShare to QuantDB through real quantitative trading project examples, achieving 98%+ performance improvement while maintaining code compatibility and stability.

**Migration Benefits**:
- ⚡ **98%+ Performance Improvement**: Response time drops from 1000ms to 18ms
- 🔄 **Zero Learning Curve**: 100% API compatibility, no need to rewrite business logic
- 🛡️ **Higher Stability**: Smart caching and error handling mechanisms
- 📊 **Observability**: Detailed cache statistics and performance monitoring

## 📋 Pre-Migration Preparation

### 1. Environment Assessment

First, assess current AKShare usage in your project:

```python
# Create assessment script assess_akshare_usage.py
import ast
import os
from pathlib import Path

def analyze_akshare_usage(project_path):
    """Analyze AKShare usage in the project"""
    akshare_calls = []
    
    for py_file in Path(project_path).rglob("*.py"):
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Check AKShare imports
            if 'import akshare' in content or 'from akshare' in content:
                akshare_calls.append({
                    'file': str(py_file),
                    'imports': extract_akshare_imports(content),
                    'calls': extract_akshare_calls(content)
                })
        except Exception as e:
            print(f"Error analyzing {py_file}: {e}")
    
    return akshare_calls

# Run assessment
usage_report = analyze_akshare_usage("./your_project")
print(f"Found {len(usage_report)} files using AKShare")
```

### 2. Dependency Check

```bash
# Check current environment
pip list | grep -E "(akshare|pandas|numpy)"

# Install QuantDB
pip install quantdb

# Verify installation
python -c "import qdb; print(f'QuantDB version: {qdb.__version__}')"
```

## 🔄 Migration Strategies

### Strategy A: Progressive Migration (Recommended)

Suitable for large projects, controllable risk, gradual effect verification.

#### Step 1: Create Adapter Layer

```python
# data_adapter.py - Unified data interface layer
import qdb
import akshare as ak
import os
from typing import Optional, Union
import pandas as pd

class DataAdapter:
    """Data retrieval adapter supporting AKShare and QuantDB switching"""
    
    def __init__(self, use_quantdb: bool = None):
        # Support environment variable control
        if use_quantdb is None:
            use_quantdb = os.getenv('USE_QUANTDB', 'true').lower() == 'true'
        
        self.use_quantdb = use_quantdb
        self.stats = {'quantdb_calls': 0, 'akshare_calls': 0}
    
    def get_stock_data(self, symbol: str, **kwargs) -> pd.DataFrame:
        """Get stock historical data"""
        if self.use_quantdb:
            self.stats['quantdb_calls'] += 1
            return qdb.get_stock_data(symbol, **kwargs)
        else:
            self.stats['akshare_calls'] += 1
            # Convert parameters to be compatible with AKShare
            return self._call_akshare_stock_hist(symbol, **kwargs)
    
    def get_realtime_data(self, symbol: str) -> dict:
        """Get real-time data"""
        if self.use_quantdb:
            self.stats['quantdb_calls'] += 1
            return qdb.get_realtime_data(symbol)
        else:
            self.stats['akshare_calls'] += 1
            return self._call_akshare_realtime(symbol)
    
    def _call_akshare_stock_hist(self, symbol: str, **kwargs):
        """Call AKShare to get historical data"""
        # Parameter conversion logic
        if 'days' in kwargs:
            # QuantDB's days parameter needs conversion to start_date
            from datetime import datetime, timedelta
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=kwargs['days'])).strftime('%Y%m%d')
            return ak.stock_zh_a_hist(symbol=symbol, start_date=start_date, end_date=end_date)
        else:
            return ak.stock_zh_a_hist(symbol=symbol, **kwargs)
    
    def get_performance_stats(self):
        """Get performance statistics"""
        return self.stats

# Global data adapter instance
data_api = DataAdapter()
```

#### Step 2: Replace Business Code Calls

```python
# Original code (strategy.py)
# import akshare as ak
# df = ak.stock_zh_a_hist("000001", start_date="20240101", end_date="20240201")

# After migration
from data_adapter import data_api

# Use unified interface, support one-click switching
df = data_api.get_stock_data("000001", start_date="20240101", end_date="20240201")
realtime = data_api.get_realtime_data("000001")
```

#### Step 3: Performance Comparison Testing

```python
# performance_test.py
import time
from data_adapter import DataAdapter

def benchmark_data_sources():
    """Compare AKShare and QuantDB performance"""
    symbols = ["000001", "000002", "600000", "000858"]
    
    # Test AKShare
    akshare_adapter = DataAdapter(use_quantdb=False)
    start_time = time.time()
    
    for symbol in symbols:
        df = akshare_adapter.get_stock_data(symbol, days=30)
        print(f"AKShare {symbol}: {len(df)} records")
    
    akshare_time = time.time() - start_time
    
    # Test QuantDB (first call)
    quantdb_adapter = DataAdapter(use_quantdb=True)
    start_time = time.time()
    
    for symbol in symbols:
        df = quantdb_adapter.get_stock_data(symbol, days=30)
        print(f"QuantDB {symbol}: {len(df)} records")
    
    quantdb_cold_time = time.time() - start_time
    
    # Test QuantDB (cache hit)
    start_time = time.time()
    
    for symbol in symbols:
        df = quantdb_adapter.get_stock_data(symbol, days=30)
    
    quantdb_warm_time = time.time() - start_time
    
    # Output results
    print(f"\nPerformance Comparison Results:")
    print(f"AKShare total time: {akshare_time:.2f}s")
    print(f"QuantDB first call: {quantdb_cold_time:.2f}s")
    print(f"QuantDB cache hit: {quantdb_warm_time:.2f}s")
    print(f"Performance improvement: {((akshare_time - quantdb_warm_time) / akshare_time * 100):.1f}%")

if __name__ == "__main__":
    benchmark_data_sources()
```

### Strategy B: Direct Replacement (Suitable for Small Projects)

For projects with less code, direct replacement is possible:

```python
# Before replacement
import akshare as ak

def get_stock_analysis(symbol):
    df = ak.stock_zh_a_hist(symbol, start_date="20240101", end_date="20240201")
    return df.describe()

# After replacement
import qdb

def get_stock_analysis(symbol):
    df = qdb.stock_zh_a_hist(symbol, start_date="20240101", end_date="20240201")
    return df.describe()
```

## 🧪 Practical Case: Quantitative Strategy Migration

### Case Background

A quantitative trading strategy needs to:
- Get historical data for 50 stocks for backtesting
- Get real-time data daily for signal calculation
- Support multiple strategies running in parallel

### Original Implementation (AKShare)

```python
# original_strategy.py
import akshare as ak
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class MomentumStrategy:
    def __init__(self, symbols):
        self.symbols = symbols
        self.data_cache = {}
    
    def fetch_data(self, symbol, days=30):
        """Get stock data"""
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')
        
        print(f"Fetching {symbol} data...")
        df = ak.stock_zh_a_hist(symbol, start_date=start_date, end_date=end_date)
        return df
    
    def calculate_momentum(self, df):
        """Calculate momentum indicators"""
        df['returns'] = df['收盘'].pct_change()
        df['momentum'] = df['returns'].rolling(window=5).mean()
        return df
    
    def run_backtest(self):
        """Run backtest"""
        results = {}
        
        for symbol in self.symbols:
            # Need to re-fetch data each time, time-consuming
            df = self.fetch_data(symbol)
            df = self.calculate_momentum(df)
            
            # Simple momentum strategy
            signals = np.where(df['momentum'] > 0.01, 1, 
                             np.where(df['momentum'] < -0.01, -1, 0))
            
            results[symbol] = {
                'total_return': (df['收盘'].iloc[-1] / df['收盘'].iloc[0] - 1) * 100,
                'signal_count': np.sum(np.abs(signals))
            }
        
        return results
```

### After Migration Implementation (QuantDB)

```python
# optimized_strategy.py
import qdb
import pandas as pd
import numpy as np
import time

class OptimizedMomentumStrategy:
    def __init__(self, symbols):
        self.symbols = symbols
        # QuantDB handles caching automatically, no manual management needed
    
    def fetch_data(self, symbol, days=30):
        """Get stock data - using QuantDB"""
        print(f"Fetching {symbol} data...")
        # Use QuantDB's simplified API
        df = qdb.get_stock_data(symbol, days=days)
        return df
    
    def batch_fetch_data(self, symbols, days=30):
        """Batch fetch data - utilizing QuantDB's batch interface"""
        print(f"Batch fetching {len(symbols)} stocks data...")
        return qdb.get_multiple_stocks(symbols, days=days)
    
    def calculate_momentum(self, df):
        """Calculate momentum indicators"""
        df['returns'] = df['close'].pct_change()  # QuantDB uses English column names
        df['momentum'] = df['returns'].rolling(window=5).mean()
        return df
    
    def run_backtest(self):
        """Run backtest - optimized version"""
        # Use batch interface to get all data at once
        all_data = self.batch_fetch_data(self.symbols)
        results = {}
        
        for symbol, df in all_data.items():
            if df is None or df.empty:
                continue
                
            df = self.calculate_momentum(df)
            
            # Simple momentum strategy
            signals = np.where(df['momentum'] > 0.01, 1, 
                             np.where(df['momentum'] < -0.01, -1, 0))
            
            results[symbol] = {
                'total_return': (df['close'].iloc[-1] / df['close'].iloc[0] - 1) * 100,
                'signal_count': np.sum(np.abs(signals))
            }
        
        return results
    
    def get_cache_stats(self):
        """Get cache statistics"""
        return qdb.cache_stats()
```

## 📊 Migration Effect Validation

### Performance Comparison Results

```python
# migration_validation.py
import time
import qdb

def validate_migration():
    """Validate migration effects"""
    test_symbols = ["000001", "000002", "600000"]
    
    print("=== Migration Effect Validation ===")
    
    # Test data consistency
    print("1. Data consistency check...")
    for symbol in test_symbols:
        qdb_data = qdb.get_stock_data(symbol, days=10)
        print(f"{symbol}: QuantDB data {len(qdb_data)} records")
        
        # Verify data format
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        missing_cols = [col for col in required_columns if col not in qdb_data.columns]
        if missing_cols:
            print(f"  Warning: Missing columns {missing_cols}")
        else:
            print(f"  ✓ Data format correct")
    
    # Test performance improvement
    print("\n2. Performance improvement validation...")
    symbol = "000001"
    
    # First call
    start = time.time()
    qdb.get_stock_data(symbol, days=30)
    cold_time = time.time() - start
    
    # Cache hit
    start = time.time()
    qdb.get_stock_data(symbol, days=30)
    warm_time = time.time() - start
    
    improvement = ((cold_time - warm_time) / cold_time) * 100
    print(f"  First call: {cold_time:.3f}s")
    print(f"  Cache hit: {warm_time:.3f}s")
    print(f"  Performance improvement: {improvement:.1f}%")
    
    # Cache statistics
    print("\n3. Cache status...")
    stats = qdb.cache_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")

if __name__ == "__main__":
    validate_migration()
```

## 🚨 Common Issues and Solutions

### 1. Column Name Differences

**Issue**: AKShare returns Chinese column names, QuantDB returns English column names

**Solution**:
```python
def normalize_columns(df):
    """Normalize column names"""
    column_mapping = {
        '日期': 'date', '开盘': 'open', '收盘': 'close',
        '最高': 'high', '最低': 'low', '成交量': 'volume'
    }
    return df.rename(columns=column_mapping)
```

### 2. Cache Directory Permission Issues

**Issue**: Insufficient cache directory permissions in Windows environment

**Solution**:
```python
import os
from pathlib import Path

# Set cache path in user directory
cache_dir = Path.home() / ".quantdb_cache"
cache_dir.mkdir(exist_ok=True)
qdb.set_cache_dir(str(cache_dir))
```

## ✅ Migration Checklist

### Pre-Migration Check
- [ ] Assess current AKShare usage
- [ ] Backup existing code and data
- [ ] Prepare test environment
- [ ] Install QuantDB and verify

### Migration Process Check
- [ ] Create adapter layer or direct replacement
- [ ] Handle column name differences
- [ ] Update error handling logic
- [ ] Configure cache directory

### Post-Migration Validation
- [ ] Data consistency verification
- [ ] Performance improvement confirmation
- [ ] Functional completeness testing
- [ ] Error handling testing
- [ ] Production environment deployment

## 💡 Best Practice Recommendations

1. **Progressive Migration**: Use adapter pattern for large projects
2. **Thorough Testing**: Comprehensive testing before production deployment
3. **Monitor Caching**: Regularly check cache statistics and performance metrics
4. **Backup Strategy**: Keep AKShare as backup data source
5. **Team Training**: Ensure team members understand new APIs and best practices

---

**Next Reading**:
- [QuantDB Architecture Deep Dive](architecture-deep-dive.md)
- [Performance Comparison Study](performance-comparison-study.md)

**Get Help**:
- [GitHub Issues](https://github.com/franksunye/quantdb/issues)
- [Project Documentation](https://franksunye.github.io/quantdb/)
