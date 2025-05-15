from pydantic import ConfigDict
# src/cache/models.py
"""
Data models for the Reservoir Cache mechanism.

This module defines the data structures used by the cache components,
including cache metadata, cache entries, and freshness status.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional, List


class FreshnessStatus(Enum):
    """Enumeration of possible freshness statuses for cached data."""
    FRESH = "fresh"  # Data is fresh and can be used
    STALE = "stale"  # Data is stale but can still be used
    EXPIRED = "expired"  # Data is expired and should be refreshed
    UNKNOWN = "unknown"  # Freshness status is unknown


class CacheEntryStatus(Enum):
    """Enumeration of possible statuses for cache entries."""
    VALID = "valid"  # Entry is valid and can be used
    INVALID = "invalid"  # Entry is invalid and should not be used
    UPDATING = "updating"  # Entry is currently being updated
    PENDING = "pending"  # Entry is pending creation


@dataclass
class CacheMetadata:
    """Metadata for a cache entry."""
    # When the entry was created
    created_at: datetime = field(default_factory=datetime.now)
    # When the entry was last updated
    updated_at: datetime = field(default_factory=datetime.now)
    # When the entry will expire
    expires_at: Optional[datetime] = None
    # Number of times the entry has been accessed
    access_count: int = 0
    # Last time the entry was accessed
    last_accessed_at: Optional[datetime] = None
    # Size of the entry in bytes
    size_bytes: int = 0
    # Status of the entry
    status: CacheEntryStatus = CacheEntryStatus.VALID
    # Additional metadata
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CacheEntry:
    """A cache entry containing data and metadata."""
    # Unique key for the cache entry
    key: str
    # The cached data
    data: Any
    # Metadata for the cache entry
    metadata: CacheMetadata = field(default_factory=CacheMetadata)


@dataclass
class FreshnessInfo:
    """Information about the freshness of a cache entry."""
    # The cache key
    cache_key: str
    # Current freshness status
    status: FreshnessStatus = FreshnessStatus.UNKNOWN
    # When the data was last updated
    last_updated: datetime = field(default_factory=datetime.now)
    # When the data will expire
    expires_at: Optional[datetime] = None
    # Whether an update is scheduled
    update_scheduled: bool = False
    # Priority of the scheduled update (0 = lowest)
    update_priority: int = 0
    # Additional information
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CacheStats:
    """Statistics for the cache."""
    # Total number of entries in the cache
    total_entries: int = 0
    # Number of hits (cache key found)
    hits: int = 0
    # Number of misses (cache key not found)
    misses: int = 0
    # Hit rate (hits / (hits + misses))
    hit_rate: float = 0.0
    # Total size of the cache in bytes
    total_size_bytes: int = 0
    # Number of expired entries
    expired_entries: int = 0
    # Number of entries by status
    entries_by_status: Dict[CacheEntryStatus, int] = field(default_factory=dict)
    # Number of entries by freshness status
    entries_by_freshness: Dict[FreshnessStatus, int] = field(default_factory=dict)
    # Top accessed keys
    top_accessed_keys: List[str] = field(default_factory=list)
    # Additional statistics
    extra: Dict[str, Any] = field(default_factory=dict)
