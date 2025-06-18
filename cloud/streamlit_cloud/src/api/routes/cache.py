"""
Cache API routes for monitoring and managing the simplified cache system.
In the simplified architecture, we use SQLite database as the primary cache.
"""
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from src.api.database import get_db
from src.logger_unified import get_logger

# Setup logger
logger = get_logger(__name__)

# Create router
router = APIRouter(
    tags=["cache"],
    responses={404: {"description": "Not found"}},
)

@router.get("/status")
async def get_cache_status(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Get cache status and statistics from SQLite database
    """
    try:
        # Get database statistics
        assets_count = db.execute(text("SELECT COUNT(*) FROM assets")).scalar()
        daily_data_count = db.execute(text("SELECT COUNT(*) FROM daily_stock_data")).scalar()

        # Get latest data timestamp (using trade_date since daily_stock_data doesn't have updated_at)
        latest_data = db.execute(text(
            "SELECT MAX(trade_date) FROM daily_stock_data"
        )).scalar()

        # Get database size (SQLite specific)
        db_size = db.execute(text(
            "SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()"
        )).scalar()

        stats = {
            "database": {
                "assets_count": assets_count or 0,
                "daily_data_count": daily_data_count or 0,
                "latest_data_date": str(latest_data) if latest_data else None,
                "database_size_bytes": db_size or 0
            },
            "cache_type": "SQLite Database",
            "status": "active"
        }

        return stats
    except Exception as e:
        logger.error(f"Error getting cache status: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting cache status: {str(e)}")

@router.delete("/clear")
async def clear_cache(
    table: str = Query(None, description="Specific table to clear: 'prices' or 'assets'. If not provided, clears all data."),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Clear cached data from SQLite database
    """
    try:
        if table:
            if table == "prices":
                db.execute(text("DELETE FROM prices"))
                db.commit()
                logger.info("Cleared prices table")
                return {"status": "success", "message": f"Table '{table}' cleared successfully"}
            elif table == "assets":
                # Clear assets and related prices (cascade)
                db.execute(text("DELETE FROM prices"))
                db.execute(text("DELETE FROM assets"))
                db.commit()
                logger.info("Cleared assets and prices tables")
                return {"status": "success", "message": f"Table '{table}' and related data cleared successfully"}
            else:
                raise HTTPException(status_code=400, detail="Invalid table name. Use 'prices' or 'assets'.")
        else:
            # Clear all cached data
            db.execute(text("DELETE FROM prices"))
            db.execute(text("DELETE FROM assets"))
            db.commit()
            logger.info("Cleared all cached data")
            return {"status": "success", "message": "All cached data cleared successfully"}
    except Exception as e:
        db.rollback()
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail=f"Error clearing cache: {str(e)}")

# Note: In the simplified architecture, we only provide basic cache management
# through database operations. Complex cache key management is not needed
# since we use SQLite database as the primary cache storage.
