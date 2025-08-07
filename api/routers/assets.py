"""
Assets API routes for QuantDB API service.

This module provides API endpoints for asset information management.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

# Import core modules
from core.database.connection import get_db
from core.services.asset_info_service import AssetInfoService
from core.services.query_service import QueryService
from core.utils.logger import logger

# Import API schemas
from ..schemas import AssetInfo, AssetResponse

# Create dependencies
def get_asset_info_service(db: Session = Depends(get_db)):
    """Get asset info service instance."""
    return AssetInfoService(db)

def get_query_service(db: Session = Depends(get_db)):
    """Get query service instance."""
    return QueryService(db)

# Create router
router = APIRouter(
    prefix="/assets",
    tags=["Assets"],
    responses={404: {"description": "Not found"}},
)

@router.get("/{symbol}", response_model=AssetResponse)
async def get_asset_info(
    symbol: str,
    db: Session = Depends(get_db),
    asset_info_service: AssetInfoService = Depends(get_asset_info_service)
):
    """
    Get asset information for a specific symbol

    - **symbol**: Stock symbol (6-digit for A-shares, 5-digit for Hong Kong stocks)
    """
    try:
        # Validate symbol format
        if not symbol.isdigit() or (len(symbol) != 6 and len(symbol) != 5):
            raise HTTPException(status_code=400, detail="Symbol must be 6 digits for A-shares or 5 digits for Hong Kong stocks")

        # Get or create asset with enhanced information
        asset, metadata = asset_info_service.get_or_create_asset(symbol)

        if not asset:
            raise HTTPException(status_code=404, detail=f"Asset {symbol} not found")

        # Convert to response format
        asset_info = AssetInfo.from_orm(asset)

        return AssetResponse(
            asset=asset_info,
            metadata=metadata
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting asset info for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting asset info: {str(e)}")

@router.get("/", response_model=List[AssetInfo])
async def list_assets(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    name: Optional[str] = Query(None, description="Filter by name (partial match)"),
    exchange: Optional[str] = Query(None, description="Filter by exchange"),
    industry: Optional[str] = Query(None, description="Filter by industry"),
    sort_by: Optional[str] = Query("symbol", description="Field to sort by"),
    sort_order: str = Query("asc", pattern="^(asc|desc)$", description="Sort order"),
    db: Session = Depends(get_db),
    query_service: QueryService = Depends(get_query_service)
):
    """
    List assets with filtering and pagination

    - **skip**: Number of records to skip (for pagination)
    - **limit**: Maximum number of records to return
    - **symbol**: Filter by symbol (exact match)
    - **name**: Filter by name (partial match)
    - **exchange**: Filter by exchange
    - **industry**: Filter by industry
    - **sort_by**: Field to sort by
    - **sort_order**: Sort order (asc or desc)
    """
    try:
        # Build filters
        filters = {}
        if symbol:
            filters["symbol"] = symbol
        if name:
            filters["name"] = {"like": name}
        if exchange:
            filters["exchange"] = exchange
        if industry:
            filters["industry"] = industry

        # Query assets
        assets, total_count = query_service.query_assets(
            filters=filters,
            sort_by=sort_by,
            sort_order=sort_order,
            skip=skip,
            limit=limit
        )

        # Convert to response format
        asset_list = [AssetInfo.from_orm(asset) for asset in assets]

        return asset_list

    except Exception as e:
        logger.error(f"Error listing assets: {e}")
        raise HTTPException(status_code=500, detail=f"Error listing assets: {str(e)}")

@router.put("/{symbol}", response_model=AssetResponse)
async def update_asset_info(
    symbol: str,
    db: Session = Depends(get_db),
    asset_info_service: AssetInfoService = Depends(get_asset_info_service)
):
    """
    Update asset information from external sources

    - **symbol**: Stock symbol to update
    """
    try:
        # Validate symbol format
        if not symbol.isdigit() or (len(symbol) != 6 and len(symbol) != 5):
            raise HTTPException(status_code=400, detail="Symbol must be 6 digits for A-shares or 5 digits for Hong Kong stocks")

        # Update asset info
        asset = asset_info_service.update_asset_info(symbol)

        if not asset:
            raise HTTPException(status_code=404, detail=f"Asset {symbol} not found")

        # Convert to response format
        asset_info = AssetInfo.from_orm(asset)

        metadata = {
            "symbol": symbol,
            "action": "updated",
            "timestamp": asset.last_updated.isoformat() if asset.last_updated else None
        }

        return AssetResponse(
            asset=asset_info,
            metadata=metadata
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating asset info for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating asset info: {str(e)}")
