"""
QuantDB API main application
"""
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from sqlalchemy.orm import Session

from src.config import API_PREFIX, DEBUG, ENVIRONMENT
from src.logger import setup_logger
from src.api.database import get_db
from src.mcp.interpreter import MCPInterpreter

# Setup logger
logger = setup_logger(__name__)

# Import cache components
from src.cache.cache_engine import CacheEngine
from src.cache.freshness_tracker import FreshnessTracker
from src.cache.akshare_adapter import AKShareAdapter

# Create cache components
cache_engine = CacheEngine()
freshness_tracker = FreshnessTracker()
akshare_adapter = AKShareAdapter(
    cache_engine=cache_engine,
    freshness_tracker=freshness_tracker
)

# Create MCP interpreter with cache components
mcp_interpreter = MCPInterpreter(
    cache_engine=cache_engine,
    freshness_tracker=freshness_tracker,
    akshare_adapter=akshare_adapter
)

# Create FastAPI app
app = FastAPI(
    title="QuantDB API",
    description="Financial data API for QuantDB",
    version="0.1.0",
    docs_url=f"{API_PREFIX}/docs",
    redoc_url=f"{API_PREFIX}/redoc",
    openapi_url=f"{API_PREFIX}/openapi.json",
    debug=DEBUG
)

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
        "environment": ENVIRONMENT
    }

# Health check endpoint
@app.get(f"{API_PREFIX}/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

# Import and include routers
from src.api.routes import assets, prices, data_import, cache, historical_data
from src.api.cache_api import router as cache_api_router
from src.mcp.schemas import MCPRequest, MCPResponse

# Include routers
app.include_router(
    assets.router,
    prefix=API_PREFIX,
    tags=["assets"]
)

app.include_router(
    prices.router,
    prefix=API_PREFIX,
    tags=["prices"]
)

app.include_router(
    data_import.router,
    prefix=API_PREFIX,
    tags=["import"]
)

app.include_router(
    cache.router,
    prefix=API_PREFIX,
    tags=["cache"]
)

app.include_router(
    cache_api_router,
    tags=["cache-management"]
)

app.include_router(
    historical_data.router,
    prefix=API_PREFIX,
    tags=["historical"]
)

# MCP endpoint
@app.post(f"{API_PREFIX}/mcp/query", response_model=MCPResponse, tags=["mcp"])
async def mcp_query(request: MCPRequest, db: Session = Depends(get_db)):
    """
    Process a natural language query using the MCP protocol
    """
    # Set the database session for the interpreter
    mcp_interpreter.set_db(db)

    # Process the request
    response = await mcp_interpreter.process_request(request)

    return response

# Exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for the API"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "message": str(exc)}
    )

# Startup event
@app.on_event("startup")
async def startup_event():
    """Runs when the API starts"""
    logger.info(f"Starting QuantDB API in {ENVIRONMENT} mode")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Runs when the API shuts down"""
    logger.info("Shutting down QuantDB API")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=8000, reload=True)
