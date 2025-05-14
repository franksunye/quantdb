"""
QuantDB API main application
"""
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging

from src.config import API_PREFIX, DEBUG, ENVIRONMENT
from src.logger import setup_logger

# Setup logger
logger = setup_logger(__name__)

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
# This will be implemented in Sprint 2

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
