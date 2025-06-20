"""
Core Database Layer

This module contains database connection management, schema definitions,
and migration utilities.
"""

from .connection import Base, engine, SessionLocal, get_db, get_db_adapter

__all__ = [
    "Base",
    "engine",
    "SessionLocal",
    "get_db",
    "get_db_adapter"
]
