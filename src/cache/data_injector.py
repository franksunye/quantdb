# src/cache/data_injector.py
"""
Data injector for the Reservoir Cache mechanism.

This module provides functionality for determining which data should be cached,
based on access patterns, data size, and update frequency.
"""

import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

from src.config import DATABASE_PATH
from src.logger import setup_logger

# Setup logger
logger = setup_logger(__name__)

# Injector database file path
INJECTOR_DB_PATH = Path(DATABASE_PATH).parent / "injector.db"

# Default TTL values (in seconds)
DEFAULT_TTL = 86400  # 24 hours
MIN_TTL = 300  # 5 minutes
MAX_TTL = 604800  # 7 days

# Data size thresholds (in bytes)
SMALL_DATA_SIZE = 1024 * 10  # 10 KB
MEDIUM_DATA_SIZE = 1024 * 1024  # 1 MB
LARGE_DATA_SIZE = 1024 * 1024 * 10  # 10 MB

# Access frequency thresholds
HIGH_ACCESS_FREQUENCY = 10  # 10 accesses per day
MEDIUM_ACCESS_FREQUENCY = 3  # 3 accesses per day

# Data types and their default TTLs
DATA_TYPE_TTLS = {
    "stock_data": 86400,  # 24 hours
    "index_data": 86400,  # 24 hours
    "price_data": 43200,  # 12 hours
    "fundamental_data": 604800,  # 7 days
    "news_data": 3600,  # 1 hour
    "default": DEFAULT_TTL
}


