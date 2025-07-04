"""
API Routers

This module contains all API route handlers for the QuantDB API service.
"""

# Import all routers for easy access
from . import stock_data
from . import assets
from . import monitoring
from . import system

__all__ = [
    "stock_data",
    "assets", 
    "monitoring",
    "system"
]
