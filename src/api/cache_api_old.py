# src/api/cache_api.py
"""
API endpoints for cache management.

This module provides API endpoints for querying cache status,
clearing cache entries, and managing cache settings.
"""

from typing import Dict, Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from src.logger import logger

# Define API models
class CacheStatsResponse(BaseModel):
    """Response model for cache statistics."""
    total_entries: int
    hits: int
    misses: int
    hit_rate: float
    total_size_bytes: int
    expired_entries: int
    entries_by_status: Dict[str, int]
    top_accessed_keys: List[str]
    avg_ttl: float
    hot_keys: List[Dict[str, Any]]

class FreshnessStatsResponse(BaseModel):
    """Response model for freshness statistics."""
    total_entries: int
    entries_by_status: Dict[str, int]
    expired_entries: int
    scheduled_updates: int

class CacheEntryResponse(BaseModel):
    """Response model for a cache entry."""
    key: str
    status: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    expires_at: Optional[str] = None
    access_count: int
    last_accessed_at: Optional[str] = None
    size_bytes: int
    freshness_status: Optional[str] = None

class CacheKeyRequest(BaseModel):
    """Request model for cache key operations."""
    key: str

class CacheKeyResponse(BaseModel):
    """Response model for cache key operations."""
    key: str
    success: bool
    message: str

# Create router
router = APIRouter(
    prefix="/api/cache",
    tags=["cache"],
    responses={404: {"description": "Not found"}},
)

# Dependency for getting cache engine
def get_cache_engine():
    """Get the cache engine instance."""
    return CacheEngine()

# Dependency for getting freshness tracker
def get_freshness_tracker():
    """Get the freshness tracker instance."""
    return FreshnessTracker()

@router.get("/stats", response_model=CacheStatsResponse)
async def get_cache_stats(
    cache_engine: CacheEngine = Depends(get_cache_engine)
) -> Dict[str, Any]:
    """
    Get cache statistics.

    Returns:
        Dictionary with cache statistics.
    """
    try:
        stats = cache_engine.get_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting cache stats: {e}")

@router.get("/freshness/stats", response_model=FreshnessStatsResponse)
async def get_freshness_stats(
    freshness_tracker: FreshnessTracker = Depends(get_freshness_tracker)
) -> Dict[str, Any]:
    """
    Get freshness statistics.

    Returns:
        Dictionary with freshness statistics.
    """
    try:
        stats = freshness_tracker.get_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting freshness stats: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting freshness stats: {e}")

@router.get("/keys", response_model=List[str])
async def get_cache_keys(
    cache_engine: CacheEngine = Depends(get_cache_engine),
    prefix: Optional[str] = Query(None, description="Filter keys by prefix"),
    limit: int = Query(100, description="Maximum number of keys to return")
) -> List[str]:
    """
    Get all cache keys.

    Args:
        prefix: Optional prefix to filter keys.
        limit: Maximum number of keys to return.

    Returns:
        List of cache keys.
    """
    try:
        keys = cache_engine.get_keys()

        # Filter by prefix if provided
        if prefix:
            keys = [key for key in keys if key.startswith(prefix)]

        # Apply limit
        keys = keys[:limit]

        return keys
    except Exception as e:
        logger.error(f"Error getting cache keys: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting cache keys: {e}")

@router.get("/entry/{key}", response_model=CacheEntryResponse)
async def get_cache_entry(
    key: str,
    cache_engine: CacheEngine = Depends(get_cache_engine),
    freshness_tracker: FreshnessTracker = Depends(get_freshness_tracker)
) -> Dict[str, Any]:
    """
    Get details about a specific cache entry.

    Args:
        key: The cache key to get details for.

    Returns:
        Dictionary with cache entry details.
    """
    try:
        # Get entry details from the database
        conn = cache_engine._get_connection()
        cursor = conn.cursor()

        cursor.execute('''
        SELECT key, status, created_at, updated_at, expires_at, access_count,
               last_accessed_at, size_bytes
        FROM cache_entries
        WHERE key = ?
        ''', (key,))

        result = cursor.fetchone()
        conn.close()

        if not result:
            raise HTTPException(status_code=404, detail=f"Cache entry not found: {key}")

        # Get freshness status
        freshness_info = freshness_tracker.get_freshness_status(key)

        # Create response
        entry = {
            "key": result[0],
            "status": result[1],
            "created_at": result[2],
            "updated_at": result[3],
            "expires_at": result[4],
            "access_count": result[5],
            "last_accessed_at": result[6],
            "size_bytes": result[7],
            "freshness_status": freshness_info["status"]
        }

        return entry
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting cache entry details: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting cache entry details: {e}")

