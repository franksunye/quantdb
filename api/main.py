"""
QuantDB API Service

FastAPI application using core business logic services.
"""

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from core.utils.config import API_PREFIX, DEBUG, ENVIRONMENT
from core.utils.logger import get_logger
from core.database import get_db
from api.error_handlers import register_exception_handlers
from fastapi.responses import HTMLResponse

# Setup logger
logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info(f"Starting QuantDB API in {ENVIRONMENT} mode")
    yield
    # Shutdown
    logger.info("Shutting down QuantDB API")

# Create FastAPI app
app = FastAPI(
    title="QuantDB API",
    description="Financial data API service using core business logic",
    version="2.1.0",
    lifespan=lifespan,
    debug=DEBUG
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register exception handlers
register_exception_handlers(app)

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Welcome to QuantDB API", "version": "2.1.0"}

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "quantdb-api", "version": "2.1.0"}

# V1 Health check endpoint
@app.get("/api/v1/health")
async def health_check_v1():
    """V1 Health check endpoint."""
    from datetime import datetime
    return {
        "status": "ok",
        "version": "2.1.0",
        "timestamp": datetime.now().isoformat()
    }

# V2 Health check endpoint
@app.get("/api/v2/health")
async def health_check_v2():
    """V2 Health check endpoint."""
    from datetime import datetime
    return {
        "status": "ok",
        "version": "2.1.0",
        "api_version": "v2",
        "timestamp": datetime.now().isoformat()
    }

# OpenAPI and Swagger UI endpoints for v2
@app.get("/api/v2/openapi.json")
async def get_openapi_v2():
    """Get OpenAPI JSON specification for v2."""
    return app.openapi()

@app.get("/api/v2/docs", response_class=HTMLResponse)
async def get_swagger_ui_v2():
    """Get Swagger UI for v2."""
    from fastapi.openapi.docs import get_swagger_ui_html
    return get_swagger_ui_html(
        openapi_url="/api/v2/openapi.json",
        title="QuantDB API v2 - Swagger UI"
    )

# Import and include routers
from api.routes import assets, stocks, cache, batch, version, asset_management

app.include_router(
    assets.router,
    prefix=f"{API_PREFIX}/assets",
    tags=["assets"]
)

app.include_router(
    stocks.router,
    prefix=f"{API_PREFIX}/stocks",
    tags=["stocks"]
)

# Add historical data route alias for backward compatibility
app.include_router(
    stocks.router,
    prefix=f"{API_PREFIX}/historical",
    tags=["historical"]
)

app.include_router(
    cache.router,
    prefix=f"{API_PREFIX}/cache",
    tags=["cache"]
)

app.include_router(
    batch.router,
    prefix=f"{API_PREFIX}/batch",
    tags=["batch"]
)

app.include_router(
    version.router,
    prefix=f"{API_PREFIX}/version",
    tags=["version"]
)

# Add v2 version router
app.include_router(
    version.router,
    prefix="/api/v2/version",
    tags=["version-v2"]
)

# Add asset management router
app.include_router(
    asset_management.router,
    prefix=f"{API_PREFIX}/management",
    tags=["asset-management"]
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
