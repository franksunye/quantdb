# src/cache/preloader.py
"""
Preloader for the Reservoir Cache mechanism.

This module provides functionality for preloading data into the cache
based on predicted usage patterns.
"""

import sqlite3
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple, Set, Callable

from src.config import DATABASE_PATH
from src.logger import setup_logger
from src.cache.cache_engine import CacheEngine
from src.cache.freshness_tracker import FreshnessTracker
from src.cache.data_injector import DataInjector

# Setup logger
logger = setup_logger(__name__)

# Preloader database file path
PRELOADER_DB_PATH = Path(DATABASE_PATH).parent / "preloader.db"

# Default preload settings
DEFAULT_PRELOAD_INTERVAL = 3600  # 1 hour
DEFAULT_PRELOAD_BATCH_SIZE = 5  # Number of items to preload in one batch
DEFAULT_PRELOAD_THRESHOLD = 0.7  # Probability threshold for preloading


class Preloader:
    """
    Preloader for the Reservoir Cache mechanism.

    This class provides methods for preloading data into the cache
    based on predicted usage patterns.
    """

    def __init__(self, 
                cache_engine: Optional[CacheEngine] = None,
                freshness_tracker: Optional[FreshnessTracker] = None,
                data_injector: Optional[DataInjector] = None,
                db_path: Optional[str] = None):
        """
        Initialize the preloader.

        Args:
            cache_engine: Cache engine instance. If None, creates a new one.
            freshness_tracker: Freshness tracker instance. If None, creates a new one.
            data_injector: Data injector instance. If None, creates a new one.
            db_path: Path to the preloader database file. If None, uses the default path.
        """
        self.db_path = db_path or str(PRELOADER_DB_PATH)
        
        # Initialize cache components
        self.cache_engine = cache_engine or CacheEngine()
        self.freshness_tracker = freshness_tracker or FreshnessTracker()
        self.data_injector = data_injector or DataInjector()
        
        # Initialize database
        self._init_db()
        
        # Preload settings
        self.preload_interval = DEFAULT_PRELOAD_INTERVAL
        self.preload_batch_size = DEFAULT_PRELOAD_BATCH_SIZE
        self.preload_threshold = DEFAULT_PRELOAD_THRESHOLD
        
        # Preload thread
        self.preload_thread = None
        self.stop_preload_thread = threading.Event()
        
        # Preload handlers
        self.preload_handlers = {}
        
        logger.info(f"Preloader initialized with database at {self.db_path}")

    def _init_db(self) -> None:
        """Initialize the preloader database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create preload_patterns table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS preload_patterns (
            pattern_id INTEGER PRIMARY KEY AUTOINCREMENT,
            pattern_type TEXT,
            pattern_key TEXT,
            pattern_value TEXT,
            confidence REAL,
            last_updated TIMESTAMP
        )
        ''')

        # Create preload_history table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS preload_history (
            history_id INTEGER PRIMARY KEY AUTOINCREMENT,
            cache_key TEXT,
            preload_time TIMESTAMP,
            access_time TIMESTAMP,
            was_accessed BOOLEAN,
            pattern_id INTEGER,
            FOREIGN KEY (pattern_id) REFERENCES preload_patterns (pattern_id)
        )
        ''')

        conn.commit()
        conn.close()
        logger.debug("Preloader database initialized")

    def register_preload_handler(self, data_type: str, handler: Callable) -> None:
        """
        Register a handler function for preloading a specific data type.

        Args:
            data_type: Type of data to preload.
            handler: Function to call for preloading data.
        """
        self.preload_handlers[data_type] = handler
        logger.info(f"Registered preload handler for data type: {data_type}")

    def start_preload_thread(self) -> None:
        """Start the preload thread."""
        if self.preload_thread is not None and self.preload_thread.is_alive():
            logger.warning("Preload thread is already running")
            return

        self.stop_preload_thread.clear()
        self.preload_thread = threading.Thread(
            target=self._preload_thread_func,
            daemon=True
        )
        self.preload_thread.start()
        logger.info("Preload thread started")

    def stop_preload_thread(self) -> None:
        """Stop the preload thread."""
        if self.preload_thread is None or not self.preload_thread.is_alive():
            logger.warning("Preload thread is not running")
            return

        self.stop_preload_thread.set()
        self.preload_thread.join(timeout=5)
        logger.info("Preload thread stopped")

    def _preload_thread_func(self) -> None:
        """Preload thread function."""
        logger.info("Preload thread started")
        
        while not self.stop_preload_thread.is_set():
            try:
                # Preload data
                self.preload_data()
                
                # Sleep for the preload interval
                for _ in range(self.preload_interval // 10):
                    if self.stop_preload_thread.is_set():
                        break
                    time.sleep(10)
                    
            except Exception as e:
                logger.error(f"Error in preload thread: {e}")
                time.sleep(60)  # Sleep for a minute before retrying
                
        logger.info("Preload thread stopped")

    def preload_data(self) -> None:
        """Preload data into the cache."""
        # Get hot keys from data injector
        hot_keys = self.data_injector.get_hot_keys(limit=self.preload_batch_size * 2)
        
        # Filter out keys that are already fresh
        keys_to_preload = []
        for key_info in hot_keys:
            cache_key = key_info["cache_key"]
            if not self.freshness_tracker.is_fresh(cache_key, freshness_requirement="relaxed"):
                keys_to_preload.append(key_info)
        
        # Limit to batch size
        keys_to_preload = keys_to_preload[:self.preload_batch_size]
        
        if not keys_to_preload:
            logger.debug("No keys to preload")
            return
            
        logger.info(f"Preloading {len(keys_to_preload)} keys")
        
        # Preload each key
        for key_info in keys_to_preload:
            cache_key = key_info["cache_key"]
            data_type = key_info["data_type"]
            
            # Check if we have a handler for this data type
            if data_type in self.preload_handlers:
                try:
                    # Call the handler to preload the data
                    handler = self.preload_handlers[data_type]
                    handler(cache_key)
                    
                    # Record preload history
                    self._record_preload(cache_key, data_type)
                    
                    logger.info(f"Preloaded data for key: {cache_key}, type: {data_type}")
                except Exception as e:
                    logger.error(f"Error preloading data for key {cache_key}: {e}")
            else:
                logger.warning(f"No preload handler for data type: {data_type}")

    def _record_preload(self, cache_key: str, data_type: str) -> None:
        """
        Record a preload operation.

        Args:
            cache_key: The cache key that was preloaded.
            data_type: Type of data that was preloaded.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Record the preload
        cursor.execute('''
        INSERT INTO preload_history
        (cache_key, preload_time, was_accessed, pattern_id)
        VALUES (?, ?, ?, NULL)
        ''', (
            cache_key,
            datetime.now().isoformat(),
            False
        ))

        conn.commit()
        conn.close()

    def update_preload_success(self, cache_key: str) -> None:
        """
        Update preload history to mark a key as accessed.

        Args:
            cache_key: The cache key that was accessed.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Update the most recent preload history for this key
        cursor.execute('''
        UPDATE preload_history
        SET was_accessed = 1, access_time = ?
        WHERE cache_key = ? AND was_accessed = 0
        ORDER BY preload_time DESC
        LIMIT 1
        ''', (
            datetime.now().isoformat(),
            cache_key
        ))

        conn.commit()
        conn.close()

    def get_preload_stats(self) -> Dict[str, Any]:
        """
        Get preload statistics.

        Returns:
            Dictionary with preload statistics.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get total preloads
        cursor.execute('SELECT COUNT(*) FROM preload_history')
        total_preloads = cursor.fetchone()[0]

        # Get successful preloads
        cursor.execute('SELECT COUNT(*) FROM preload_history WHERE was_accessed = 1')
        successful_preloads = cursor.fetchone()[0]

        # Get preload success rate
        success_rate = successful_preloads / total_preloads if total_preloads > 0 else 0

        # Get average time between preload and access
        cursor.execute('''
        SELECT AVG((julianday(access_time) - julianday(preload_time)) * 86400)
        FROM preload_history
        WHERE was_accessed = 1
        ''')
        avg_time_to_access = cursor.fetchone()[0] or 0

        conn.close()

        return {
            "total_preloads": total_preloads,
            "successful_preloads": successful_preloads,
            "success_rate": success_rate,
            "avg_time_to_access": avg_time_to_access
        }
