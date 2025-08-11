"""
QuantDB Core Business Logic Layer

This module contains the core business logic that can be shared across
different deployment modes (API, Admin, WebApp, Cloud).

Architecture:
- models/: Data models and database schemas
- services/: Business service layer
- database/: Database connection and management
- cache/: Caching layer and adapters
- utils/: Shared utilities and helpers
"""

__version__ = "2.2.8"
__author__ = "QuantDB Team"

# Core module imports for easy access
from . import models
from . import services
from . import database
from . import cache
from . import utils

__all__ = ["models", "services", "database", "cache", "utils"]
