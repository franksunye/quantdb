"""
API version routes.

This module provides routes for retrieving API version information.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Path
from pydantic import BaseModel

from core.utils.logger import get_logger

# Setup logger
logger = get_logger(__name__)

# Create router
router = APIRouter(
    tags=["version"],
    responses={404: {"description": "Not found"}},
)


class APIVersion(str, Enum):
    """API version enum."""

    V1 = "v1"
    V2 = "v2"

    @classmethod
    def get_latest(cls) -> "APIVersion":
        """Get the latest API version."""
        return APIVersion.V2  # Latest version

    @classmethod
    def get_all(cls) -> list["APIVersion"]:
        """Get all API versions."""
        return [v for v in APIVersion]

    @classmethod
    def is_valid(cls, version: str) -> bool:
        """Check if a version string is valid."""
        try:
            APIVersion(version.lower())
            return True
        except ValueError:
            return False


class VersionInfo(BaseModel):
    """API version information model."""

    version: str
    api_version: str
    release_date: str
    deprecated: bool = False
    description: str


class VersionResponse(BaseModel):
    """API version response model."""

    version: str
    api_version: str
    release_date: str
    deprecated: bool
    description: str


class VersionsResponse(BaseModel):
    """API versions response model."""

    versions: Dict[str, VersionResponse]
    latest: str
    current: str


# Version information
VERSION_INFO = {
    "v1": VersionInfo(
        version="2.2.8",
        api_version="v1",
        release_date="2025-08-04",
        deprecated=False,
        description="Production-ready version with Streamlit Cloud deployment and Core/API architecture",
    ),
    "v2": VersionInfo(
        version="2.2.8",
        api_version="v2",
        release_date="2025-08-04",
        deprecated=False,
        description="Enhanced API version with improved features and performance optimizations",
    ),
}


def get_all_versions() -> Dict[str, VersionInfo]:
    """
    Get information about all API versions.

    Returns:
        Dictionary with version information for all API versions.
    """
    return VERSION_INFO


def get_latest_version_info() -> VersionInfo:
    """
    Get information about the latest API version.

    Returns:
        Version information for the latest API version.
    """
    latest = APIVersion.get_latest()
    return VERSION_INFO[latest.value]


@router.get("/", response_model=VersionsResponse)
async def get_versions():
    """
    Get information about all API versions.

    Returns:
        Dictionary with version information for all API versions.
    """
    logger.info("Getting information about all API versions")

    versions = {k: VersionResponse(**v.model_dump()) for k, v in VERSION_INFO.items()}

    return VersionsResponse(
        versions=versions,
        latest="v2",  # Latest version is v2
        current="v1",  # Current production version is v1
    )


@router.get("/latest", response_model=VersionResponse)
async def get_latest_version():
    """
    Get information about the latest API version.

    Returns:
        Version information for the latest API version.
    """
    logger.info("Getting information about the latest API version")

    return VersionResponse(**VERSION_INFO["v2"].model_dump())  # Return latest version (v2)


@router.get("/{version}", response_model=VersionResponse)
async def get_version(version: str = Path(..., description="API version to get information for")):
    """
    Get information about a specific API version.

    Args:
        version: API version to get information for.

    Returns:
        Version information for the specified version.
    """
    logger.info(f"Getting information about API version: {version}")

    if version not in VERSION_INFO:
        logger.warning(f"Invalid API version: {version}")
        raise HTTPException(status_code=404, detail=f"API version '{version}' not found")

    return VersionResponse(**VERSION_INFO[version].model_dump())
