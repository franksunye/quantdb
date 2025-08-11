# src/config.py

import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Base paths - unified to project root
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent  # Go to project root
DATABASE_PATH = os.path.join(BASE_DIR, "database/stock_data.db")  # Use unified database
RAW_DATA_DIR = os.path.join(BASE_DIR, "data/raw/")
PROCESSED_DATA_DIR = os.path.join(BASE_DIR, "data/processed/")


# Database configuration with fallback paths for cloud deployment
def get_database_url():
    """Get database URL with multiple fallback paths"""
    # Check environment variable first
    env_url = os.getenv("DATABASE_URL")
    if env_url:
        return env_url

    # Try multiple possible paths - prioritize unified database
    possible_paths = [
        DATABASE_PATH,  # Unified project root database
        os.path.join(BASE_DIR, "database", "stock_data.db"),  # Alternative
        "../../database/stock_data.db",  # Relative to cloud directory
        "../../../database/stock_data.db",  # Alternative relative path
        "database/stock_data.db",  # Fallback relative path
        "./database/stock_data.db",  # Current dir relative
    ]

    for path in possible_paths:
        if os.path.exists(path):
            return f"sqlite:///{path}"

    # Fallback to standard path even if file doesn't exist
    return f"sqlite:///{DATABASE_PATH}"


DATABASE_URL = get_database_url()

# Determine database type
DB_TYPE = "supabase" if DATABASE_URL.startswith("postgresql") else "sqlite"

# Supabase configuration
SUPABASE_DB_HOST = os.getenv("SUPABASE_DB_HOST", "aws-0-us-west-1.pooler.supabase.com")
SUPABASE_DB_PORT = os.getenv("SUPABASE_DB_PORT", "6543")
SUPABASE_DB_NAME = os.getenv("SUPABASE_DB_NAME", "postgres")
SUPABASE_DB_USER = os.getenv("SUPABASE_DB_USER", "postgres.dvusiqfijdmjcsubyapw")
SUPABASE_DB_PASSWORD = os.getenv("SUPABASE_DB_PASSWORD")
SUPABASE_SSL_CERT = os.getenv("SUPABASE_SSL_CERT", "prod-ca-2021.crt")

# API configuration
API_PREFIX = os.getenv("API_PREFIX", "/api/v1")
DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1", "t")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# Security
SECRET_KEY = os.getenv("SECRET_KEY", "temporarysecretkey123456789")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "logs/quantdb.log")

# External services
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")

# Indices configuration
INDEX_CONFIG = {
    # "000300": "沪深300",
    # "000905": "中证500", # 中证小盘500指数
    # "000904": "中证200", # 中证中盘200指数
    # "000903": "中证100",
    # "000852": "中证1000",
    # "932000": "中证2000",
    # "000699": "科创200",
    # "000698": "科创100",
    # "000688": "科创50",
    # "399006": "创业板指",
    # "000001": "上证指数",
    "399001": "深证成指",
    # Hong Kong major indexes for demo
    "HSI": "恒生指数",
    "HSCEI": "恒生中国企业指数",
    "HSTECH": "恒生科技指数",
}


# Function to convert index config to list of dictionaries
def indices_to_list(config):
    return [
        {
            "code": code,
            "name": name,
            "csv": f"{code}_{name.replace(' ', '_').lower()}.csv",
        }
        for code, name in config.items()
    ]


# Get the list of indices
INDICES = indices_to_list(INDEX_CONFIG)
