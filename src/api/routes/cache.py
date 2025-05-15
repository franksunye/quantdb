"""
Cache API routes for monitoring and managing the cache system.
"""
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query
from src.logger import setup_logger
from src.cache.cache_engine import CacheEngine
from src.cache.freshness_tracker import FreshnessTracker

# Setup logger
logger = setup_logger(__name__)

# Create cache components
cache_engine = CacheEngine()
freshness_tracker = FreshnessTracker()

# Create router
router = APIRouter(
    prefix="/cache",
    tags=["cache"],
    responses={404: {"description": "Not found"}},
)

@router.get("/status")
async def get_cache_status() -> Dict[str, Any]:
    """
    Get cache status and statistics
    """
    try:
        # Get cache statistics
        cache_stats = cache_engine.get_stats()

        # Get freshness statistics
        freshness_stats = freshness_tracker.get_stats()

        # Combine statistics
        stats = {
            "cache": cache_stats,
            "freshness": freshness_stats
        }

        return stats
    except Exception as e:
        logger.error(f"Error getting cache status: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting cache status: {str(e)}")

@router.delete("/clear")
async def clear_cache(
    key: str = Query(None, description="Specific cache key to clear. If not provided, clears all cache.")
) -> Dict[str, Any]:
    """
    Clear cache entries
    """
    try:
        if key:
            # Clear specific key
            success = cache_engine.delete(key)
            if success:
                freshness_tracker.delete(key)
                return {"status": "success", "message": f"Cache key {key} cleared"}
            else:
                return {"status": "warning", "message": f"Cache key {key} not found"}
        else:
            # Clear all cache
            cache_engine.clear()
            freshness_tracker.clear()
            return {"status": "success", "message": "All cache entries cleared"}
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail=f"Error clearing cache: {str(e)}")

@router.get("/keys")
async def get_cache_keys(
    prefix: Optional[str] = Query(None, description="Filter keys by prefix")
) -> Dict[str, Any]:
    """
    Get all cache keys

    Args:
        prefix: Optional prefix to filter keys
    """
    try:
        keys = cache_engine.get_keys()

        # Filter by prefix if provided
        if prefix:
            keys = [key for key in keys if key.startswith(prefix)]

        return {
            "keys": keys,
            "count": len(keys)
        }
    except Exception as e:
        logger.error(f"Error getting cache keys: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting cache keys: {str(e)}")

@router.get("/key/{key}")
async def get_cache_entry(key: str) -> Dict[str, Any]:
    """
    Get details about a specific cache entry

    Args:
        key: Cache key to retrieve
    """
    try:
        # Get cache entry
        value = cache_engine.get(key)

        if value is None:
            raise HTTPException(status_code=404, detail=f"Cache key '{key}' not found")

        # Get freshness info
        freshness = freshness_tracker.get_freshness_status(key)

        return {
            "key": key,
            "value_type": type(value).__name__,
            "freshness": freshness,
            "has_value": value is not None
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting cache entry: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting cache entry: {str(e)}")

@router.post("/refresh")
async def refresh_cache(
    key: str = Query(..., description="Cache key to refresh")
) -> Dict[str, Any]:
    """
    Force refresh a cache entry

    Args:
        key: Cache key to refresh
    """
    try:
        # Check if key exists
        if cache_engine.get(key) is None:
            raise HTTPException(status_code=404, detail=f"Cache key '{key}' not found")

        # Mark as expired in freshness tracker
        success = freshness_tracker.mark_expired(key)

        if success:
            return {
                "status": "success",
                "message": f"Cache key '{key}' marked for refresh"
            }
        else:
            return {
                "status": "warning",
                "message": f"Failed to mark cache key '{key}' for refresh"
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error refreshing cache: {e}")
        raise HTTPException(status_code=500, detail=f"Error refreshing cache: {str(e)}")