@router.delete("/clear", response_model=Dict[str, Any])
async def clear_cache(
    cache_engine: CacheEngine = Depends(get_cache_engine),
    freshness_tracker: FreshnessTracker = Depends(get_freshness_tracker)
) -> Dict[str, Any]:
    """
    Clear all cache entries.

    Returns:
        Dictionary with operation result.
    """
    try:
        cache_success = cache_engine.clear()
        freshness_success = freshness_tracker.clear()

        return {
            "success": cache_success and freshness_success,
            "message": "Cache cleared successfully" if (cache_success and freshness_success) else "Error clearing cache"
        }
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail=f"Error clearing cache: {e}")

@router.delete("/entry", response_model=CacheKeyResponse)
async def delete_cache_entry(
    request: CacheKeyRequest,
    cache_engine: CacheEngine = Depends(get_cache_engine),
    freshness_tracker: FreshnessTracker = Depends(get_freshness_tracker)
) -> Dict[str, Any]:
    """
    Delete a specific cache entry.

    Args:
        request: Request with the cache key to delete.

    Returns:
        Dictionary with operation result.
    """
    try:
        key = request.key
        cache_success = cache_engine.delete(key)
        # Also delete from freshness tracker
        freshness_tracker.delete(key)

        if not cache_success:
            return {
                "key": key,
                "success": False,
                "message": f"Cache entry not found: {key}"
            }

        return {
            "key": key,
            "success": True,
            "message": "Cache entry deleted successfully"
        }
    except Exception as e:
        logger.error(f"Error deleting cache entry: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting cache entry: {e}")

@router.delete("/entry/{key}", response_model=CacheKeyResponse)
async def delete_cache_entry_by_key(
    key: str,
    cache_engine: CacheEngine = Depends(get_cache_engine),
    freshness_tracker: FreshnessTracker = Depends(get_freshness_tracker)
) -> Dict[str, Any]:
    """
    Delete a specific cache entry by key.

    Args:
        key: The cache key to delete.

    Returns:
        Dictionary with operation result.
    """
    try:
        cache_success = cache_engine.delete(key)
        # Also delete from freshness tracker
        freshness_tracker.delete(key)

        if not cache_success:
            return {
                "key": key,
                "success": False,
                "message": f"Cache entry not found: {key}"
            }

        return {
            "key": key,
            "success": True,
            "message": "Cache entry deleted successfully"
        }
    except Exception as e:
        logger.error(f"Error deleting cache entry: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting cache entry: {e}")

@router.post("/invalidate", response_model=CacheKeyResponse)
async def invalidate_cache_entry(
    request: CacheKeyRequest,
    cache_engine: CacheEngine = Depends(get_cache_engine),
    freshness_tracker: FreshnessTracker = Depends(get_freshness_tracker)
) -> Dict[str, Any]:
    """
    Invalidate a specific cache entry.

    Args:
        request: Request with the cache key to invalidate.

    Returns:
        Dictionary with operation result.
    """
    try:
        key = request.key
        cache_success = cache_engine.invalidate(key)
        # Also mark as expired in freshness tracker
        freshness_tracker.mark_expired(key)

        if not cache_success:
            return {
                "key": key,
                "success": False,
                "message": f"Cache entry not found: {key}"
            }

        return {
            "key": key,
            "success": True,
            "message": "Cache entry invalidated successfully"
        }
    except Exception as e:
        logger.error(f"Error invalidating cache entry: {e}")
        raise HTTPException(status_code=500, detail=f"Error invalidating cache entry: {e}")
