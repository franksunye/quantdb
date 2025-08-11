"""
API Error Classes and Handlers

This module exports error classes and handlers from the middleware module
for backward compatibility and easier imports.
"""

from api.error_handlers import (
    AKShareException,
    DatabaseException,
    DataFetchException,
    DataNotFoundException,
    ErrorCode,
    MCPProcessingException,
    QuantDBException,
    create_error_response,
    global_exception_handler,
    http_exception_handler,
    quantdb_exception_handler,
    register_exception_handlers,
    validation_exception_handler,
)

__all__ = [
    "ErrorCode",
    "QuantDBException",
    "DataNotFoundException",
    "DataFetchException",
    "AKShareException",
    "DatabaseException",
    "MCPProcessingException",
    "create_error_response",
    "quantdb_exception_handler",
    "validation_exception_handler",
    "http_exception_handler",
    "global_exception_handler",
    "register_exception_handlers",
]