class DataInjector:
    """
    Data injector for the Reservoir Cache mechanism.

    This class provides methods for determining which data should be cached,
    based on access patterns, data size, and update frequency.
    """

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the data injector.

        Args:
            db_path: Path to the injector database file. If None, uses the default path.
        """
        self.db_path = db_path or str(INJECTOR_DB_PATH)
        self._init_db()
        logger.info(f"Data injector initialized with database at {self.db_path}")

    def _init_db(self) -> None:
        """Initialize the injector database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create access_patterns table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS access_patterns (
            cache_key TEXT PRIMARY KEY,
            access_count INTEGER,
            first_access TIMESTAMP,
            last_access TIMESTAMP,
            data_type TEXT,
            data_size INTEGER,
            metadata TEXT
        )
        ''')

        # Create cache_decisions table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS cache_decisions (
            cache_key TEXT PRIMARY KEY,
            should_cache BOOLEAN,
            ttl INTEGER,
            decision_time TIMESTAMP,
            decision_reason TEXT
        )
        ''')

        conn.commit()
        conn.close()
        logger.debug("Injector database initialized")

    def should_cache(self, data_type: str, data_size: int, 
                    access_pattern: Optional[Dict[str, Any]] = None) -> bool:
        """
        Determine if data should be cached.

        Args:
            data_type: Type of data (e.g., "stock_data", "index_data").
            data_size: Size of data in bytes.
            access_pattern: Access pattern information (optional).

        Returns:
            True if the data should be cached, False otherwise.
        """
        # Always cache small data
        if data_size <= SMALL_DATA_SIZE:
            return True

        # For medium-sized data, check access frequency
        if data_size <= MEDIUM_DATA_SIZE:
            if access_pattern and access_pattern.get("frequency", 0) >= MEDIUM_ACCESS_FREQUENCY:
                return True
            # Default to cache for medium data
            return True

        # For large data, only cache if frequently accessed
        if data_size <= LARGE_DATA_SIZE:
            if access_pattern and access_pattern.get("frequency", 0) >= HIGH_ACCESS_FREQUENCY:
                return True
            # Default to not cache for large data
            return False

        # For very large data, don't cache unless explicitly required
        if access_pattern and access_pattern.get("force_cache", False):
            return True
        
        return False

    def get_ttl(self, data_type: str, 
               access_pattern: Optional[Dict[str, Any]] = None) -> int:
        """
        Get the time-to-live for cached data.

        Args:
            data_type: Type of data (e.g., "stock_data", "index_data").
            access_pattern: Access pattern information (optional).

        Returns:
            TTL in seconds.
        """
        # Get base TTL for data type
        base_ttl = DATA_TYPE_TTLS.get(data_type, DEFAULT_TTL)

        # Adjust TTL based on access frequency
        if access_pattern:
            frequency = access_pattern.get("frequency", 0)
            if frequency >= HIGH_ACCESS_FREQUENCY:
                # Frequently accessed data gets longer TTL
                return min(base_ttl * 2, MAX_TTL)
            elif frequency <= 1:
                # Rarely accessed data gets shorter TTL
                return max(base_ttl // 2, MIN_TTL)

        return base_ttl

    def update_access_pattern(self, cache_key: str, access_time: Optional[datetime] = None,
                             data_type: Optional[str] = None, 
                             data_size: Optional[int] = None) -> None:
        """
        Update access pattern for a cache key.

        Args:
            cache_key: The cache key.
            access_time: Time of access. If None, uses current time.
            data_type: Type of data (optional).
            data_size: Size of data in bytes (optional).
        """
        if access_time is None:
            access_time = datetime.now()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Check if the key already exists
        cursor.execute('SELECT cache_key, access_count, first_access, data_type, data_size FROM access_patterns WHERE cache_key = ?', 
                      (cache_key,))
        result = cursor.fetchone()

        if result:
            # Update existing entry
            _, access_count, first_access_str, existing_data_type, existing_data_size = result
            
            # Increment access count
            access_count += 1
            
            # Use existing values if new ones not provided
            if data_type is None:
                data_type = existing_data_type
            if data_size is None:
                data_size = existing_data_size

            cursor.execute('''
            UPDATE access_patterns
            SET access_count = ?, last_access = ?, data_type = ?, data_size = ?
            WHERE cache_key = ?
            ''', (
                access_count,
                access_time.isoformat(),
                data_type,
                data_size,
                cache_key
            ))
        else:
            # Insert new entry
            cursor.execute('''
            INSERT INTO access_patterns
            (cache_key, access_count, first_access, last_access, data_type, data_size, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                cache_key,
                1,  # Initial access count
                access_time.isoformat(),
                access_time.isoformat(),
                data_type or "unknown",
                data_size or 0,
                "{}"  # Empty metadata
            ))

        conn.commit()
        conn.close()
        logger.debug(f"Updated access pattern for key: {cache_key}")

    def get_access_pattern(self, cache_key: str) -> Dict[str, Any]:
        """
        Get access pattern for a cache key.

        Args:
            cache_key: The cache key.

        Returns:
            Dictionary with access pattern information.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get the access pattern
        cursor.execute('''
        SELECT access_count, first_access, last_access, data_type, data_size, metadata
        FROM access_patterns
        WHERE cache_key = ?
        ''', (cache_key,))

        result = cursor.fetchone()
        conn.close()

        if result is None:
            return {
                "cache_key": cache_key,
                "access_count": 0,
                "first_access": None,
                "last_access": None,
                "data_type": "unknown",
                "data_size": 0,
                "frequency": 0,
                "metadata": {}
            }

        access_count, first_access_str, last_access_str, data_type, data_size, metadata_str = result

        # Parse dates
        first_access = datetime.fromisoformat(first_access_str) if first_access_str else None
        last_access = datetime.fromisoformat(last_access_str) if last_access_str else None

        # Calculate access frequency (accesses per day)
        frequency = 0
        if first_access and last_access:
            days_diff = max(1, (last_access - first_access).total_seconds() / 86400)
            frequency = access_count / days_diff

        # Parse metadata
        try:
            metadata = json.loads(metadata_str)
        except (json.JSONDecodeError, TypeError):
            metadata = {}

        return {
            "cache_key": cache_key,
            "access_count": access_count,
            "first_access": first_access_str,
            "last_access": last_access_str,
            "data_type": data_type,
            "data_size": data_size,
            "frequency": frequency,
            "metadata": metadata
        }

    def get_hot_keys(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get the most frequently accessed cache keys.

        Args:
            limit: Maximum number of keys to return.

        Returns:
            List of dictionaries with access pattern information.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get the most frequently accessed keys
        cursor.execute('''
        SELECT cache_key, access_count, first_access, last_access, data_type, data_size
        FROM access_patterns
        ORDER BY access_count DESC
        LIMIT ?
        ''', (limit,))

        results = cursor.fetchall()
        conn.close()

        hot_keys = []
        for result in results:
            cache_key, access_count, first_access_str, last_access_str, data_type, data_size = result

            # Calculate access frequency
            first_access = datetime.fromisoformat(first_access_str) if first_access_str else None
            last_access = datetime.fromisoformat(last_access_str) if last_access_str else None
            
            frequency = 0
            if first_access and last_access:
                days_diff = max(1, (last_access - first_access).total_seconds() / 86400)
                frequency = access_count / days_diff

            hot_keys.append({
                "cache_key": cache_key,
                "access_count": access_count,
                "first_access": first_access_str,
                "last_access": last_access_str,
                "data_type": data_type,
                "data_size": data_size,
                "frequency": frequency
            })

        return hot_keys

    def record_cache_decision(self, cache_key: str, should_cache: bool, 
                             ttl: int, reason: str) -> None:
        """
        Record a cache decision.

        Args:
            cache_key: The cache key.
            should_cache: Whether the data should be cached.
            ttl: Time-to-live in seconds.
            reason: Reason for the decision.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Record the decision
        cursor.execute('''
        INSERT OR REPLACE INTO cache_decisions
        (cache_key, should_cache, ttl, decision_time, decision_reason)
        VALUES (?, ?, ?, ?, ?)
        ''', (
            cache_key,
            should_cache,
            ttl,
            datetime.now().isoformat(),
            reason
        ))

        conn.commit()
        conn.close()
        logger.debug(f"Recorded cache decision for key: {cache_key}, should_cache: {should_cache}")
