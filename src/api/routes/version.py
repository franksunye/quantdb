# src/api/routes/version.py
"""
API version routes.

This module provides routes for retrieving API version information.
"""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Path, Query
from pydantic import BaseModel

from src.api.version import (
    APIVersion,
    get_version_info,
    get_all_versions,
    get_latest_version_info,
    is_version_deprecated
)
from src.logger import setup_logger

# Setup logger
logger = setup_logger(__name__)

# Create router
router = APIRouter(
    tags=["version"],
    responses={404: {"description": "Not found"}},
)

class VersionResponse(BaseModel):
    """API version response model."""
    version: str
    api_version: str
    release_date: str
    deprecated: bool
    sunset_date: str = ""
    description: str

class VersionsResponse(BaseModel):
    """API versions response model."""
    versions: Dict[str, VersionResponse]
    latest: str
    current: str

@router.get("/", response_model=VersionsResponse)
async def get_versions():
    """
    Get information about all API versions.

    Returns:
        Dictionary with version information for all API versions.
    """
    logger.info("Getting information about all API versions")

    versions = get_all_versions()
    latest = APIVersion.get_latest().value

    return {
        "versions": versions,
        "latest": latest,
        "current": latest
    }

@router.get("/latest", response_model=VersionResponse)
async def get_latest_version():
    """
    Get information about the latest API version.

    Returns:
        Version information for the latest API version.
    """
    logger.info("Getting information about the latest API version")

    return get_latest_version_info()

@router.get("/{version}", response_model=VersionResponse)
async def get_version(
    version: str = Path(..., description="API version to get information for")
):
    """
    Get information about a specific API version.

    Args:
        version: API version to get information for.

    Returns:
        Version information for the specified version.
    """
    logger.info(f"Getting information about API version: {version}")

    if not APIVersion.is_valid(version):
        logger.warning(f"Invalid API version: {version}")
        raise HTTPException(status_code=404, detail=f"API version '{version}' not found")

    info = get_version_info(version)
    if not info:
        logger.warning(f"API version not found: {version}")
        raise HTTPException(status_code=404, detail=f"API version '{version}' not found")

    if is_version_deprecated(version):
        logger.warning(f"Deprecated API version: {version}")

    return info
