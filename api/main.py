"""
QuantDB API Service Main Application

This is the main FastAPI application that provides REST API endpoints
for the QuantDB system using the core business layer.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import time

# Import core modules
from core.utils.config import API_HOST, API_PORT, is_development
from core.utils.logger import logger
from core.database.connection import engine, Base

# Import API routers
from .routers import stock_data, assets, monitoring, system

# Import middleware
from .middleware.monitoring import MonitoringMiddleware

# Create FastAPI application
app = FastAPI(
    title="QuantDB API",
    description="Financial data API service powered by QuantDB core",
    version="2.0.0-alpha",
    docs_url="/docs" if is_development() else None,
    redoc_url="/redoc" if is_development() else None,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if is_development() else ["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add monitoring middleware
app.add_middleware(MonitoringMiddleware)

# Include routers
app.include_router(stock_data.router, prefix="/api/v1", tags=["Stock Data"])
app.include_router(assets.router, prefix="/api/v1", tags=["Assets"])
app.include_router(monitoring.router, prefix="/api/v1", tags=["Monitoring"])
app.include_router(system.router, prefix="/api/v1", tags=["System"])

@app.on_event("startup")
async def startup_event():
    """Application startup event"""
    logger.info("Starting QuantDB API service...")
    
    # Create database tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created/verified")
    
    logger.info("QuantDB API service started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event"""
    logger.info("Shutting down QuantDB API service...")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "QuantDB API Service",
        "version": "2.0.0-alpha",
        "status": "running",
        "timestamp": time.time()
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "service": "quantdb-api"
    }

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc) if is_development() else "An error occurred",
            "timestamp": time.time()
        }
    )

def run_server():
    """Run the API server"""
    uvicorn.run(
        "api.main:app",
        host=API_HOST,
        port=API_PORT,
        reload=is_development(),
        log_level="info"
    )

if __name__ == "__main__":
    run_server()
