# src/cache/cache_engine.py
"""
Cache engine for the Reservoir Cache mechanism.

This module provides the core functionality for the cache, including
key generation, data storage and retrieval, expiration management,
and cache hit rate statistics.
"""

import hashlib
import json
import logging
import sqlite3
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import pandas as pd
import pickle

from src.cache.models import (
    CacheEntry, CacheEntryStatus, CacheMetadata, CacheStats, FreshnessStatus
)
from src.config import DATABASE_PATH
from src.logger import logger

# Cache database file path
CACHE_DB_PATH = Path(DATABASE_PATH).parent / "cache.db"


class CacheEngine:
    """
    Core cache engine for the Reservoir Cache mechanism.

    This class provides methods for storing and retrieving data from the cache,
    managing cache expiration, and tracking cache statistics.
    """

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the cache engine.

        Args:
            db_path: Path to the cache database file. If None, uses the default path.
        """
        self.db_path = db_path or str(CACHE_DB_PATH)
        self._init_db()
        self.hits = 0
        self.misses = 0
        logger.info(f"Cache engine initialized with database at {self.db_path}")

    def _get_connection(self) -> sqlite3.Connection:
        """
        Get a connection to the cache database.

        Returns:
            A connection to the cache database.
        """
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        """Initialize the cache database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create cache_entries table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS cache_entries (
            key TEXT PRIMARY KEY,
            data BLOB,
            created_at TIMESTAMP,
            updated_at TIMESTAMP,
            expires_at TIMESTAMP,
            access_count INTEGER,
            last_accessed_at TIMESTAMP,
            size_bytes INTEGER,
            status TEXT
        )
        ''')

        # Create cache_metadata table for additional metadata
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS cache_metadata (
            key TEXT,
            meta_key TEXT,
            meta_value TEXT,
            PRIMARY KEY (key, meta_key),
            FOREIGN KEY (key) REFERENCES cache_entries(key) ON DELETE CASCADE
        )
        ''')

        # Create cache_stats table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS cache_stats (
            stat_key TEXT PRIMARY KEY,
            stat_value TEXT
        )
        ''')

        conn.commit()
        conn.close()
        logger.debug("Cache database initialized")

    def generate_key(self, *args, **kwargs) -> str:
        """
        Generate a cache key from the provided arguments.

        Args:
            *args: Positional arguments to include in the key.
            **kwargs: Keyword arguments to include in the key.
                Special kwargs:
                - prefix: A prefix to add to the key.
                - namespace: A namespace to add to the key.
                - version: A version to add to the key.

        Returns:
            A string key generated from the arguments.
        """
        # Extract special kwargs
        prefix = kwargs.pop("prefix", None)
        namespace = kwargs.pop("namespace", None)
        version = kwargs.pop("version", None)

        # Create a dictionary of all arguments
        key_dict = {
            "args": self._normalize_args(args),
            "kwargs": {k: self._normalize_value(v) for k, v in sorted(kwargs.items())}
        }

        # Convert to a stable JSON string
        try:
            key_str = json.dumps(key_dict, sort_keys=True, default=self._json_serializer)
        except (TypeError, ValueError) as e:
            logger.warning(f"Error serializing cache key: {e}. Using string representation.")
            # Fallback to string representation
            key_str = str(key_dict)

        # Generate a hash
        key_hash = hashlib.md5(key_str.encode()).hexdigest()

        # Build the final key with optional components
        key_parts = []

        if namespace:
            key_parts.append(str(namespace))

        if prefix:
            key_parts.append(str(prefix))

        key_parts.append(key_hash)

        if version:
            key_parts.append(f"v{version}")

        return ":".join(key_parts)

    def _normalize_args(self, args):
        """
        Normalize positional arguments for consistent key generation.

        Args:
            args: Positional arguments to normalize.

        Returns:
            Normalized arguments.
        """
        return [self._normalize_value(arg) for arg in args]

    def _normalize_value(self, value):
        """
        Normalize a value for consistent key generation.

        Args:
            value: Value to normalize.

        Returns:
            Normalized value.
        """
        # Handle pandas DataFrame
        if isinstance(value, pd.DataFrame):
            return f"DataFrame(shape={value.shape}, columns={value.columns.tolist()})"

        # Handle date and datetime objects
        if isinstance(value, datetime):
            return value.isoformat()

        # Handle lists and tuples
        if isinstance(value, (list, tuple)):
            return [self._normalize_value(item) for item in value]

        # Handle dictionaries
        if isinstance(value, dict):
            return {k: self._normalize_value(v) for k, v in sorted(value.items())}

        return value

    def _json_serializer(self, obj):
        """
        Custom JSON serializer for objects not serializable by default json code.

        Args:
            obj: Object to serialize.

        Returns:
            Serialized representation of the object.
        """
        if isinstance(obj, (datetime, pd.Timestamp)):
            return obj.isoformat()

        if isinstance(obj, pd.DataFrame):
            return f"DataFrame(shape={obj.shape}, columns={obj.columns.tolist()})"

        if hasattr(obj, '__dict__'):
            return obj.__dict__

        return str(obj)

    def generate_structured_key(self, category: str, operation: str, *args, **kwargs) -> str:
        """
        Generate a structured cache key with category and operation.

        Args:
            category: Category of the operation (e.g., "stock", "index").
            operation: Type of operation (e.g., "data", "info").
            *args: Additional positional arguments to include in the key.
            **kwargs: Additional keyword arguments to include in the key.

        Returns:
            A structured string key.
        """
        # Create a dictionary of all arguments
        key_dict = {
            "args": args,
            "kwargs": {k: v for k, v in sorted(kwargs.items())}
        }

        # Convert to a stable JSON string
        args_str = json.dumps(key_dict, sort_keys=True, default=str)

        # Generate a hash of the arguments
        args_hash = hashlib.md5(args_str.encode()).hexdigest()

        # Create a structured key
        return f"{category}:{operation}:{args_hash}"

    def get(self, cache_key: str) -> Optional[Any]:
        """
        Retrieve data from the cache.

        Args:
            cache_key: The key to look up in the cache.

        Returns:
            The cached data if found and valid, None otherwise.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get the cache entry
        cursor.execute('''
        SELECT data, expires_at, status, access_count, size_bytes
        FROM cache_entries
        WHERE key = ?
        ''', (cache_key,))

        result = cursor.fetchone()

        if result is None:
            self.misses += 1
            conn.close()
            logger.debug(f"Cache miss for key: {cache_key}")
            return None

        data_blob, expires_at_str, status_str, access_count, size_bytes = result

        # Check if the entry is valid
        if status_str != CacheEntryStatus.VALID.value:
            self.misses += 1
            conn.close()
            logger.debug(f"Cache entry invalid for key: {cache_key}, status: {status_str}")
            return None

        # Check if the entry has expired
        if expires_at_str is not None:
            expires_at = datetime.fromisoformat(expires_at_str)
            if expires_at < datetime.now():
                self.misses += 1
                conn.close()
                logger.debug(f"Cache entry expired for key: {cache_key}")
                return None

        # Update access count and last accessed time
        cursor.execute('''
        UPDATE cache_entries
        SET access_count = access_count + 1, last_accessed_at = ?
        WHERE key = ?
        ''', (datetime.now().isoformat(), cache_key))

        conn.commit()
        conn.close()

        # Deserialize the data
        try:
            data = pickle.loads(data_blob)
            self.hits += 1
            logger.debug(f"Cache hit for key: {cache_key}")
            return data
        except Exception as e:
            self.misses += 1
            logger.error(f"Error deserializing cache data for key {cache_key}: {e}")
            return None

    def set(self, cache_key: str, data: Any, ttl: Optional[int] = None) -> bool:
        """
        Store data in the cache.

        Args:
            cache_key: The key to store the data under.
            data: The data to store.
            ttl: Time-to-live in seconds. If None, the data doesn't expire.

        Returns:
            True if the data was successfully stored, False otherwise.
        """
        try:
            # Serialize the data
            data_blob = pickle.dumps(data)
            size_bytes = len(data_blob)

            # Default TTL if not provided
            if ttl is None:
                ttl = 86400  # 24 hours

            # Calculate expiration time
            now = datetime.now()
            expires_at = None
            if ttl is not None:
                expires_at = (now + timedelta(seconds=ttl)).isoformat()

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Check if the key already exists
            cursor.execute('SELECT key FROM cache_entries WHERE key = ?', (cache_key,))
            exists = cursor.fetchone() is not None

            if exists:
                # Update existing entry
                cursor.execute('''
                UPDATE cache_entries
                SET data = ?, updated_at = ?, expires_at = ?, size_bytes = ?, status = ?
                WHERE key = ?
                ''', (
                    data_blob,
                    now.isoformat(),
                    expires_at,
                    size_bytes,
                    CacheEntryStatus.VALID.value,
                    cache_key
                ))
            else:
                # Insert new entry
                cursor.execute('''
                INSERT INTO cache_entries
                (key, data, created_at, updated_at, expires_at, access_count, size_bytes, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    cache_key,
                    data_blob,
                    now.isoformat(),
                    now.isoformat(),
                    expires_at,
                    0,
                    size_bytes,
                    CacheEntryStatus.VALID.value
                ))

            conn.commit()
            conn.close()

            logger.debug(f"Cache entry set for key: {cache_key}, size: {size_bytes} bytes, ttl: {ttl}s")
            return True

        except Exception as e:
            logger.error(f"Error setting cache entry for key {cache_key}: {e}")
            return False

    def invalidate(self, cache_key: str) -> bool:
        """
        Invalidate a cache entry.

        Args:
            cache_key: The key to invalidate.

        Returns:
            True if the entry was invalidated, False otherwise.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Check if the key exists
            cursor.execute('SELECT key FROM cache_entries WHERE key = ?', (cache_key,))
            exists = cursor.fetchone() is not None

            if not exists:
                conn.close()
                logger.debug(f"Cache key not found for invalidation: {cache_key}")
                return False

            # Update the entry status
            cursor.execute('''
            UPDATE cache_entries
            SET status = ?
            WHERE key = ?
            ''', (CacheEntryStatus.INVALID.value, cache_key))

            conn.commit()
            conn.close()

            logger.debug(f"Cache entry invalidated for key: {cache_key}")
            return True

        except Exception as e:
            logger.error(f"Error invalidating cache entry for key {cache_key}: {e}")
            return False

    def get_keys(self, prefix: Optional[str] = None) -> List[str]:
        """
        Get all cache keys.

        Args:
            prefix: Optional prefix to filter keys.

        Returns:
            A list of all cache keys.
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Get keys with optional prefix filter
            if prefix:
                cursor.execute('SELECT key FROM cache_entries WHERE key LIKE ?', (f"{prefix}%",))
            else:
                cursor.execute('SELECT key FROM cache_entries')

            keys = [row[0] for row in cursor.fetchall()]

            conn.close()

            return keys

        except Exception as e:
            logger.error(f"Error getting cache keys: {e}")
            return []

    def delete(self, cache_key: str) -> bool:
        """
        Delete a cache entry.

        Args:
            cache_key: The key to delete.

        Returns:
            True if the entry was deleted, False otherwise.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Check if the key exists
            cursor.execute('SELECT 1 FROM cache_entries WHERE key = ?', (cache_key,))
            if cursor.fetchone() is None:
                conn.close()
                return False

            # Delete the entry
            cursor.execute('DELETE FROM cache_entries WHERE key = ?', (cache_key,))

            # Delete metadata
            cursor.execute('DELETE FROM cache_metadata WHERE key = ?', (cache_key,))

            conn.commit()
            conn.close()

            return True

        except Exception as e:
            logger.error(f"Error deleting cache entry {cache_key}: {e}")
            return False

    def clear(self) -> bool:
        """
        Clear all cache entries.

        Returns:
            True if the cache was cleared, False otherwise.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Delete all entries
            cursor.execute('DELETE FROM cache_entries')

            # Delete all metadata
            cursor.execute('DELETE FROM cache_metadata')

            conn.commit()
            conn.close()

            # Reset hit/miss counters
            self.hits = 0
            self.misses = 0

            return True

        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            A dictionary of cache statistics.
        """
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Get total entries
            cursor.execute('SELECT COUNT(*) FROM cache_entries')
            total_entries = cursor.fetchone()[0]

            # Get total size
            cursor.execute('SELECT SUM(size_bytes) FROM cache_entries')
            total_size = cursor.fetchone()[0] or 0

            # Get entries by status
            cursor.execute('''
            SELECT status, COUNT(*)
            FROM cache_entries
            GROUP BY status
            ''')
            entries_by_status = {status: count for status, count in cursor.fetchall()}

            # Get expired entries
            now = datetime.now().isoformat()
            cursor.execute('''
            SELECT COUNT(*)
            FROM cache_entries
            WHERE expires_at IS NOT NULL AND expires_at < ?
            ''', (now,))
            expired_entries = cursor.fetchone()[0]

            # Get top accessed keys
            cursor.execute('''
            SELECT key, access_count
            FROM cache_entries
            ORDER BY access_count DESC
            LIMIT 10
            ''')
            top_accessed_keys = [key for key, _ in cursor.fetchall()]

            # Get average TTL
            cursor.execute('''
            SELECT AVG(
                CASE
                    WHEN expires_at IS NOT NULL
                    THEN (julianday(expires_at) - julianday(updated_at)) * 86400
                    ELSE NULL
                END
            ) FROM cache_entries
            ''')
            avg_ttl = cursor.fetchone()[0] or 0

            # Get top accessed keys with access counts
            cursor.execute('''
            SELECT key, access_count
            FROM cache_entries
            ORDER BY access_count DESC
            LIMIT 5
            ''')
            hot_keys = [{"cache_key": key, "access_count": count} for key, count in cursor.fetchall()]

            # Get recently added keys
            cursor.execute('''
            SELECT key, created_at
            FROM cache_entries
            ORDER BY created_at DESC
            LIMIT 5
            ''')
            recent_keys = [{"cache_key": key, "created_at": created_at} for key, created_at in cursor.fetchall()]

            # Get recently accessed keys
            cursor.execute('''
            SELECT key, last_accessed_at
            FROM cache_entries
            WHERE last_accessed_at IS NOT NULL
            ORDER BY last_accessed_at DESC
            LIMIT 5
            ''')
            recent_accessed_keys = [{"cache_key": key, "last_accessed_at": last_accessed}
                                   for key, last_accessed in cursor.fetchall()]

            # Get soon to expire keys
            cursor.execute('''
            SELECT key, expires_at
            FROM cache_entries
            WHERE expires_at IS NOT NULL AND expires_at > ?
            ORDER BY expires_at ASC
            LIMIT 5
            ''', (now,))
            soon_expire_keys = [{"cache_key": key, "expires_at": expires_at}
                               for key, expires_at in cursor.fetchall()]

            # Get largest entries
            cursor.execute('''
            SELECT key, size_bytes
            FROM cache_entries
            ORDER BY size_bytes DESC
            LIMIT 5
            ''')
            largest_entries = [{"cache_key": key, "size_bytes": size_bytes}
                              for key, size_bytes in cursor.fetchall()]

            # Calculate hit rate
            total_requests = self.hits + self.misses
            hit_rate = self.hits / total_requests if total_requests > 0 else 0

            # Calculate memory efficiency (bytes per entry)
            bytes_per_entry = total_size / total_entries if total_entries > 0 else 0

            # Calculate expiration rate
            expiration_rate = expired_entries / total_entries if total_entries > 0 else 0

            stats = CacheStats(
                total_entries=total_entries,
                hits=self.hits,
                misses=self.misses,
                hit_rate=hit_rate,
                total_size_bytes=total_size,
                expired_entries=expired_entries,
                entries_by_status=entries_by_status,
                top_accessed_keys=top_accessed_keys
            )

            # Close the database connection
            if conn:
                conn.close()

            return {
                "total_entries": stats.total_entries,
                "hits": stats.hits,
                "misses": stats.misses,
                "hit_rate": hit_rate,
                "total_size_bytes": stats.total_size_bytes,
                "expired_entries": stats.expired_entries,
                "entries_by_status": stats.entries_by_status,
                "top_accessed_keys": stats.top_accessed_keys,
                "avg_ttl": avg_ttl,
                "hot_keys": hot_keys,
                "recent_keys": recent_keys,
                "recent_accessed_keys": recent_accessed_keys,
                "soon_expire_keys": soon_expire_keys,
                "largest_entries": largest_entries,
                "bytes_per_entry": bytes_per_entry,
                "expiration_rate": expiration_rate,
                "cache_health": {
                    "hit_rate_health": "good" if hit_rate > 0.8 else "medium" if hit_rate > 0.5 else "poor",
                    "memory_usage": "high" if total_size > 1024*1024*100 else "medium" if total_size > 1024*1024*10 else "low",
                    "expiration_health": "good" if expiration_rate < 0.1 else "medium" if expiration_rate < 0.3 else "poor"
                }
            }

        except Exception as e:
            logger.error(f"Error getting cache statistics: {e}")
            # Close the database connection if it's open
            if conn:
                try:
                    conn.close()
                except:
                    pass
            return {
                "error": str(e)
            }
