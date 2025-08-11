"""
API Routers

This module contains all API route handlers for the QuantDB API service.
"""

# Import all routers for easy access
from . import assets, index_data, monitoring, stock_data, system

__all__ = ["stock_data", "assets", "monitoring", "system", "index_data"]
