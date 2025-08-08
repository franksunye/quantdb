# AKShare Performance Optimization with QuantDB (Draft)

## Background
- Pain point: Direct AKShare calls are slow for iterative research workflows.
- Goal: 90%+ faster by smart caching and trading calendar awareness.

## Method
- Smart SQLite cache with TTL tuned by market hours
- Incremental fetching by detecting missing date ranges
- Unified models/services reused across products (API/Cloud/Package)

## Benchmark
- Table: baseline vs QuantDB (response time, cache hit)
- Chart: latency distribution (p50/p90/p99)

## Usage Example
```python
import qdb
print(qdb.get_stock_data('000001', days=30).head())
```

## Appendix
- Environment notes
- Repro steps
- Further work

