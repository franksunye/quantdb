# src/cache/__init__.py
"""
Reservoir Cache Mechanism package.

This package contains the components of the "Reservoir Cache" mechanism,
which serves as an intelligent middleware layer above external data sources
like AKShare, optimizing data acquisition and caching processes.
"""

from src.cache.cache_engine import CacheEngine
from src.cache.freshness_tracker import FreshnessTracker
from src.cache.akshare_adapter import AKShareAdapter

__all__ = ['CacheEngine', 'FreshnessTracker', 'AKShareAdapter']
