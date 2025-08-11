# src/api/routes/batch_assets.py
"""
Batch asset information API endpoints for performance optimization.

This module provides batch processing capabilities for asset information
to improve performance when dealing with multiple stocks.
"""

from typing import Any, Dict, List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_db
from core.services.asset_info_service import AssetInfoService
from core.utils.logger import logger

router = APIRouter(prefix="/batch", tags=["batch"])


class BatchAssetRequest(BaseModel):
    """Request model for batch asset information."""

    symbols: List[str]
    include_financial_data: bool = True
    use_cache: bool = True


class BatchAssetResponse(BaseModel):
    """Response model for batch asset information."""

    success_count: int
    error_count: int
    assets: Dict[str, Dict[str, Any]]
    errors: Dict[str, str]
    metadata: Dict[str, Any]


@router.post("/assets", response_model=BatchAssetResponse)
async def get_batch_assets(
    request: BatchAssetRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)
):
    """
    Get asset information for multiple stocks in batch.

    This endpoint is optimized for performance:
    - Uses cached data when available
    - Processes known stocks with default values
    - Minimizes external API calls

    Args:
        request: Batch request with list of symbols
        background_tasks: Background tasks for async processing
        db: Database session

    Returns:
        Batch response with asset information
    """
    logger.info(f"Processing batch asset request for {len(request.symbols)} symbols")

    try:
        asset_service = AssetInfoService(db)

        assets = {}
        errors = {}
        success_count = 0
        error_count = 0

        # Process each symbol
        for symbol in request.symbols:
            try:
                # Standardize symbol
                symbol = symbol.strip().upper()
                if len(symbol) != 6 or not symbol.isdigit():
                    errors[symbol] = "Invalid symbol format"
                    error_count += 1
                    continue

                # Get asset information
                asset, metadata = asset_service.get_or_create_asset(symbol)

                if asset:
                    # Convert asset to dictionary
                    asset_dict = {
                        "symbol": asset.symbol,
                        "name": asset.name,
                        "isin": asset.isin,
                        "asset_type": asset.asset_type,
                        "exchange": asset.exchange,
                        "currency": asset.currency,
                        "industry": asset.industry,
                        "concept": asset.concept,
                        "listing_date": (
                            asset.listing_date.isoformat() if asset.listing_date else None
                        ),
                        "total_shares": asset.total_shares,
                        "circulating_shares": asset.circulating_shares,
                        "market_cap": asset.market_cap,
                        "pe_ratio": asset.pe_ratio,
                        "pb_ratio": asset.pb_ratio,
                        "roe": asset.roe,
                        "last_updated": (
                            asset.last_updated.isoformat() if asset.last_updated else None
                        ),
                        "data_source": asset.data_source,
                        "cache_info": metadata.get("cache_info", {}),
                    }

                    assets[symbol] = asset_dict
                    success_count += 1

                else:
                    errors[symbol] = "Failed to get asset information"
                    error_count += 1

            except Exception as e:
                logger.error(f"Error processing symbol {symbol}: {e}")
                errors[symbol] = str(e)
                error_count += 1

        # Create response metadata
        response_metadata = {
            "total_requested": len(request.symbols),
            "success_count": success_count,
            "error_count": error_count,
            "cache_enabled": request.use_cache,
            "include_financial_data": request.include_financial_data,
        }

        logger.info(f"Batch asset request completed: {success_count} success, {error_count} errors")

        return BatchAssetResponse(
            success_count=success_count,
            error_count=error_count,
            assets=assets,
            errors=errors,
            metadata=response_metadata,
        )

    except Exception as e:
        logger.error(f"Error in batch asset processing: {e}")
        raise HTTPException(status_code=500, detail=f"Batch processing failed: {str(e)}")


@router.post("/assets/minimal", response_model=Dict[str, Dict[str, Any]])
async def get_batch_assets_minimal(symbols: List[str], db: Session = Depends(get_db)):
    """
    Get minimal asset information for multiple stocks (name and basic info only).

    This is the fastest endpoint for getting basic stock information.
    Uses only cached data and defaults, no external API calls.

    Args:
        symbols: List of stock symbols
        db: Database session

    Returns:
        Dictionary with symbol as key and minimal asset info as value
    """
    logger.info(f"Processing minimal batch asset request for {len(symbols)} symbols")

    try:
        asset_service = AssetInfoService(db)
        known_defaults = asset_service._get_known_stock_defaults()

        result = {}

        for symbol in symbols:
            symbol = symbol.strip().upper()

            # First check if we have defaults
            if symbol in known_defaults:
                defaults = known_defaults[symbol]
                result[symbol] = {
                    "name": defaults["name"],
                    "industry": defaults["industry"],
                    "concept": defaults["concept"],
                    "data_source": "defaults",
                }
            else:
                # Check database for existing asset
                from core.models import Asset

                asset = db.query(Asset).filter(Asset.symbol == symbol).first()

                if asset:
                    result[symbol] = {
                        "name": asset.name,
                        "industry": asset.industry or "其他",
                        "concept": asset.concept or "其他概念",
                        "data_source": "database",
                    }
                else:
                    # Use fallback
                    result[symbol] = {
                        "name": f"Stock {symbol}",
                        "industry": "其他",
                        "concept": "其他概念",
                        "data_source": "fallback",
                    }

        logger.info(f"Minimal batch asset request completed for {len(result)} symbols")
        return result

    except Exception as e:
        logger.error(f"Error in minimal batch asset processing: {e}")
        raise HTTPException(status_code=500, detail=f"Minimal batch processing failed: {str(e)}")
