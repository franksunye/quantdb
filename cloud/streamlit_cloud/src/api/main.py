"""
QuantDB API main application
"""

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
import logging
from sqlalchemy.orm import Session
from datetime import datetime

from core.utils.config import API_PREFIX, DEBUG, ENVIRONMENT
from core.utils.logger import get_logger
from core.database import get_db

# MCP functionality archived
from api.openapi.openapi_utils import setup_openapi, setup_swagger_ui
from api.version import APIVersion, get_version_prefix, get_latest_version_info
from api.errors import (
    register_exception_handlers,
    QuantDBException,
    DataNotFoundException,
    DataFetchException,
)

# Setup enhanced logger
logger = get_logger(__name__)

# Import simplified components
from core.cache.akshare_adapter import AKShareAdapter
from core.services.stock_data_service import StockDataService
from core.services.database_cache import DatabaseCache

# Create simplified components
akshare_adapter = AKShareAdapter()

# Create MCP interpreter with simplified components
# mcp_interpreter = MCPInterpreter(  # MCP功能已归档
#     akshare_adapter=akshare_adapter
# )

# Lifespan context manager for startup and shutdown events
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    logger.info(f"Starting QuantDB API in {ENVIRONMENT} mode")
    yield
    # Shutdown logic
    logger.info("Shutting down QuantDB API")


# Get latest version info
latest_version_info = get_latest_version_info()

# Create FastAPI app
app = FastAPI(
    title="QuantDB API",
    description="Financial data API for QuantDB",
    version=latest_version_info.version,
    docs_url=f"{API_PREFIX}/docs",
    redoc_url=f"{API_PREFIX}/redoc",
    openapi_url=f"{API_PREFIX}/openapi.json",
    debug=DEBUG,
    lifespan=lifespan,
)

# Set up OpenAPI documentation
setup_openapi(app)
setup_swagger_ui(app)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint that redirects to API documentation"""
    return {
        "message": "Welcome to QuantDB API",
        "documentation": f"{API_PREFIX}/docs",
        "environment": ENVIRONMENT,
    }


# Health check endpoint
@app.get(f"{API_PREFIX}/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "version": latest_version_info.version,
        "api_version": latest_version_info.api_version,
        "timestamp": datetime.now().isoformat(),
    }


# Health check endpoint (v2)
@app.get(f"/api/v2/health")
async def health_check_v2():
    """Health check endpoint (v2)"""
    return {
        "status": "ok",
        "version": latest_version_info.version,
        "api_version": latest_version_info.api_version,
        "timestamp": datetime.now().isoformat(),
    }


# Import and include routers
from api.routes import assets, cache, historical_data, batch_assets
from api.routes.version import router as version_router
from api.cache_api import router as cache_api_router

# from api.endpoints.monitoring import router as monitoring_router  # 暂时注释
# MCP schemas archived

# Include routers with consistent prefixes
app.include_router(assets.router, prefix=f"{API_PREFIX}/assets", tags=["assets"])

app.include_router(cache.router, prefix=f"{API_PREFIX}/cache", tags=["cache"])

app.include_router(
    cache_api_router, prefix=f"{API_PREFIX}/cache-management", tags=["cache-management"]
)

app.include_router(historical_data.router, prefix=f"{API_PREFIX}/historical", tags=["historical"])

app.include_router(batch_assets.router, prefix=f"{API_PREFIX}", tags=["batch"])

# app.include_router(
#     monitoring_router,
#     prefix=f"{API_PREFIX}/monitoring",
#     tags=["monitoring"]
# )

# Include version router (available in both v1 and v2)
app.include_router(version_router, prefix=f"{API_PREFIX}/version", tags=["version"])

# Include version router for v2 as well
app.include_router(version_router, prefix=f"/api/v2/version", tags=["version-v2"])

# MCP endpoint - 已归档
# @app.post(f"{API_PREFIX}/mcp/query", response_model=MCPResponse, tags=["mcp"])
# async def mcp_query(request: MCPRequest, db: Session = Depends(get_db)):
#     """
#     Process a natural language query using the MCP protocol
#     """
#     # Set the database session for the interpreter
#     mcp_interpreter.set_db(db)
#
#     # Process the request
#     response = await mcp_interpreter.process_request(request)
#
#     return response

# Register exception handlers
register_exception_handlers(app)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.api.main:app", host="0.0.0.0", port=8000, reload=True)
