# src/cache/__init__.py
"""
Simplified Cache Mechanism package.

This package contains the simplified cache components,
which serve as an intelligent middleware layer above external data sources
like AKShare, optimizing data acquisition and caching processes.
"""

from core.cache.akshare_adapter import AKShareAdapter

__all__ = ['AKShareAdapter']
