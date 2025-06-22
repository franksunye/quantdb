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
    version="2.0.0",
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

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "quantdb-api", "version": "2.0.0"}

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

# Import and include routers
from api.routes import assets, stocks, cache, batch, version

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
