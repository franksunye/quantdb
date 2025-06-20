"""
Core Configuration Module

This module contains configuration settings and environment variables
for the QuantDB core layer.
"""
import os
from pathlib import Path

# Base paths - compatible with cloud deployment
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATABASE_PATH = os.path.join(BASE_DIR, 'database/stock_data.db')

# Database configuration with fallback paths for cloud deployment
def get_database_url():
    """Get database URL with multiple fallback paths"""
    # Check environment variable first
    env_url = os.getenv('DATABASE_URL')
    if env_url:
        return env_url

    # Try multiple possible paths for different deployment scenarios
    possible_paths = [
        DATABASE_PATH,  # Standard path from BASE_DIR
        os.path.join(BASE_DIR, 'database', 'stock_data.db'),  # Alternative
        os.path.join(BASE_DIR, 'cloud', 'streamlit_cloud', 'database', 'stock_data.db'),  # Cloud deployment
        'database/stock_data.db',  # Relative path
        './database/stock_data.db',  # Current dir relative
        'cloud/streamlit_cloud/database/stock_data.db',  # Cloud relative path
    ]

    for path in possible_paths:
        if os.path.exists(path):
            return f'sqlite:///{path}'

    # Fallback to standard path even if file doesn't exist
    return f'sqlite:///{DATABASE_PATH}'

DATABASE_URL = get_database_url()
DB_TYPE = 'supabase' if DATABASE_URL.startswith('postgresql') else 'sqlite'

# API configuration
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))
API_PREFIX = os.getenv("API_PREFIX", "/api/v1")
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# Logging configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "logs/quantdb.log")

# Cache configuration
CACHE_TTL = int(os.getenv("CACHE_TTL", "3600"))  # 1 hour default
ENABLE_CACHE = os.getenv("ENABLE_CACHE", "true").lower() == "true"

# AKShare configuration
AKSHARE_TIMEOUT = int(os.getenv("AKSHARE_TIMEOUT", "30"))
AKSHARE_RETRY_COUNT = int(os.getenv("AKSHARE_RETRY_COUNT", "3"))

# Security configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

def get_log_level() -> str:
    """Get the logging level for the current environment."""
    return LOG_LEVEL

def is_development() -> bool:
    """Check if running in development mode."""
    return os.getenv("ENVIRONMENT", "development").lower() == "development"

def is_production() -> bool:
    """Check if running in production mode."""
    return os.getenv("ENVIRONMENT", "development").lower() == "production"
