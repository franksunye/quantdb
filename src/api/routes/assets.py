"""
Asset API routes
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from src.api.database import get_db
from src.api.models import Asset
from src.api.schemas import Asset as AssetSchema
from src.logger_unified import get_logger

# Setup logger
logger = get_logger(__name__)

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
    db: Session = Depends(get_db)
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

@router.get("/symbol/{symbol}", response_model=AssetSchema)
async def get_asset_by_symbol(symbol: str, db: Session = Depends(get_db)):
    """
    Get a specific asset by symbol
    """
    try:
        asset = db.query(Asset).filter(Asset.symbol == symbol).first()
        if asset is None:
            raise HTTPException(status_code=404, detail="Asset not found")
        return asset
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error when getting asset with symbol {symbol}: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    except Exception as e:
        logger.error(f"Unexpected error when getting asset with symbol {symbol}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
