"""
Unified error handling module for QuantDB API.

This module defines custom exception classes and error handling utilities
to ensure consistent error responses across the API.
"""
from typing import Dict, Any, Optional, List, Type, Union
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
import traceback
import logging
from datetime import datetime

from src.logger import setup_logger

# Setup logger
logger = setup_logger(__name__)

# Error codes
class ErrorCode:
    """Error code constants for the API."""
    # General errors
    INTERNAL_ERROR = "INTERNAL_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    BAD_REQUEST = "BAD_REQUEST"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    
    # Data-specific errors
    DATA_NOT_FOUND = "DATA_NOT_FOUND"
    DATA_FETCH_ERROR = "DATA_FETCH_ERROR"
    DATA_PROCESSING_ERROR = "DATA_PROCESSING_ERROR"
    
    # External service errors
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"
    AKSHARE_ERROR = "AKSHARE_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    
    # Cache errors
    CACHE_ERROR = "CACHE_ERROR"
    CACHE_MISS = "CACHE_MISS"
    
    # MCP errors
    MCP_PROCESSING_ERROR = "MCP_PROCESSING_ERROR"
    MCP_INTENT_ERROR = "MCP_INTENT_ERROR"

# Base exception class
class QuantDBException(Exception):
    """Base exception class for QuantDB API."""
    def __init__(
        self, 
        message: str, 
        error_code: str = ErrorCode.INTERNAL_ERROR,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        self.timestamp = datetime.now().isoformat()
        super().__init__(self.message)

# Specific exception classes
class DataNotFoundException(QuantDBException):
    """Exception raised when requested data is not found."""
    def __init__(
        self, 
        message: str = "Requested data not found", 
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code=ErrorCode.DATA_NOT_FOUND,
            status_code=status.HTTP_404_NOT_FOUND,
            details=details
        )

class DataFetchException(QuantDBException):
    """Exception raised when there's an error fetching data from external sources."""
    def __init__(
        self, 
        message: str = "Error fetching data from external source", 
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code=ErrorCode.DATA_FETCH_ERROR,
            status_code=status.HTTP_502_BAD_GATEWAY,
            details=details
        )

class AKShareException(QuantDBException):
    """Exception raised when there's an error with AKShare."""
    def __init__(
        self, 
        message: str = "Error with AKShare service", 
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code=ErrorCode.AKSHARE_ERROR,
            status_code=status.HTTP_502_BAD_GATEWAY,
            details=details
        )

class DatabaseException(QuantDBException):
    """Exception raised when there's a database error."""
    def __init__(
        self, 
        message: str = "Database error", 
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code=ErrorCode.DATABASE_ERROR,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details
        )

class MCPProcessingException(QuantDBException):
    """Exception raised when there's an error processing an MCP request."""
    def __init__(
        self, 
        message: str = "Error processing MCP request", 
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code=ErrorCode.MCP_PROCESSING_ERROR,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details
        )

# Error response model
def create_error_response(
    error_code: str,
    message: str,
    status_code: int,
    details: Optional[Dict[str, Any]] = None,
    path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a standardized error response.
    
    Args:
        error_code: Error code
        message: Error message
        status_code: HTTP status code
        details: Additional error details
        path: Request path
        
    Returns:
        Standardized error response dictionary
    """
    return {
        "error": {
            "code": error_code,
            "message": message,
            "status_code": status_code,
            "details": details or {},
            "path": path,
            "timestamp": datetime.now().isoformat()
        }
    }

# Exception handlers
async def quantdb_exception_handler(request: Request, exc: QuantDBException) -> JSONResponse:
    """
    Handle QuantDBException instances.
    
    Args:
        request: FastAPI request
        exc: QuantDBException instance
        
    Returns:
        JSON response with error details
    """
    # Log the error
    logger.error(
        f"QuantDBException: {exc.error_code} - {exc.message} - "
        f"Status: {exc.status_code} - Details: {exc.details}"
    )
    
    # Create error response
    error_response = create_error_response(
        error_code=exc.error_code,
        message=exc.message,
        status_code=exc.status_code,
        details=exc.details,
        path=request.url.path
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response
    )

async def validation_exception_handler(request: Request, exc: Union[RequestValidationError, ValidationError]) -> JSONResponse:
    """
    Handle validation errors.
    
    Args:
        request: FastAPI request
        exc: Validation error
        
    Returns:
        JSON response with validation error details
    """
    # Extract error details
    error_details = []
    for error in exc.errors():
        error_details.append({
            "loc": error.get("loc", []),
            "msg": error.get("msg", ""),
            "type": error.get("type", "")
        })
    
    # Log the error
    logger.error(f"Validation error: {error_details}")
    
    # Create error response
    error_response = create_error_response(
        error_code=ErrorCode.VALIDATION_ERROR,
        message="Validation error",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        details={"errors": error_details},
        path=request.url.path
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response
    )

async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Handle HTTPException instances.
    
    Args:
        request: FastAPI request
        exc: HTTPException instance
        
    Returns:
        JSON response with error details
    """
    # Map status code to error code
    error_code = ErrorCode.INTERNAL_ERROR
    if exc.status_code == 404:
        error_code = ErrorCode.NOT_FOUND
    elif exc.status_code == 400:
        error_code = ErrorCode.BAD_REQUEST
    elif exc.status_code == 401:
        error_code = ErrorCode.UNAUTHORIZED
    elif exc.status_code == 403:
        error_code = ErrorCode.FORBIDDEN
    
    # Log the error
    logger.error(f"HTTPException: {error_code} - {exc.detail} - Status: {exc.status_code}")
    
    # Create error response
    error_response = create_error_response(
        error_code=error_code,
        message=str(exc.detail),
        status_code=exc.status_code,
        path=request.url.path
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response
    )

async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Global exception handler for unhandled exceptions.
    
    Args:
        request: FastAPI request
        exc: Exception instance
        
    Returns:
        JSON response with error details
    """
    # Get traceback
    tb = traceback.format_exc()
    
    # Log the error with traceback
    logger.error(f"Unhandled exception: {type(exc).__name__}: {str(exc)}\n{tb}")
    
    # Create error response
    error_response = create_error_response(
        error_code=ErrorCode.INTERNAL_ERROR,
        message="Internal server error",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        details={"error_type": type(exc).__name__, "error": str(exc)},
        path=request.url.path
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response
    )

# Register exception handlers with FastAPI app
def register_exception_handlers(app):
    """
    Register all exception handlers with the FastAPI app.
    
    Args:
        app: FastAPI application instance
    """
    app.add_exception_handler(QuantDBException, quantdb_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ValidationError, validation_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(Exception, global_exception_handler)
