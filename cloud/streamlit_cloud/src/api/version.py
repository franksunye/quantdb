# src/api/version.py
"""
API version management utilities.

This module provides utilities for managing API versions and ensuring backward compatibility.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Union

from pydantic import BaseModel

from core.utils.logger import get_logger

# Setup logger
logger = get_logger(__name__)


class APIVersion(str, Enum):
    """API version enum."""

    V1 = "v1"
    V2 = "v2"

    @classmethod
    def get_latest(cls) -> "APIVersion":
        """Get the latest API version."""
        return APIVersion.V1  # Current production version

    @classmethod
    def get_all(cls) -> List["APIVersion"]:
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
    sunset_date: Optional[str] = ""
    description: str


# Version information for each API version
VERSION_INFO: Dict[APIVersion, VersionInfo] = {
    APIVersion.V1: VersionInfo(
        version="2.2.8",
        api_version="v1",
        release_date="2025-08-04",
        deprecated=False,
        sunset_date="",
        description="Production-ready version with Streamlit Cloud deployment, Core/API architecture, and comprehensive testing.",
    ),
    APIVersion.V2: VersionInfo(
        version="2.2.8",
        api_version="v2",
        release_date="2025-08-04",
        deprecated=False,
        sunset_date="",
        description="Enhanced API version with improved features and performance optimizations.",
    ),
}


def get_version_info(version: Union[APIVersion, str]) -> Optional[VersionInfo]:
    """
    Get information about a specific API version.

    Args:
        version: API version to get information for.

    Returns:
        Version information or None if version is not found.
    """
    if isinstance(version, str):
        try:
            version = APIVersion(version.lower())
        except ValueError:
            logger.warning(f"Invalid API version: {version}")
            return None

    return VERSION_INFO.get(version)


def get_all_versions() -> Dict[str, VersionInfo]:
    """
    Get information about all API versions.

    Returns:
        Dictionary with version information for all API versions.
    """
    return {v.value: info for v, info in VERSION_INFO.items()}


def get_version_prefix(version: Union[APIVersion, str]) -> str:
    """
    Get the URL prefix for a specific API version.

    Args:
        version: API version to get prefix for.

    Returns:
        URL prefix for the specified version.
    """
    if isinstance(version, str):
        try:
            version = APIVersion(version.lower())
        except ValueError:
            logger.warning(f"Invalid API version: {version}")
            return "/api/v1"  # Default to v1 for invalid versions

    return f"/api/{version.value}"


def is_version_deprecated(version: Union[APIVersion, str]) -> bool:
    """
    Check if an API version is deprecated.

    Args:
        version: API version to check.

    Returns:
        True if the version is deprecated, False otherwise.
    """
    info = get_version_info(version)
    if not info:
        return False

    return info.deprecated


def get_latest_version_info() -> VersionInfo:
    """
    Get information about the latest API version.

    Returns:
        Version information for the latest API version.
    """
    latest = APIVersion.get_latest()
    return VERSION_INFO[latest]
