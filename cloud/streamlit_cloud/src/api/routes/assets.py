"""
Asset API routes
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from core.database import get_db
from core.models import Asset
from api.schemas import Asset as AssetSchema, AssetWithMetadata
from core.services.asset_info_service import AssetInfoService
from core.utils.logger import get_logger

# Setup logger
logger = get_logger(__name__)


# Create dependencies
def get_asset_info_service(db: Session = Depends(get_db)):
    """Get asset info service instance."""
    return AssetInfoService(db)


# Create router
router = APIRouter(
    tags=["assets"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=List[AssetSchema])
async def get_assets(
    skip: int = Query(0, ge=0, description="Number of assets to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of assets to return"),
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    name: Optional[str] = Query(None, description="Filter by name"),
    asset_type: Optional[str] = Query(None, description="Filter by asset type"),
    exchange: Optional[str] = Query(None, description="Filter by exchange"),
    db: Session = Depends(get_db),
):
    """
    Get a list of assets with optional filtering
    """
    try:
        query = db.query(Asset)

        # Apply filters if provided
        if symbol:
            query = query.filter(Asset.symbol.ilike(f"%{symbol}%"))
        if name:
            query = query.filter(Asset.name.ilike(f"%{name}%"))
        if asset_type:
            query = query.filter(Asset.asset_type == asset_type)
        if exchange:
            query = query.filter(Asset.exchange == exchange)

        # Apply pagination
        assets = query.offset(skip).limit(limit).all()

        return assets
    except SQLAlchemyError as e:
        logger.error(f"Database error when getting assets: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    except Exception as e:
        logger.error(f"Unexpected error when getting assets: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{asset_id}", response_model=AssetSchema)
async def get_asset(asset_id: int, db: Session = Depends(get_db)):
    """
    Get a specific asset by ID
    """
    try:
        asset = db.query(Asset).filter(Asset.asset_id == asset_id).first()
        if asset is None:
            raise HTTPException(status_code=404, detail="Asset not found")
        return asset
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error when getting asset {asset_id}: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    except Exception as e:
        logger.error(f"Unexpected error when getting asset {asset_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/symbol/{symbol}", response_model=AssetWithMetadata)
async def get_asset_by_symbol(
    symbol: str, asset_info_service: AssetInfoService = Depends(get_asset_info_service)
):
    """
    Get a specific asset by symbol with enhanced information and cache metadata
    """
    try:
        # Use asset info service to get or create asset with enhanced info
        asset, metadata = asset_info_service.get_or_create_asset(symbol)
        return AssetWithMetadata(asset=asset, metadata=metadata)
    except SQLAlchemyError as e:
        logger.error(f"Database error when getting asset with symbol {symbol}: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    except Exception as e:
        logger.error(f"Unexpected error when getting asset with symbol {symbol}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/symbol/{symbol}/refresh", response_model=AssetSchema)
async def refresh_asset_info(
    symbol: str, asset_info_service: AssetInfoService = Depends(get_asset_info_service)
):
    """
    Refresh asset information from AKShare
    """
    try:
        asset = asset_info_service.update_asset_info(symbol)
        if asset is None:
            raise HTTPException(status_code=404, detail="Asset not found")
        return asset
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error when refreshing asset {symbol}: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    except Exception as e:
        logger.error(f"Unexpected error when refreshing asset {symbol}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
